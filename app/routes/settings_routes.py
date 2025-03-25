"""
设置路由模块 - 处理系统设置相关路由
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from app.routes.auth_routes import login_required
import datetime
from app.utils.database import db_cursor

# 创建蓝图
settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/')
@login_required
def index():
    """设置页面"""
    return render_template('settings/settings.html')

@settings_bp.route('/profile', methods=['POST'])
@login_required
def update_profile():
    """更新用户资料"""
    # 示例实现，实际需根据数据库设计修改
    if request.method == 'POST':
        # 获取表单数据
        email = request.form.get('email')
        department = request.form.get('department')
        
        # 更新用户信息
        user_id = session.get('user_id')
        try:
            with db_cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET email = ?, department = ? WHERE id = ?",
                    (email, department, user_id)
                )
            flash("个人资料更新成功", "success")
        except Exception as e:
            current_app.logger.error(f"更新用户资料失败: {str(e)}")
            flash("更新失败，请稍后重试", "danger")
            
    return redirect(url_for('settings.index'))

@settings_bp.route('/help')
@login_required
def help():
    """帮助与反馈页面"""
    return render_template('settings/help.html')

@settings_bp.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    """用户反馈页面"""
    if request.method == 'POST':
        # 获取表单数据
        feedback_type = request.form.get('type')
        title = request.form.get('title')
        content = request.form.get('content')
        
        # 保存反馈信息
        try:
            with db_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO feedback (user_id, type, title, content, created_at) VALUES (?, ?, ?, ?, ?)",
                    (session.get('user_id'), feedback_type, title, content, 
                     datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                )
            flash("感谢您的反馈，我们会尽快处理", "success")
        except Exception as e:
            current_app.logger.error(f"保存反馈信息失败: {str(e)}")
            flash("提交反馈失败，请稍后重试", "danger")
    
    return render_template('settings/feedback.html') 