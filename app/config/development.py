"""
开发环境配置
"""
from app.config.base import BaseConfig

class DevelopmentConfig(BaseConfig):
    """开发环境配置类"""
    DEBUG = True
    TESTING = False
    
    # 日志配置
    LOG_LEVEL = 'DEBUG'
    
    # 开发环境特定配置
    EXPLAIN_TEMPLATE_LOADING = True  # 调试模板加载 