"""
开发环境配置文件
"""
from .base import BaseConfig

class DevelopmentConfig(BaseConfig):
    """开发环境配置类"""
    # 调试模式
    DEBUG = True
    TESTING = False
    
    # 日志级别
    LOG_LEVEL = 'DEBUG'
    
    # 会话配置
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # 数据库配置
    DATABASE_TIMEOUT = 30
    DATABASE_CACHE_SIZE = 2000
    DATABASE_JOURNAL_MODE = 'WAL'
    DATABASE_SYNCHRONOUS = 'NORMAL'
    
    # 性能监控
    PERFORMANCE_MONITORING = True
    PERFORMANCE_LOG_INTERVAL = 30  # 开发环境更频繁地记录性能数据
    
    # 跨域配置
    CORS_ORIGINS = ['*']
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_HEADERS = ['Content-Type', 'Authorization']
    
    # 缓存配置
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300  # 5分钟
    
    # 通知配置
    NOTIFICATION_ENABLED = True
    NOTIFICATION_CHANNELS = ['web']  # 开发环境只使用web通知
    
    # 主题配置
    THEME = 'default'
    CUSTOM_CSS = None
    CUSTOM_JS = None
    
    # 开发环境特定配置
    EXPLAIN_TEMPLATE_LOADING = True  # 调试模板加载 