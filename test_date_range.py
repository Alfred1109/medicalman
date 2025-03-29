#!/usr/bin/env python
import os
import sqlite3
from datetime import datetime, timedelta

def main():
    # 使用2025年的固定日期范围
    end_date = "2025-03-29"
    start_date = "2025-02-28"
    
    print(f"检查固定日期范围: {start_date} 至 {end_date}")
    
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
    
    # 检查收入数据的详细分布
    cursor.execute("""
        SELECT revenue_type, SUM(amount) as total_amount 
        FROM revenue 
        WHERE date BETWEEN ? AND ? 
        GROUP BY revenue_type
    """, (start_date, end_date))
    revenue_distribution = cursor.fetchall()
    print(f"收入分布:")
    for revenue_type, amount in revenue_distribution:
        print(f"  {revenue_type}: {amount}")
    
    conn.close()

if __name__ == "__main__":
    main() 