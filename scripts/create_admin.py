#!/usr/bin/env python
"""
创建管理员用户脚本
"""
import os
import sys

# 添加父目录到sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from app import create_app
from app.models.user import User
from app.extensions import db

def create_admin_user():
    """创建管理员用户"""
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com', is_admin=True)
            admin.set_password('Admin123!')
            db.session.add(admin)
            db.session.commit()
            print('管理员用户已创建')
        else:
            print('管理员用户已存在')

if __name__ == '__main__':
    create_admin_user() 