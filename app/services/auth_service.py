"""
认证服务模块
"""
from typing import Dict, Any, Optional, Tuple
from flask import session
import string
import random
from PIL import Image, ImageDraw, ImageFont
import io
from app.models.user import User
from app.config import config
import os

class AuthService:
    """认证服务类"""
    
    @staticmethod
    def login(username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        用户登录
        
        参数:
            username: 用户名
            password: 密码
            
        返回:
            如果登录成功，返回用户信息；否则返回None
        """
        # 获取用户
        user = User.get_by_username(username)
        
        # 验证用户和密码
        if user and user.check_password(password):
            # 设置会话
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['department'] = user.department
            
            # 返回用户信息
            return user.to_dict()
        
        # 登录失败
        return None
    
    @staticmethod
    def logout() -> bool:
        """
        用户登出
        
        返回:
            登出是否成功
        """
        try:
            # 清除会话
            session.pop('user_id', None)
            session.pop('username', None)
            session.pop('role', None)
            session.pop('department', None)
            return True
        except Exception as e:
            print(f"登出时出错: {str(e)}")
            return False
    
    @staticmethod
    def register(username: str, password: str, email: str, 
                 department: str, role: str = 'user') -> Tuple[bool, Optional[str]]:
        """
        注册新用户
        
        参数:
            username: 用户名
            password: 密码
            email: 电子邮件
            department: 所属科室
            role: 用户角色，默认为'user'
            
        返回:
            (注册是否成功, 错误信息)
        """
        # 检查用户名是否已存在
        existing_user = User.get_by_username(username)
        if existing_user:
            return False, "用户名已存在"
        
        # 创建新用户
        from app.extensions import db
        try:
            new_user = User(username=username, email=email, department=department, role=role)
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            print(f"注册用户时出错: {str(e)}")
            return False, "注册失败，请稍后再试"
    
    @staticmethod
    def is_authenticated() -> bool:
        """
        检查用户是否已认证
        
        返回:
            用户是否已认证
        """
        return 'user_id' in session
    
    @staticmethod
    def get_current_user() -> Optional[Dict[str, Any]]:
        """
        获取当前登录用户信息
        
        返回:
            当前用户信息，如果未登录则返回None
        """
        if not AuthService.is_authenticated():
            return None
        
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if not user:
            # 会话中有用户ID但找不到用户，清除会话
            AuthService.logout()
            return None
        
        return user.to_dict()
    
    @staticmethod
    def generate_captcha(width: int, height: int, chars: str, length: int) -> Tuple[str, bytes]:
        """
        生成验证码
        
        参数:
            width: 图片宽度
            height: 图片高度
            chars: 验证码字符集
            length: 验证码长度
            
        返回:
            (验证码文本, 验证码图片字节)
        """
        # 生成随机验证码文本
        captcha_text = ''.join(random.choice(chars) for _ in range(length))
        
        # 创建图片 - 使用浅蓝色背景以提高对比度
        image = Image.new('RGB', (width, height), color=(240, 248, 255))
        draw = ImageDraw.Draw(image)
        
        # 尝试加载字体，如果失败则使用默认字体
        try:
            # 从配置中获取字体路径
            font_path = config.CAPTCHA_FONT_PATH
            if font_path and os.path.exists(font_path):
                font = ImageFont.truetype(font_path, 45)
            else:
                # 尝试加载系统字体
                system_font_path = config.CAPTCHA_SYSTEM_FONT_PATH
                if system_font_path and os.path.exists(system_font_path):
                    font = ImageFont.truetype(system_font_path, 45)
                else:
                    # 如果无法加载指定字体，使用默认字体
                    font = ImageFont.load_default()
        except Exception as e:
            print(f"加载字体时出错: {str(e)}")
            font = ImageFont.load_default()
        
        # 计算单个字符的平均宽度
        try:
            # 对于较新版本的Pillow
            left, top, right, bottom = draw.textbbox((0, 0), "A", font=font)
            char_width = right - left
        except AttributeError:
            # 对于较旧版本的Pillow
            char_width, _ = draw.textsize("A", font=font)
        
        # 计算总宽度，包括字符间距
        total_width = char_width * length + (length - 1) * 10  # 10像素的间距
        
        # 计算起始x坐标，使文本居中
        start_x = (width - total_width) // 2
        
        # 逐个绘制字符，增加间距
        for i, char in enumerate(captcha_text):
            # 计算当前字符的x坐标
            x = start_x + i * (char_width + 10)  # 10像素的间距
            
            # 随机y轴偏移，使字符高度不同
            y_offset = random.randint(-10, 10)
            y = (height - char_width) // 2 + y_offset
            
            # 使用深蓝色绘制文本
            draw.text((x, y), char, font=font, fill=(0, 0, 128))
        
        # 添加少量干扰点，但不影响可读性
        for _ in range(30):
            x = random.randint(0, width)
            y = random.randint(0, height)
            draw.point((x, y), fill=(169, 169, 169))  # 使用浅灰色
        
        # 将图片转换为字节
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        return captcha_text, img_byte_arr 