"""
数据库连接和基础操作模块
"""
import sqlite3
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
import os
from flask import current_app

def init_db(app):
    """
    初始化数据库
    
    参数:
        app: Flask应用实例
    """
    try:
        db_path = app.config.get('DATABASE_PATH', 'instance/medical_workload.db')
        app.logger.info(f"初始化数据库: {db_path}")
        
        # 确保数据库所在目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 如果数据库文件不存在，则创建必要的表
        if not os.path.exists(db_path):
            app.logger.info("数据库文件不存在，创建新数据库")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 创建用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    query TEXT NOT NULL,
                    result TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建知识库表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_base_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            app.logger.info("基础表结构创建完成")
        else:
            app.logger.info("数据库已存在，跳过初始化")
            
    except Exception as e:
        app.logger.error(f"初始化数据库出错: {str(e)}")
        raise

class Database:
    """数据库连接和操作类"""
    
    @staticmethod
    def get_connection():
        """获取数据库连接"""
        db_path = current_app.config.get('DATABASE_PATH', 'instance/medical_workload.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        return conn
    
    @staticmethod
    def execute_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        执行查询并返回结果
        
        参数:
            query: SQL查询语句
            params: 查询参数
            
        返回:
            查询结果列表
        """
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            return results
        finally:
            conn.close()
    
    @staticmethod
    def execute_update(query: str, params: tuple = ()) -> int:
        """
        执行更新操作并返回受影响的行数
        
        参数:
            query: SQL更新语句
            params: 更新参数
            
        返回:
            受影响的行数
        """
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()
    
    @staticmethod
    def query_to_dataframe(query: str, params: tuple = ()) -> pd.DataFrame:
        """
        执行查询并返回DataFrame
        
        参数:
            query: SQL查询语句
            params: 查询参数
            
        返回:
            查询结果DataFrame
        """
        conn = Database.get_connection()
        try:
            return pd.read_sql_query(query, conn, params=params)
        finally:
            conn.close()
    
    @staticmethod
    def get_database_schema() -> str:
        """
        获取数据库表结构信息
        
        返回:
            数据库结构描述字符串
        """
        schema_info = """
        数据库包含以下表：
        1. 门诊量:
           - 科室 (TEXT): 医院的科室名称
           - 专科 (TEXT): 科室下的专科分类
           - 日期 (TEXT): 数据记录的日期，格式为YYYY-MM-DD
           - 数量 (REAL): 就诊人数
        
        2. 目标值:
           - 科室 (TEXT): 医院的科室名称
           - 专科 (TEXT): 科室下的专科分类
           - 年 (TEXT): 目标年份
           - 月 (TEXT): 目标月份
           - 目标值 (INTEGER): 设定的目标就诊人数
        
        3. drg_records:
           - record_date (DATE): 记录日期
           - department (TEXT): 科室名称
           - drg_group (TEXT): DRG分组
           - weight_score (REAL): 权重分值
           - cost_index (REAL): 成本指数
           - time_index (REAL): 时间指数
           - total_cost (REAL): 总成本
           - length_of_stay (INTEGER): 住院天数
        
        常用查询示例：
        1. 查询门诊量的月度趋势：
           SELECT strftime('%Y-%m', 日期) as 月份, SUM(数量) as 总门诊量 
           FROM 门诊量 
           GROUP BY strftime('%Y-%m', 日期) 
           ORDER BY 月份
        
        2. 查询某个科室的门诊量：
           SELECT 日期, SUM(数量) as 总量 FROM 门诊量 WHERE 科室='内科' GROUP BY 日期
        
        3. 查询某个时间段的目标完成情况：
           SELECT a.科室, a.专科, SUM(a.数量) as 实际量, b.目标值
           FROM 门诊量 a
           JOIN 目标值 b ON a.科室=b.科室 AND a.专科=b.专科
           WHERE strftime('%Y',a.日期)=b.年 AND strftime('%m',a.日期)=b.月
           GROUP BY a.科室, a.专科
        
        4. 查询DRG指标：
           SELECT department, AVG(weight_score) as 平均权重, AVG(cost_index) as 平均成本指数
           FROM drg_records
           GROUP BY department
        """
        return schema_info
    
    @staticmethod
    def validate_sql_query(query: str) -> bool:
        """
        验证SQL查询是否安全
        
        参数:
            query: SQL查询语句
            
        返回:
            查询是否安全
        """
        # 检查是否包含危险操作
        dangerous_keywords = [
            "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", 
            "TRUNCATE", "GRANT", "REVOKE", "ATTACH", "DETACH"
        ]
        
        # 将查询转换为大写以便检查关键字
        query_upper = query.upper()
        
        # 检查是否包含危险关键字
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return False
        
        return True 