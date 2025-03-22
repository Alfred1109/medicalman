"""
设置控制器模块
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app.controllers.auth import login_required, role_required
from app.models.database import Database
from app.models.user import User
import traceback
import os
import json

# 创建蓝图
settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
@login_required
@role_required('admin')
def index():
    """设置页面"""
    return render_template('settings.html')

@settings_bp.route('/user-management')
@login_required
@role_required('admin')
def user_management():
    """用户管理页面"""
    return render_template('user-management.html')

@settings_bp.route('/help')
@login_required
def help():
    """帮助与反馈页面"""
    return render_template('help.html')

@settings_bp.route('/feedback')
@login_required
def feedback():
    """用户反馈页面"""
    return render_template('feedback.html')

@settings_bp.route('/logs')
@login_required
@role_required('admin')
def logs():
    """系统日志页面"""
    return render_template('logs.html')

@settings_bp.route('/api/settings/system', methods=['GET'])
@login_required
@role_required('admin')
def get_system_settings():
    """获取系统设置"""
    try:
        # 从配置文件加载设置
        settings_file = os.path.join('config', 'settings.json')
        
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        else:
            # 默认设置
            settings = {
                "general": {
                    "site_name": "医疗管理系统",
                    "logo_url": "/static/img/logo.png",
                    "language": "zh_CN"
                },
                "security": {
                    "password_expiry_days": 90,
                    "session_timeout_minutes": 30,
                    "login_attempts_before_lockout": 5
                },
                "notifications": {
                    "email_alerts": True,
                    "browser_notifications": True
                }
            }
        
        return jsonify(success=True, data=settings)
        
    except Exception as e:
        return jsonify(success=False, error=str(e))
        
@settings_bp.route('/api/settings/system', methods=['POST'])
@login_required
@role_required('admin')
def update_system_settings():
    """更新系统设置"""
    try:
        data = request.get_json()
        
        # 确保配置目录存在
        os.makedirs('config', exist_ok=True)
        
        # 保存到配置文件
        settings_file = os.path.join('config', 'settings.json')
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        return jsonify(success=True, message="设置已更新")
        
    except Exception as e:
        return jsonify(success=False, error=str(e))

@settings_bp.route('/api/settings/users', methods=['GET'])
@login_required
@role_required('admin')
def get_users():
    """获取所有用户"""
    try:
        users = User.get_all_users()
        
        # 转换为JSON格式
        user_list = []
        for user in users:
            user_list.append({
                'id': user.user_id,
                'username': user.username,
                'role': user.role,
                'email': user.email,
                'department': user.department
            })
        
        return jsonify(success=True, data=user_list)
        
    except Exception as e:
        error_message = f"获取用户列表时出错: {str(e)}"
        traceback.print_exc()
        
        return jsonify(success=False, error=error_message)

@settings_bp.route('/api/settings/users', methods=['POST'])
@login_required
@role_required('admin')
def create_user():
    """创建用户"""
    try:
        # 获取请求数据
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'user')
        email = data.get('email', '')
        department = data.get('department', '')
        
        # 验证必填字段
        if not username or not password:
            return jsonify(success=False, error="用户名和密码不能为空")
        
        # 创建用户
        success, error_message = User.register(username, password, email, department, role)
        
        if success:
            return jsonify(success=True, message="用户创建成功")
        else:
            return jsonify(success=False, error=error_message)
            
    except Exception as e:
        error_message = f"创建用户时出错: {str(e)}"
        traceback.print_exc()
        
        return jsonify(success=False, error=error_message)

@settings_bp.route('/api/settings/users/<int:user_id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_user(user_id):
    """更新用户"""
    try:
        # 获取用户
        user = User.get_by_id(user_id)
        
        if not user:
            return jsonify(success=False, error="用户不存在")
        
        # 获取请求数据
        data = request.get_json()
        
        # 更新用户信息
        if 'username' in data:
            user.username = data['username']
        
        if 'password' in data and data['password']:
            user.password_hash = User.hash_password(data['password'])
        
        if 'role' in data:
            user.role = data['role']
        
        if 'email' in data:
            user.email = data['email']
        
        if 'department' in data:
            user.department = data['department']
        
        # 保存用户
        if user.save():
            return jsonify(success=True, message="用户更新成功")
        else:
            return jsonify(success=False, error="用户更新失败")
            
    except Exception as e:
        error_message = f"更新用户时出错: {str(e)}"
        traceback.print_exc()
        
        return jsonify(success=False, error=error_message)

@settings_bp.route('/api/settings/users/<int:user_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_user(user_id):
    """删除用户"""
    try:
        # 获取用户
        user = User.get_by_id(user_id)
        
        if not user:
            return jsonify(success=False, error="用户不存在")
        
        # 执行删除
        query = "DELETE FROM users WHERE id = ?"
        affected_rows = Database.execute_update(query, (user_id,))
        
        if affected_rows > 0:
            return jsonify(success=True, message="用户删除成功")
        else:
            return jsonify(success=False, error="用户删除失败")
            
    except Exception as e:
        error_message = f"删除用户时出错: {str(e)}"
        traceback.print_exc()
        
        return jsonify(success=False, error=error_message)

@settings_bp.route('/api/settings/backup', methods=['POST'])
@login_required
@role_required('admin')
def backup_database():
    """备份数据库"""
    try:
        # 获取数据库路径
        db_path = "medical_workload.db"
        
        # 创建备份目录
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        # 生成备份文件名
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/medical_workload_{timestamp}.db"
        
        # 复制数据库文件
        import shutil
        shutil.copy2(db_path, backup_file)
        
        return jsonify(
            success=True,
            message="数据库备份成功",
            backup_file=backup_file
        )
            
    except Exception as e:
        error_message = f"备份数据库时出错: {str(e)}"
        traceback.print_exc()
        
        return jsonify(success=False, error=error_message)

@settings_bp.route('/api/settings/restore', methods=['POST'])
@login_required
@role_required('admin')
def restore_database():
    """恢复数据库"""
    try:
        # 获取请求数据
        data = request.get_json()
        backup_file = data.get('backup_file')
        
        if not backup_file:
            return jsonify(success=False, error="未指定备份文件")
        
        # 检查备份文件是否存在
        if not os.path.exists(backup_file):
            return jsonify(success=False, error="备份文件不存在")
        
        # 获取数据库路径
        db_path = "medical_workload.db"
        
        # 复制备份文件到数据库文件
        import shutil
        shutil.copy2(backup_file, db_path)
        
        return jsonify(
            success=True,
            message="数据库恢复成功"
        )
            
    except Exception as e:
        error_message = f"恢复数据库时出错: {str(e)}"
        traceback.print_exc()
        
        return jsonify(success=False, error=error_message) 