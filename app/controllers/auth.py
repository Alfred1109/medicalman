"""
认证控制器模块
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, make_response
from flask_login import login_user, logout_user, login_required, current_user
from app.services.auth_service import AuthService
from app.models.user import User
from functools import wraps
from app.utils.validators import Validators
from app.extensions import db
import hashlib
import random
import string

# 创建蓝图
auth_bp = Blueprint('auth', __name__)

# 认证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AuthService.is_authenticated():
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# 角色装饰器
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not AuthService.is_authenticated():
                return redirect(url_for('auth.login', next=request.url))
            
            current_user = AuthService.get_current_user()
            if current_user and current_user.get('role') != role:
                flash('您没有权限访问此页面', 'error')
                return redirect(url_for('dashboard.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def generate_captcha():
    """生成随机验证码"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

# 登录页面
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        # 生成验证码并存储在会话中
        captcha = generate_captcha()
        session['captcha'] = captcha
        return render_template('login.html')
    
    # 处理AJAX登录请求
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '无效的请求数据'})
    
    username = data.get('username')
    password = data.get('password')
    captcha = data.get('captcha')
    
    # 验证验证码
    if not captcha or captcha.upper() != session.get('captcha', '').upper():
        return jsonify({'success': False, 'message': '验证码错误'})
    
    # 查找用户
    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return jsonify({'success': False, 'message': '用户名或密码错误'})
    
    # 登录用户
    login_user(user)
    
    # 生成新的验证码
    session['captcha'] = generate_captcha()
    
    return jsonify({
        'success': True,
        'message': '登录成功',
        'redirect': url_for('dashboard.index')
    })

# 登出
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已成功退出登录。', 'success')
    return redirect(url_for('auth.login'))

# 注册页面
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    # 处理注册请求
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '无效的请求数据'})
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    department = data.get('department')
    
    # 验证用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': '用户名已存在'})
    
    # 验证邮箱是否已存在
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': '邮箱已被注册'})
    
    # 创建新用户
    user = User(username=username, email=email, department=department)
    user.set_password(password)
    
    # 如果是第一个用户，设置为管理员
    if User.query.count() == 0:
        user.is_admin = True
    
    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '注册成功',
            'redirect': url_for('auth.login')
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': '注册失败，请稍后重试'})

# 生成验证码
@auth_bp.route('/captcha')
def captcha():
    """生成验证码"""
    # 大幅增大验证码尺寸
    width = 240
    height = 100
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    length = 4
    
    captcha_text, captcha_image = AuthService.generate_captcha(width, height, chars, length)
    
    # 将验证码文本存储在会话中
    session['captcha'] = captcha_text
    
    # 返回验证码图片
    response = make_response(captcha_image)
    response.headers.set('Content-Type', 'image/png')
    return response

# 用户信息
@auth_bp.route('/user-info')
@login_required
def user_info():
    """获取当前用户信息"""
    user_info = AuthService.get_current_user()
    return jsonify(user_info)

# 用户个人资料页面
@auth_bp.route('/profile')
@login_required
def profile():
    """用户个人资料页面"""
    user_info = AuthService.get_current_user()
    return render_template('profile.html', user=user_info) 