"""
用户模型模块
"""
from typing import Dict, List, Any, Optional
import hashlib
import os
from .database import Database
from app.extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    department = db.Column(db.String(50))
    is_admin = db.Column(db.Boolean, default=False)
    permissions = db.Column(db.String(255), default='')  # 权限列表，以逗号分隔
    
    def __init__(self, username, email, department=None, is_admin=False):
        self.username = username
        self.email = email
        self.department = department
        self.is_admin = is_admin
    
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
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    """Flask-Login用户加载回调"""
    return User.query.get(int(user_id))

class User:
    """用户模型类"""
    
    def __init__(self, user_id: int = None, username: str = None, 
                 password_hash: str = None, role: str = None, 
                 email: str = None, department: str = None):
        """
        初始化用户对象
        
        参数:
            user_id: 用户ID
            username: 用户名
            password_hash: 密码哈希
            role: 用户角色
            email: 电子邮件
            department: 所属科室
        """
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.email = email
        self.department = department
    
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
    def get_by_id(cls, user_id: int) -> Optional['User']:
        """
        根据ID获取用户
        
        参数:
            user_id: 用户ID
            
        返回:
            用户对象，如果不存在则返回None
        """
        query = "SELECT * FROM users WHERE id = ?"
        results = Database.execute_query(query, (user_id,))
        
        if not results:
            return None
        
        user_data = results[0]
        return cls(
            user_id=user_data['id'],
            username=user_data['username'],
            password_hash=user_data['password_hash'],
            role=user_data['role'],
            email=user_data['email'],
            department=user_data['department']
        )
    
    @classmethod
    def get_by_username(cls, username: str) -> Optional['User']:
        """
        根据用户名获取用户
        
        参数:
            username: 用户名
            
        返回:
            用户对象，如果不存在则返回None
        """
        query = "SELECT * FROM users WHERE username = ?"
        results = Database.execute_query(query, (username,))
        
        if not results:
            return None
        
        user_data = results[0]
        return cls(
            user_id=user_data['id'],
            username=user_data['username'],
            password_hash=user_data['password_hash'],
            role=user_data['role'],
            email=user_data['email'],
            department=user_data['department']
        )
    
    def save(self) -> bool:
        """
        保存用户到数据库
        
        返回:
            保存是否成功
        """
        if self.user_id:
            # 更新现有用户
            query = """
            UPDATE users 
            SET username = ?, password_hash = ?, role = ?, email = ?, department = ?
            WHERE id = ?
            """
            params = (
                self.username, self.password_hash, self.role, 
                self.email, self.department, self.user_id
            )
        else:
            # 创建新用户
            query = """
            INSERT INTO users (username, password_hash, role, email, department)
            VALUES (?, ?, ?, ?, ?)
            """
            params = (
                self.username, self.password_hash, self.role, 
                self.email, self.department
            )
        
        try:
            affected_rows = Database.execute_update(query, params)
            return affected_rows > 0
        except Exception as e:
            print(f"保存用户时出错: {str(e)}")
            return False
    
    @staticmethod
    def get_all_users() -> List['User']:
        """
        获取所有用户
        
        返回:
            用户对象列表
        """
        query = "SELECT * FROM users"
        results = Database.execute_query(query)
        
        users = []
        for user_data in results:
            user = User(
                user_id=user_data['id'],
                username=user_data['username'],
                password_hash=user_data['password_hash'],
                role=user_data['role'],
                email=user_data['email'],
                department=user_data['department']
            )
            users.append(user)
        
        return users 