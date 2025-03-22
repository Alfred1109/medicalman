"""
验证工具模块
"""
import re
from typing import Dict, Any, Optional, Tuple, List

class Validators:
    """验证工具类"""
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, Optional[str]]:
        """
        验证必填字段
        
        参数:
            data: 数据字典
            required_fields: 必填字段列表
            
        返回:
            (验证是否通过, 错误消息)
        """
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                return False, f"字段 '{field}' 不能为空"
        
        return True, None
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        验证电子邮件格式
        
        参数:
            email: 电子邮件地址
            
        返回:
            是否有效
        """
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
        """
        验证密码强度
        
        参数:
            password: 密码
            
        返回:
            (是否有效, 错误消息)
        """
        if len(password) < 8:
            return False, "密码长度必须至少为8个字符"
        
        if not re.search(r'[A-Z]', password):
            return False, "密码必须包含至少一个大写字母"
        
        if not re.search(r'[a-z]', password):
            return False, "密码必须包含至少一个小写字母"
        
        if not re.search(r'[0-9]', password):
            return False, "密码必须包含至少一个数字"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "密码必须包含至少一个特殊字符"
        
        return True, None
    
    @staticmethod
    def validate_date_format(date_str: str, format_str: str = '%Y-%m-%d') -> bool:
        """
        验证日期格式
        
        参数:
            date_str: 日期字符串
            format_str: 日期格式
            
        返回:
            是否有效
        """
        try:
            from datetime import datetime
            datetime.strptime(date_str, format_str)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_numeric(value: str) -> bool:
        """
        验证是否为数字
        
        参数:
            value: 要验证的值
            
        返回:
            是否有效
        """
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_integer(value: str) -> bool:
        """
        验证是否为整数
        
        参数:
            value: 要验证的值
            
        返回:
            是否有效
        """
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_range(value: float, min_value: float = None, max_value: float = None) -> bool:
        """
        验证数值范围
        
        参数:
            value: 要验证的值
            min_value: 最小值
            max_value: 最大值
            
        返回:
            是否有效
        """
        if min_value is not None and value < min_value:
            return False
        
        if max_value is not None and value > max_value:
            return False
        
        return True 