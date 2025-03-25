from flask_migrate import Migrate
from flask_login import LoginManager

# 初始化Migrate
migrate = Migrate()

# 初始化LoginManager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录以访问此页面。'
login_manager.login_message_category = 'warning'

def init_extensions(app):
    """初始化所有Flask扩展"""
    # 初始化数据库迁移
    from app import db
    migrate.init_app(app, db)
    
    # 初始化登录管理器
    login_manager.init_app(app)
    
    # 创建所有表
    with app.app_context():
        db.create_all() 