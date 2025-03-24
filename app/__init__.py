from flask import Flask, render_template
from flask_session import Session
import os
from datetime import timedelta, datetime
from app.extensions import init_extensions
from app.config import config
import logging
from logging.handlers import RotatingFileHandler

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
    register_blueprints(app)
    
    # 注册错误处理
    register_error_handlers(app)
    
    # 注册上下文处理器
    register_context_processors(app)
    
    # 初始化日志
    init_logger(app)
    
    # 数据库初始化
    from app.models.database import init_db
    with app.app_context():
        init_db(app)
    
    return app

def register_blueprints(app):
    """注册蓝图"""
    from app.routes.main_routes import main_bp, dashboard_bp as main_dashboard_bp
    from app.routes.dashboard_routes import dashboard_bp
    from app.routes.api_routes import api_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.ai_chat_routes import ai_chat_bp
    from app.routes.analytics_routes import analytics_bp
    from app.routes.nlp_routes import nlp_bp
    from app.routes.settings_routes import settings_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(main_dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(dashboard_bp)  # 仪表盘API路由，已有url_prefix
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(ai_chat_bp, url_prefix='/chat')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(nlp_bp, url_prefix='/nlp')
    app.register_blueprint(settings_bp)

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

def init_logger(app):
    """初始化日志配置"""
    if not os.path.exists('logs'):
        os.mkdir('logs')
        
    file_handler = RotatingFileHandler('logs/medical_workload.log', 
                                      maxBytes=10240, 
                                      backupCount=10)
    
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('医疗工作量系统启动') 