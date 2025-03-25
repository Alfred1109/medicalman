"""
数据库工具模块 - 提供统一的数据库操作接口
"""
import sqlite3
import os
import json
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from contextlib import contextmanager
import time
import logging
from flask import current_app
import pandas as pd
import traceback

from app.config import config
from app.utils.error_handler import ErrorType, ErrorCode, error_response
from app.utils.logger import log_query, log_error

# 连接数据库
@contextmanager
def get_db_connection():
    """
    获取数据库连接
    
    返回:
        数据库连接
    """
    try:
        # 从应用配置中获取数据库路径
        database_path = config.DATABASE_PATH
        
        # 确保数据库文件所在目录存在
        os.makedirs(os.path.dirname(database_path), exist_ok=True)
        
        # 创建连接
        conn = sqlite3.connect(database_path)
        conn.row_factory = sqlite3.Row  # 使结果以字典形式返回
        
        # 设置数据库参数
        for pragma, value in config.DB_PRAGMA_SETTINGS.items():
            conn.execute(f"PRAGMA {pragma} = {value}")
        
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        log_error(config.DB_ERROR_MESSAGES['connection_error'].format(str(e)), 
                  error_code=config.DB_ERROR_CODES['connection'], 
                  error_type=ErrorType.DATABASE_ERROR)
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        if 'conn' in locals():
            conn.close()

# 执行SQL查询
def execute_query(query: str, params: Optional[Tuple] = None, fetch_one: bool = False) -> Union[List[Dict], Dict, None]:
    """
    执行SQL查询
    
    参数:
        query: SQL查询
        params: 查询参数
        fetch_one: 是否只获取一条记录
        
    返回:
        查询结果
    """
    start_time = time.time()
    params = params or ()
    result = None
    
    try:
        with get_db_connection() as conn:
            cur = conn.execute(query, params)
            
            if query.strip().upper().startswith(('SELECT', 'PRAGMA')):
                if fetch_one:
                    row = cur.fetchone()
                    result = dict(row) if row else None
                else:
                    rows = cur.fetchall()
                    result = [dict(row) for row in rows]
            else:
                result = {"affected_rows": cur.rowcount, "last_insert_id": cur.lastrowid}
        
        # 记录查询（仅记录SELECT，不记录参数以避免敏感信息泄露）
        if query.strip().upper().startswith('SELECT'):
            execution_time = time.time() - start_time
            log_query(query, execution_time)
            
        return result
    except sqlite3.Error as e:
        error_message = str(e)
        log_error(config.DB_ERROR_MESSAGES['query_error'].format(error_message), 
                  error_code=config.DB_ERROR_CODES['query'], 
                  error_type=ErrorType.DATABASE_ERROR,
                  details={"query": query})
        raise

# 事务处理
@contextmanager
def transaction():
    """
    事务上下文管理器
    """
    conn = None
    try:
        database_path = config.DATABASE_PATH
        conn = sqlite3.connect(database_path)
        conn.row_factory = sqlite3.Row
        
        # 设置数据库参数
        for pragma, value in config.DB_PRAGMA_SETTINGS.items():
            conn.execute(f"PRAGMA {pragma} = {value}")
            
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        log_error(config.DB_ERROR_MESSAGES['transaction_error'].format(str(e)), 
                  error_code=config.DB_ERROR_CODES['transaction'], 
                  error_type=ErrorType.DATABASE_ERROR)
        raise
    finally:
        if conn:
            conn.close()

# 通用CRUD操作
def insert_record(table: str, data: Dict[str, Any]) -> Optional[int]:
    """
    插入记录
    
    参数:
        table: 表名
        data: 记录数据
        
    返回:
        新记录ID或None
    """
    try:
        # 构建SQL
        placeholders = ', '.join(['?'] * len(data))
        columns = ', '.join(data.keys())
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        with get_db_connection() as conn:
            cur = conn.execute(query, tuple(data.values()))
            return cur.lastrowid
    except sqlite3.Error as e:
        log_error(config.DB_ERROR_MESSAGES['data_error'].format(str(e)), 
                  error_code=config.DB_ERROR_CODES['data'], 
                  error_type=ErrorType.DATABASE_ERROR,
                  details={"table": table})
        return None

def update_record(table: str, data: Dict[str, Any], condition: str, params: Tuple) -> bool:
    """
    更新记录
    
    参数:
        table: 表名
        data: 更新数据
        condition: 条件
        params: 条件参数
        
    返回:
        是否成功
    """
    try:
        # 构建SQL
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        
        # 组合参数（先是SET子句的参数，再是WHERE子句的参数）
        all_params = tuple(data.values()) + params
        
        with get_db_connection() as conn:
            conn.execute(query, all_params)
            return True
    except sqlite3.Error as e:
        log_error(config.DB_ERROR_MESSAGES['data_error'].format(str(e)), 
                  error_code=config.DB_ERROR_CODES['data'], 
                  error_type=ErrorType.DATABASE_ERROR,
                  details={"table": table})
        return False

def delete_record(table: str, condition: str, params: Tuple) -> bool:
    """
    删除记录
    
    参数:
        table: 表名
        condition: 条件
        params: 条件参数
        
    返回:
        是否成功
    """
    try:
        query = f"DELETE FROM {table} WHERE {condition}"
        
        with get_db_connection() as conn:
            conn.execute(query, params)
            return True
    except sqlite3.Error as e:
        log_error(config.DB_ERROR_MESSAGES['data_error'].format(str(e)), 
                  error_code=config.DB_ERROR_CODES['data'], 
                  error_type=ErrorType.DATABASE_ERROR,
                  details={"table": table})
        return False

def get_record(table: str, fields: str = '*', condition: str = '', params: Tuple = ()) -> Optional[Dict]:
    """
    获取单条记录
    
    参数:
        table: 表名
        fields: 字段
        condition: 条件
        params: 条件参数
        
    返回:
        记录或None
    """
    try:
        query = f"SELECT {fields} FROM {table}"
        if condition:
            query += f" WHERE {condition}"
        
        with get_db_connection() as conn:
            cur = conn.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None
    except sqlite3.Error as e:
        log_error(config.DB_ERROR_MESSAGES['query_error'].format(str(e)), 
                  error_code=config.DB_ERROR_CODES['query'], 
                  error_type=ErrorType.DATABASE_ERROR,
                  details={"table": table})
        return None

def get_records(table: str, fields: str = '*', condition: str = '', params: Tuple = (), 
               order_by: str = '', limit: int = 0, offset: int = 0) -> List[Dict]:
    """
    获取多条记录
    
    参数:
        table: 表名
        fields: 字段
        condition: 条件
        params: 条件参数
        order_by: 排序
        limit: 限制
        offset: 偏移
        
    返回:
        记录列表
    """
    try:
        query = f"SELECT {fields} FROM {table}"
        if condition:
            query += f" WHERE {condition}"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {limit}"
        if offset:
            query += f" OFFSET {offset}"
        
        with get_db_connection() as conn:
            cur = conn.execute(query, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    except sqlite3.Error as e:
        log_error(f"获取记录列表错误: {str(e)}", 
                  error_code=ErrorCode.DB_QUERY_ERROR, 
                  error_type=ErrorType.DATABASE_ERROR,
                  details={"table": table})
        return []

def count_records(table: str, condition: str = '', params: Tuple = ()) -> int:
    """
    统计记录数
    
    参数:
        table: 表名
        condition: 条件
        params: 条件参数
        
    返回:
        记录数
    """
    try:
        query = f"SELECT COUNT(*) AS count FROM {table}"
        if condition:
            query += f" WHERE {condition}"
        
        with get_db_connection() as conn:
            cur = conn.execute(query, params)
            row = cur.fetchone()
            return row['count'] if row else 0
    except sqlite3.Error as e:
        log_error(f"统计记录数错误: {str(e)}", 
                  error_code=ErrorCode.DB_QUERY_ERROR, 
                  error_type=ErrorType.DATABASE_ERROR,
                  details={"table": table})
        return 0

# 数据库初始化
def init_database(schema_file: str = None) -> bool:
    """
    初始化数据库
    
    参数:
        schema_file: SQL schema文件路径（可选）
        
    返回:
        是否成功
    """
    try:
        # 从应用配置中获取数据库路径
        database_path = config.DATABASE_PATH
        
        # 确保目录存在
        os.makedirs(os.path.dirname(database_path), exist_ok=True)
        
        # 创建数据库连接
        conn = sqlite3.connect(database_path)
        
        # 启用外键约束
        conn.execute("PRAGMA foreign_keys = ON")
        
        # 如果提供了schema文件，则使用它
        if schema_file and os.path.exists(schema_file):
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema = f.read()
            conn.executescript(schema)
        else:
            # 否则创建必要的表结构
            create_mock_tables(conn)
            
            # 插入模拟数据
            insert_mock_data(conn)
        
        conn.commit()
        conn.close()
        
        return True
    except (sqlite3.Error, IOError) as e:
        log_error(f"初始化数据库错误: {str(e)}", 
                  error_code=ErrorCode.DB_INIT_ERROR, 
                  error_type=ErrorType.DATABASE_ERROR)
        return False

def create_mock_tables(conn):
    """创建模拟表结构"""
    # 创建门诊表
    conn.execute('''
    CREATE TABLE IF NOT EXISTS visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        visit_date TEXT NOT NULL,
        visit_type TEXT NOT NULL,
        department TEXT NOT NULL,
        patient_id TEXT,
        doctor_id TEXT,
        visit_reason TEXT,
        diagnosis TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建手术表
    conn.execute('''
    CREATE TABLE IF NOT EXISTS surgeries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        surgery_date TEXT NOT NULL,
        patient_id TEXT NOT NULL,
        doctor_id TEXT NOT NULL,
        department TEXT NOT NULL,
        surgery_type TEXT NOT NULL,
        duration INTEGER,  -- 手术时长（分钟）
        status TEXT DEFAULT 'completed',
        complications TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建收入表
    conn.execute('''
    CREATE TABLE IF NOT EXISTS revenue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        revenue_type TEXT NOT NULL,
        amount REAL NOT NULL,
        department TEXT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 创建住院表
    conn.execute('''
    CREATE TABLE IF NOT EXISTS admissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        admission_date TEXT NOT NULL,
        discharge_date TEXT,
        length_of_stay INTEGER,
        department TEXT NOT NULL,
        diagnosis_group TEXT,
        doctor_id TEXT,
        status TEXT DEFAULT 'active',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建警报表
    conn.execute('''
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_time TEXT NOT NULL,
        alert_type TEXT NOT NULL, -- critical, warning, info
        description TEXT NOT NULL,
        status TEXT DEFAULT 'new', -- new, processing, resolved, ignored
        related_entity TEXT, -- department, patient, system
        related_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建门诊量表（中文表名示例）
    conn.execute('''
    CREATE TABLE IF NOT EXISTS 门诊量 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        科室 TEXT NOT NULL,
        专科 TEXT,
        日期 TEXT NOT NULL,
        数量 INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建目标值表（中文表名示例）
    conn.execute('''
    CREATE TABLE IF NOT EXISTS 目标值 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        科室 TEXT NOT NULL,
        专科 TEXT,
        年 TEXT NOT NULL,
        月 TEXT NOT NULL,
        目标值 INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建DRG记录表
    conn.execute('''
    CREATE TABLE IF NOT EXISTS drg_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_date TEXT NOT NULL,
        department TEXT NOT NULL,
        drg_group TEXT NOT NULL,
        weight_score REAL,
        cost_index REAL,
        time_index REAL,
        total_cost REAL,
        length_of_stay INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建聊天会话表
    conn.execute('''
    CREATE TABLE IF NOT EXISTS chats (
        chat_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建聊天消息表
    conn.execute('''
    CREATE TABLE IF NOT EXISTS chat_messages (
        message_id TEXT PRIMARY KEY,
        chat_id TEXT NOT NULL,
        role TEXT NOT NULL,  -- user或ai
        content TEXT NOT NULL,
        content_type TEXT DEFAULT 'text',  -- text, markdown, html
        time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        structured_data TEXT,  -- 存储JSON格式的结构化数据，如图表、表格等
        FOREIGN KEY (chat_id) REFERENCES chats(chat_id)
    )
    ''')

def insert_mock_data(conn):
    """插入模拟数据"""
    import random
    from datetime import datetime, timedelta
    
    # 获取当前日期
    current_date = datetime.now()
    
    # 科室列表
    departments = ['内科', '外科', '妇产科', '儿科', '眼科', '骨科', '皮肤科', '神经科', '耳鼻喉科', '口腔科']
    
    # 专科列表
    specialties = {
        '内科': ['心内科', '消化内科', '呼吸内科', '内分泌科', '肾内科', '血液科', '风湿免疫科'],
        '外科': ['普通外科', '胸外科', '心脏外科', '神经外科', '泌尿外科', '整形外科', '烧伤科'],
        '妇产科': ['妇科', '产科', '计划生育科', '生殖医学科'],
        '儿科': ['儿科综合', '新生儿科', '儿童保健科', '小儿内科', '小儿外科'],
        '眼科': ['眼科综合', '白内障科', '青光眼科', '眼底病科', '屈光科'],
        '骨科': ['脊柱外科', '关节外科', '创伤骨科', '手外科', '足踝外科'],
        '皮肤科': ['皮肤综合', '性病科', '皮肤美容科'],
        '神经科': ['神经内科', '神经外科', '神经康复科'],
        '耳鼻喉科': ['耳科', '鼻科', '咽喉科', '头颈外科'],
        '口腔科': ['口腔内科', '口腔外科', '正畸科', '修复科', '种植科']
    }
    
    # 收入类型
    revenue_types = ['门诊', '住院', '药房', '检查', '手术', '其他']
    
    # 诊断组
    diagnosis_groups = ['心血管疾病', '呼吸系统疾病', '消化系统疾病', '神经系统疾病', '骨科疾病', 
                        '内分泌疾病', '感染性疾病', '肿瘤', '妇产科疾病', '儿科疾病']
    
    # 手术类型
    surgery_types = ['普通外科手术', '骨科手术', '心脏手术', '神经外科手术', '眼科手术', 
                    '耳鼻喉科手术', '妇产科手术', '泌尿外科手术', '整形外科手术', '微创手术']
    
    # 手术并发症
    complications = [None, None, None, None, '出血', '感染', '过敏反应', '麻醉并发症', '心律失常', '伤口裂开']
    
    # 警报类型和状态
    alert_types = ['critical', 'warning', 'info']
    alert_statuses = ['new', 'processing', 'resolved', 'ignored']
    alert_descriptions = [
        'ICU床位使用率超过95%',
        '心内科门诊量异常增加',
        '系统维护通知',
        '药品库存不足警告',
        '设备维护提醒',
        '人员配置警告',
        '门诊等待时间过长',
        '收入异常波动',
        '患者满意度降低',
        '急诊科负荷过高'
    ]
    
    # 插入门诊记录
    for i in range(1000):
        # 随机日期（过去30天内）
        days_ago = random.randint(0, 30)
        visit_date = (current_date - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        # 随机科室
        department = random.choice(departments)
        
        # 随机专科
        specialty = random.choice(specialties[department]) if department in specialties else None
        
        # 门诊类型
        visit_type = '门诊' if random.random() < 0.7 else '急诊'
        
        # 患者ID和医生ID
        patient_id = f'P{random.randint(10000, 99999)}'
        doctor_id = f'D{random.randint(100, 999)}'
        
        # 插入数据
        conn.execute(
            'INSERT INTO visits (date, visit_date, visit_type, department, patient_id, doctor_id) VALUES (?, ?, ?, ?, ?, ?)',
            (visit_date, visit_date, visit_type, department, patient_id, doctor_id)
        )
        
        # 插入门诊量数据
        visit_count = random.randint(1, 5)  # 每条记录代表1-5人次
        conn.execute(
            'INSERT INTO 门诊量 (科室, 专科, 日期, 数量) VALUES (?, ?, ?, ?)',
            (department, specialty, visit_date, visit_count)
        )
        
        # 插入目标值数据（每月一次）
        if i % 30 == 0:
            year = visit_date.split('-')[0]
            month = visit_date.split('-')[1]
            target_value = random.randint(50, 200) * 30  # 月目标值
            conn.execute(
                'INSERT INTO 目标值 (科室, 专科, 年, 月, 目标值) VALUES (?, ?, ?, ?, ?)',
                (department, specialty, year, month, target_value)
            )
    
    # 插入手术记录
    for i in range(200):
        # 随机日期（过去30天内）
        days_ago = random.randint(0, 30)
        surgery_date = (current_date - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        # 随机患者ID和医生ID
        patient_id = f'P{random.randint(10000, 99999)}'
        doctor_id = f'D{random.randint(100, 999)}'
        
        # 随机科室和手术类型
        department = random.choice(departments)
        surgery_type = random.choice(surgery_types)
        
        # 随机手术时长（30分钟到5小时）
        duration = random.randint(30, 300)
        
        # 随机状态
        status = random.choice(['scheduled', 'in_progress', 'completed', 'cancelled'])
        
        # 随机并发症
        complication = random.choice(complications)
        
        # 随机备注
        notes = f'患者{patient_id}的{surgery_type}' if random.random() < 0.3 else None
        
        # 插入数据
        conn.execute(
            'INSERT INTO surgeries (surgery_date, patient_id, doctor_id, department, surgery_type, duration, status, complications, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (surgery_date, patient_id, doctor_id, department, surgery_type, duration, status, complication, notes)
        )
    
    # 插入收入记录
    for i in range(500):
        # 随机日期（过去30天内）
        days_ago = random.randint(0, 30)
        revenue_date = (current_date - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        # 随机科室
        department = random.choice(departments)
        
        # 随机收入类型
        revenue_type = random.choice(revenue_types)
        
        # 随机金额
        amount = round(random.uniform(100, 10000), 2)
        
        # 描述
        description = f'{department}{revenue_type}收入'
        
        # 插入数据
        conn.execute(
            'INSERT INTO revenue (date, revenue_type, amount, department, description) VALUES (?, ?, ?, ?, ?)',
            (revenue_date, revenue_type, amount, department, description)
        )
    
    # 插入住院记录
    for i in range(300):
        # 随机日期（过去60天内）
        days_ago = random.randint(0, 60)
        admission_date = (current_date - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        # 随机住院天数
        length_of_stay = random.randint(1, 30)
        
        # 计算出院日期（如果已出院）
        if days_ago > length_of_stay:
            discharge_date = (current_date - timedelta(days=days_ago-length_of_stay)).strftime('%Y-%m-%d')
            status = 'discharged'
        else:
            discharge_date = None
            status = 'active'
            length_of_stay = days_ago  # 仍在住院，住院天数为已经过去的天数
        
        # 随机科室和诊断组
        department = random.choice(departments)
        diagnosis_group = random.choice(diagnosis_groups)
        
        # 患者ID和医生ID
        patient_id = f'P{random.randint(10000, 99999)}'
        doctor_id = f'D{random.randint(100, 999)}'
        
        # 插入数据
        conn.execute(
            'INSERT INTO admissions (patient_id, admission_date, discharge_date, length_of_stay, department, diagnosis_group, doctor_id, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (patient_id, admission_date, discharge_date, length_of_stay, department, diagnosis_group, doctor_id, status)
        )
    
    # 插入警报记录
    for i in range(50):
        # 随机日期（过去7天内）
        days_ago = random.randint(0, 7)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        alert_time = (current_date - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)).strftime('%Y-%m-%d %H:%M:%S')
        
        # 随机警报类型和状态
        alert_type = random.choice(alert_types)
        status = random.choice(alert_statuses)
        
        # 随机描述
        description = random.choice(alert_descriptions)
        
        # 随机关联实体
        related_entity = random.choice(['department', 'patient', 'system', None])
        related_id = random.randint(1, 100) if related_entity else None
        
        # 插入数据
        conn.execute(
            'INSERT INTO alerts (alert_time, alert_type, description, status, related_entity, related_id) VALUES (?, ?, ?, ?, ?, ?)',
            (alert_time, alert_type, description, status, related_entity, related_id)
        )
        
    # 插入DRG记录
    for i in range(200):
        # 随机日期（过去90天内）
        days_ago = random.randint(0, 90)
        record_date = (current_date - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        # 随机科室
        department = random.choice(departments)
        
        # 随机DRG组
        drg_group = f'DRG{random.randint(1, 30):02d}'
        
        # 随机权重分值
        weight_score = round(random.uniform(0.5, 3.0), 2)
        
        # 随机成本和时间指数
        cost_index = round(random.uniform(0.8, 1.2), 2)
        time_index = round(random.uniform(0.8, 1.2), 2)
        
        # 随机总成本和住院天数
        total_cost = round(random.uniform(5000, 50000), 2)
        length_of_stay = random.randint(1, 20)
        
        # 插入数据
        conn.execute(
            'INSERT INTO drg_records (record_date, department, drg_group, weight_score, cost_index, time_index, total_cost, length_of_stay) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (record_date, department, drg_group, weight_score, cost_index, time_index, total_cost, length_of_stay)
        )
    
    # 插入聊天记录
    import uuid
    
    # 创建几个聊天会话
    for i in range(5):
        # 生成聊天ID
        chat_id = str(uuid.uuid4())
        
        # 随机用户ID
        user_id = f'user_{random.randint(1, 10)}'
        
        # 聊天标题
        titles = [
            "问诊记录", 
            "医疗指标咨询", 
            "科室绩效分析", 
            "DRG分析讨论",
            "医疗工作量分析"
        ]
        title = titles[i]
        
        # 创建时间（过去30天内）
        days_ago = random.randint(0, 30)
        chat_time = (current_date - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
        
        # 插入聊天会话
        conn.execute(
            'INSERT INTO chats (chat_id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
            (chat_id, user_id, title, chat_time, chat_time)
        )
        
        # 为每个聊天添加3-8条消息
        messages_count = random.randint(3, 8)
        for j in range(messages_count):
            # 消息ID
            message_id = str(uuid.uuid4())
            
            # 角色交替
            role = 'user' if j % 2 == 0 else 'ai'
            
            # 内容和类型
            content_type = 'text' if role == 'user' else 'markdown'
            
            # 用户提问
            user_questions = [
                "请分析一下我们科室的工作量情况",
                "最近儿科的门诊量如何？",
                "DRG绩效指标跟去年相比有什么变化？",
                "各科室收入构成是怎样的？",
                "请对比一下内科和外科的工作量"
            ]
            
            # AI回复
            ai_responses = [
                "根据数据分析，您科室的工作量在过去30天内总体呈上升趋势。门诊量增长了12.5%，住院量增长了8.3%。\n\n主要增长点在以下几个方面：\n1. 专科门诊患者增加\n2. 手术量提升\n3. 平均住院日缩短",
                "儿科门诊量数据显示，过去30天内总接诊量为1,245人次，较上月增长15.8%，较去年同期增长23.4%。其中，呼吸道感染患者占比最高，达42.3%。",
                "DRG绩效指标与去年相比有显著提升。CMI指数从0.95上升到1.12，提高了17.9%。时间指数从1.05下降到0.98，表明医疗效率有所提高。总体来看，DRG管理水平有明显进步。",
                "各科室收入构成分析如下：\n\n1. 内科：门诊收入占比42%，住院收入占比47%，其他收入占比11%\n2. 外科：门诊收入占比25%，住院收入占比65%，其他收入占比10%\n3. 妇产科：门诊收入占比38%，住院收入占比52%，其他收入占比10%",
                "内科和外科工作量对比分析：\n\n- 门诊量：内科3,256人次/月，外科2,187人次/月\n- 住院量：内科528人次/月，外科823人次/月\n- 手术量：内科85台/月，外科372台/月\n- 平均住院日：内科8.3天，外科6.7天"
            ]
            
            if role == 'user':
                content = random.choice(user_questions)
            else:
                content = random.choice(ai_responses)
                
            # 消息时间（从聊天创建时间往后递增）
            msg_minutes_later = j * random.randint(2, 10)
            message_time = (datetime.strptime(chat_time, '%Y-%m-%d %H:%M:%S') + timedelta(minutes=msg_minutes_later)).strftime('%Y-%m-%d %H:%M:%S')
            
            # 结构化数据（仅AI回复有）
            structured_data = None
            if role == 'ai':
                # 随机决定是否添加结构化数据
                if random.random() > 0.3:
                    # 表格数据示例
                    table_data = {
                        'tables': [
                            {
                                'title': '科室工作量统计',
                                'type': 'table',
                                'headers': ['科室', '门诊量', '住院量', '手术量', '增长率'],
                                'rows': [
                                    ['内科', '3256', '528', '85', '12.5%'],
                                    ['外科', '2187', '823', '372', '8.7%'],
                                    ['妇产科', '1875', '463', '212', '15.2%'],
                                    ['儿科', '1245', '156', '45', '23.4%'],
                                    ['骨科', '978', '325', '203', '5.6%']
                                ]
                            }
                        ]
                    }
                    structured_data = json.dumps(table_data, ensure_ascii=False)
            
            # 插入消息
            if structured_data:
                conn.execute(
                    'INSERT INTO chat_messages (message_id, chat_id, role, content, content_type, time, structured_data) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (message_id, chat_id, role, content, content_type, message_time, structured_data)
                )
            else:
                conn.execute(
                    'INSERT INTO chat_messages (message_id, chat_id, role, content, content_type, time) VALUES (?, ?, ?, ?, ?, ?)',
                    (message_id, chat_id, role, content, content_type, message_time)
                )

# JSON字段处理
def json_field_handler(conn, obj):
    """
    自定义JSON字段处理器，用于将Python对象转换为JSON字符串
    """
    if isinstance(obj, (dict, list)):
        return json.dumps(obj, ensure_ascii=False)
    return obj

def register_json_converter():
    """
    注册JSON转换器
    """
    sqlite3.register_adapter(dict, lambda d: json.dumps(d, ensure_ascii=False))
    sqlite3.register_adapter(list, lambda l: json.dumps(l, ensure_ascii=False))
    sqlite3.register_converter("JSON", lambda s: json.loads(s.decode('utf-8')))

# 注册JSON转换器
register_json_converter()

# 高级查询构建器
class QueryBuilder:
    """
    SQL查询构建器
    """
    def __init__(self, table: str):
        self.table = table
        self.fields = '*'
        self.conditions = []
        self.params = []
        self.order_by_clause = ''
        self.limit_value = 0
        self.offset_value = 0
        self.joins = []
        self.group_by_clause = ''
        self.having_clause = ''
        self.having_params = []
        
    def select(self, fields: str) -> 'QueryBuilder':
        """设置选择字段"""
        self.fields = fields
        return self
        
    def where(self, condition: str, *params) -> 'QueryBuilder':
        """添加WHERE条件"""
        self.conditions.append(condition)
        self.params.extend(params)
        return self
        
    def order_by(self, clause: str) -> 'QueryBuilder':
        """设置排序"""
        self.order_by_clause = clause
        return self
        
    def limit(self, value: int) -> 'QueryBuilder':
        """设置限制"""
        self.limit_value = value
        return self
        
    def offset(self, value: int) -> 'QueryBuilder':
        """设置偏移"""
        self.offset_value = value
        return self
        
    def join(self, table: str, condition: str, join_type: str = 'INNER') -> 'QueryBuilder':
        """添加JOIN"""
        self.joins.append((join_type, table, condition))
        return self
        
    def left_join(self, table: str, condition: str) -> 'QueryBuilder':
        """添加LEFT JOIN"""
        return self.join(table, condition, 'LEFT')
        
    def right_join(self, table: str, condition: str) -> 'QueryBuilder':
        """添加RIGHT JOIN"""
        return self.join(table, condition, 'RIGHT')
        
    def group_by(self, clause: str) -> 'QueryBuilder':
        """设置GROUP BY"""
        self.group_by_clause = clause
        return self
        
    def having(self, condition: str, *params) -> 'QueryBuilder':
        """添加HAVING条件"""
        self.having_clause = condition
        self.having_params.extend(params)
        return self
        
    def build(self) -> Tuple[str, Tuple]:
        """构建SQL查询"""
        query = f"SELECT {self.fields} FROM {self.table}"
        
        # 添加JOIN
        for join_type, table, condition in self.joins:
            query += f" {join_type} JOIN {table} ON {condition}"
            
        # 添加WHERE
        if self.conditions:
            query += " WHERE " + " AND ".join(self.conditions)
            
        # 添加GROUP BY
        if self.group_by_clause:
            query += f" GROUP BY {self.group_by_clause}"
            
        # 添加HAVING
        if self.having_clause:
            query += f" HAVING {self.having_clause}"
            
        # 添加ORDER BY
        if self.order_by_clause:
            query += f" ORDER BY {self.order_by_clause}"
            
        # 添加LIMIT和OFFSET
        if self.limit_value:
            query += f" LIMIT {self.limit_value}"
        if self.offset_value:
            query += f" OFFSET {self.offset_value}"
            
        # 合并参数
        all_params = tuple(self.params + self.having_params)
        
        return query, all_params
        
    def get_one(self) -> Optional[Dict]:
        """执行查询并获取一条记录"""
        query, params = self.build()
        return execute_query(query, params, fetch_one=True)
        
    def get_all(self) -> List[Dict]:
        """执行查询并获取所有记录"""
        query, params = self.build()
        return execute_query(query, params, fetch_one=False) or []
        
    def count(self) -> int:
        """获取记录数"""
        # 保存原始字段
        original_fields = self.fields
        # 修改为COUNT(*)
        self.fields = 'COUNT(*) as count'
        
        # 构建查询并执行
        query, params = self.build()
        result = execute_query(query, params, fetch_one=True)
        
        # 恢复原始字段
        self.fields = original_fields
        
        return result['count'] if result else 0

def get_database_schema() -> str:
    """
    获取数据库表结构信息
    
    返回:
        数据库结构描述字符串
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
    """
    return schema_info

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

# 从db.py整合的专业数据查询函数
def get_outpatient_data(department=None, specialty=None, start_date=None, end_date=None):
    """
    获取门诊量数据
    
    参数:
        department (str, optional): 科室名称
        specialty (str, optional): 专科分类
        start_date (str, optional): 开始日期，格式为YYYY-MM-DD
        end_date (str, optional): 结束日期，格式为YYYY-MM-DD
        
    返回:
        门诊量数据结果集
    """
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
    
    return execute_query(query, params)

def get_target_data(department=None, specialty=None, year=None, month=None):
    """
    获取目标值数据
    
    参数:
        department (str, optional): 科室名称
        specialty (str, optional): 专科分类
        year (str, optional): 年份
        month (str, optional): 月份
        
    返回:
        目标值数据结果集
    """
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
    
    return execute_query(query, params)

def get_completion_rate(year=None, month=None):
    """
    获取目标完成率数据
    
    参数:
        year (str, optional): 年份
        month (str, optional): 月份
        
    返回:
        目标完成率数据结果集
    """
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
    
    return execute_query(query, params)

def connect_db():
    """
    创建数据库连接
    
    返回:
        数据库连接对象
    """
    # 从应用配置中获取数据库路径
    database_path = config.DATABASE_PATH
    
    # 确保数据库文件所在目录存在
    os.makedirs(os.path.dirname(database_path), exist_ok=True)
    
    # 创建连接
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row  # 使结果以字典形式返回
    
    # 设置超时时间和pragma
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    
    return conn 

def execute_query_to_dataframe(query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
    """
    执行SQL查询并返回DataFrame结果
    
    参数:
        query: SQL查询语句
        params: 查询参数（可选）
        
    返回:
        包含查询结果的pandas DataFrame
    """
    try:
        # 记录开始时间
        start_time = time.time()
        
        # 执行查询获取结果
        results = execute_query(query, params)
        
        if not results:
            print("查询执行成功，但未返回数据")
            return pd.DataFrame()
            
        # 转换为DataFrame
        df = pd.DataFrame(results)
        
        # 处理日期列
        date_columns = [col for col in df.columns if 'date' in col.lower() or '时间' in col]
        for col in date_columns:
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception as e:
                print(f"转换日期列 {col} 时出错: {str(e)}")
        
        # 处理数值列
        numeric_columns = df.select_dtypes(include=['object']).columns
        for col in numeric_columns:
            try:
                # 尝试转换为数值类型
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except Exception as e:
                print(f"转换数值列 {col} 时出错: {str(e)}")
        
        # 记录查询执行时间
        execution_time = time.time() - start_time
        log_query(query, execution_time)
        
        print(f"查询执行成功，返回 {len(df)} 行数据")
        print(f"数据列: {df.columns.tolist()}")
        print(f"数据类型:\n{df.dtypes}")
        
        return df
        
    except Exception as e:
        error_msg = f"查询转DataFrame失败: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        
        log_error(error_msg, 
                  error_code=ErrorCode.DB_QUERY_ERROR, 
                  error_type=ErrorType.DATABASE_ERROR,
                  details={"query": query})
        
        return pd.DataFrame()

@contextmanager
def db_cursor():
    """
    数据库游标上下文管理器
    
    用法:
        with db_cursor() as cursor:
            cursor.execute("SELECT * FROM table")
            results = cursor.fetchall()
    
    返回:
        数据库游标对象
    """
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        log_error(f"数据库游标操作错误: {str(e)}", 
                   error_code=ErrorCode.DB_QUERY_ERROR, 
                   error_type=ErrorType.DATABASE_ERROR)
        raise
    finally:
        if conn:
            conn.close() 

def execute_many(query: str, params_list: list):
    """
    执行批量查询
    
    参数:
        query: SQL查询语句
        params_list: 参数列表
    """
    try:
        database_path = config.DATABASE_PATH
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        conn.commit()
        return True
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        log_error(f"批量执行查询失败: {str(e)}", 
                  error_code=ErrorCode.DB_QUERY_ERROR, 
                  error_type=ErrorType.DATABASE_ERROR)
        return False
    finally:
        if conn:
            conn.close()

def execute_transaction(queries: list):
    """
    执行事务
    
    参数:
        queries: 查询列表，每个元素是(query, params)元组
    """
    try:
        database_path = config.DATABASE_PATH
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        for query, params in queries:
            cursor.execute(query, params)
            
        conn.commit()
        return True
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        log_error(f"执行事务失败: {str(e)}", 
                  error_code=ErrorCode.DB_QUERY_ERROR, 
                  error_type=ErrorType.DATABASE_ERROR)
        return False
    finally:
        if conn:
            conn.close() 