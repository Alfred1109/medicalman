"""
演示数据生成工具 - 为系统提供各模块的模拟数据
"""
import random
import sqlite3
import json
import os
from datetime import datetime, timedelta
import traceback
from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np

from app.utils.database import get_db_connection
from app.config import config

class DemoDataGenerator:
    """
    演示数据生成器，为系统提供各模块模拟数据
    """
    
    # 通用变量定义（所有生成器共用）
    DEPARTMENTS = [
        '内科', '外科', '妇产科', '儿科', '骨科', '眼科', '耳鼻喉科', '神经科', 
        '心胸外科', '皮肤科', '泌尿外科', '康复科', '口腔科', '中医科', '急诊科'
    ]
    
    DOCTOR_TITLES = ['主任医师', '副主任医师', '主治医师', '住院医师', '医师']
    
    DIAGNOSIS_GROUPS = [
        '呼吸系统疾病', '心血管系统疾病', '消化系统疾病', '泌尿系统疾病', '神经系统疾病', 
        '内分泌系统疾病', '血液系统疾病', '肿瘤', '创伤', '感染性疾病', '先天性疾病', '其他'
    ]
    
    SURGERY_TYPES = [
        '普通外科手术', '骨科手术', '神经外科手术', '心胸外科手术', '泌尿外科手术', 
        '妇产科手术', '眼科手术', '耳鼻喉科手术', '口腔科手术', '其他'
    ]
    
    REVENUE_TYPES = [
        '门诊收入', '住院收入', '药品收入', '检查收入', '手术收入', '其他收入'
    ]
    
    # DRG相关
    DRG_GROUPS = [
        'A组-呼吸系统疾病', 'B组-心血管系统疾病', 'C组-消化系统疾病', 'D组-泌尿系统疾病', 
        'E组-神经系统疾病', 'F组-肌肉骨骼系统', 'G组-内分泌系统', 'H组-皮肤系统', 
        'I组-传染病', 'J组-精神疾病', 'K组-其他'
    ]
    
    INSURANCE_TYPES = [
        '医保', '商业保险', '自费', '公费', '其他'
    ]
    
    PATIENT_TYPES = [
        '普通门诊', '专家门诊', '急诊', '住院', '体检', '复诊', '转诊'
    ]
    
    WEEKDAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    
    # 生成基于正态分布的随机整数
    @staticmethod
    def normal_random_int(mean, std_dev, min_val=None, max_val=None):
        """生成基于正态分布的随机整数"""
        val = int(round(random.normalvariate(mean, std_dev)))
        if min_val is not None:
            val = max(val, min_val)
        if max_val is not None:
            val = min(val, max_val)
        return val
    
    # 生成基于正态分布的随机浮点数
    @staticmethod
    def normal_random_float(mean, std_dev, min_val=None, max_val=None, decimal_places=2):
        """生成基于正态分布的随机浮点数"""
        val = round(random.normalvariate(mean, std_dev), decimal_places)
        if min_val is not None:
            val = max(val, min_val)
        if max_val is not None:
            val = min(val, max_val)
        return val
    
    # 生成随机日期
    @staticmethod
    def random_date(start_date, end_date):
        """在两个日期之间生成随机日期"""
        delta = end_date - start_date
        random_days = random.randint(0, delta.days)
        return start_date + timedelta(days=random_days)
    
    # 创建数据表（如果不存在）
    @staticmethod
    def create_table_if_not_exists(table_name, schema):
        """如果数据表不存在，则创建"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 检查表是否存在
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                if not cursor.fetchone():
                    cursor.execute(schema)
                    conn.commit()
                    print(f"已创建表 {table_name}")
                    return True
                return False
        except Exception as e:
            print(f"创建表 {table_name} 时出错: {str(e)}")
            traceback.print_exc()
            return False
    
    # 检查表中是否有足够数据
    @staticmethod
    def has_sufficient_data(table_name, min_count=100):
        """检查表中是否有足够数据"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                return count >= min_count
        except Exception as e:
            print(f"检查表 {table_name} 数据量时出错: {str(e)}")
            return False
    
    # 批量插入数据
    @staticmethod
    def batch_insert(table_name, columns, data, batch_size=1000):
        """批量插入数据"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 构建占位符
                placeholders = ', '.join(['?'] * len(columns.split(',')))
                
                # 分批处理
                for i in range(0, len(data), batch_size):
                    batch = data[i:i+batch_size]
                    cursor.executemany(
                        f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})",
                        batch
                    )
                
                conn.commit()
                return True
        except Exception as e:
            print(f"向表 {table_name} 批量插入数据时出错: {str(e)}")
            traceback.print_exc()
            return False
    
    # 生成增长或下降趋势的数据
    @staticmethod
    def generate_trend_data(start_value, end_value, periods, noise_level=0.1):
        """生成带噪声的线性趋势数据"""
        # 计算线性趋势
        trend = np.linspace(start_value, end_value, periods)
        
        # 添加随机噪声
        noise = np.random.normal(0, noise_level * abs(end_value - start_value), periods)
        
        # 合并趋势和噪声
        data = trend + noise
        
        # 确保没有负值
        data = np.maximum(data, 0)
        
        return data.tolist()
        
    # 生成分布数据
    @staticmethod
    def generate_distribution_data(categories, total, distribution_type='normal', skew=None):
        """
        生成分布数据
        
        参数:
            categories: 类别列表
            total: 总数
            distribution_type: 分布类型 ('normal', 'uniform', 'exponential', 'pareto')
            skew: 偏斜参数（用于某些分布）
            
        返回:
            每个类别对应的数值列表
        """
        n = len(categories)
        
        if distribution_type == 'uniform':
            # 均匀分布
            weights = np.ones(n)
            
        elif distribution_type == 'exponential':
            # 指数分布（高度偏斜）
            rate = skew or 2.0
            weights = np.exp(-rate * np.arange(n))
            
        elif distribution_type == 'pareto':
            # 帕累托分布（幂律分布）
            alpha = skew or 1.0
            weights = 1.0 / (np.arange(1, n+1) ** alpha)
            
        else:  # 默认为正态分布
            # 正态分布
            center = n / 2
            std = n / (skew or 4)
            weights = np.exp(-((np.arange(n) - center) ** 2) / (2 * std ** 2))
        
        # 归一化权重
        weights = weights / weights.sum()
        
        # 计算每个类别的值
        values = (weights * total).round().astype(int)
        
        # 处理舍入误差，确保总和为total
        remainder = total - values.sum()
        values[0] += remainder
        
        return values.tolist()
    
    # ======================
    # 科室分析相关数据生成
    # ======================
    @classmethod
    def initialize_department_analysis_data(cls):
        """
        初始化科室分析相关数据
        """
        # 创建科室工作量表
        cls.create_department_workload_table()
        
        # 创建科室效率表
        cls.create_department_efficiency_table()
        
        # 创建科室资源表
        cls.create_department_resources_table()
        
        # 创建科室收入表
        cls.create_department_revenue_table()
        
        print("科室分析数据初始化完成。")
        
    @classmethod
    def create_department_workload_table(cls):
        """创建科室工作量表并生成数据"""
        table_name = 'department_workload'
        
        # 创建表
        schema = """
        CREATE TABLE department_workload (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            department TEXT,
            outpatient_count INTEGER,
            inpatient_count INTEGER,
            surgery_count INTEGER,
            emergency_count INTEGER,
            consultation_count INTEGER,
            total_count INTEGER
        )
        """
        cls.create_table_if_not_exists(table_name, schema)
        
        # 如果数据已足够，则跳过
        if cls.has_sufficient_data(table_name, 500):
            print(f"表 {table_name} 已有足够数据")
            return
        
        # 生成数据
        today = datetime.now()
        start_date = today - timedelta(days=365)  # 过去一年的数据
        
        # 为每个科室生成一年的数据
        data = []
        for department in cls.DEPARTMENTS:
            # 为每个科室设置基础工作量（使不同科室有差异）
            base_outpatient = random.randint(20, 100)
            base_inpatient = random.randint(5, 30)
            base_surgery = random.randint(2, 15)
            base_emergency = random.randint(1, 10)
            base_consultation = random.randint(3, 15)
            
            # 为每一天生成数据
            current_date = start_date
            while current_date <= today:
                date_str = current_date.strftime('%Y-%m-%d')
                
                # 根据星期几调整工作量
                weekday = current_date.weekday()
                weekday_factor = 1.0
                if weekday >= 5:  # 周末
                    weekday_factor = 0.6
                
                # 添加季节性变化
                month = current_date.month
                season_factor = 1.0
                if month in [12, 1, 2]:  # 冬季
                    season_factor = 1.2  # 冬季疾病增多
                elif month in [6, 7, 8]:  # 夏季
                    season_factor = 0.9  # 夏季略有下降
                
                # 计算最终工作量
                outpatient_count = cls.normal_random_int(
                    base_outpatient * weekday_factor * season_factor, 
                    base_outpatient * 0.2
                )
                inpatient_count = cls.normal_random_int(
                    base_inpatient * weekday_factor * season_factor, 
                    base_inpatient * 0.15
                )
                surgery_count = cls.normal_random_int(
                    base_surgery * weekday_factor, 
                    base_surgery * 0.3
                )
                emergency_count = cls.normal_random_int(
                    base_emergency * season_factor, 
                    base_emergency * 0.4
                )
                consultation_count = cls.normal_random_int(
                    base_consultation * weekday_factor, 
                    base_consultation * 0.2
                )
                
                # 计算总工作量
                total_count = (
                    outpatient_count + 
                    inpatient_count * 3 +  # 住院权重更高
                    surgery_count * 5 +    # 手术权重更高
                    emergency_count * 2 +  # 急诊权重更高
                    consultation_count
                )
                
                # 添加记录
                data.append((
                    date_str,
                    department,
                    outpatient_count,
                    inpatient_count,
                    surgery_count,
                    emergency_count,
                    consultation_count,
                    total_count
                ))
                
                current_date += timedelta(days=1)
        
        # 批量插入数据
        cls.batch_insert(
            table_name,
            "date, department, outpatient_count, inpatient_count, surgery_count, emergency_count, consultation_count, total_count",
            data
        )
        print(f"已生成 {len(data)} 条科室工作量数据")
    
    @classmethod
    def create_department_efficiency_table(cls):
        """创建科室效率表并生成数据"""
        table_name = 'department_efficiency'
        
        # 创建表
        schema = """
        CREATE TABLE department_efficiency (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            department TEXT,
            avg_treatment_time REAL,  -- 平均就诊时长（分钟）
            avg_waiting_time REAL,    -- 平均等待时间（分钟）
            bed_turnover_rate REAL,   -- 床位周转率
            bed_occupancy_rate REAL,  -- 床位使用率
            avg_los REAL,             -- 平均住院日
            readmission_rate REAL     -- 再入院率
        )
        """
        cls.create_table_if_not_exists(table_name, schema)
        
        # 如果数据已足够，则跳过
        if cls.has_sufficient_data(table_name, 500):
            print(f"表 {table_name} 已有足够数据")
            return
        
        # 生成数据
        today = datetime.now()
        start_date = today - timedelta(days=365)  # 过去一年的数据
        
        # 为每个科室生成数据（按月统计）
        data = []
        for department in cls.DEPARTMENTS:
            # 为每个科室设置基础效率指标
            base_treatment_time = random.uniform(10, 30)  # 基础就诊时长
            base_waiting_time = random.uniform(15, 60)    # 基础等待时间
            base_turnover_rate = random.uniform(3, 8)     # 基础周转率
            base_occupancy_rate = random.uniform(0.6, 0.9) # 基础使用率
            base_los = random.uniform(5, 15)              # 基础住院日
            base_readmission = random.uniform(0.01, 0.08) # 基础再入院率
            
            # 按月生成数据
            current_date = start_date
            while current_date <= today:
                # 月末
                month_end = datetime(current_date.year, current_date.month, 1)
                if month_end.month == 12:
                    month_end = datetime(month_end.year + 1, 1, 1) - timedelta(days=1)
                else:
                    month_end = datetime(month_end.year, month_end.month + 1, 1) - timedelta(days=1)
                
                date_str = current_date.strftime('%Y-%m')
                
                # 添加季节和趋势变化
                month = current_date.month
                month_factor = 1.0
                if month in [1, 2, 7, 8]:  # 寒暑假
                    month_factor = 1.2  # 医院可能更忙
                
                # 添加一些随机波动和趋势改进
                time_factor = 1.0 - (today - current_date).days / (365 * 3)  # 3年内效率提升10%
                
                # 计算最终效率指标
                avg_treatment_time = cls.normal_random_float(
                    base_treatment_time * month_factor * time_factor, 
                    base_treatment_time * 0.1
                )
                avg_waiting_time = cls.normal_random_float(
                    base_waiting_time * month_factor * time_factor, 
                    base_waiting_time * 0.15
                )
                bed_turnover_rate = cls.normal_random_float(
                    base_turnover_rate / time_factor,  # 周转率提高
                    base_turnover_rate * 0.1
                )
                bed_occupancy_rate = cls.normal_random_float(
                    base_occupancy_rate,
                    base_occupancy_rate * 0.05
                )
                avg_los = cls.normal_random_float(
                    base_los * time_factor,  # 住院日降低
                    base_los * 0.1
                )
                readmission_rate = cls.normal_random_float(
                    base_readmission * time_factor,  # 再入院率降低
                    base_readmission * 0.2
                )
                
                # 添加记录
                data.append((
                    date_str,
                    department,
                    avg_treatment_time,
                    avg_waiting_time,
                    bed_turnover_rate,
                    bed_occupancy_rate,
                    avg_los,
                    readmission_rate
                ))
                
                # 移到下个月
                if current_date.month == 12:
                    current_date = datetime(current_date.year + 1, 1, 1)
                else:
                    current_date = datetime(current_date.year, current_date.month + 1, 1)
        
        # 批量插入数据
        cls.batch_insert(
            table_name,
            "date, department, avg_treatment_time, avg_waiting_time, bed_turnover_rate, bed_occupancy_rate, avg_los, readmission_rate",
            data
        )
        print(f"已生成 {len(data)} 条科室效率数据")
    
    @classmethod
    def create_department_resources_table(cls):
        """创建科室资源表并生成数据"""
        table_name = 'department_resources'
        
        # 创建表
        schema = """
        CREATE TABLE department_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            department TEXT,
            doctor_count INTEGER,     -- 医生数量
            nurse_count INTEGER,      -- 护士数量
            bed_count INTEGER,        -- 床位数量
            equipment_count INTEGER,  -- 设备数量
            room_count INTEGER,       -- 房间数量
            space_square_meters REAL  -- 空间（平方米）
        )
        """
        cls.create_table_if_not_exists(table_name, schema)
        
        # 如果数据已足够，则跳过
        if cls.has_sufficient_data(table_name, 50):
            print(f"表 {table_name} 已有足够数据")
            return
        
        # 生成数据
        today = datetime.now()
        start_date = today - timedelta(days=365)  # 过去一年的数据
        
        # 按季度生成数据
        data = []
        for department in cls.DEPARTMENTS:
            # 为每个科室设置基础资源数量
            base_doctor_count = random.randint(5, 20)
            base_nurse_count = random.randint(10, 40)
            base_bed_count = random.randint(10, 50)
            base_equipment_count = random.randint(5, 25)
            base_room_count = random.randint(3, 15)
            base_space = random.randint(100, 500)
            
            # 按季度生成数据
            current_date = datetime(start_date.year, (start_date.month - 1) // 3 * 3 + 1, 1)
            while current_date <= today:
                quarter = (current_date.month - 1) // 3 + 1
                date_str = f"{current_date.year}Q{quarter}"
                
                # 资源随时间略有增长
                time_factor = 1.0 + (current_date - start_date).days / (365 * 2) * 0.1  # 每2年增长10%
                
                # 计算最终资源数量
                doctor_count = int(base_doctor_count * time_factor)
                nurse_count = int(base_nurse_count * time_factor)
                bed_count = int(base_bed_count * time_factor)
                equipment_count = int(base_equipment_count * time_factor)
                room_count = int(base_room_count * time_factor)
                space_square_meters = round(base_space * time_factor, 1)
                
                # 添加记录
                data.append((
                    date_str,
                    department,
                    doctor_count,
                    nurse_count,
                    bed_count,
                    equipment_count,
                    room_count,
                    space_square_meters
                ))
                
                # 移到下一季度
                month = current_date.month
                if month == 10:  # Q4
                    current_date = datetime(current_date.year + 1, 1, 1)
                else:
                    current_date = datetime(current_date.year, month + 3, 1)
        
        # 批量插入数据
        cls.batch_insert(
            table_name,
            "date, department, doctor_count, nurse_count, bed_count, equipment_count, room_count, space_square_meters",
            data
        )
        print(f"已生成 {len(data)} 条科室资源数据")
    
    @classmethod
    def create_department_revenue_table(cls):
        """创建科室收入表并生成数据"""
        table_name = 'department_revenue'
        
        # 创建表
        schema = """
        CREATE TABLE department_revenue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            department TEXT,
            outpatient_income REAL,   -- 门诊收入
            inpatient_income REAL,    -- 住院收入
            drug_income REAL,         -- 药品收入
            material_income REAL,     -- 耗材收入
            examination_income REAL,  -- 检查收入
            surgery_income REAL,      -- 手术收入
            other_income REAL,        -- 其他收入
            total_income REAL         -- 总收入
        )
        """
        cls.create_table_if_not_exists(table_name, schema)
        
        # 如果数据已足够，则跳过
        if cls.has_sufficient_data(table_name, 500):
            print(f"表 {table_name} 已有足够数据")
            return
        
        # 生成数据
        today = datetime.now()
        start_date = today - timedelta(days=365)  # 过去一年的数据
        
        # 为每个科室按月生成数据
        data = []
        for department in cls.DEPARTMENTS:
            # 为每个科室设置基础收入
            if department in ['妇产科', '儿科', '内科', '外科', '骨科']:
                base_level = random.uniform(1.5, 2.5)  # 大科室
            else:
                base_level = random.uniform(0.8, 1.5)  # 小科室
                
            base_outpatient = 50000 * base_level
            base_inpatient = 200000 * base_level
            base_drug = 80000 * base_level
            base_material = 50000 * base_level
            base_examination = 70000 * base_level
            base_surgery = 100000 * base_level
            base_other = 20000 * base_level
            
            # 按月生成数据
            current_date = start_date
            while current_date <= today:
                date_str = current_date.strftime('%Y-%m')
                
                # 添加季节性变化和趋势变化
                month = current_date.month
                season_factor = 1.0
                if month in [12, 1, 2]:  # 冬季
                    season_factor = 1.2  # 冬季收入增加
                elif month in [6, 7, 8]:  # 夏季
                    season_factor = 0.9  # 夏季收入减少
                
                # 年增长率约4%
                time_factor = 1.0 + (current_date - start_date).days / 365 * 0.04
                
                # 计算各项收入
                outpatient_income = cls.normal_random_float(
                    base_outpatient * season_factor * time_factor, 
                    base_outpatient * 0.1
                )
                inpatient_income = cls.normal_random_float(
                    base_inpatient * season_factor * time_factor, 
                    base_inpatient * 0.08
                )
                drug_income = cls.normal_random_float(
                    base_drug * season_factor * time_factor, 
                    base_drug * 0.12
                )
                material_income = cls.normal_random_float(
                    base_material * season_factor * time_factor, 
                    base_material * 0.15
                )
                examination_income = cls.normal_random_float(
                    base_examination * season_factor * time_factor, 
                    base_examination * 0.1
                )
                surgery_income = cls.normal_random_float(
                    base_surgery * season_factor * time_factor, 
                    base_surgery * 0.2
                )
                other_income = cls.normal_random_float(
                    base_other * season_factor * time_factor, 
                    base_other * 0.2
                )
                
                # 计算总收入
                total_income = (
                    outpatient_income + 
                    inpatient_income + 
                    drug_income + 
                    material_income + 
                    examination_income + 
                    surgery_income + 
                    other_income
                )
                
                # 添加记录
                data.append((
                    date_str,
                    department,
                    outpatient_income,
                    inpatient_income,
                    drug_income,
                    material_income,
                    examination_income,
                    surgery_income,
                    other_income,
                    total_income
                ))
                
                # 移到下个月
                if current_date.month == 12:
                    current_date = datetime(current_date.year + 1, 1, 1)
                else:
                    current_date = datetime(current_date.year, current_date.month + 1, 1)
        
        # 批量插入数据
        cls.batch_insert(
            table_name,
            "date, department, outpatient_income, inpatient_income, drug_income, material_income, examination_income, surgery_income, other_income, total_income",
            data
        )
        print(f"已生成 {len(data)} 条科室收入数据")
    
    # ======================
    # 主初始化函数
    # ======================
    @classmethod
    def initialize_all_demo_data(cls):
        """初始化所有模块的演示数据"""
        try:
            print("开始初始化各模块演示数据...")
            
            # 初始化仪表盘数据
            print("\n===== 初始化仪表盘数据 =====")
            from app.routes.dashboard_routes import initialize_demo_data
            initialize_demo_data()
            
            # 初始化科室分析数据
            print("\n===== 初始化科室分析数据 =====")
            cls.initialize_department_analysis_data()
            
            # TODO: 添加其他模块的数据初始化
            # 初始化财务分析数据
            
            # 初始化患者分析数据
            
            # 初始化医生绩效数据
            
            # 初始化DRG分析数据
            
            # 初始化预警数据
            
            print("\n所有演示数据初始化完成！")
            return True
        except Exception as e:
            print(f"初始化演示数据时出错: {str(e)}")
            traceback.print_exc()
            return False 