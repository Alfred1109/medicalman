"""
应用启动脚本
"""
import os
import argparse
import traceback
import sys
from app import create_app
import logging
import sqlite3

# 设置日志格式
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 解析命令行参数
parser = argparse.ArgumentParser(description='医疗管理系统')
parser.add_argument('--port', type=int, help='服务端口号', default=None)
parser.add_argument('--host', type=str, help='服务主机地址', default=None)
parser.add_argument('--debug', action='store_true', help='是否开启调试模式')
args = parser.parse_args()

# 打印一些环境信息
print(f"当前工作目录: {os.getcwd()}")
print(f"instance 目录是否存在: {os.path.exists('instance')}")
print(f"instance/medical_workload.db 是否存在: {os.path.exists(os.path.join('instance', 'medical_workload.db'))}")

# 测试数据库连接
try:
    db_path = os.path.abspath(os.path.join('instance', 'medical_workload.db'))
    print(f"数据库完整路径: {db_path}")
    print(f"数据库文件存在: {os.path.exists(db_path)}")
    print(f"数据库文件权限: {oct(os.stat(db_path).st_mode)[-3:]}")
    
    # 尝试直接连接数据库
    conn = sqlite3.connect(db_path)
    print("直接连接数据库成功!")
    conn.close()
except Exception as e:
    print(f"测试数据库连接时出错: {str(e)}")
    traceback.print_exc()

# 创建应用实例
try:
    print("正在创建应用实例...")
    app = create_app()
    print("应用实例创建成功！")
except Exception as e:
    print(f"创建应用实例时出错: {str(e)}")
    print("详细错误信息:")
    traceback.print_exc()
    sys.exit(1)

if __name__ == '__main__':
    # 获取环境变量，并允许命令行参数覆盖
    host = args.host or os.environ.get('FLASK_HOST', '0.0.0.0')
    port = args.port or int(os.environ.get('FLASK_PORT', 5101))
    debug = args.debug or os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"启动服务：http://{host}:{port}")
    
    # 启动应用
    try:
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        print(f"启动应用时出错: {str(e)}")
        print("详细错误信息:")
        traceback.print_exc()
        sys.exit(1) 