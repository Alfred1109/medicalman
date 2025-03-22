from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """
    检查当前用户是否为管理员的装饰器
    如果不是管理员，则重定向到首页
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('请先登录。', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('您没有权限访问此页面。', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission):
    """
    检查当前用户是否具有特定权限的装饰器
    如果没有权限，则返回403错误
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('请先登录。', 'warning')
                return redirect(url_for('auth.login'))
            if not current_user.has_permission(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator 