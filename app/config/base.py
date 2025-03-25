"""
基础配置文件，包含所有环境共享的配置
"""
import os
import string
from datetime import timedelta
import secrets

# 基础路径定义
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
UPLOAD_DIR = os.path.join(STATIC_DIR, 'uploads')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# 子目录配置
DOCUMENT_UPLOAD_DIR = os.path.join(UPLOAD_DIR, 'documents')
IMAGE_UPLOAD_DIR = os.path.join(UPLOAD_DIR, 'images')
REPORTS_DIR = os.path.join(UPLOAD_DIR, 'reports')

# 确保所有目录存在
for directory in [INSTANCE_DIR, STATIC_DIR, UPLOAD_DIR, TEMPLATE_DIR, LOG_DIR,
                 DOCUMENT_UPLOAD_DIR, IMAGE_UPLOAD_DIR, REPORTS_DIR]:
    os.makedirs(directory, exist_ok=True)

# 应用配置
APP_NAME = 'MedicalMan'
SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or secrets.token_hex(32)
WTF_CSRF_ENABLED = True

# 会话配置
SESSION_TYPE = 'filesystem'
SESSION_PERMANENT = True
SESSION_FILE_DIR = os.path.join(BASE_DIR, 'flask_session')
PERMANENT_SESSION_LIFETIME = 3600  # 会话有效期（秒）
SESSION_USE_SIGNER = False
SESSION_KEY_PREFIX = 'session:'
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# 日志配置
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FILE = os.path.join(LOG_DIR, 'app.log')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# 数据库配置
DATABASE_PATH = os.path.abspath(os.path.join(INSTANCE_DIR, 'medical_workload.db'))
DATABASE_SCHEMA = os.path.join(BASE_DIR, 'schema.sql')
DATABASE_TIMEOUT = 30
DATABASE_CACHE_SIZE = 2000
DATABASE_JOURNAL_MODE = 'WAL'
DATABASE_SYNCHRONOUS = 'NORMAL'

# 上传文件配置
UPLOAD_FOLDER = UPLOAD_DIR
ALLOWED_EXTENSIONS = {
    'document': {'pdf', 'doc', 'docx', 'txt', 'md'},
    'spreadsheet': {'xls', 'xlsx', 'csv'},
    'image': {'png', 'jpg', 'jpeg', 'gif'}
}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# 验证码配置
CAPTCHA_FONT_PATH = os.path.join(STATIC_DIR, 'fonts', 'arial.ttf')
CAPTCHA_SYSTEM_FONT_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"
CAPTCHA_WIDTH = 200
CAPTCHA_HEIGHT = 80
CAPTCHA_CHARS = string.ascii_letters + string.digits
CAPTCHA_LENGTH = 4

# API配置
VOLCENGINE_API_KEY = os.environ.get('VOLCENGINE_API_KEY', "3470059d-f774-4302-81e0-50fa017fea38")
VOLCENGINE_API_URL = os.environ.get('VOLCENGINE_API_URL', "https://ark.cn-beijing.volces.com/api/v3/chat/completions")
VOLCENGINE_MODEL = os.environ.get('VOLCENGINE_MODEL', "deepseek-v3-241226")

# 请求配置
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1

# 数据分析配置
DATA_ANALYSIS_KEYWORDS = [
    '门诊量', '住院量', '收入', '趋势', '统计', '比较', 
    '增长', '下降', '变化', '占比', '分布', '排名', 
    '科室', '专科', '医生', '患者', '对比', '分析',
    '目标', '达成', '完成率', '绩效'
]

# 图表配置
CHART_DEFAULT_TYPE = "line"
CHART_DEFAULT_TITLE = "未命名图表"
CHART_DEFAULT_SERIES_NAME = "未命名系列"
CHART_DEFAULT_WIDTH = 800
CHART_DEFAULT_HEIGHT = 400
CHART_DEFAULT_THEME = "light"
CHART_DEFAULT_COLORS = ["#5470c6", "#91cc75", "#fac858", "#ee6666", "#73c0de", "#3ba272"]

# 数据导出配置
EXPORT_FOLDER = os.path.join(UPLOAD_DIR, 'exports')
EXPORT_FORMATS = ['pdf', 'excel', 'csv']

# 缓存配置
CACHE_TYPE = 'simple'
CACHE_DEFAULT_TIMEOUT = 300  # 5分钟

# 跨域配置
CORS_ORIGINS = ['*']
CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
CORS_HEADERS = ['Content-Type', 'Authorization']

# 文件处理配置
MAX_WORKERS = 4
CHUNK_SIZE = 8192  # 8KB

# 数据验证配置
VALIDATION_TIMEOUT = 30  # 秒
MAX_RETRIES = 3

# 错误处理配置
ERROR_TYPES = {
    'database': 'database_error',
    'api': 'api_error',
    'auth': 'auth_error',
    'validation': 'validation_error',
    'file': 'file_error',
    'model': 'model_error',
    'internal': 'internal_error',
    'not_found': 'not_found'
}

ERROR_CODES = {
    # 数据库错误 (1xxx)
    'db_connection': 1001,
    'db_query': 1002,
    'db_transaction': 1003,
    'db_data': 1004,
    
    # API错误 (2xxx)
    'api_invalid_request': 2001,
    'api_rate_limit': 2002,
    'api_resource_not_found': 2003,
    'api_permission_denied': 2004,
    
    # 认证错误 (3xxx)
    'auth_invalid_credentials': 3001,
    'auth_token_expired': 3002,
    'auth_insufficient_permissions': 3003,
    
    # 验证错误 (4xxx)
    'validation_missing_field': 4001,
    'validation_invalid_format': 4002,
    'validation_invalid_value': 4003,
    
    # 文件错误 (5xxx)
    'file_not_found': 5001,
    'file_invalid_format': 5002,
    'file_too_large': 5003,
    'file_permission_denied': 5004,
    
    # 模型错误 (6xxx)
    'model_load': 6001,
    'model_inference': 6002,
    'model_timeout': 6003,
    
    # 系统内部错误 (7xxx)
    'internal_server': 7001,
    'internal_dependency': 7002,
    
    # 未找到错误 (8xxx)
    'resource_not_found': 8001,
    'endpoint_not_found': 8002
}

ERROR_STATUS_CODES = {
    'bad_request': 400,
    'unauthorized': 401,
    'forbidden': 403,
    'not_found': 404,
    'internal_server': 500
}

ERROR_MESSAGES = {
    'internal_server': '内部服务器错误: {}',
    'validation_error': '验证错误: {}',
    'file_not_found': '文件未找到: {}',
    'file_permission': '文件权限错误: {}'
}

# 性能监控配置
PERFORMANCE_MONITORING = True
PERFORMANCE_LOG_INTERVAL = 60  # 秒

# 备份配置
BACKUP_FOLDER = os.path.join(UPLOAD_DIR, 'backups')
BACKUP_RETENTION_DAYS = 7
BACKUP_SCHEDULE = '0 0 * * *'  # 每天午夜

# 通知配置
NOTIFICATION_ENABLED = True
NOTIFICATION_CHANNELS = ['email', 'web']

# 国际化配置
LANGUAGES = ['zh', 'en']
DEFAULT_LANGUAGE = 'zh'

# 主题配置
THEME = 'default'
CUSTOM_CSS = None
CUSTOM_JS = None

# 调试配置
TESTING = False

# AI聊天服务配置
CHAT_TABLE_NAME = 'chat_messages'
CHATS_TABLE_NAME = 'chats'
CHAT_QUERIES = {
    'get_history': """
    SELECT message_id, role, content, content_type, time, structured_data
    FROM chat_messages
    WHERE chat_id = ?
    ORDER BY time ASC
    """,
    'get_title': "SELECT title FROM chats WHERE chat_id = ?"
}
CHAT_ERROR_MESSAGES = {
    'history_error': '获取聊天历史出错: {}',
    'title_error': '获取聊天标题出错: {}'
}
CHAT_STRUCTURED_DATA_FIELDS = ['charts', 'tables', 'analysis', 'summary']

# 基础LLM服务配置
LLM_ENV_VARS = {
    'api_key': 'VOLCENGINE_API_KEY',
    'api_url': 'VOLCENGINE_API_URL',
    'model': 'VOLCENGINE_MODEL'
}
LLM_DEFAULTS = {
    'model': 'gpt-3.5-turbo',
    'temperature': 0.7,
    'top_p': 0.8,
    'top_k': 50,
    'timeout': 60,
    'max_retries': 3,
    'retry_delay': 2
}
LLM_ERROR_MESSAGES = {
    'api_timeout': 'API请求超时，请稍后再试或简化您的问题。',
    'api_connection': 'API连接异常，请检查网络连接后重试。',
    'api_error': '系统发生错误: {}',
    'no_response': '无法从AI服务获取响应，请稍后重试。',
    'invalid_input': '系统提示和用户消息必须是字符串类型',
    'invalid_response': 'API响应没有包含有效的选择'
}
LLM_HEADERS = {
    'Content-Type': 'application/json'
}
LLM_PAYLOAD_TEMPLATE = {
    'messages': [
        {'role': 'system', 'content': ''},
        {'role': 'user', 'content': ''}
    ]
}

# 通用工具配置
UTILS = {
    # MIME类型映射
    'mime_types': {
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'csv': 'text/csv',
        'txt': 'text/plain',
        'md': 'text/markdown',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif'
    },
    
    # 文件处理配置
    'file': {
        'default_type': 'document',
        'timestamp_format': '%Y%m%d%H%M%S',
        'default_extension': 'txt',
        'default_mime_type': 'application/octet-stream'
    },
    
    # 文本处理配置
    'text': {
        'max_length': 200,
        'suffix': '...',
        'separator': '.',
        'url_safe_chars': string.ascii_letters + string.digits + '-_'
    },
    
    # 时间格式配置
    'datetime': {
        'default_format': '%Y-%m-%d %H:%M:%S',
        'date_format': '%Y-%m-%d',
        'time_format': '%H:%M:%S'
    },
    
    # 数字格式化配置
    'number': {
        'decimal_places': 2,
        'currency_symbol': '¥',
        'percentage_format': '{:.2f}%'
    },
    
    # JSON处理配置
    'json': {
        'ensure_ascii': False,
        'indent': 2,
        'separator': '.'
    }
}

class BaseConfig:
    """基础配置类"""
    # 应用配置
    APP_NAME = APP_NAME
    SECRET_KEY = SECRET_KEY
    WTF_CSRF_SECRET_KEY = WTF_CSRF_SECRET_KEY
    WTF_CSRF_ENABLED = WTF_CSRF_ENABLED
    
    # 会话配置
    SESSION_TYPE = SESSION_TYPE
    SESSION_PERMANENT = SESSION_PERMANENT
    SESSION_FILE_DIR = SESSION_FILE_DIR
    PERMANENT_SESSION_LIFETIME = PERMANENT_SESSION_LIFETIME
    SESSION_USE_SIGNER = SESSION_USE_SIGNER
    SESSION_KEY_PREFIX = SESSION_KEY_PREFIX
    SESSION_COOKIE_SECURE = SESSION_COOKIE_SECURE
    SESSION_COOKIE_HTTPONLY = SESSION_COOKIE_HTTPONLY
    SESSION_COOKIE_SAMESITE = SESSION_COOKIE_SAMESITE
    
    # 日志配置
    LOG_LEVEL = LOG_LEVEL
    LOG_FILE = LOG_FILE
    LOG_FORMAT = LOG_FORMAT
    
    # 数据库配置
    DATABASE_PATH = DATABASE_PATH
    DATABASE_SCHEMA = DATABASE_SCHEMA
    DATABASE_TIMEOUT = DATABASE_TIMEOUT
    DATABASE_CACHE_SIZE = DATABASE_CACHE_SIZE
    DATABASE_JOURNAL_MODE = DATABASE_JOURNAL_MODE
    DATABASE_SYNCHRONOUS = DATABASE_SYNCHRONOUS
    
    # 上传文件配置
    UPLOAD_FOLDER = UPLOAD_FOLDER
    ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS
    MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH
    
    # 验证码配置
    CAPTCHA_FONT_PATH = CAPTCHA_FONT_PATH
    CAPTCHA_SYSTEM_FONT_PATH = CAPTCHA_SYSTEM_FONT_PATH
    CAPTCHA_WIDTH = CAPTCHA_WIDTH
    CAPTCHA_HEIGHT = CAPTCHA_HEIGHT
    CAPTCHA_CHARS = CAPTCHA_CHARS
    CAPTCHA_LENGTH = CAPTCHA_LENGTH
    
    # API配置
    VOLCENGINE_API_KEY = VOLCENGINE_API_KEY
    VOLCENGINE_API_URL = VOLCENGINE_API_URL
    VOLCENGINE_MODEL = VOLCENGINE_MODEL
    
    # 请求配置
    REQUEST_TIMEOUT = REQUEST_TIMEOUT
    MAX_RETRIES = MAX_RETRIES
    RETRY_DELAY = RETRY_DELAY
    
    # 数据分析配置
    DATA_ANALYSIS_KEYWORDS = DATA_ANALYSIS_KEYWORDS
    
    # 图表配置
    CHART_DEFAULT_TYPE = CHART_DEFAULT_TYPE
    CHART_DEFAULT_TITLE = CHART_DEFAULT_TITLE
    CHART_DEFAULT_SERIES_NAME = CHART_DEFAULT_SERIES_NAME
    CHART_DEFAULT_WIDTH = CHART_DEFAULT_WIDTH
    CHART_DEFAULT_HEIGHT = CHART_DEFAULT_HEIGHT
    CHART_DEFAULT_THEME = CHART_DEFAULT_THEME
    CHART_DEFAULT_COLORS = CHART_DEFAULT_COLORS
    
    # 数据导出配置
    EXPORT_FOLDER = EXPORT_FOLDER
    EXPORT_FORMATS = EXPORT_FORMATS
    
    # 缓存配置
    CACHE_TYPE = CACHE_TYPE
    CACHE_DEFAULT_TIMEOUT = CACHE_DEFAULT_TIMEOUT
    
    # 跨域配置
    CORS_ORIGINS = CORS_ORIGINS
    CORS_METHODS = CORS_METHODS
    CORS_HEADERS = CORS_HEADERS
    
    # 文件处理配置
    MAX_WORKERS = MAX_WORKERS
    CHUNK_SIZE = CHUNK_SIZE
    
    # 数据验证配置
    VALIDATION_TIMEOUT = VALIDATION_TIMEOUT
    MAX_RETRIES = MAX_RETRIES
    
    # 错误处理配置
    ERROR_TYPES = ERROR_TYPES
    ERROR_CODES = ERROR_CODES
    ERROR_STATUS_CODES = ERROR_STATUS_CODES
    ERROR_MESSAGES = ERROR_MESSAGES
    
    # 性能监控配置
    PERFORMANCE_MONITORING = PERFORMANCE_MONITORING
    PERFORMANCE_LOG_INTERVAL = PERFORMANCE_LOG_INTERVAL
    
    # 备份配置
    BACKUP_FOLDER = BACKUP_FOLDER
    BACKUP_RETENTION_DAYS = BACKUP_RETENTION_DAYS
    BACKUP_SCHEDULE = BACKUP_SCHEDULE
    
    # 通知配置
    NOTIFICATION_ENABLED = NOTIFICATION_ENABLED
    NOTIFICATION_CHANNELS = NOTIFICATION_CHANNELS
    
    # 国际化配置
    LANGUAGES = LANGUAGES
    DEFAULT_LANGUAGE = DEFAULT_LANGUAGE
    
    # 主题配置
    THEME = THEME
    CUSTOM_CSS = CUSTOM_CSS
    CUSTOM_JS = CUSTOM_JS
    
    # 调试配置
    TESTING = TESTING
    
    # AI聊天服务配置
    CHAT_TABLE_NAME = CHAT_TABLE_NAME
    CHATS_TABLE_NAME = CHATS_TABLE_NAME
    CHAT_QUERIES = CHAT_QUERIES
    CHAT_ERROR_MESSAGES = CHAT_ERROR_MESSAGES
    CHAT_STRUCTURED_DATA_FIELDS = CHAT_STRUCTURED_DATA_FIELDS
    
    # 基础LLM服务配置
    LLM_ENV_VARS = LLM_ENV_VARS
    LLM_DEFAULTS = LLM_DEFAULTS
    LLM_ERROR_MESSAGES = LLM_ERROR_MESSAGES
    LLM_HEADERS = LLM_HEADERS
    LLM_PAYLOAD_TEMPLATE = LLM_PAYLOAD_TEMPLATE
    
    # 通用工具配置
    UTILS = UTILS 