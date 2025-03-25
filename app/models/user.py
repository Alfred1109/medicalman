"""
用户模型模块
"""
from typing import Dict, List, Any, Optional
import hashlib
import os
# 移除对已删除模块的导入
# from .database import Database
from app.extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    """用户模型类"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    department = db.Column(db.String(50))
    is_admin = db.Column(db.Boolean, default=False)
    permissions = db.Column(db.String(255), default='')  # 权限列表，以逗号分隔
    role = db.Column(db.String(20), default='user')  # 添加role字段以兼容旧代码
    
    def __init__(self, username, email, department=None, is_admin=False, role='user'):
        self.username = username
        self.email = email
        self.department = department
        self.is_admin = is_admin
        self.role = role
    
    def set_password(self, password):
        """设置用户密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证用户密码"""
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission):
        """检查用户是否具有特定权限"""
        if self.is_admin:  # 管理员拥有所有权限
            return True
        return permission in self.permissions.split(',')
    
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
        # 如果是使用werkzeug生成的密码哈希，直接使用check_password_hash
        if not stored_password.count(':'):
            return check_password_hash(stored_password, provided_password)
            
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
    
    @classmethod
    def get_by_username(cls, username: str) -> Optional['User']:
        """
        根据用户名获取用户
        
        参数:
            username: 用户名
            
        返回:
            用户对象，如果不存在则返回None
        """
        return cls.query.filter_by(username=username).first()
    
    @classmethod
    def get_by_id(cls, user_id: int) -> Optional['User']:
        """
        根据ID获取用户
        
        参数:
            user_id: 用户ID
            
        返回:
            用户对象，如果不存在则返回None
        """
        return cls.query.get(user_id)
    
    def save(self) -> bool:
        """
        保存用户到数据库
        
        返回:
            保存是否成功
        """
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"保存用户时出错: {str(e)}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将用户对象转换为字典
        
        返回:
            用户信息字典
        """
        return {
            'id': self.id,
            'user_id': self.id,  # 兼容旧代码
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'department': self.department,
            'is_admin': self.is_admin
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    """Flask-Login用户加载回调"""
    return User.query.get(int(user_id)) 