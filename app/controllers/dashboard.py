"""
仪表盘控制器模块
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.models.database import Database
import pandas as pd
import json
from datetime import datetime

# 创建蓝图
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """仪表盘首页"""
    current_year = datetime.now().year
    return render_template('dashboard.html', current_year=current_year)

@dashboard_bp.route('/alerts')
@login_required
def alerts():
    """预警通知页面"""
    return render_template('alerts.html')

@dashboard_bp.route('/api/dashboard/summary')
@login_required
def dashboard_summary():
    """获取仪表盘摘要数据"""
    try:
        # 获取门诊量总数
        outpatient_query = "SELECT SUM(数量) as total FROM 门诊量"
        outpatient_result = Database.execute_query(outpatient_query)
        outpatient_total = outpatient_result[0]['total'] if outpatient_result else 0
        
        # 获取科室数量
        department_query = "SELECT COUNT(DISTINCT 科室) as count FROM 门诊量"
        department_result = Database.execute_query(department_query)
        department_count = department_result[0]['count'] if department_result else 0
        
        # 获取专科数量
        specialty_query = "SELECT COUNT(DISTINCT 专科) as count FROM 门诊量"
        specialty_result = Database.execute_query(specialty_query)
        specialty_count = specialty_result[0]['count'] if specialty_result else 0
        
        # 获取DRG分组数量
        drg_query = "SELECT COUNT(DISTINCT drg_group) as count FROM drg_records"
        drg_result = Database.execute_query(drg_query)
        drg_count = drg_result[0]['count'] if drg_result else 0
        
        # 返回摘要数据
        summary_data = {
            'outpatient_total': outpatient_total,
            'department_count': department_count,
            'specialty_count': specialty_count,
            'drg_count': drg_count
        }
        
        return jsonify(success=True, data=summary_data)
        
    except Exception as e:
        return jsonify(success=False, error=str(e))

@dashboard_bp.route('/api/dashboard/outpatient-trend')
@login_required
def outpatient_trend():
    """获取门诊量趋势数据"""
    try:
        # 获取门诊量趋势
        query = """
        SELECT 日期, SUM(数量) as 总量
        FROM 门诊量
        GROUP BY 日期
        ORDER BY 日期
        """
        
        df = Database.query_to_dataframe(query)
        
        # 转换为JSON格式
        trend_data = {
            'dates': df['日期'].tolist(),
            'values': df['总量'].tolist()
        }
        
        return jsonify(success=True, data=trend_data)
        
    except Exception as e:
        return jsonify(success=False, error=str(e))

@dashboard_bp.route('/api/dashboard/department-distribution')
@login_required
def department_distribution():
    """获取科室分布数据"""
    try:
        # 获取科室分布
        query = """
        SELECT 科室, SUM(数量) as 总量
        FROM 门诊量
        GROUP BY 科室
        ORDER BY 总量 DESC
        """
        
        df = Database.query_to_dataframe(query)
        
        # 转换为JSON格式
        distribution_data = {
            'departments': df['科室'].tolist(),
            'values': df['总量'].tolist()
        }
        
        return jsonify(success=True, data=distribution_data)
        
    except Exception as e:
        return jsonify(success=False, error=str(e))

@dashboard_bp.route('/api/dashboard/target-completion')
@login_required
def target_completion():
    """获取目标完成情况数据"""
    try:
        # 获取目标完成情况
        query = """
        SELECT a.科室, a.专科, SUM(a.数量) as 实际量, b.目标值,
               ROUND(SUM(a.数量) * 100.0 / b.目标值, 2) as 完成率
        FROM 门诊量 a
        JOIN 目标值 b ON a.科室=b.科室 AND a.专科=b.专科
        WHERE strftime('%Y',a.日期)=b.年 AND strftime('%m',a.日期)=b.月
        GROUP BY a.科室, a.专科
        ORDER BY 完成率 DESC
        """
        
        df = Database.query_to_dataframe(query)
        
        # 转换为JSON格式
        completion_data = []
        for _, row in df.iterrows():
            completion_data.append({
                'department': row['科室'],
                'specialty': row['专科'],
                'actual': float(row['实际量']),
                'target': float(row['目标值']),
                'completion_rate': float(row['完成率'])
            })
        
        return jsonify(success=True, data=completion_data)
        
    except Exception as e:
        return jsonify(success=False, error=str(e))

@dashboard_bp.route('/api/dashboard/drg-analysis')
@login_required
def drg_analysis():
    """获取DRG分析数据"""
    try:
        # 获取DRG分析数据
        query = """
        SELECT department, drg_group, 
               AVG(weight_score) as avg_weight,
               AVG(cost_index) as avg_cost_index,
               AVG(time_index) as avg_time_index,
               AVG(total_cost) as avg_total_cost,
               AVG(length_of_stay) as avg_los
        FROM drg_records
        GROUP BY department, drg_group
        ORDER BY department, avg_weight DESC
        """
        
        df = Database.query_to_dataframe(query)
        
        # 转换为JSON格式
        drg_data = []
        for _, row in df.iterrows():
            drg_data.append({
                'department': row['department'],
                'drg_group': row['drg_group'],
                'avg_weight': float(row['avg_weight']),
                'avg_cost_index': float(row['avg_cost_index']),
                'avg_time_index': float(row['avg_time_index']),
                'avg_total_cost': float(row['avg_total_cost']),
                'avg_los': float(row['avg_los'])
            })
        
        return jsonify(success=True, data=drg_data)
        
    except Exception as e:
        return jsonify(success=False, error=str(e)) 