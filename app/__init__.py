from flask import Flask, render_template
from flask_session import Session
import os
from datetime import timedelta, datetime
from app.extensions import init_extensions
from app.config import config

# 初始化扩展
session = Session()

def create_app(config_name=None):
    """
    应用工厂函数，创建并配置Flask应用
    
    参数:
        config_name: 配置名称，默认为None，将使用环境变量中的配置
        
    返回:
        Flask应用实例
    """
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # 加载配置
    app.config.from_object(config)
    
    # 从环境变量加载配置
    app.config.from_prefixed_env()
    
    # 确保会话文件夹存在
    os.makedirs('flask_session', exist_ok=True)
    
    # 初始化扩展
    session.init_app(app)
    init_extensions(app)
    
    # 注册蓝图
    from app.controllers.auth import auth_bp
    from app.controllers.dashboard import dashboard_bp
    from app.controllers.analysis import analysis_bp
    from app.controllers.ai_chat import ai_chat_bp
    from app.controllers.settings import settings_bp
    from app.controllers.logs import logs_bp
    from app.controllers.api import api_bp, upload_bp, auth_api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(ai_chat_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(auth_api_bp)
    
    # 注册错误处理
    register_error_handlers(app)
    
    # 注册上下文处理器
    register_context_processors(app)
    
    return app

def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

def register_context_processors(app):
    """注册上下文处理器"""
    
    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.now().year} 