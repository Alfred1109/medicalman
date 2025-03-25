import os
from datetime import timedelta

# 获取当前文件所在目录的绝对路径
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """基础配置类"""
    # 安全配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    
    # 会话配置
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.abspath(os.path.join(basedir, '..', 'instance', 'medical_workload.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 应用配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 限制上传文件大小为16MB
    
    # 日志配置
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # 缓存配置
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300
    
    # CSRF配置
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or 'csrf-key'
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(basedir, '..', 'uploads')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv', 'xlsx'}
    
    # API配置
    API_TITLE = '医疗工作量系统API'
    API_VERSION = 'v1'
    OPENAPI_VERSION = '3.0.2'
    
    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    @staticmethod
    def init_app(app):
        """初始化应用"""
        # 确保上传目录存在
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

# 开发环境配置
class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.abspath(os.path.join(basedir, '..', 'instance', 'medical_workload.db'))

# 测试环境配置
class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# 生产环境配置
class ProductionConfig(Config):
    """生产环境配置"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.abspath(os.path.join(basedir, '..', 'instance', 'medical_workload.db'))

# 配置字典
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# 导出默认配置
config = DevelopmentConfig 