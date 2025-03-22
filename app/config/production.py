"""
生产环境配置
"""
from app.config.base import BaseConfig

class ProductionConfig(BaseConfig):
    """生产环境配置类"""
    DEBUG = False
    TESTING = False
    
    # 日志配置
    LOG_LEVEL = 'ERROR'
    
    # 安全配置
    SESSION_COOKIE_SECURE = True  # 仅通过HTTPS发送cookie
    SESSION_COOKIE_HTTPONLY = True  # 防止JavaScript访问cookie 