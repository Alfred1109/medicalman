"""
生产环境配置文件
"""
from .base import BaseConfig

class ProductionConfig(BaseConfig):
    """生产环境配置类"""
    # 调试模式
    DEBUG = False
    TESTING = False
    
    # 日志级别
    LOG_LEVEL = 'ERROR'
    
    # 会话配置
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # 数据库配置
    DATABASE_TIMEOUT = 60
    DATABASE_CACHE_SIZE = 5000
    DATABASE_JOURNAL_MODE = 'WAL'
    DATABASE_SYNCHRONOUS = 'FULL'
    
    # 性能监控
    PERFORMANCE_MONITORING = True
    PERFORMANCE_LOG_INTERVAL = 300  # 生产环境降低性能数据记录频率
    
    # 跨域配置
    CORS_ORIGINS = ['https://your-production-domain.com']
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE']
    CORS_HEADERS = ['Content-Type', 'Authorization']
    
    # 缓存配置
    CACHE_TYPE = 'redis'
    CACHE_DEFAULT_TIMEOUT = 3600  # 1小时
    
    # 通知配置
    NOTIFICATION_ENABLED = True
    NOTIFICATION_CHANNELS = ['email', 'web']
    
    # 主题配置
    THEME = 'default'
    CUSTOM_CSS = None
    CUSTOM_JS = None
    
    # 安全配置
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 3600  # 1小时 