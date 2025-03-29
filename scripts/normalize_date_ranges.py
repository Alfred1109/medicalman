#!/usr/bin/env python
"""
统一数据库中所有表的日期范围脚本
将所有表中的日期字段调整为2025年1月1日至2025年3月31日范围内
"""
import os
import sys
import sqlite3
from datetime import datetime, timedelta
import random

# 添加父目录到sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from app import create_app
from app.config import config

# 目标日期范围
START_DATE = "2025-01-01"
END_DATE = "2025-03-31"

def normalize_date_ranges():
    """统一所有表的日期范围为2025年1月1日至2025年3月31日"""
    print(f"开始统一数据库日期范围为 {START_DATE} 至 {END_DATE}...")
    
    # 获取数据库路径
    app = create_app()
    with app.app_context():
        db_path = config.DATABASE_PATH
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. 调整visits表的日期
        normalize_visits_dates(cursor)
        
        # 2. 调整admissions表的日期
        normalize_admissions_dates(cursor)
        
        # 3. 调整revenue表的日期
        normalize_revenue_dates(cursor)
        
        # 4. 调整surgeries表的日期
        normalize_surgeries_dates(cursor)
        
        # 5. 调整alerts表的日期
        normalize_alerts_dates(cursor)
        
        # 提交所有更改
        conn.commit()
        print("日期范围统一调整完成！")
    
    except Exception as e:
        conn.rollback()
        print(f"调整日期范围时出错: {str(e)}")
    finally:
        conn.close()

def normalize_visits_dates(cursor):
    """调整visits表的日期范围"""
    print("调整visits表的日期范围...")
    
    # 获取总记录数
    cursor.execute("SELECT COUNT(*) FROM visits")
    total_records = cursor.fetchone()[0]
    
    # 计算需要分配的天数
    target_days = (datetime.strptime(END_DATE, '%Y-%m-%d') - datetime.strptime(START_DATE, '%Y-%m-%d')).days + 1
    
    # 计算每天平均需要分配的记录数
    records_per_day = total_records / target_days
    
    # 获取所有记录ID
    cursor.execute("SELECT id FROM visits")
    all_ids = [row[0] for row in cursor.fetchall()]
    
    # 打乱ID顺序，以便随机分配日期
    random.shuffle(all_ids)
    
    # 为每条记录分配新日期
    target_date = datetime.strptime(START_DATE, '%Y-%m-%d')
    end_datetime = datetime.strptime(END_DATE, '%Y-%m-%d')
    
    current_day_count = 0
    day_record_count = 0
    
    for record_id in all_ids:
        # 分配日期，考虑周末减少30%的访问量
        date_str = target_date.strftime('%Y-%m-%d')
        
        # 更新记录
        cursor.execute("""
        UPDATE visits
        SET visit_date = ?, date = ?
        WHERE id = ?
        """, (date_str, date_str, record_id))
        
        # 记录计数
        day_record_count += 1
        
        # 检查是否需要移到下一天
        # 周末减少访问量
        weekday = target_date.weekday()
        day_target = records_per_day * (0.7 if weekday >= 5 else 1.0)
        
        if day_record_count >= day_target:
            day_record_count = 0
            target_date += timedelta(days=1)
            current_day_count += 1
            
            # 如果超过了目标日期范围，重新从开始日期开始
            if target_date > end_datetime:
                target_date = datetime.strptime(START_DATE, '%Y-%m-%d')
    
    print(f"已调整 {total_records} 条visits记录的日期")

def normalize_admissions_dates(cursor):
    """调整admissions表的日期范围"""
    print("调整admissions表的日期范围...")
    
    # 获取所有记录
    cursor.execute("SELECT id, length_of_stay FROM admissions")
    admissions = cursor.fetchall()
    
    # 计算需要分配的天数
    target_days = (datetime.strptime(END_DATE, '%Y-%m-%d') - datetime.strptime(START_DATE, '%Y-%m-%d')).days + 1
    
    # 获取所有记录的ID和住院天数
    admissions_data = [(row[0], row[1] or random.randint(1, 14)) for row in admissions]
    
    # 打乱顺序，以便随机分配日期
    random.shuffle(admissions_data)
    
    # 为每条记录分配新日期
    for admission_id, length_of_stay in admissions_data:
        # 确保出院日期不超过目标结束日期
        max_admission_date = datetime.strptime(END_DATE, '%Y-%m-%d') - timedelta(days=length_of_stay)
        min_admission_date = datetime.strptime(START_DATE, '%Y-%m-%d')
        
        # 如果max_admission_date小于min_admission_date，表示住院时间过长
        # 这种情况下，我们减少住院时间以确保能在日期范围内
        if max_admission_date < min_admission_date:
            length_of_stay = (datetime.strptime(END_DATE, '%Y-%m-%d') - min_admission_date).days
            max_admission_date = min_admission_date
        
        # 在可能的入院日期范围内随机选择一天
        random_days = random.randint(0, (max_admission_date - min_admission_date).days)
        admission_date = (min_admission_date + timedelta(days=random_days)).strftime('%Y-%m-%d')
        
        # 计算出院日期
        discharge_date_obj = datetime.strptime(admission_date, '%Y-%m-%d') + timedelta(days=length_of_stay)
        discharge_date = discharge_date_obj.strftime('%Y-%m-%d')
        
        # 更新记录
        cursor.execute("""
        UPDATE admissions
        SET admission_date = ?, discharge_date = ?, length_of_stay = ?
        WHERE id = ?
        """, (admission_date, discharge_date, length_of_stay, admission_id))
    
    print(f"已调整 {len(admissions_data)} 条admissions记录的日期")

def normalize_revenue_dates(cursor):
    """调整revenue表的日期范围"""
    print("调整revenue表的日期范围...")
    
    # 获取总记录数
    cursor.execute("SELECT COUNT(*) FROM revenue")
    total_records = cursor.fetchone()[0]
    
    # 计算需要分配的天数
    target_days = (datetime.strptime(END_DATE, '%Y-%m-%d') - datetime.strptime(START_DATE, '%Y-%m-%d')).days + 1
    
    # 获取所有记录ID
    cursor.execute("SELECT id FROM revenue")
    all_ids = [row[0] for row in cursor.fetchall()]
    
    # 打乱ID顺序，以便随机分配日期
    random.shuffle(all_ids)
    
    # 为每条记录分配新日期
    days_range = range(target_days)
    date_distribution = []
    
    # 创建符合某种模式的日期分布（例如，工作日收入高于周末）
    for day in range(target_days):
        current_date = datetime.strptime(START_DATE, '%Y-%m-%d') + timedelta(days=day)
        weekday = current_date.weekday()
        
        # 周末减少记录数
        weight = 0.7 if weekday >= 5 else 1.0
        
        # 月初和月末可能有更多收入记录
        day_of_month = current_date.day
        if day_of_month <= 5 or day_of_month >= 25:
            weight *= 1.2
            
        # 将日期按权重添加到分布中
        date_distribution.extend([day] * int(10 * weight))
    
    # 为每条记录分配日期
    for record_id in all_ids:
        # 随机选择一个日期索引
        day_index = random.choice(date_distribution)
        date_str = (datetime.strptime(START_DATE, '%Y-%m-%d') + timedelta(days=day_index)).strftime('%Y-%m-%d')
        
        # 更新记录
        cursor.execute("""
        UPDATE revenue
        SET date = ?
        WHERE id = ?
        """, (date_str, record_id))
    
    print(f"已调整 {total_records} 条revenue记录的日期")

def normalize_surgeries_dates(cursor):
    """调整surgeries表的日期范围"""
    print("调整surgeries表的日期范围...")
    
    # 获取总记录数
    cursor.execute("SELECT COUNT(*) FROM surgeries")
    total_records = cursor.fetchone()[0]
    
    # 计算需要分配的天数
    target_days = (datetime.strptime(END_DATE, '%Y-%m-%d') - datetime.strptime(START_DATE, '%Y-%m-%d')).days + 1
    
    # 获取所有记录ID
    cursor.execute("SELECT id FROM surgeries")
    all_ids = [row[0] for row in cursor.fetchall()]
    
    # 打乱ID顺序，以便随机分配日期
    random.shuffle(all_ids)
    
    # 为每条记录分配新日期
    days_range = range(target_days)
    date_distribution = []
    
    # 创建符合某种模式的日期分布（例如，周末手术较少）
    for day in range(target_days):
        current_date = datetime.strptime(START_DATE, '%Y-%m-%d') + timedelta(days=day)
        weekday = current_date.weekday()
        
        # 周末减少手术
        weight = 0.3 if weekday >= 5 else 1.0
        
        # 将日期按权重添加到分布中
        date_distribution.extend([day] * int(10 * weight))
    
    # 为每条记录分配日期
    for record_id in all_ids:
        # 随机选择一个日期索引
        day_index = random.choice(date_distribution)
        date_str = (datetime.strptime(START_DATE, '%Y-%m-%d') + timedelta(days=day_index)).strftime('%Y-%m-%d')
        
        # 更新记录
        cursor.execute("""
        UPDATE surgeries
        SET surgery_date = ?
        WHERE id = ?
        """, (date_str, record_id))
    
    print(f"已调整 {total_records} 条surgeries记录的日期")

def normalize_alerts_dates(cursor):
    """调整alerts表的日期范围"""
    print("调整alerts表的日期范围...")
    
    # 获取总记录数
    cursor.execute("SELECT COUNT(*) FROM alerts")
    total_records = cursor.fetchone()[0]
    
    # 获取所有记录ID
    cursor.execute("SELECT id FROM alerts")
    all_ids = [row[0] for row in cursor.fetchall()]
    
    # 打乱ID顺序，以便随机分配日期
    random.shuffle(all_ids)
    
    # 计算开始和结束日期的时间戳范围
    start_timestamp = int(datetime.strptime(START_DATE, '%Y-%m-%d').timestamp())
    end_timestamp = int(datetime.strptime(END_DATE, '%Y-%m-%d').timestamp() + 86399)  # 加上一天的秒数减1
    
    # 为每条记录分配新日期时间
    for record_id in all_ids:
        # 随机选择一个时间戳
        random_timestamp = random.randint(start_timestamp, end_timestamp)
        alert_datetime = datetime.fromtimestamp(random_timestamp)
        alert_time = alert_datetime.strftime('%Y-%m-%d %H:%M:%S')
        
        # 更新记录
        cursor.execute("""
        UPDATE alerts
        SET alert_time = ?
        WHERE id = ?
        """, (alert_time, record_id))
    
    print(f"已调整 {total_records} 条alerts记录的日期")

if __name__ == "__main__":
    normalize_date_ranges() 