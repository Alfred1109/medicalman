import os
from datetime import timedelta

# 获取当前文件所在目录的绝对路径
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """基础配置类"""
    # 安全配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-hard-to-guess-string'
    
    # 会话配置
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.path.join(basedir, '..', 'flask_session')
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # 数据库配置
    DATABASE_PATH = os.path.join(basedir, '..', 'instance', 'medical_workload.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 应用配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 限制上传文件大小为16MB
    
    # 日志配置
    LOG_DIR = os.path.join(basedir, '..', 'logs')
    
    # CSRF配置
    WTF_CSRF_ENABLED = False  # 开发环境禁用CSRF保护方便API测试
    WTF_CSRF_TIME_LIMIT = 3600
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(basedir, '..', 'uploads')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv', 'xlsx'}
    
    # API配置
    API_TITLE = '医疗工作量系统API'
    API_VERSION = 'v1'
    OPENAPI_VERSION = '3.0.2'
    
    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.example.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
    
    # 生成验证码的配置
    CAPTCHA_FONT_PATH = os.path.join(basedir, '..', 'static', 'fonts', 'Arial.ttf')
    CAPTCHA_WIDTH = 160
    CAPTCHA_HEIGHT = 60
    
    @staticmethod
    def init_app(app):
        """初始化应用"""
        # 创建必要的目录
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.LOG_DIR, exist_ok=True)
        os.makedirs(Config.SESSION_FILE_DIR, exist_ok=True)

# 开发环境配置
class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False
    
    # 开发环境禁用CSRF保护，方便API测试
    WTF_CSRF_ENABLED = False
    # 为来自相同源的API请求提供CSRF豁免
    WTF_CSRF_CHECK_DEFAULT = False
    # 增加CSRF令牌有效期
    WTF_CSRF_TIME_LIMIT = 86400  # 24小时

# 测试环境配置
class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    # 使用内存数据库进行测试
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# 生产环境配置
class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False
    WTF_CSRF_ENABLED = True  # 生产环境启用CSRF保护
    
    # 生产环境应该使用更强的密钥
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 生产环境日志配置
        import logging
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            os.path.join(cls.LOG_DIR, 'medical_workload.log'),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)

# 配置字典
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# 导出默认配置
config = DevelopmentConfig 