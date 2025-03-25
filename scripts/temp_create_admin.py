#!/usr/bin/env python
"""
临时脚本：创建管理员用户
"""
import os
import sys

# 添加父目录到sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from app import create_app, db
from app.models.user import User

def create_admin_user():
    """创建管理员用户"""
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print('管理员用户已存在，密码将被重置')
            admin.set_password('Admin123!')
        else:
            print('创建新的管理员用户')
            admin = User(username='admin', email='admin@example.com', is_admin=True, role='admin')
            admin.set_password('Admin123!')
            db.session.add(admin)
        
        db.session.commit()
        print('管理员用户已创建/更新，用户名: admin，密码: Admin123!')

if __name__ == '__main__':
    create_admin_user() 