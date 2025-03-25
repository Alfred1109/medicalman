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
from flask_wtf.csrf import CSRFProtect

from app.utils.database import db_cursor
from app.utils.security import verify_captcha, generate_captcha
from app.utils.logger import log_user_login, log_error, log_auth_activity
from app.config import config
from app.models.user import User
from app import db

# 创建蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# 创建 CSRF 保护实例
csrf = CSRFProtect()

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
@csrf.exempt  # 豁免CSRF验证
def login():
    """
    处理用户登录请求
    
    GET: 显示登录页面
    POST: 处理登录表单提交
    """
    # 如果用户已登录，重定向到仪表盘
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    
    # 获取next参数，如果没有则默认为仪表盘
    next_url = request.args.get('next') or request.form.get('next')
    if not next_url or not next_url.startswith('/'):
        next_url = url_for('dashboard.index')
    
    if request.method == 'GET':
        return render_template('auth/login.html', next=next_url)
    
    # 处理POST请求
    try:
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        captcha = data.get('captcha')
        
        # 验证码校验
        if not captcha or captcha.lower() != session.get('captcha', '').lower():
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': '验证码错误'
                })
            flash('验证码错误', 'danger')
            return redirect(url_for('auth.login', next=next_url))
        
        # 查找用户
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # 登录成功
            login_user(user)
            session['user_id'] = user.id
            session.permanent = True  # 设置会话为永久性
            log_auth_activity(user.id, 'login', 'success')
            
            # 生成新的验证码
            generate_captcha()
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': '登录成功',
                    'redirect': next_url
                })
            return redirect(next_url)
        else:
            # 登录失败
            log_auth_activity(user.id if user else None, 'login', 'failed')
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': '用户名或密码错误'
                })
            flash('用户名或密码错误', 'danger')
            return redirect(url_for('auth.login', next=next_url))
            
    except Exception as e:
        logging.error(f"登录过程发生错误: {str(e)}")
        if request.is_json:
            return jsonify({
                'success': False,
                'message': '登录过程发生错误，请稍后重试'
            }), 500
        flash('登录过程发生错误，请稍后重试', 'danger')
        return redirect(url_for('auth.login', next=next_url))

@auth_bp.route('/logout')
@login_required
def logout():
    """处理用户登出请求"""
    user_id = current_user.id
    logout_user()
    log_auth_activity(user_id, 'logout', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """处理用户注册请求"""
    if request.method == 'GET':
        return render_template('auth/register.html')
    
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({
                'success': False,
                'message': '用户名已存在'
            })
        
        # 创建新用户
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        log_auth_activity(user.id, 'register', 'success')
        
        return jsonify({
            'success': True,
            'message': '注册成功，请登录',
            'redirect': url_for('auth.login')
        })
        
    except Exception as e:
        logging.error(f"注册过程发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '注册过程发生错误，请稍后重试'
        }), 500

@auth_bp.route('/captcha')
def captcha():
    """生成验证码"""
    # 生成验证码内容和图片
    captcha_text, captcha_image = generate_captcha()
    
    # 将验证码文本存储在会话中
    session['captcha'] = captcha_text
    
    # 返回验证码图片
    response = Response(captcha_image, mimetype='image/png')
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

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