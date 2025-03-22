"""
安全工具模块
"""
import hashlib
import os
import re
import secrets
from typing import Tuple, Optional

class Security:
    """安全工具类"""
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """
        生成安全令牌
        
        参数:
            length: 令牌长度
            
        返回:
            安全令牌
        """
        return secrets.token_hex(length // 2)
    
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
    
    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """
        清理输入字符串，防止XSS攻击
        
        参数:
            input_str: 输入字符串
            
        返回:
            清理后的字符串
        """
        # 替换HTML特殊字符
        sanitized = input_str.replace('&', '&amp;')
        sanitized = sanitized.replace('<', '&lt;')
        sanitized = sanitized.replace('>', '&gt;')
        sanitized = sanitized.replace('"', '&quot;')
        sanitized = sanitized.replace("'", '&#x27;')
        
        return sanitized
    
    @staticmethod
    def is_safe_path(path: str) -> bool:
        """
        检查路径是否安全，防止路径遍历攻击
        
        参数:
            path: 文件路径
            
        返回:
            路径是否安全
        """
        # 检查是否包含路径遍历模式
        if '..' in path or '//' in path:
            return False
        
        # 检查是否是绝对路径
        if path.startswith('/') or path.startswith('\\'):
            return False
        
        # 检查是否包含危险字符
        if re.search(r'[<>:"|?*]', path):
            return False
        
        return True
    
    @staticmethod
    def validate_sql_query(query: str) -> bool:
        """
        验证SQL查询是否安全
        
        参数:
            query: SQL查询语句
            
        返回:
            查询是否安全
        """
        # 检查是否包含危险操作
        dangerous_keywords = [
            "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", 
            "TRUNCATE", "GRANT", "REVOKE", "ATTACH", "DETACH"
        ]
        
        # 将查询转换为大写以便检查关键字
        query_upper = query.upper()
        
        # 检查是否包含危险关键字
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return False
        
        return True 