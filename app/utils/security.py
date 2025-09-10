"""
安全工具模块
"""
import hashlib
import os
import re
import secrets
from typing import Tuple, Optional
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

class Security:
    """安全工具类"""
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """
        生成安全令牌
        
        参数:
            length: 令牌长度
            
        返回:
            安全令牌
        """
        return secrets.token_hex(length // 2)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        对密码进行哈希处理
        
        参数:
            password: 原始密码
            
        返回:
            密码哈希值
        """
        salt = os.urandom(32)  # 生成随机盐值
        key = hashlib.pbkdf2_hmac(
            'sha256',  # 使用的哈希算法
            password.encode('utf-8'),  # 将密码转换为字节
            salt,  # 盐值
            100000,  # 迭代次数
            dklen=128  # 派生密钥长度
        )
        # 将盐值和密钥组合存储
        return salt.hex() + ':' + key.hex()
    
    @staticmethod
    def verify_password(stored_password: str, provided_password: str) -> bool:
        """
        验证密码
        
        参数:
            stored_password: 存储的密码哈希
            provided_password: 提供的密码
            
        返回:
            密码是否匹配
        """
        salt_hex, key_hex = stored_password.split(':')
        salt = bytes.fromhex(salt_hex)
        stored_key = bytes.fromhex(key_hex)
        
        # 使用相同的参数计算提供密码的哈希
        key = hashlib.pbkdf2_hmac(
            'sha256',
            provided_password.encode('utf-8'),
            salt,
            100000,
            dklen=128
        )
        
        return key == stored_key
    
    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """
        清理输入字符串，防止XSS攻击
        
        参数:
            input_str: 输入字符串
            
        返回:
            清理后的字符串
        """
        # 替换HTML特殊字符
        sanitized = input_str.replace('&', '&amp;')
        sanitized = sanitized.replace('<', '&lt;')
        sanitized = sanitized.replace('>', '&gt;')
        sanitized = sanitized.replace('"', '&quot;')
        sanitized = sanitized.replace("'", '&#x27;')
        
        return sanitized
    
    @staticmethod
    def is_safe_path(path: str) -> bool:
        """
        检查路径是否安全，防止路径遍历攻击
        
        参数:
            path: 文件路径
            
        返回:
            路径是否安全
        """
        # 检查是否包含路径遍历模式
        if '..' in path or '//' in path:
            return False
        
        # 检查是否是绝对路径
        if path.startswith('/') or path.startswith('\\'):
            return False
        
        # 检查是否包含危险字符
        if re.search(r'[<>:"|?*]', path):
            return False
        
        return True
    
    @staticmethod
    def validate_sql_query(query: str) -> bool:
        """
        验证SQL查询是否安全
        
        参数:
            query: SQL查询语句
            
        返回:
            查询是否安全
        """
        # 检查是否包含危险操作
        dangerous_keywords = [
            "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", 
            "TRUNCATE", "GRANT", "REVOKE", "ATTACH", "DETACH"
        ]
        
        # 将查询转换为大写以便检查关键字
        query_upper = query.upper()
        
        # 检查是否包含危险关键字
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return False
        
        return True

def generate_captcha(width=300, height=120, length=4):
    """
    生成图形验证码
    
    参数:
        width: 图片宽度
        height: 图片高度
        length: 验证码长度
        
    返回:
        (验证码文本, 图片二进制数据)
    """
    # 生成随机验证码文本
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    captcha_text = ''.join(random.choices(chars, k=length))
    
    # 创建图片 - 使用浅灰色背景提高对比度
    image = Image.new('RGB', (width, height), color=(245, 245, 245))
    draw = ImageDraw.Draw(image)
    
    # 尝试加载字体 - 增大字体大小
    try:
        font = ImageFont.truetype('arial.ttf', 80)
    except IOError:
        try:
            font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 80)
        except IOError:
            try:
                # 尝试Linux系统字体
                font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 80)
            except IOError:
                font = ImageFont.load_default()
    
    # 绘制文本
    try:
        # 较新的Pillow版本
        if hasattr(font, 'getbbox'):
            bbox = font.getbbox(captcha_text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        # 较旧版本
        elif hasattr(draw, 'textsize'):
            text_width, text_height = draw.textsize(captcha_text, font=font)
        else:
            # 默认情况
            text_width, text_height = width-40, height-40
    except Exception:
        text_width, text_height = width-40, height-40
        
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # 添加干扰线
    for i in range(8):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(200, 200, 200), width=2)
    
    # 绘制字符
    for i, char in enumerate(captcha_text):
        char_x = x + i * (text_width // length)
        char_y = y + random.randint(-10, 10)
        draw.text((char_x, char_y), char, font=font, fill=(0, 0, 139))
    
    # 添加干扰点
    for _ in range(100):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=(220, 220, 220))
    
    # 将图片保存到字节流
    out = BytesIO()
    image.save(out, 'PNG')
    out.seek(0)
    
    return captcha_text, out.getvalue()

def verify_captcha(user_input, stored_captcha):
    """
    验证用户输入的验证码
    
    参数:
        user_input: 用户输入的验证码
        stored_captcha: 存储的验证码
        
    返回:
        验证结果(布尔值)
    """
    if not user_input or not stored_captcha:
        return False
        
    return user_input.upper() == stored_captcha.upper() 