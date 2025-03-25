from flask import Flask, render_template
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import os
from datetime import timedelta, datetime
import logging
from logging.handlers import RotatingFileHandler
from app.config import DevelopmentConfig as Config

# 修改导入ydata_profiling的方式，使其不会重复打印提示信息
try:
    import ydata_profiling
    YDATA_PROFILING_AVAILABLE = True
except ImportError:
    try:
        # 有时候包名与导入名不一致，尝试其他方式
        from pandas_profiling import ProfileReport
        YDATA_PROFILING_AVAILABLE = True
    except ImportError:
        YDATA_PROFILING_AVAILABLE = False
        # 仅在实际运行而非导入时打印
        if __name__ != 'app':
            print("提示: ydata_profiling 包未安装，将使用替代方案提供基本数据分析功能")

# 初始化扩展
db = SQLAlchemy()
session = Session()
login_manager = LoginManager()
csrf = CSRFProtect()

@login_manager.user_loader
def load_user(user_id):
    """加载用户对象"""
    return User.query.get(int(user_id))

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
    app.config.from_object(Config)
    
    # 从环境变量加载配置
    app.config.from_prefixed_env()
    
    # 确保实例文件夹存在
    os.makedirs('instance', exist_ok=True)
    
    # 确保会话文件夹存在
    os.makedirs('flask_session', exist_ok=True)
    
    # 修正数据库URI，使用绝对路径
    db_path = os.path.abspath(os.path.join(os.getcwd(), 'instance', 'medical_workload.db'))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.logger.info(f'修正后的数据库URI: {app.config["SQLALCHEMY_DATABASE_URI"]}')
    
    # 初始化扩展
    db.init_app(app)
    session.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)  # 初始化 CSRF 保护
    
    # 设置登录视图
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    login_manager.login_message_category = 'warning'
    
    # 设置登录重定向URL
    login_manager.login_url = '/auth/login'
    
    # 设置登录后的重定向视图
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    login_manager.login_message_category = 'warning'
    
    # 注册蓝图
    register_blueprints(app)
    
    # 注册错误处理
    register_error_handlers(app)
    
    # 注册上下文处理器
    register_context_processors(app)
    
    # 初始化日志
    init_logger(app)
    
    # 数据库初始化
    with app.app_context():
        # 初始化数据库
        app.logger.info('开始初始化数据库...')
        # 添加调试输出
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '未设置')
        app.logger.info(f'数据库URI: {db_uri}')
        if 'DATABASE_PATH' in app.config:
            app.logger.info(f'数据库路径: {app.config["DATABASE_PATH"]}')
            app.logger.info(f'数据库路径是否存在: {os.path.exists(app.config["DATABASE_PATH"])}')
        # 创建数据库表
        db.create_all()
        app.logger.info('数据库初始化完成')
        
        # 初始化演示数据
        try:
            from app.utils.demo_data_generator import DemoDataGenerator
            DemoDataGenerator.initialize_all_demo_data()
            app.logger.info('演示数据初始化完成')
        except Exception as e:
            app.logger.error(f'初始化演示数据时出错: {str(e)}')
    
    return app

def register_blueprints(app):
    """注册蓝图"""
    from app.routes.main_routes import main_bp, dashboard_bp
    from app.routes.dashboard_routes import dashboard_api_bp
    from app.routes.api_routes import api_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.ai_chat_routes import ai_chat_bp
    from app.routes.analytics_routes import analytics_bp
    from app.routes.nlp_routes import nlp_bp
    from app.routes.settings_routes import settings_bp
    
    # 首先注册主路由(处理根路径)
    app.register_blueprint(main_bp)
    
    # 然后注册认证路由
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # 然后注册仪表盘API路由
    app.register_blueprint(dashboard_api_bp, url_prefix='/api/dashboard')
    
    # 然后注册仪表盘视图路由
    app.register_blueprint(dashboard_bp)
    
    # 最后注册其他路由
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(ai_chat_bp, url_prefix='/chat')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(nlp_bp, url_prefix='/nlp')
    app.register_blueprint(settings_bp, url_prefix='/settings')

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