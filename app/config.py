"""
配置管理模块 - 集中管理应用配置
"""
import os
import json
from typing import Dict, Any, Optional
import logging
from datetime import timedelta

# 基础路径定义
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

# 数据库配置
DATABASE_PATH = os.path.join(INSTANCE_DIR, 'medical_workload.db')
DATABASE_SCHEMA = os.path.join(BASE_DIR, 'schema.sql')

# 服务器配置
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', '5101'))
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 't')

# 默认LLM配置
DEFAULT_LLM_MODEL = os.environ.get('DEFAULT_LLM_MODEL', 'gpt-3.5-turbo')
DEFAULT_LLM_TEMPERATURE = float(os.environ.get('DEFAULT_LLM_TEMPERATURE', '0.7'))
DEFAULT_LLM_TOP_P = float(os.environ.get('DEFAULT_LLM_TOP_P', '0.9'))

# 日志配置
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FILE = os.path.join(LOG_DIR, 'app.log')

# 应用安全配置
SECRET_KEY = os.environ.get('SECRET_KEY', 'medical_man_default_secret_key')

# 文件上传配置
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {
    'document': {'pdf', 'doc', 'docx', 'txt', 'md'},
    'spreadsheet': {'xls', 'xlsx', 'csv'},
    'image': {'png', 'jpg', 'jpeg', 'gif'}
}

# 扩展配置字典，用于应用启动时加载
config_dict = {
    'DEBUG': DEBUG,
    'SECRET_KEY': SECRET_KEY,
    'DATABASE_PATH': DATABASE_PATH,
    'DATABASE_SCHEMA': DATABASE_SCHEMA,
    'UPLOAD_FOLDER': UPLOAD_DIR,
    'MAX_CONTENT_LENGTH': MAX_CONTENT_LENGTH,
    'ALLOWED_EXTENSIONS': ALLOWED_EXTENSIONS,
    'DEFAULT_LLM_MODEL': DEFAULT_LLM_MODEL,
    'DEFAULT_LLM_TEMPERATURE': DEFAULT_LLM_TEMPERATURE,
    'DEFAULT_LLM_TOP_P': DEFAULT_LLM_TOP_P
}

# 从环境文件加载配置
def load_env_from_file(env_file: str = '.env') -> None:
    """
    从环境文件加载配置到环境变量
    
    参数:
        env_file: 环境变量文件路径
    """
    env_path = os.path.join(BASE_DIR, env_file)
    
    if os.path.exists(env_path):
        print(f"加载环境变量文件: {env_path}")
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
    else:
        print(f"环境变量文件未找到: {env_path}")

# 保存自定义配置到文件
def save_custom_config(config_data: Dict[str, Any], file_name: str = 'custom_config.json') -> bool:
    """
    保存自定义配置到文件
    
    参数:
        config_data: 配置数据
        file_name: 配置文件名
        
    返回:
        是否保存成功
    """
    try:
        config_path = os.path.join(INSTANCE_DIR, file_name)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.error(f"保存配置文件出错: {str(e)}")
        return False

# 加载自定义配置
def load_custom_config(file_name: str = 'custom_config.json') -> Optional[Dict[str, Any]]:
    """
    从文件加载自定义配置
    
    参数:
        file_name: 配置文件名
        
    返回:
        配置数据或None
    """
    try:
        config_path = os.path.join(INSTANCE_DIR, file_name)
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        logging.error(f"加载配置文件出错: {str(e)}")
        return None

# 更新配置
def update_config(app_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    更新应用配置
    
    参数:
        app_config: 当前应用配置
        
    返回:
        更新后的配置
    """
    # 加载环境变量
    load_env_from_file()
    
    # 加载自定义配置
    custom_config = load_custom_config()
    
    # 更新配置
    if custom_config:
        app_config.update(custom_config)
    
    # 设置默认数据库路径（如果未指定）
    if 'DATABASE_PATH' not in app_config:
        app_config['DATABASE_PATH'] = DATABASE_PATH
    
    return app_config

# 配置类
class Config:
    """基础配置类"""
    # 应用名称
    APP_NAME = 'MedicalMan'
    
    # 密钥配置
    SECRET_KEY = SECRET_KEY
    
    # 数据库配置
    DATABASE_PATH = DATABASE_PATH
    
    # 会话配置
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.path.join(BASE_DIR, 'flask_session')
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # 日志配置
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    LOG_LEVEL = LOG_LEVEL
    
    # 上传文件配置
    UPLOAD_FOLDER = UPLOAD_DIR
    MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH
    
    # 允许上传的文件类型
    ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS
    
    # API配置
    API_RATE_LIMIT = '100/hour'
    API_RATE_LIMIT_EXEMPT_ROLES = ['admin']
    
    # 默认每页记录数
    DEFAULT_PAGE_SIZE = 20
    
    # 调试模式
    DEBUG = DEBUG

# 导出配置对象
config = Config() 