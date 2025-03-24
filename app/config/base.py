"""
基础配置文件，包含所有环境共享的配置
"""
import os
from datetime import timedelta

# 应用配置
SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-key')
SESSION_TYPE = 'filesystem'
SESSION_PERMANENT = True
SESSION_FILE_DIR = 'flask_session'
PERMANENT_SESSION_LIFETIME = timedelta(days=7)
SESSION_USE_SIGNER = False  # 修改为False，避免因签名导致的字节/字符串问题
SESSION_KEY_PREFIX = 'session:'  # 添加前缀，确保session键正确处理
SESSION_COOKIE_SECURE = False  # 在开发环境中设为False，生产环境建议设为True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'  # 防止CSRF攻击

# 日志配置
LOG_LEVEL = 'INFO'

# 数据库配置
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "instance", "medical_workload.db")

# 上传文件配置
UPLOAD_FOLDER = 'static/uploads/documents'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'xlsx', 'xls', 'csv', 'xlsm', 'ods'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# 验证码配置
CAPTCHA_WIDTH = 160
CAPTCHA_HEIGHT = 60
CAPTCHA_LENGTH = 4
CAPTCHA_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# API配置
VOLCENGINE_API_KEY = os.environ.get('VOLCENGINE_API_KEY', "3470059d-f774-4302-81e0-50fa017fea38")
VOLCENGINE_API_URL = os.environ.get('VOLCENGINE_API_URL', "https://ark.cn-beijing.volces.com/api/v3/chat/completions")
VOLCENGINE_MODEL = os.environ.get('VOLCENGINE_MODEL', "deepseek-v3-241226")

# 请求配置
REQUEST_TIMEOUT = 30  # 请求超时时间（秒）
MAX_RETRIES = 2       # 最大重试次数
RETRY_DELAY = 1       # 重试延迟（秒）

class BaseConfig:
    """基础配置类"""
    # 应用配置
    SECRET_KEY = SECRET_KEY
    SESSION_TYPE = SESSION_TYPE
    SESSION_PERMANENT = SESSION_PERMANENT
    SESSION_FILE_DIR = SESSION_FILE_DIR
    PERMANENT_SESSION_LIFETIME = PERMANENT_SESSION_LIFETIME
    SESSION_USE_SIGNER = SESSION_USE_SIGNER
    SESSION_KEY_PREFIX = SESSION_KEY_PREFIX  # 添加SESSION_KEY_PREFIX
    SESSION_COOKIE_SECURE = SESSION_COOKIE_SECURE
    SESSION_COOKIE_HTTPONLY = SESSION_COOKIE_HTTPONLY
    SESSION_COOKIE_SAMESITE = SESSION_COOKIE_SAMESITE
    
    # 日志配置
    LOG_LEVEL = LOG_LEVEL
    
    # 数据库配置
    DATABASE_PATH = DATABASE_PATH
    
    # 上传文件配置
    UPLOAD_FOLDER = UPLOAD_FOLDER
    ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS
    MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH
    
    # 验证码配置
    CAPTCHA_WIDTH = CAPTCHA_WIDTH
    CAPTCHA_HEIGHT = CAPTCHA_HEIGHT
    CAPTCHA_LENGTH = CAPTCHA_LENGTH
    CAPTCHA_CHARS = CAPTCHA_CHARS
    
    # API配置
    VOLCENGINE_API_KEY = VOLCENGINE_API_KEY
    VOLCENGINE_API_URL = VOLCENGINE_API_URL
    VOLCENGINE_MODEL = VOLCENGINE_MODEL
    
    # 请求配置
    REQUEST_TIMEOUT = REQUEST_TIMEOUT
    MAX_RETRIES = MAX_RETRIES
    RETRY_DELAY = RETRY_DELAY 