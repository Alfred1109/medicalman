"""
控制器包初始化文件
"""
from .auth import auth_bp, login_required, role_required
from .dashboard import dashboard_bp
from .analysis import analysis_bp
from .ai_chat import ai_chat_bp
from .settings import settings_bp

# 导出蓝图和装饰器
__all__ = [
    'auth_bp', 'login_required', 'role_required',
    'dashboard_bp', 'analysis_bp', 'ai_chat_bp', 'settings_bp'
] 