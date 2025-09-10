import io
import random
import string
from PIL import Image, ImageDraw, ImageFont

# 验证码配置
CAPTCHA_CHARS = string.ascii_uppercase + string.digits
CAPTCHA_LENGTH = 4
CAPTCHA_WIDTH = 200
CAPTCHA_HEIGHT = 80

def generate_captcha():
    """
    生成验证码图像
    
    返回:
        tuple: (验证码文本, 图像IO对象)
    """
    # 创建图像 - 使用浅灰色背景提高对比度
    image = Image.new('RGB', (CAPTCHA_WIDTH, CAPTCHA_HEIGHT), color=(245, 245, 245))
    draw = ImageDraw.Draw(image)
    
    # 生成随机字符
    captcha_text = ''.join(random.choice(CAPTCHA_CHARS) for _ in range(CAPTCHA_LENGTH))
    
    # 添加字符到图像
    font_size = 50
    try:
        # 尝试使用项目中的字体文件
        import os
        font_path = os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'fonts', 'Arial.ttf')
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, font_size)
        else:
            # 尝试系统字体
            font = ImageFont.truetype('arial.ttf', font_size)
    except:
        try:
            # 尝试系统默认字体
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size)
        except:
            # 使用默认字体但设置更大的尺寸
            font = ImageFont.load_default()
    
    # 计算文字位置使其居中
    text_width = font.getlength(captcha_text)
    text_height = font_size
    x = (CAPTCHA_WIDTH - text_width) / 2
    y = (CAPTCHA_HEIGHT - text_height) / 2
    
    # 绘制文字 - 使用深蓝色，更容易识别
    draw.text((x, y), captcha_text, font=font, fill=(0, 0, 139))
    
    # 添加干扰线 - 减少数量，使用更淡的颜色
    for _ in range(3):
        x1 = random.randint(0, CAPTCHA_WIDTH)
        y1 = random.randint(0, CAPTCHA_HEIGHT)
        x2 = random.randint(0, CAPTCHA_WIDTH)
        y2 = random.randint(0, CAPTCHA_HEIGHT)
        draw.line([(x1, y1), (x2, y2)], fill=(200, 200, 200), width=1)
    
    # 添加噪点 - 减少数量，使用更淡的颜色
    for _ in range(30):
        x = random.randint(0, CAPTCHA_WIDTH)
        y = random.randint(0, CAPTCHA_HEIGHT)
        draw.point((x, y), fill=(220, 220, 220))
    
    # 将图像保存到内存中
    image_io = io.BytesIO()
    image.save(image_io, 'PNG')
    image_io.seek(0)
    
    return captcha_text, image_io 