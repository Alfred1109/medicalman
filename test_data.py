#!/usr/bin/env python
import os
import sqlite3
from datetime import datetime, timedelta

def main():
    # 获取日期范围
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    print(f"检查日期范围: {start_date} 至 {end_date}")
    
    # 连接数据库
    db_path = os.path.join('instance', 'medical_workload.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查门诊数据
    cursor.execute("SELECT COUNT(*) FROM visits WHERE visit_date BETWEEN ? AND ?", (start_date, end_date))
    outpatient_count = cursor.fetchone()[0]
    print(f"门诊数据数量: {outpatient_count}")
    
    # 检查住院数据
    cursor.execute("SELECT COUNT(*) FROM admissions WHERE admission_date BETWEEN ? AND ?", (start_date, end_date))
    inpatient_count = cursor.fetchone()[0]
    print(f"住院数据数量: {inpatient_count}")
    
    # 检查收入数据
    cursor.execute("SELECT SUM(amount) FROM revenue WHERE date BETWEEN ? AND ?", (start_date, end_date))
    total_revenue = cursor.fetchone()[0]
    print(f"总收入: {total_revenue or 0}")
    
    # 检查数据分布
    cursor.execute("SELECT date, COUNT(*) FROM revenue WHERE date BETWEEN ? AND ? GROUP BY date", (start_date, end_date))
    date_counts = cursor.fetchall()
    print(f"收入数据日期分布: {date_counts}")
    
    # 获取所有收入数据的日期范围
    cursor.execute("SELECT MIN(date), MAX(date) FROM revenue")
    min_date, max_date = cursor.fetchone()
    print(f"收入数据日期范围: {min_date} 至 {max_date}")
    
    # 检查表中的日期格式是否正确
    cursor.execute("SELECT date FROM revenue LIMIT 10")
    date_samples = cursor.fetchall()
    print(f"收入日期示例: {date_samples}")
    
    conn.close()

if __name__ == "__main__":
    main() 