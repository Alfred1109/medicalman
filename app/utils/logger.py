"""
日志工具模块 - 提供日志记录功能
"""
import sqlite3
import datetime
from flask import current_app
import traceback

def log_user_query(username, query, result=None):
    """
    记录用户查询
    
    参数:
        username: 用户名
        query: 查询内容
        result: 查询结果，默认为None
    """
    try:
        # 获取数据库路径
        db_path = current_app.config.get('DATABASE_PATH', 'instance/medical_workload.db')
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 当前时间
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 如果结果太长，进行截断
        if result and len(str(result)) > 500:
            result = str(result)[:500] + "..."
        
        # 记录日志
        cursor.execute(
            'INSERT INTO logs (user, timestamp, module, level, message, details) VALUES (?, ?, ?, ?, ?, ?)',
            (username, timestamp, 'ai_chat', 'INFO', f'用户查询: {query}', result)
        )
        conn.commit()
        
    except Exception as e:
        current_app.logger.error(f"记录用户查询时出错: {str(e)}")
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

def get_query_logs(limit=100, username=None):
    """
    获取查询日志
    
    参数:
        limit: 返回的日志数量限制
        username: 过滤特定用户的日志，默认为None（返回所有用户）
        
    返回:
        日志列表
    """
    logs = []
    conn = None
    try:
        # 获取数据库路径
        db_path = current_app.config.get('DATABASE_PATH', 'instance/medical_workload.db')
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 构建查询
        query = 'SELECT * FROM logs'
        params = []
        
        if username:
            query += ' WHERE username = ?'
            params.append(username)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        # 执行查询
        cursor.execute(query, params)
        
        # 转换为字典列表
        for row in cursor.fetchall():
            logs.append(dict(row))
        
    except Exception as e:
        current_app.logger.error(f"获取查询日志时出错: {str(e)}")
        traceback.print_exc()
    finally:
        if conn:
            conn.close()
    
    return logs 