#!/usr/bin/env python
"""
初始化仪表盘模拟数据脚本
"""
import os
import sys
import sqlite3
import random
from datetime import datetime, timedelta
import pandas as pd

# 添加父目录到sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from app import create_app
from app.config import config

def init_dashboard_data():
    """初始化仪表盘模拟数据"""
    print("开始初始化仪表盘模拟数据...")
    
    # 获取数据库路径
    app = create_app()
    with app.app_context():
        db_path = config.DATABASE_PATH
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 生成日期范围（过去90天）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    date_range = [start_date + timedelta(days=i) for i in range(91)]
    
    try:
        # 1. 初始化门诊数据
        create_outpatient_data(cursor, date_range)
        
        # 2. 初始化收入数据
        create_revenue_data(cursor, date_range)
        
        # 3. 初始化住院数据
        create_inpatient_data(cursor, date_range)
        
        # 4. 初始化手术数据
        create_surgery_data(cursor, date_range)
        
        # 5. 初始化警报数据
        create_alert_data(cursor, date_range)
        
        # 提交所有更改
        conn.commit()
        print("仪表盘模拟数据初始化完成！")
    
    except Exception as e:
        conn.rollback()
        print(f"初始化仪表盘数据时出错: {str(e)}")
    finally:
        conn.close()

def create_outpatient_data(cursor, date_range):
    """创建门诊数据"""
    print("创建门诊访问数据...")
    
    # 确保表存在（使用现有的表结构）
    # 不创建新表，使用现有的visits表
    
    # 科室列表
    departments = [
        "内科", "外科", "儿科", "妇产科", "眼科", "耳鼻喉科", "皮肤科", 
        "神经内科", "神经外科", "心胸外科", "泌尿外科", "骨科", "口腔科", 
        "中医科", "肿瘤科", "急诊科", "康复科", "精神科"
    ]
    
    # 生成随机门诊记录
    records = []
    
    # 清空原有数据
    cursor.execute("DELETE FROM visits")
    
    # 为每一天生成门诊数据
    for date in date_range:
        # 每天200-500个门诊患者
        daily_patients = random.randint(200, 500)
        
        for _ in range(daily_patients):
            dept = random.choice(departments)
            patient_id = f"P{random.randint(10000, 99999)}"
            doctor_id = f"D{random.randint(1000, 9999)}"
            visit_type = "门诊"
            diagnosis = f"{dept}常见疾病{random.randint(1, 10)}"
            visit_reason = f"因{diagnosis}就诊"
            
            records.append((
                date.strftime('%Y-%m-%d'),  # date
                date.strftime('%Y-%m-%d'),  # visit_date
                visit_type,
                dept,
                patient_id,
                doctor_id,
                visit_reason,
                diagnosis
            ))
    
    # 批量插入数据
    cursor.executemany('''
    INSERT INTO visits (date, visit_date, visit_type, department, patient_id, doctor_id, visit_reason, diagnosis)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', records)
    
    print(f"已生成 {len(records)} 条门诊记录")

def create_revenue_data(cursor, date_range):
    """创建收入数据"""
    print("创建收入数据...")
    
    # 收入类型
    revenue_types = ["门诊收入", "住院收入", "药品收入", "手术收入", "检查收入", "治疗收入"]
    
    # 清空原有数据
    cursor.execute("DELETE FROM revenue")
    
    # 生成随机收入记录
    records = []
    
    # 为每一天生成收入数据
    for date in date_range:
        # 每种收入类型一条记录
        for revenue_type in revenue_types:
            # 根据收入类型设置不同的金额范围
            if revenue_type == "门诊收入":
                amount = random.uniform(50000, 100000)
                description = "日常门诊收入"
            elif revenue_type == "住院收入":
                amount = random.uniform(100000, 200000)
                description = "住院病床及服务收入"
            elif revenue_type == "药品收入":
                amount = random.uniform(30000, 80000)
                description = "处方药及非处方药收入"
            elif revenue_type == "手术收入":
                amount = random.uniform(80000, 150000)
                description = "手术及麻醉相关收入"
            elif revenue_type == "检查收入":
                amount = random.uniform(40000, 70000)
                description = "医学影像及实验室检查收入"
            else:  # 治疗收入
                amount = random.uniform(20000, 50000)
                description = "理疗及其他治疗项目收入"
            
            records.append((
                date.strftime('%Y-%m-%d'),
                revenue_type,
                round(amount, 2),
                None,  # 部门为空
                description
            ))
    
    # 批量插入数据
    cursor.executemany('''
    INSERT INTO revenue (date, revenue_type, amount, department, description)
    VALUES (?, ?, ?, ?, ?)
    ''', records)
    
    print(f"已生成 {len(records)} 条收入记录")

def create_inpatient_data(cursor, date_range):
    """创建住院数据"""
    print("创建住院数据...")
    
    # 科室列表
    departments = ["内科", "外科", "儿科", "妇产科", "神经内科", "骨科", "肿瘤科"]
    
    # 诊断组
    diagnosis_groups = [
        "呼吸系统疾病", "消化系统疾病", "循环系统疾病", "泌尿系统疾病",
        "神经系统疾病", "内分泌系统疾病", "肌肉骨骼系统疾病", "血液系统疾病",
        "肿瘤", "外伤"
    ]
    
    # 清空原有数据
    cursor.execute("DELETE FROM admissions")
    
    # 生成随机住院记录
    records = []
    
    # 为每一天生成住院数据
    for date in date_range:
        # 每天10-30个新住院患者
        daily_patients = random.randint(10, 30)
        
        for _ in range(daily_patients):
            dept = random.choice(departments)
            doctor_id = f"D{random.randint(1000, 9999)}"
            patient_id = f"P{random.randint(10000, 99999)}"
            length_of_stay = random.randint(3, 15)  # 3-15天不等
            diagnosis_group = random.choice(diagnosis_groups)
            discharge_date = date + timedelta(days=length_of_stay)
            
            # 如果出院日期超过了当前日期，则设为NULL
            if discharge_date > datetime.now():
                discharge_date_str = None
                status = "active"
            else:
                discharge_date_str = discharge_date.strftime('%Y-%m-%d')
                status = "discharged"
            
            notes = f"患者因{diagnosis_group}入院，预计住院{length_of_stay}天"
            
            records.append((
                patient_id,
                date.strftime('%Y-%m-%d'),
                discharge_date_str,
                length_of_stay,
                dept,
                diagnosis_group,
                doctor_id,
                status,
                notes
            ))
    
    # 批量插入数据
    cursor.executemany('''
    INSERT INTO admissions (patient_id, admission_date, discharge_date, length_of_stay, department, diagnosis_group, doctor_id, status, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', records)
    
    print(f"已生成 {len(records)} 条住院记录")

def create_surgery_data(cursor, date_range):
    """创建手术数据"""
    print("创建手术数据...")
    
    # 手术科室
    surgery_departments = ["外科", "神经外科", "心胸外科", "泌尿外科", "骨科", "妇产科"]
    
    # 手术类型
    surgery_types = {
        "外科": ["阑尾切除术", "疝气修补术", "胆囊切除术"],
        "神经外科": ["开颅手术", "椎间盘切除术", "脑膜瘤切除术"],
        "心胸外科": ["冠状动脉搭桥术", "心脏瓣膜置换术", "肺叶切除术"],
        "泌尿外科": ["肾切除术", "前列腺切除术", "膀胱肿瘤切除术"],
        "骨科": ["髋关节置换术", "膝关节置换术", "脊椎融合术"],
        "妇产科": ["子宫切除术", "卵巢囊肿切除术", "剖宫产术"]
    }
    
    # 手术状态
    statuses = ["scheduled", "in_progress", "completed", "cancelled"]
    status_weights = [0.1, 0.1, 0.75, 0.05]  # 大部分已完成
    
    # 清空原有数据
    cursor.execute("DELETE FROM surgeries")
    
    # 生成随机手术记录
    records = []
    
    # 为每一天生成手术数据
    for date in date_range:
        # 每天5-15台手术
        daily_surgeries = random.randint(5, 15)
        
        for _ in range(daily_surgeries):
            dept = random.choice(surgery_departments)
            surgery_type = random.choice(surgery_types[dept])
            doctor_id = f"D{random.randint(1000, 9999)}"
            patient_id = f"P{random.randint(10000, 99999)}"
            duration = random.randint(30, 300)  # 30分钟到5小时
            
            # 手术日期越早，越可能已完成
            days_ago = (datetime.now() - date).days
            if days_ago > 60:
                status = "completed"
            elif days_ago > 30:
                status = random.choices(statuses, weights=[0.05, 0.05, 0.85, 0.05])[0]
            else:
                status = random.choices(statuses, weights=status_weights)[0]
            
            # 只有已完成的手术才可能有并发症
            complications = None
            if status == "completed" and random.random() < 0.15:  # 15%的几率有并发症
                complications = random.choice(["出血", "感染", "麻醉不良反应", "术后疼痛", "切口愈合不良"])
            
            notes = f"患者接受{surgery_type}手术，预计时长{duration}分钟"
            
            records.append((
                date.strftime('%Y-%m-%d'),
                patient_id,
                doctor_id,
                dept,
                surgery_type,
                duration,
                status,
                complications,
                notes
            ))
    
    # 批量插入数据
    cursor.executemany('''
    INSERT INTO surgeries (surgery_date, patient_id, doctor_id, department, surgery_type, duration, status, complications, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', records)
    
    print(f"已生成 {len(records)} 条手术记录")

def create_alert_data(cursor, date_range):
    """创建警报数据"""
    print("创建警报数据...")
    
    # 警报类型
    alert_types = ["critical", "warning", "info"]
    
    # 警报描述
    alert_descriptions = {
        "critical": ["服务器CPU使用率超过90%", "MRI设备故障", "床位使用率超过95%", "发现异常登录尝试", "数据备份失败"],
        "warning": ["服务器内存不足", "CT设备需要维护", "手术室排期冲突", "患者信息访问异常", "门诊挂号系统响应缓慢"],
        "info": ["系统更新待安装", "X光机校准偏差", "药品库存不足", "网络流量异常", "影像系统存储空间不足"]
    }
    
    # 警报状态
    alert_statuses = ["new", "processing", "resolved", "ignored"]
    
    # 相关实体类型
    related_entities = ["department", "patient", "system"]
    
    # 清空原有数据
    cursor.execute("DELETE FROM alerts")
    
    # 生成随机警报记录
    records = []
    
    # 生成最近30天的警报数据
    recent_dates = date_range[-30:]
    
    # 每天1-3条警报
    for date in recent_dates:
        num_alerts = random.randint(1, 3)
        
        for _ in range(num_alerts):
            # 随机生成时间（0-23小时，0-59分钟）
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            alert_time = date.replace(hour=hour, minute=minute)
            
            # 根据严重程度设置不同的类型概率
            alert_type = random.choices(alert_types, weights=[0.2, 0.5, 0.3])[0]
            description = random.choice(alert_descriptions[alert_type])
            
            # 更早的警报更可能已经处理
            days_ago = (datetime.now() - alert_time).days
            if days_ago > 20:
                status_weights = [0.1, 0.2, 0.6, 0.1]  # 大部分已处理
            elif days_ago > 10:
                status_weights = [0.2, 0.4, 0.3, 0.1]  # 部分已处理
            else:
                status_weights = [0.5, 0.3, 0.1, 0.1]  # 大部分未处理
            
            status = random.choices(alert_statuses, weights=status_weights)[0]
            
            # 随机选择相关实体
            related_entity = random.choice(related_entities)
            if related_entity == "department":
                related_id = random.randint(1, 10)  # 假设1-10是科室ID
            elif related_entity == "patient":
                related_id = random.randint(10000, 99999)  # 患者ID范围
            else:  # system
                related_id = random.randint(1, 5)  # 系统组件ID
            
            records.append((
                alert_time.strftime('%Y-%m-%d %H:%M:%S'),
                alert_type,
                description,
                status,
                related_entity,
                related_id
            ))
    
    # 批量插入数据
    cursor.executemany('''
    INSERT INTO alerts (alert_time, alert_type, description, status, related_entity, related_id)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', records)
    
    print(f"已生成 {len(records)} 条警报记录")

if __name__ == '__main__':
    init_dashboard_data() 