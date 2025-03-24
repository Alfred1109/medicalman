import sqlite3
import pandas as pd
import re
import os
from contextlib import contextmanager

def connect_db():
    """
    连接到SQLite数据库并配置行工厂

    返回:
        sqlite3.Connection: 数据库连接对象
    """
    db_path = os.path.join("instance", "medical_workload.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
    return conn

def get_database_schema():
    """
    获取数据库表结构信息
    
    返回:
        str: 数据库结构的描述文本
    """
    schema_info = """
    数据库包含以下表：
    1. 门诊量 (门诊表):
       - 科室 (TEXT): 科室名称
       - 专科 (TEXT): 专科分类
       - 日期 (TEXT): 就诊日期，格式为YYYY-MM-DD
       - 数量 (REAL): 就诊人数
    
    2. 目标值 (目标表):
       - 科室 (TEXT): 科室名称
       - 专科 (TEXT): 专科分类
       - 年 (TEXT): 年份
       - 月 (TEXT): 月份
       - 目标值 (INTEGER): 设定的目标就诊人数
    
    常用查询示例：
    1. 查询某个科室的门诊量：
       SELECT 日期, SUM(数量) as total FROM 门诊量 WHERE 科室='内科' GROUP BY 日期
    
    2. 查询某个时间段的目标完成情况：
       SELECT o.科室, o.专科, SUM(o.数量) as actual_count, t.目标值,
       ROUND(SUM(o.数量) * 100.0 / t.目标值, 2) as completion_rate
       FROM 门诊量 o
       JOIN 目标值 t ON o.科室=t.科室 AND o.专科=t.专科
       WHERE strftime('%Y', o.日期)=t.年 AND strftime('%m', o.日期)=t.月
       GROUP BY o.科室, o.专科
    """
    return schema_info

def execute_database_queries(query, params=None):
    """
    执行SQL查询并返回结果
    
    参数:
        query (str): SQL查询语句
        params (tuple, optional): 查询参数
        
    返回:
        list: 查询结果
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        results = cursor.fetchall()
        conn.close()
        
        # 将结果转换为字典列表
        result_list = []
        for row in results:
            row_dict = {key: row[key] for key in row.keys()}
            result_list.append(row_dict)
        
        return result_list
    except Exception as e:
        print(f"执行查询时出错: {str(e)}")
        return []

def execute_query_to_dataframe(query, params=None):
    """
    执行SQL查询并返回pandas DataFrame
    
    参数:
        query (str): SQL查询语句
        params (tuple, optional): 查询参数
        
    返回:
        pandas.DataFrame: 查询结果
    """
    try:
        conn = connect_db()
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        print(f"执行查询时出错: {str(e)}")
        return pd.DataFrame()

def get_outpatient_data(department=None, specialty=None, start_date=None, end_date=None):
    """
    获取门诊量数据
    
    参数:
        department (str, optional): 科室名称
        specialty (str, optional): 专科分类
        start_date (str, optional): 开始日期，格式为YYYY-MM-DD
        end_date (str, optional): 结束日期，格式为YYYY-MM-DD
        
    返回:
        pandas.DataFrame: 门诊量数据
    """
    try:
        query = "SELECT * FROM 门诊量 WHERE 1=1"
        params = []
        
        if department:
            query += " AND 科室=?"
            params.append(department)
            
        if specialty:
            query += " AND 专科=?"
            params.append(specialty)
            
        if start_date:
            query += " AND 日期>=?"
            params.append(start_date)
            
        if end_date:
            query += " AND 日期<=?"
            params.append(end_date)
            
        query += " ORDER BY 日期"
        
        conn = connect_db()
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        print(f"获取门诊量数据出错: {str(e)}")
        return pd.DataFrame()

def get_target_data(department=None, specialty=None, year=None, month=None):
    """
    获取目标值数据
    
    参数:
        department (str, optional): 科室名称
        specialty (str, optional): 专科分类
        year (str, optional): 年份
        month (str, optional): 月份
        
    返回:
        pandas.DataFrame: 目标值数据
    """
    try:
        query = "SELECT * FROM 目标值 WHERE 1=1"
        params = []
        
        if department:
            query += " AND 科室=?"
            params.append(department)
            
        if specialty:
            query += " AND 专科=?"
            params.append(specialty)
            
        if year:
            query += " AND 年=?"
            params.append(year)
            
        if month:
            query += " AND 月=?"
            params.append(month)
            
        query += " ORDER BY 年, 月"
        
        conn = connect_db()
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        print(f"获取目标值数据出错: {str(e)}")
        return pd.DataFrame()

def get_completion_rate(year=None, month=None):
    """
    获取目标完成率数据
    
    参数:
        year (str, optional): 年份
        month (str, optional): 月份
        
    返回:
        pandas.DataFrame: 目标完成率数据
    """
    try:
        query = """
            SELECT 
                o.科室, 
                o.专科, 
                SUM(o.数量) as 实际量, 
                t.目标值,
                ROUND(SUM(o.数量) * 100.0 / t.目标值, 2) as 完成率
            FROM 门诊量 o
            JOIN 目标值 t ON o.科室=t.科室 AND o.专科=t.专科
            WHERE strftime('%Y', o.日期)=t.年 AND strftime('%m', o.日期)=t.月
        """
        params = []
        
        if year and month:
            query += " AND t.年=? AND t.月=?"
            params.append(year)
            params.append(month)
        
        query += " GROUP BY o.科室, o.专科"
        
        conn = connect_db()
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        print(f"获取目标完成率数据出错: {str(e)}")
        return pd.DataFrame()

# 添加数据库光标上下文管理器
@contextmanager
def db_cursor():
    """
    获取数据库光标的上下文管理器，自动处理提交和回滚操作
    
    用法示例:
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
    
    返回:
        sqlite3.Cursor: 数据库光标对象
    """
    conn = connect_db()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close() 