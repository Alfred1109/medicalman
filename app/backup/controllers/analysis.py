"""
分析控制器模块
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.models.database import Database
import pandas as pd
import json
import traceback

# 创建蓝图
analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/department-analysis')
@login_required
def department_analysis():
    """科室分析页面"""
    return render_template('department-analysis.html')

@analysis_bp.route('/financial-analysis')
@login_required
def financial_analysis():
    """财务分析页面"""
    return render_template('financial-analysis.html')

@analysis_bp.route('/patient-analysis')
@login_required
def patient_analysis():
    """患者分析页面"""
    return render_template('patient-analysis.html')

@analysis_bp.route('/doctor-performance')
@login_required
def doctor_performance():
    """医生绩效页面"""
    return render_template('doctor-performance.html')

@analysis_bp.route('/drg-analysis')
@login_required
def drg_analysis():
    """DRG分析页面"""
    return render_template('drg-analysis.html')

@analysis_bp.route('/api/analysis/department-workload')
@login_required
def department_workload():
    """获取科室工作量数据"""
    try:
        # 获取请求参数
        department = request.args.get('department', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        # 构建查询条件
        conditions = []
        params = []
        
        if department:
            conditions.append("科室 = ?")
            params.append(department)
        
        if start_date:
            conditions.append("日期 >= ?")
            params.append(start_date)
        
        if end_date:
            conditions.append("日期 <= ?")
            params.append(end_date)
        
        # 构建查询语句
        query = """
        SELECT 科室, 专科, 日期, SUM(数量) as 总量
        FROM 门诊量
        """
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += """
        GROUP BY 科室, 专科, 日期
        ORDER BY 日期, 科室, 专科
        """
        
        # 执行查询
        df = Database.query_to_dataframe(query, tuple(params))
        
        # 转换为JSON格式
        result_data = []
        for _, row in df.iterrows():
            result_data.append({
                'department': row['科室'],
                'specialty': row['专科'],
                'date': row['日期'],
                'count': float(row['总量'])
            })
        
        return jsonify(success=True, data=result_data)
        
    except Exception as e:
        error_message = f"获取科室工作量数据时出错: {str(e)}"
        traceback.print_exc()
        
        return jsonify(success=False, error=error_message)

@analysis_bp.route('/api/analysis/department-target')
@login_required
def department_target():
    """获取科室目标完成情况数据"""
    try:
        # 获取请求参数
        department = request.args.get('department', '')
        year = request.args.get('year', '')
        month = request.args.get('month', '')
        
        # 构建查询条件
        conditions = []
        params = []
        
        if department:
            conditions.append("a.科室 = ?")
            params.append(department)
        
        if year:
            conditions.append("b.年 = ?")
            params.append(year)
        
        if month:
            conditions.append("b.月 = ?")
            params.append(month)
        
        # 构建查询语句
        query = """
        SELECT a.科室, a.专科, SUM(a.数量) as 实际量, b.目标值,
               ROUND(SUM(a.数量) * 100.0 / b.目标值, 2) as 完成率
        FROM 门诊量 a
        JOIN 目标值 b ON a.科室=b.科室 AND a.专科=b.专科
        WHERE strftime('%Y',a.日期)=b.年 AND strftime('%m',a.日期)=b.月
        """
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        query += """
        GROUP BY a.科室, a.专科
        ORDER BY 完成率 DESC
        """
        
        # 执行查询
        df = Database.query_to_dataframe(query, tuple(params))
        
        # 转换为JSON格式
        result_data = []
        for _, row in df.iterrows():
            result_data.append({
                'department': row['科室'],
                'specialty': row['专科'],
                'actual': float(row['实际量']),
                'target': float(row['目标值']),
                'completion_rate': float(row['完成率'])
            })
        
        return jsonify(success=True, data=result_data)
        
    except Exception as e:
        error_message = f"获取科室目标完成情况数据时出错: {str(e)}"
        traceback.print_exc()
        
        return jsonify(success=False, error=error_message)

@analysis_bp.route('/api/analysis/drg-indicators')
@login_required
def drg_indicators():
    """获取DRG指标数据"""
    try:
        # 获取请求参数
        department = request.args.get('department', '')
        drg_group = request.args.get('drg_group', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        # 构建查询条件
        conditions = []
        params = []
        
        if department:
            conditions.append("department = ?")
            params.append(department)
        
        if drg_group:
            conditions.append("drg_group = ?")
            params.append(drg_group)
        
        if start_date:
            conditions.append("case_date >= ?")
            params.append(start_date)
        
        if end_date:
            conditions.append("case_date <= ?")
            params.append(end_date)
        
        # 构建查询语句
        query = """
        SELECT department, drg_group, 
               AVG(weight_score) as avg_weight,
               AVG(cost_index) as avg_cost_index,
               AVG(time_index) as avg_time_index,
               AVG(total_cost) as avg_total_cost,
               AVG(length_of_stay) as avg_los
        FROM drg_records
        """
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += """
        GROUP BY department, drg_group
        ORDER BY department, avg_weight DESC
        """
        
        # 执行查询
        df = Database.query_to_dataframe(query, tuple(params))
        
        # 转换为JSON格式
        result_data = []
        for _, row in df.iterrows():
            result_data.append({
                'department': row['department'],
                'drg_group': row['drg_group'],
                'avg_weight': float(row['avg_weight']),
                'avg_cost_index': float(row['avg_cost_index']),
                'avg_time_index': float(row['avg_time_index']),
                'avg_total_cost': float(row['avg_total_cost']),
                'avg_los': float(row['avg_los'])
            })
        
        return jsonify(success=True, data=result_data)
        
    except Exception as e:
        error_message = f"获取DRG指标数据时出错: {str(e)}"
        traceback.print_exc()
        
        return jsonify(success=False, error=error_message)

@analysis_bp.route('/api/analysis/doctors')
@login_required
def get_doctors():
    """获取医生列表"""
    try:
        # 获取请求参数
        department = request.args.get('department', '')
        
        # 构建查询条件
        conditions = []
        params = []
        
        if department:
            conditions.append("department = ?")
            params.append(department)
        
        # 构建查询语句
        query = "SELECT * FROM doctors"
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY department, name"
        
        # 执行查询
        doctors = Database.execute_query(query, tuple(params))
        
        return jsonify(success=True, data=doctors)
        
    except Exception as e:
        error_message = f"获取医生列表时出错: {str(e)}"
        traceback.print_exc()
        
        return jsonify(success=False, error=error_message)

@analysis_bp.route('/api/analysis/doctor-performance')
@login_required
def get_doctor_performance():
    """获取医生绩效数据"""
    try:
        # 获取请求参数
        doctor_id = request.args.get('doctor_id', '')
        year = request.args.get('year', '')
        month = request.args.get('month', '')
        
        # 构建查询条件
        conditions = []
        params = []
        
        if doctor_id:
            conditions.append("p.doctor_id = ?")
            params.append(doctor_id)
        
        if year:
            conditions.append("p.year = ?")
            params.append(year)
        
        if month:
            conditions.append("p.month = ?")
            params.append(month)
        
        # 构建查询语句
        query = """
        SELECT d.name, d.department, d.title, d.specialty,
               p.year, p.month, p.outpatient_count, p.surgery_count,
               p.paper_count, p.research_project_count, p.teaching_hours,
               p.patient_satisfaction, p.quality_score
        FROM doctor_performance p
        JOIN doctors d ON p.doctor_id = d.id
        """
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY p.year DESC, p.month DESC"
        
        # 执行查询
        performance_data = Database.execute_query(query, tuple(params))
        
        return jsonify(success=True, data=performance_data)
        
    except Exception as e:
        error_message = f"获取医生绩效数据时出错: {str(e)}"
        traceback.print_exc()
        
        return jsonify(success=False, error=error_message)

@analysis_bp.route('/api/analysis/patient-statistics')
@login_required
def patient_statistics():
    """获取患者统计数据"""
    try:
        # 获取请求参数
        department = request.args.get('department', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        group_by = request.args.get('group_by', 'gender')  # 默认按性别分组
        
        # 构建查询条件
        conditions = []
        params = []
        
        if department:
            conditions.append("department = ?")
            params.append(department)
        
        if start_date:
            conditions.append("visit_date >= ?")
            params.append(start_date)
        
        if end_date:
            conditions.append("visit_date <= ?")
            params.append(end_date)
        
        # 验证分组字段
        valid_groupings = ['gender', 'age_group', 'visit_type', 'insurance_type']
        if group_by not in valid_groupings:
            group_by = 'gender'
        
        # 构建查询语句
        query = f"""
        SELECT {group_by}, COUNT(*) as patient_count,
               SUM(total_fee) as total_fee,
               AVG(total_fee) as avg_fee
        FROM patient_records
        """
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += f" GROUP BY {group_by} ORDER BY patient_count DESC"
        
        # 执行查询
        statistics = Database.execute_query(query, tuple(params))
        
        return jsonify(success=True, data=statistics)
        
    except Exception as e:
        error_message = f"获取患者统计数据时出错: {str(e)}"
        traceback.print_exc()
        
        return jsonify(success=False, error=error_message) 