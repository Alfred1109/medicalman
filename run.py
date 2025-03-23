"""
应用启动脚本
"""
import os
from app import create_app

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    # 获取环境变量
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5101))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # 启动应用
    app.run(host=host, port=port, debug=debug) 