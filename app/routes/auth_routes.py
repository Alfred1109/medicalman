"""
认证路由模块 - 处理用户认证相关的路由
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app, jsonify, Response
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import traceback
from functools import wraps
import random
import string
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import secrets
import logging
import json
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

from app.utils.database import db_cursor
from app.utils.security import verify_captcha, generate_captcha
from app.utils.logger import log_user_login, log_error

# 创建蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# API请求登录验证装饰器
def api_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': '未授权访问', 'code': 401}), 401
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        # 判断是否为AJAX请求
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # AJAX请求处理
        if is_ajax:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            captcha = data.get('captcha')
            
            # 输出调试信息
            current_app.logger.info(f"收到登录请求: 用户名={username}, 验证码={captcha}")
            current_app.logger.info(f"会话中的验证码: {session.get('captcha', '无')}")
            
            # 验证码验证
            if not captcha or captcha.upper() != session.get('captcha', '').upper():
                current_app.logger.warning(f"验证码不匹配: 输入={captcha}, 会话中={session.get('captcha', '无')}")
                return jsonify({'success': False, 'message': '验证码错误'})
        else:
            # 表单提交处理
            username = request.form.get('username')
            password = request.form.get('password')
        
        # 简单的验证
        if not username or not password:
            if is_ajax:
                return jsonify({'success': False, 'message': '请输入用户名和密码'})
            else:
                flash('请输入用户名和密码')
                return render_template('auth/login.html')
        
        try:
            # 连接数据库
            db_path = current_app.config.get('DATABASE_PATH', 'instance/medical_workload.db')
            current_app.logger.info(f"尝试连接数据库: {db_path}")
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 查询用户
            query = 'SELECT * FROM users WHERE username = ?'
            current_app.logger.info(f"执行查询: {query} 参数: {username}")
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            
            if user:
                current_app.logger.info(f"找到用户: {username}")
                password_match = check_password_hash(user['password_hash'], password)
                current_app.logger.info(f"密码验证结果: {password_match}")
                
                if password_match:
                    # 登录成功
                    session.clear()
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['role'] = user['role']
                    
                    # 生成新的验证码
                    session['captcha'] = ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=4))
                    current_app.logger.info(f"登录成功，新验证码: {session['captcha']}")
                    
                    if is_ajax:
                        return jsonify({
                            'success': True,
                            'message': '登录成功',
                            'redirect': url_for('main.dashboard')
                        })
                    else:
                        return redirect(url_for('main.dashboard'))
                else:
                    current_app.logger.warning(f"密码错误: {username}")
                    if is_ajax:
                        return jsonify({'success': False, 'message': '用户名或密码错误'})
                    else:
                        flash('用户名或密码错误')
            else:
                current_app.logger.warning(f"未找到用户: {username}")
                if is_ajax:
                    return jsonify({'success': False, 'message': '用户名或密码错误'})
                else:
                    flash('用户名或密码错误')
                    
        except Exception as e:
            current_app.logger.error(f'登录出错: {str(e)}')
            current_app.logger.error(traceback.format_exc())
            
            if is_ajax:
                return jsonify({'success': False, 'message': '登录时发生错误，请稍后重试'})
            else:
                flash('登录时发生错误，请稍后重试')
        finally:
            if 'conn' in locals() and conn:
                conn.close()
                current_app.logger.info("数据库连接已关闭")
    
    # 生成验证码
    if 'captcha' not in session:
        session['captcha'] = ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=4))
        current_app.logger.info(f"为登录页生成新验证码: {session['captcha']}")
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    """登出"""
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if request.method == 'POST':
        # 判断是否为AJAX请求
        is_ajax = request.is_json
        
        if is_ajax:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            email = data.get('email')
            department = data.get('department')
            captcha = data.get('captcha')
            
            # 验证码验证
            if not captcha or captcha.upper() != session.get('captcha', '').upper():
                return jsonify({'success': False, 'message': '验证码错误'})
                
            # 验证字段
            if not username or not password or not email:
                return jsonify({'success': False, 'message': '所有带*的字段都是必填的'})
        else:
            # 表单提交处理
            username = request.form.get('username')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            # 简单的验证
            if not username or not password:
                flash('请输入用户名和密码')
                return render_template('auth/register.html')
            
            if password != confirm_password:
                flash('两次输入的密码不一致')
                return render_template('auth/register.html')
        
        try:
            # 连接数据库
            db_path = current_app.config.get('DATABASE_PATH', 'instance/medical_workload.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 检查用户名是否已存在
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                if is_ajax:
                    return jsonify({'success': False, 'message': '用户名已存在'})
                else:
                    flash('用户名已存在')
                    return render_template('auth/register.html')
            
            # 检查邮箱是否已存在（如果是AJAX请求并且提供了邮箱）
            if is_ajax and email:
                cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
                if cursor.fetchone():
                    return jsonify({'success': False, 'message': '邮箱已被注册'})
            
            # 注册新用户
            hashed_password = generate_password_hash(password)
            
            if is_ajax and email and department:
                cursor.execute(
                    'INSERT INTO users (username, password_hash, email, department, role) VALUES (?, ?, ?, ?, ?)',
                    (username, hashed_password, email, department, 'user')
                )
            else:
                cursor.execute(
                    'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
                    (username, hashed_password, 'user')
                )
                
            conn.commit()
            
            if is_ajax:
                return jsonify({
                    'success': True,
                    'message': '注册成功，请登录',
                    'redirect': url_for('auth.login')
                })
            else:
                flash('注册成功，请登录')
                return redirect(url_for('auth.login'))
            
        except Exception as e:
            current_app.logger.error(f'注册出错: {str(e)}')
            traceback.print_exc()
            
            if is_ajax:
                return jsonify({'success': False, 'message': '注册时发生错误，请稍后重试'})
            else:
                flash('注册时发生错误，请稍后重试')
        finally:
            if conn:
                conn.close()
    
    return render_template('auth/register.html')

@auth_bp.route('/captcha')
def captcha():
    """生成验证码"""
    # 验证码图片尺寸
    width = 240
    height = 100
    
    # 生成随机验证码文本
    chars = string.ascii_uppercase + string.digits
    captcha_text = ''.join(random.choices(chars, k=4))
    
    # 保存验证码到会话
    session['captcha'] = captcha_text
    
    # 创建图片
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # 尝试加载字体
    try:
        font = ImageFont.truetype('arial.ttf', 70)
    except IOError:
        try:
            font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 70)
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
        char_x = x + i * (text_width // 4)
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
    
    # 返回响应
    return Response(out.getvalue(), mimetype='image/png')

@auth_bp.route('/profile')
@login_required
def profile():
    """用户个人资料页面"""
    user_id = session.get('user_id')
    
    # 从数据库获取完整的用户信息
    user = None
    try:
        with db_cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
    except Exception as e:
        current_app.logger.error(f"查询用户信息失败: {str(e)}")
        flash("无法获取用户信息", "danger")
    
    if not user:
        flash("用户信息不存在", "danger")
        return redirect(url_for('auth.login'))
    
    # 用户信息
    user_info = {
        'id': user.get('id'),
        'username': user.get('username'),
        'role': user.get('role'),
        'email': user.get('email', '')
    }
    
    return render_template('auth/profile.html', user=user_info) 