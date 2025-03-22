import io
import random
import string
from PIL import Image, ImageDraw, ImageFont

# 验证码配置
CAPTCHA_CHARS = string.ascii_uppercase + string.digits
CAPTCHA_LENGTH = 4
CAPTCHA_WIDTH = 120
CAPTCHA_HEIGHT = 40

def generate_captcha():
    """
    生成验证码图像
    
    返回:
        tuple: (验证码文本, 图像IO对象)
    """
    # 创建图像
    image = Image.new('RGB', (CAPTCHA_WIDTH, CAPTCHA_HEIGHT), color='white')
    draw = ImageDraw.Draw(image)
    
    # 生成随机字符
    captcha_text = ''.join(random.choice(CAPTCHA_CHARS) for _ in range(CAPTCHA_LENGTH))
    
    # 添加字符到图像
    font_size = 30
    try:
        font = ImageFont.truetype('static/fonts/Arial.ttf', font_size)
    except:
        font = ImageFont.load_default()
    
    # 计算文字位置使其居中
    text_width = font.getlength(captcha_text)
    text_height = font_size
    x = (CAPTCHA_WIDTH - text_width) / 2
    y = (CAPTCHA_HEIGHT - text_height) / 2
    
    # 绘制文字
    draw.text((x, y), captcha_text, font=font, fill='black')
    
    # 添加干扰线
    for _ in range(5):
        x1 = random.randint(0, CAPTCHA_WIDTH)
        y1 = random.randint(0, CAPTCHA_HEIGHT)
        x2 = random.randint(0, CAPTCHA_WIDTH)
        y2 = random.randint(0, CAPTCHA_HEIGHT)
        draw.line([(x1, y1), (x2, y2)], fill='gray')
    
    # 添加噪点
    for _ in range(50):
        x = random.randint(0, CAPTCHA_WIDTH)
        y = random.randint(0, CAPTCHA_HEIGHT)
        draw.point((x, y), fill='gray')
    
    # 将图像保存到内存中
    image_io = io.BytesIO()
    image.save(image_io, 'PNG')
    image_io.seek(0)
    
    return captcha_text, image_io 