import sqlite3
import pandas as pd
import re

def connect_db():
    """
    连接到SQLite数据库并配置行工厂

    返回:
        sqlite3.Connection: 数据库连接对象
    """
    conn = sqlite3.connect("medical_workload.db")
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
    1. outpatient (门诊表):
       - department (TEXT): 科室名称
       - specialty (TEXT): 专科分类
       - visit_date (TEXT): 就诊日期，格式为YYYY-MM-DD
       - visit_count (INTEGER): 就诊人数
    
    2. target (目标表):
       - department (TEXT): 科室名称
       - specialty (TEXT): 专科分类
       - month (TEXT): 目标月份，格式为YYYY-MM
       - target_count (INTEGER): 设定的目标就诊人数
    
    常用查询示例：
    1. 查询某个科室的门诊量：
       SELECT visit_date, SUM(visit_count) as total FROM outpatient WHERE department='内科' GROUP BY visit_date
    
    2. 查询某个时间段的目标完成情况：
       SELECT o.department, o.specialty, SUM(o.visit_count) as actual_count, t.target_count,
       ROUND(SUM(o.visit_count) * 100.0 / t.target_count, 2) as completion_rate
       FROM outpatient o
       JOIN target t ON o.department=t.department AND o.specialty=t.specialty
       WHERE substr(o.visit_date, 1, 7)=t.month
       GROUP BY o.department, o.specialty
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