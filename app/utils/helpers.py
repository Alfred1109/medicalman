"""
辅助函数工具模块
"""
import os
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, date
import pandas as pd
import random
import string

class Helpers:
    """辅助函数工具类"""
    
    @staticmethod
    def get_current_date() -> str:
        """
        获取当前日期
        
        返回:
            当前日期字符串，格式为YYYY-MM-DD
        """
        return datetime.now().strftime('%Y-%m-%d')
    
    @staticmethod
    def get_current_datetime() -> str:
        """
        获取当前日期时间
        
        返回:
            当前日期时间字符串，格式为YYYY-MM-DD HH:MM:SS
        """
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    @staticmethod
    def generate_random_string(length: int = 8) -> str:
        """
        生成随机字符串
        
        参数:
            length: 字符串长度
            
        返回:
            随机字符串
        """
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    @staticmethod
    def ensure_dir_exists(directory: str) -> None:
        """
        确保目录存在，如果不存在则创建
        
        参数:
            directory: 目录路径
        """
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    @staticmethod
    def json_serialize(obj: Any) -> Any:
        """
        JSON序列化，处理特殊类型
        
        参数:
            obj: 要序列化的对象
            
        返回:
            可JSON序列化的对象
        """
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    @staticmethod
    def to_json(data: Any) -> str:
        """
        将数据转换为JSON字符串
        
        参数:
            data: 要转换的数据
            
        返回:
            JSON字符串
        """
        return json.dumps(data, ensure_ascii=False, default=Helpers.json_serialize)
    
    @staticmethod
    def from_json(json_str: str) -> Any:
        """
        将JSON字符串转换为Python对象
        
        参数:
            json_str: JSON字符串
            
        返回:
            Python对象
        """
        return json.loads(json_str)
    
    @staticmethod
    def dataframe_to_dict_list(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        将DataFrame转换为字典列表
        
        参数:
            df: DataFrame对象
            
        返回:
            字典列表
        """
        return df.to_dict(orient='records')
    
    @staticmethod
    def dict_list_to_dataframe(dict_list: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        将字典列表转换为DataFrame
        
        参数:
            dict_list: 字典列表
            
        返回:
            DataFrame对象
        """
        return pd.DataFrame(dict_list)
    
    @staticmethod
    def format_number(number: Union[int, float], decimal_places: int = 2) -> str:
        """
        格式化数字
        
        参数:
            number: 要格式化的数字
            decimal_places: 小数位数
            
        返回:
            格式化后的字符串
        """
        format_str = f"{{:.{decimal_places}f}}"
        return format_str.format(number)
    
    @staticmethod
    def format_percentage(value: float, decimal_places: int = 2) -> str:
        """
        格式化百分比
        
        参数:
            value: 要格式化的值（0-1之间）
            decimal_places: 小数位数
            
        返回:
            格式化后的百分比字符串
        """
        percentage = value * 100
        format_str = f"{{:.{decimal_places}f}}%"
        return format_str.format(percentage) 