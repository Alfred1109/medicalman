"""
模型包初始化文件
"""
from .database import Database

# 不在这里导入User类，避免循环导入问题
# from .user import User

# 导出模型类
__all__ = ['Database'] 