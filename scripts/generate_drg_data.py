"""
生成DRG模拟数据脚本
"""
import pandas as pd
import sqlite3
import numpy as np
import random
from datetime import datetime, timedelta
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def generate_drg_data(db_file='medical_workload.db', reference_file='docs/医疗数据表.xlsx'):
    """
    生成DRG模拟数据并存入数据库
    
    参数:
        db_file: 数据库文件路径
        reference_file: 参考数据文件路径
    """
    # 连接到SQLite数据库
    conn = sqlite3.connect(db_file)
    
    try:
        # 获取数据库中的科室列表
        query = "SELECT DISTINCT 科室 FROM 门诊量"
        departments = pd.read_sql_query(query, conn)['科室'].tolist()
        
        if not departments:
            departments = ['内科', '外科', '妇产科', '儿科', '骨科', '神经内科', '心血管内科', '泌尿外科', '眼科', '耳鼻喉科']
            print("未找到科室数据，使用默认科室列表")
        
        # DRG组的定义
        drg_groups = [
            'CABG', 'PCI', 'AMI', 'CHF', 'Stroke', 'Pneumonia', 'COPD', 
            'Joint Replacement', 'Cholecystectomy', 'Appendectomy',
            'Cesarean Section', 'Vaginal Delivery', 'Neonatal Care',
            'Urinary Tract Infection', 'Kidney Disease', 'Hip Fracture',
            'Spine Surgery', 'Diabetes', 'GI Bleed', 'Sepsis'
        ]
        
        # 生成随机DRG数据
        records = []
        
        # 生成最近三年的数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365*3)
        
        # 每个科室每个DRG组每个月生成若干条记录
        for department in departments:
            # 为每个科室随机分配3-8个DRG组
            dept_drg_groups = random.sample(drg_groups, random.randint(3, min(8, len(drg_groups))))
            
            for drg_group in dept_drg_groups:
                # 每个月生成10-30条记录
                current_date = start_date
                while current_date < end_date:
                    month_records = random.randint(10, 30)
                    
                    for _ in range(month_records):
                        # 随机生成病例日期（当月内）
                        case_date = current_date + timedelta(days=random.randint(0, 28))
                        
                        # 生成随机指标数据
                        weight_score = round(random.uniform(0.5, 3.0), 2)
                        cost_index = round(random.uniform(0.7, 1.3), 2)
                        time_index = round(random.uniform(0.7, 1.3), 2)
                        total_cost = round(random.uniform(5000, 50000), 2)
                        length_of_stay = random.randint(1, 20)
                        
                        records.append({
                            'department': department,
                            'drg_group': drg_group,
                            'case_date': case_date.strftime('%Y-%m-%d'),
                            'weight_score': weight_score,
                            'cost_index': cost_index,
                            'time_index': time_index,
                            'total_cost': total_cost,
                            'length_of_stay': length_of_stay
                        })
                    
                    # 进入下一个月
                    current_date = datetime(current_date.year + (current_date.month//12), 
                                           ((current_date.month % 12) + 1), 1)
        
        # 创建DataFrame
        df = pd.DataFrame(records)
        
        # 创建DRG表并导入数据
        df.to_sql('drg_records', conn, if_exists='replace', index=False)
        
        print(f"已生成DRG模拟数据并导入drg_records表，共{len(df)}条记录")
        
    except Exception as e:
        print(f"生成DRG数据时出错: {str(e)}")
    finally:
        conn.close()

def generate_patient_data(db_file='medical_workload.db'):
    """
    生成患者数据并存入数据库
    
    参数:
        db_file: 数据库文件路径
    """
    # 连接到SQLite数据库
    conn = sqlite3.connect(db_file)
    
    try:
        # 获取数据库中的科室列表
        query = "SELECT DISTINCT 科室 FROM 门诊量"
        departments = pd.read_sql_query(query, conn)['科室'].tolist()
        
        if not departments:
            departments = ['内科', '外科', '妇产科', '儿科', '骨科', '神经内科', '心血管内科', '泌尿外科', '眼科', '耳鼻喉科']
            print("未找到科室数据，使用默认科室列表")
        
        # 患者性别
        genders = ['男', '女']
        
        # 患者年龄段
        age_groups = ['0-10', '11-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71-80', '81+']
        
        # 就诊类型
        visit_types = ['初诊', '复诊', '急诊', '转诊', '会诊']
        
        # 保险类型
        insurance_types = ['医保', '商业保险', '自费', '公费医疗', '其他']
        
        # 生成随机患者数据
        records = []
        
        # 生成最近三年的数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365*3)
        
        # 每个科室每天生成若干条记录
        for department in departments:
            current_date = start_date
            while current_date < end_date:
                # 每天生成5-20条记录
                daily_records = random.randint(5, 20)
                
                for _ in range(daily_records):
                    # 随机生成患者数据
                    gender = random.choice(genders)
                    age_group = random.choice(age_groups)
                    visit_type = random.choice(visit_types)
                    insurance_type = random.choice(insurance_types)
                    
                    # 随机生成诊断和治疗数据
                    diagnosis = f"诊断{random.randint(1, 100)}"
                    treatment = f"治疗{random.randint(1, 50)}"
                    
                    # 随机生成费用数据
                    total_fee = round(random.uniform(100, 10000), 2)
                    medicine_fee = round(total_fee * random.uniform(0.2, 0.5), 2)
                    examination_fee = round(total_fee * random.uniform(0.1, 0.3), 2)
                    treatment_fee = round(total_fee - medicine_fee - examination_fee, 2)
                    
                    records.append({
                        'department': department,
                        'visit_date': current_date.strftime('%Y-%m-%d'),
                        'gender': gender,
                        'age_group': age_group,
                        'visit_type': visit_type,
                        'insurance_type': insurance_type,
                        'diagnosis': diagnosis,
                        'treatment': treatment,
                        'total_fee': total_fee,
                        'medicine_fee': medicine_fee,
                        'examination_fee': examination_fee,
                        'treatment_fee': treatment_fee
                    })
                
                # 进入下一天
                current_date += timedelta(days=1)
        
        # 创建DataFrame
        df = pd.DataFrame(records)
        
        # 创建患者表并导入数据
        df.to_sql('patient_records', conn, if_exists='replace', index=False)
        
        print(f"已生成患者模拟数据并导入patient_records表，共{len(df)}条记录")
        
    except Exception as e:
        print(f"生成患者数据时出错: {str(e)}")
    finally:
        conn.close()

def generate_doctor_performance_data(db_file='medical_workload.db'):
    """
    生成医生绩效数据并存入数据库
    
    参数:
        db_file: 数据库文件路径
    """
    # 连接到SQLite数据库
    conn = sqlite3.connect(db_file)
    
    try:
        # 获取数据库中的科室列表
        query = "SELECT DISTINCT 科室 FROM 门诊量"
        departments = pd.read_sql_query(query, conn)['科室'].tolist()
        
        if not departments:
            departments = ['内科', '外科', '妇产科', '儿科', '骨科', '神经内科', '心血管内科', '泌尿外科', '眼科', '耳鼻喉科']
            print("未找到科室数据，使用默认科室列表")
        
        # 为每个科室定义若干医生
        doctors = []
        doctor_id = 1
        
        for department in departments:
            # 每个科室生成3-8名医生
            num_doctors = random.randint(3, 8)
            
            for i in range(num_doctors):
                doctors.append({
                    'id': doctor_id,
                    'name': f"{department}医生{i+1}",
                    'department': department,
                    'title': random.choice(['主任医师', '副主任医师', '主治医师', '住院医师']),
                    'specialty': random.choice(['心血管', '消化', '呼吸', '神经', '内分泌', '普通外科', '骨科', '妇科', '产科', '儿科'])
                })
                doctor_id += 1
        
        # 创建医生表
        df_doctors = pd.DataFrame(doctors)
        df_doctors.to_sql('doctors', conn, if_exists='replace', index=False)
        
        print(f"已生成医生数据并导入doctors表，共{len(df_doctors)}条记录")
        
        # 生成医生绩效数据
        performance_records = []
        
        # 生成最近一年的数据，按月统计
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        # 按月生成每个医生的绩效数据
        current_date = start_date
        while current_date < end_date:
            year = current_date.year
            month = current_date.month
            
            for doctor in doctors:
                # 随机生成绩效数据
                outpatient_count = random.randint(50, 300)
                surgery_count = random.randint(0, 30) if doctor['title'] in ['主任医师', '副主任医师', '主治医师'] else 0
                paper_count = random.randint(0, 2)
                research_project_count = random.randint(0, 1)
                teaching_hours = random.randint(0, 30)
                patient_satisfaction = round(random.uniform(3.0, 5.0), 1)
                quality_score = round(random.uniform(70, 100), 1)
                
                performance_records.append({
                    'doctor_id': doctor['id'],
                    'year': year,
                    'month': month,
                    'outpatient_count': outpatient_count,
                    'surgery_count': surgery_count,
                    'paper_count': paper_count,
                    'research_project_count': research_project_count,
                    'teaching_hours': teaching_hours,
                    'patient_satisfaction': patient_satisfaction,
                    'quality_score': quality_score
                })
            
            # 进入下一个月
            current_date = datetime(current_date.year + (current_date.month//12), 
                                   ((current_date.month % 12) + 1), 1)
        
        # 创建绩效表
        df_performance = pd.DataFrame(performance_records)
        df_performance.to_sql('doctor_performance', conn, if_exists='replace', index=False)
        
        print(f"已生成医生绩效数据并导入doctor_performance表，共{len(df_performance)}条记录")
        
    except Exception as e:
        print(f"生成医生绩效数据时出错: {str(e)}")
    finally:
        conn.close()

if __name__ == '__main__':
    # 生成DRG数据
    generate_drg_data()
    
    # 生成患者数据
    generate_patient_data()
    
    # 生成医生绩效数据
    generate_doctor_performance_data() 