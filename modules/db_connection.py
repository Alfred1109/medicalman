import sqlite3
import pandas as pd
import re

def connect_db():
    """连接到数据库"""
    conn = sqlite3.connect("medical_workload.db")
    conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
    return conn

def get_database_schema():
    """获取数据库表结构信息"""
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
    1. 查询某个科室的门诊量：
       SELECT 日期, SUM(数量) as 总量 FROM 门诊量 WHERE 科室='内科' GROUP BY 日期
    
    2. 查询某个时间段的目标完成情况：
       SELECT a.科室, a.专科, SUM(a.数量) as 实际量, b.目标值
       FROM 门诊量 a
       JOIN 目标值 b ON a.科室=b.科室 AND a.专科=b.专科
       WHERE strftime('%Y',a.日期)=b.年 AND strftime('%m',a.日期)=b.月
       GROUP BY a.科室, a.专科
    
    3. 查询DRG指标：
       SELECT department, AVG(weight_score) as 平均权重, AVG(cost_index) as 平均成本指数
       FROM drg_records
       GROUP BY department
    """
    return schema_info

def execute_safe_query(query, params=None):
    """
    安全执行SQL查询
    
    参数:
        query: SQL查询语句
        params: 查询参数(可选)
        
    返回:
        DataFrame: 查询结果
    """
    try:
        conn = connect_db()
        if params:
            df = pd.read_sql_query(query, conn, params=params)
        else:
            df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        print(f"执行查询时出错: {str(e)}")
        return pd.DataFrame()
    finally:
        conn.close()

def validate_sql_query(query):
    """
    验证SQL查询的安全性
    
    参数:
        query: SQL查询语句
        
    返回:
        bool: 查询是否安全
    """
    # 检查是否包含危险关键字
    dangerous_keywords = [
        "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", 
        "TRUNCATE", "REPLACE", "RENAME"
    ]
    
    query_upper = query.upper()
    
    # 检查危险关键字
    for keyword in dangerous_keywords:
        if f" {keyword} " in f" {query_upper} ":
            print(f"检测到危险关键字: {keyword}")
            return False
    
    # 允许的表名（包括中文）
    allowed_tables = ["门诊量", "目标值", "drg_records", "documents"]
    
    # 提取查询中的表名
    # 使用正则表达式匹配FROM和JOIN后面的表名
    table_pattern = r'(?:FROM|JOIN)\s+([^\s,;()]+)'
    tables_in_query = re.findall(table_pattern, query, re.IGNORECASE)
    
    # 验证所有表名是否在允许列表中
    for table in tables_in_query:
        table = table.strip('"\'`[]')  # 移除可能的引号和括号
        if table not in allowed_tables:
            print(f"检测到未授权的表名: {table}")
            return False
    
    return True

def execute_database_queries(queries):
    """
    执行多个数据库查询
    
    参数:
        queries: 包含多个查询的列表，每个查询是一个字典，包含 name 和 sql
        
    返回:
        Dict: 查询结果字典，键为查询名称，值为查询结果DataFrame
    """
    results = {}
    try:
        conn = connect_db()
        
        for query in queries:
            name = query.get('name')
            sql = query.get('sql')
            
            if name and sql:
                try:
                    df = pd.read_sql_query(sql, conn)
                    results[name] = df
                except Exception as e:
                    print(f"执行查询 {name} 时出错: {str(e)}")
                    results[name] = None
                    
        return results
    except Exception as e:
        print(f"执行数据库查询时出错: {str(e)}")
        return results
    finally:
        if 'conn' in locals():
            conn.close() 