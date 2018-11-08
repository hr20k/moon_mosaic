from PIL import Image, ImageDraw, ImageFont
import numpy as np
from flask import Flask, render_template, request

app = Flask(__name__)

SLICE_SIZE = 4
MOONS = ['🌕', '🌖', '🌗', '🌘', '🌑', '🌒', '🌓', '🌔']
MOON_INDEX = [4, 5, 6, 6, 2, 7, 0, 7, 3, 4, 1, 0, 2, 0, 1, 0]


def array_to_number(arr):
    return int('0b{0[0]}{0[1]}{0[2]}{0[3]}'.format([1 if i else 0 for i in arr]), 0)


def text_to_image(size, text, pixels):
    img = Image.new("L", size, 255)
    draw = ImageDraw.Draw(img)
    draw.font = ImageFont.truetype(font='fonts/KozGoPr6N-Bold.otf', size=int(SLICE_SIZE * pixels), encoding='utf-8')
    draw.text((0, 0), text)
    return img


def get_margin_size(col_max):
    top = 0
    bottom = 0
    for i in col_max:
        if i != 0:
            break
        top += 1
    for i in col_max[::-1]:
        if i != 0:
            break
        bottom += 1
    return top - 1 if top > 0 else 0, bottom - 1 if bottom > 0 else 0


def drop_margin(np_list, vertical):
    col_max = np.max(np_list, axis=1 if vertical else 0)
    top, bottom = get_margin_size(col_max)
    if top > 0:
        np_list = np_list[top:, :] if vertical else np_list[:, top:]
    if bottom > 0:
        np_list = np_list[:-bottom, :] if vertical else np_list[:, :-bottom]
    return np_list


def draw_moon_mosaic(img, size, pixels, vertical):
    np_list = np.empty((0, pixels), int)
    for y in range(0, size[1], SLICE_SIZE):
        s = np.array([])
        for x in range(0, size[0], SLICE_SIZE):
            block = img[y:y + SLICE_SIZE, x:x + SLICE_SIZE]
            col_ave = np.average(block, axis=0)
            num = array_to_number(col_ave < np.array([127.5] * 4))
            s = np.append(s, num)
        np_list = np.append(np_list, np.reshape(s, (1, pixels)), axis=0)
    np_list = drop_margin(np_list, vertical)
    return np_list


def connect_words(np_list, vertical):
    base = np_list[0]
    for word in np_list[1:]:
        base = np.vstack((base, word)) if vertical else np.hstack((base, word))
    return base


def string_to_moon(vertical, pixels, text):
    np_list = []
    for word in list(text):
        size = (SLICE_SIZE * pixels, SLICE_SIZE * pixels)
        img = text_to_image(size, word, pixels)
        np_list.append(draw_moon_mosaic(np.array(img), size, pixels, vertical))

    index_text = connect_words(np_list, vertical)
    moon_text = '\n'.join([''.join(list(map(lambda x: MOONS[MOON_INDEX[int(x)]], i))) for i in index_text])
    # print(moon_text)
    return moon_text, np.shape(index_text)[0]


@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == 'GET':
        params = {
            'vertical': False,
            'pixels': 15,
            'text': ''
        }
        return render_template('index.html', params=params)
    elif request.method == 'POST':
        params = {
            'vertical': 'vertical' in request.form,
            'pixels': int(request.form['pixels']),
            'text': request.form['text'] if 'text' in request.form else ''
        }
        out, rows = string_to_moon(params['vertical'], params['pixels'], params['text'])
        return render_template('index.html', params=params, out=out, rows=rows)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
