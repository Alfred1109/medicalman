#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta

# 添加应用目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def get_db_connection():
    """获取数据库连接"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'medical_workload.db')
    print(f"连接数据库: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_dashboard_metrics():
    """获取仪表盘数据"""
    try:
        # 设置日期范围
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        print(f"查询日期范围: {start_date} 至 {end_date}")
        
        # 使用with语句正确处理数据库连接
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 1. 获取门诊趋势数据
            outpatient_data = get_outpatient_trend(cursor, start_date, end_date)
            
            # 2. 获取收入分布数据
            revenue_data = get_revenue_distribution(cursor, start_date, end_date)
            
            # 3. 获取住院病种TOP10数据
            admission_diagnosis_data = get_top_admission_diagnosis(cursor, start_date, end_date)
            
            # 4. 获取手术类型分布数据
            surgery_data = get_surgery_distribution(cursor, start_date, end_date)
            
            # 5. 获取基础统计数据
            stats_data = get_basic_stats(cursor, start_date, end_date)
            
            # 6. 获取科室工作量数据
            department_workload_data = get_department_workload(cursor, start_date, end_date)
            
            # 7. 获取最新警报数据
            alerts_data = get_alerts(cursor, 5)
        
        # 打印获取到的数据
        print("== 门诊趋势数据 ==")
        print(f"数据条数: {len(outpatient_data)}")
        if outpatient_data:
            print(f"样例: {outpatient_data[0]}")
        
        print("\n== 收入分布数据 ==")
        print(f"数据条数: {len(revenue_data)}")
        if revenue_data:
            print(f"样例: {revenue_data[0]}")
        
        print("\n== 住院病种TOP10数据 ==")
        print(f"数据条数: {len(admission_diagnosis_data)}")
        if admission_diagnosis_data:
            print(f"样例: {admission_diagnosis_data[0]}")
        
        print("\n== 手术类型分布数据 ==")
        print(f"数据条数: {len(surgery_data)}")
        if surgery_data:
            print(f"样例: {surgery_data[0]}")
        
        print("\n== 统计数据 ==")
        print(stats_data)
        
        print("\n== 科室工作量数据 ==")
        print(department_workload_data)
        
        print("\n== 警报数据 ==")
        print(f"数据条数: {len(alerts_data)}")
        if alerts_data:
            print(f"样例: {alerts_data[0]}")
        
        # 格式化数据以符合前端期望的结构
        formatted_data = {
            'stats': {
                'outpatient': {
                    'value': f"{stats_data.get('outpatient_count', 0)}",
                    'change': 5.2  # 假设的增长率
                },
                'inpatient': {
                    'value': f"{stats_data.get('inpatient_count', 0)}",
                    'change': 2.8  # 假设的增长率
                },
                'revenue': {
                    'value': f"¥{stats_data.get('total_revenue', 0):,.2f}",
                    'change': 4.5  # 假设的增长率
                },
                'bedUsage': {
                    'value': "85%",  # 添加百分号
                    'change': 0.5  # 假设的增长率
                }
            },
            'charts': {
                'outpatientTrend': {
                    'xAxis': [item['date'] for item in outpatient_data],
                    'series': [{
                        'name': '门诊量',
                        'type': 'line',
                        'data': [item['count'] for item in outpatient_data],
                        'smooth': True,
                        'itemStyle': {
                            'color': '#5470c6'
                        }
                    }]
                },
                'revenueComposition': {
                    'data': [{'name': item['revenue_type'], 'value': item['amount']} for item in revenue_data]
                },
                'departmentWorkload': {
                    'yAxis': department_workload_data['departments'],
                    'series': [
                        {
                            'name': '门诊量',
                            'type': 'bar',
                            'data': department_workload_data['outpatient'],
                            'itemStyle': {
                                'color': '#5470c6'
                            }
                        },
                        {
                            'name': '住院量',
                            'type': 'bar',
                            'data': department_workload_data['inpatient'],
                            'itemStyle': {
                                'color': '#91cc75'
                            }
                        },
                        {
                            'name': '手术量',
                            'type': 'bar',
                            'data': department_workload_data['surgery'],
                            'itemStyle': {
                                'color': '#fac858'
                            }
                        }
                    ]
                },
                'inpatientDistribution': {
                    'legend': [item['diagnosis_group'] for item in admission_diagnosis_data],
                    'data': [{'name': item['diagnosis_group'], 'value': item['count']} for item in admission_diagnosis_data]
                }
            },
            'alerts': alerts_data
        }
        
        print("\n== 格式化后的数据 ==")
        print(json.dumps(formatted_data, ensure_ascii=False, indent=2))
        
        return formatted_data
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"获取仪表盘数据时出错: {str(e)}")
        return None

def get_outpatient_trend(cursor, start_date, end_date):
    """获取门诊趋势数据"""
    query = """
    SELECT visit_date as date, COUNT(*) as count 
    FROM visits 
    WHERE visit_date BETWEEN ? AND ? 
    GROUP BY date 
    ORDER BY date
    """
    cursor.execute(query, (start_date, end_date))
    rows = cursor.fetchall()
    
    # 确保每一天都有数据
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    days = (end - start).days + 1
    
    # 创建一个包含所有日期的字典
    result_dict = {(start + timedelta(days=i)).strftime('%Y-%m-%d'): 0 for i in range(days)}
    
    # 填充查询结果
    for row in rows:
        date_str = row[0]
        count = row[1]
        if date_str in result_dict:
            result_dict[date_str] = count
    
    # 转换为列表格式
    result = [{'date': date, 'count': count} for date, count in result_dict.items()]
    result.sort(key=lambda x: x['date'])
    
    return result

def get_revenue_distribution(cursor, start_date, end_date):
    """获取收入分布数据"""
    query = """
    SELECT revenue_type, SUM(amount) as total_amount 
    FROM revenue 
    WHERE date BETWEEN ? AND ? 
    GROUP BY revenue_type
    """
    cursor.execute(query, (start_date, end_date))
    rows = cursor.fetchall()
    
    result = [{'revenue_type': row[0], 'amount': row[1]} for row in rows]
    return result

def get_top_admission_diagnosis(cursor, start_date, end_date):
    """获取住院病种TOP10数据"""
    query = """
    SELECT diagnosis_group, COUNT(*) as count 
    FROM admissions 
    WHERE admission_date BETWEEN ? AND ? 
    GROUP BY diagnosis_group 
    ORDER BY count DESC 
    LIMIT 10
    """
    cursor.execute(query, (start_date, end_date))
    rows = cursor.fetchall()
    
    result = [{'diagnosis_group': row[0], 'count': row[1]} for row in rows]
    return result

def get_surgery_distribution(cursor, start_date, end_date):
    """获取手术类型分布数据"""
    query = """
    SELECT surgery_type, COUNT(*) as count 
    FROM surgeries 
    WHERE surgery_date BETWEEN ? AND ? 
    GROUP BY surgery_type
    """
    cursor.execute(query, (start_date, end_date))
    rows = cursor.fetchall()
    
    result = [{'surgery_type': row[0], 'count': row[1]} for row in rows]
    return result

def get_basic_stats(cursor, start_date, end_date):
    """获取基础统计数据"""
    # 门诊量
    cursor.execute("""
    SELECT COUNT(*) as count 
    FROM visits 
    WHERE visit_date BETWEEN ? AND ?
    """, (start_date, end_date))
    outpatient_count = cursor.fetchone()[0]
    
    # 住院量
    cursor.execute("""
    SELECT COUNT(*) as count 
    FROM admissions 
    WHERE admission_date BETWEEN ? AND ?
    """, (start_date, end_date))
    inpatient_count = cursor.fetchone()[0]
    
    # 收入总额
    cursor.execute("""
    SELECT SUM(amount) as total 
    FROM revenue 
    WHERE date BETWEEN ? AND ?
    """, (start_date, end_date))
    total_revenue = cursor.fetchone()[0] or 0
    
    return {
        'outpatient_count': outpatient_count,
        'inpatient_count': inpatient_count,
        'total_revenue': total_revenue
    }

def get_department_workload(cursor, start_date, end_date):
    """获取科室工作量数据"""
    # 获取所有科室
    cursor.execute("""
    SELECT DISTINCT department 
    FROM visits 
    WHERE visit_date BETWEEN ? AND ?
    """, (start_date, end_date))
    departments = [row[0] for row in cursor.fetchall()]
    
    outpatient_counts = []
    inpatient_counts = []
    surgery_counts = []
    
    # 获取各科室门诊量
    for dept in departments:
        cursor.execute("""
        SELECT COUNT(*) 
        FROM visits 
        WHERE department = ? AND visit_date BETWEEN ? AND ?
        """, (dept, start_date, end_date))
        outpatient_counts.append(cursor.fetchone()[0])
        
        cursor.execute("""
        SELECT COUNT(*) 
        FROM admissions 
        WHERE department = ? AND admission_date BETWEEN ? AND ?
        """, (dept, start_date, end_date))
        inpatient_counts.append(cursor.fetchone()[0])
        
        cursor.execute("""
        SELECT COUNT(*) 
        FROM surgeries 
        WHERE department = ? AND surgery_date BETWEEN ? AND ?
        """, (dept, start_date, end_date))
        surgery_counts.append(cursor.fetchone()[0])
    
    return {
        'departments': departments,
        'outpatient': outpatient_counts,
        'inpatient': inpatient_counts,
        'surgery': surgery_counts
    }

def get_alerts(cursor, limit=5):
    """获取最新警报数据"""
    query = """
    SELECT alert_time, alert_type, description, status, 'view' as action, id
    FROM alerts
    ORDER BY alert_time DESC
    LIMIT ?
    """
    cursor.execute(query, (limit,))
    rows = cursor.fetchall()
    
    result = []
    for row in rows:
        result.append([
            row[0],  # alert_time
            row[1],  # alert_type
            row[2],  # description
            row[3],  # status
            row[4],  # action
            row[5]   # id
        ])
    
    return result

if __name__ == "__main__":
    get_dashboard_metrics() 