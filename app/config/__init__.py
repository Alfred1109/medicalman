"""
配置初始化文件
"""
import os
from datetime import timedelta
from .development import DevelopmentConfig
from .production import ProductionConfig
from .base import (
    DATA_ANALYSIS_KEYWORDS,
    UPLOAD_FOLDER,
    ALLOWED_EXTENSIONS,
    DATABASE_PATH,
    ERROR_CODES,
    ERROR_TYPES,
    ERROR_MESSAGES,
    ERROR_STATUS_CODES
)

# 获取当前文件所在目录的绝对路径
basedir = os.path.abspath(os.path.dirname(__file__))

# 错误类型定义
ERROR_TYPES = {
    'database': 'DATABASE_ERROR',
    'auth': 'AUTHENTICATION_ERROR',
    'validation': 'VALIDATION_ERROR',
    'not_found': 'NOT_FOUND_ERROR',
    'permission': 'PERMISSION_ERROR',
    'server': 'SERVER_ERROR',
    'api': 'API_ERROR',
    'file': 'FILE_ERROR',
    'model': 'MODEL_ERROR',
    'internal': 'INTERNAL_ERROR'
}

# 错误代码定义
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

# 错误状态码定义
ERROR_STATUS_CODES = {
    'bad_request': 400,
    'unauthorized': 401,
    'forbidden': 403,
    'not_found': 404,
    'method_not_allowed': 405,
    'conflict': 409,
    'internal_server': 500,
    'service_unavailable': 503
}

# SQL查询状态码
SQL_STATUS_CODES = {
    'success': 'success',
    'error': 'error',
    'warning': 'warning',
    'info': 'info'
}

# SQL错误消息
SQL_ERROR_MESSAGES = {
    'invalid_query': '无效的SQL查询',
    'unsafe_query': '不安全的SQL查询，仅支持SELECT语句',
    'processing_failed': '处理SQL查询失败: {}',
    'execution_failed': '执行SQL查询失败: {}',
    'optimization_failed': '优化SQL查询失败: {}',
    'analysis_failed': '分析SQL查询结果失败: {}'
}

# LLM环境变量配置
LLM_ENV_VARS = {
    'api_key': 'VOLCENGINE_API_KEY',
    'api_url': 'VOLCENGINE_API_URL',
    'model': 'VOLCENGINE_MODEL'
}

# LLM默认配置
LLM_DEFAULTS = {
    'model': 'moonshot-v1-8k',
    'timeout': 60,
    'max_retries': 3,
    'retry_delay': 5
}

# LLM请求头配置
LLM_HEADERS = {
    'Content-Type': 'application/json'
}

# LLM请求体模板
LLM_PAYLOAD_TEMPLATE = {
    'stream': False
}

# LLM错误消息
LLM_ERROR_MESSAGES = {
    'invalid_input': '输入类型错误: 系统提示和用户消息必须是字符串类型',
    'invalid_response': 'API响应格式无效',
    'api_timeout': '请求超时，请稍后重试',
    'api_connection': '连接API服务器失败，请检查网络连接',
    'api_error': '调用API时发生错误: {}',
    'no_response': '多次尝试后仍未获得有效响应'
}

class Config:
    """基础配置类"""
    # 安全配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    
    # 会话配置
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.abspath(os.path.join(basedir, '../..', 'instance', 'medical_workload.db'))
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
    UPLOAD_FOLDER = os.path.join(basedir, '../..', 'uploads')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv', 'xlsx'}
    
    # 错误类型配置
    ERROR_TYPES = ERROR_TYPES
    ERROR_CODES = ERROR_CODES
    ERROR_STATUS_CODES = ERROR_STATUS_CODES
    
    # LLM配置
    LLM_ENV_VARS = LLM_ENV_VARS
    LLM_DEFAULTS = LLM_DEFAULTS
    LLM_HEADERS = LLM_HEADERS
    LLM_PAYLOAD_TEMPLATE = LLM_PAYLOAD_TEMPLATE
    LLM_ERROR_MESSAGES = LLM_ERROR_MESSAGES
    
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
        'sqlite:///' + os.path.abspath(os.path.join(basedir, '../..', 'instance', 'medical_workload.db'))
    
    # 修改数据库路径配置，指向正确的数据库文件
    DATABASE_PATH = os.path.abspath(os.path.join(basedir, '../..', 'instance', 'medical_workload.db'))
    
    # 添加数据库PRAGMA设置
    DB_PRAGMA_SETTINGS = {
        'journal_mode': 'WAL',
        'foreign_keys': 'ON',
        'cache_size': 2000,
        'synchronous': 1
    }
    
    # 数据库错误代码和消息
    DB_ERROR_CODES = {
        'connection': 1001,
        'query': 1002,
        'transaction': 1003,
        'data': 1004
    }
    
    DB_ERROR_MESSAGES = {
        'connection_error': '数据库连接错误: {}',
        'query_error': '查询执行错误: {}',
        'transaction_error': '事务执行错误: {}',
        'data_error': '数据操作错误: {}'
    }

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
        'sqlite:///' + os.path.abspath(os.path.join(basedir, '../..', 'instance', 'medical_workload.db'))
    
    # 与开发环境使用相同的数据库配置
    DATABASE_PATH = os.path.abspath(os.path.join(basedir, '../..', 'instance', 'medical_workload.db'))
    
    # 数据库PRAGMA设置
    DB_PRAGMA_SETTINGS = {
        'journal_mode': 'WAL',
        'foreign_keys': 'ON',
        'cache_size': 2000,
        'synchronous': 2  # 生产环境使用更安全的同步模式
    }
    
    DB_ERROR_CODES = {
        'connection': 1001,
        'query': 1002,
        'transaction': 1003,
        'data': 1004
    }
    
    DB_ERROR_MESSAGES = {
        'connection_error': '数据库连接错误: {}',
        'query_error': '查询执行错误: {}',
        'transaction_error': '事务执行错误: {}',
        'data_error': '数据操作错误: {}'
    }

# 配置字典
config_dict = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# 导出默认配置
config = DevelopmentConfig

# 导出配置
__all__ = [
    'config',
    'DATA_ANALYSIS_KEYWORDS',
    'UPLOAD_FOLDER',
    'ALLOWED_EXTENSIONS',
    'DATABASE_PATH',
    'ERROR_CODES',
    'ERROR_TYPES',
    'ERROR_MESSAGES',
    'ERROR_STATUS_CODES'
] 