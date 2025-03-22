"""
配置初始化文件
"""
import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# 获取环境变量
ENV = os.environ.get('FLASK_ENV', 'development')

# 根据环境选择配置类
if ENV == 'production':
    from app.config.production import ProductionConfig as Config
else:
    from app.config.development import DevelopmentConfig as Config

# 导出配置
config = Config 