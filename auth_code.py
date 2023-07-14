from captcha.image import ImageCaptcha
from flask import url_for, session
import random


def generate_captcha(code_length):
    # 生成隨機數字
    code = ''.join(random.choices('02345689', k=code_length))

    # 創建驗證碼圖像
    captcha = ImageCaptcha()
    image = captcha.generate(code)

    # 保存驗證碼圖像到資料夾，格式為 JPG
    image_file = 'captcha_img.png'
    captcha.write(code, f'static/{image_file}')
    image_url = url_for('static', filename=image_file)

    return image_url, code
