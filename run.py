"""
应用启动脚本
"""
import os
import argparse
import traceback
import sys
from app import create_app

# 解析命令行参数
parser = argparse.ArgumentParser(description='医疗管理系统')
parser.add_argument('--port', type=int, help='服务端口号', default=None)
parser.add_argument('--host', type=str, help='服务主机地址', default=None)
parser.add_argument('--debug', action='store_true', help='是否开启调试模式')
args = parser.parse_args()

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