"""
仪表盘路由模块 - 处理仪表盘相关的路由
"""
from flask import Blueprint, render_template, request, jsonify, make_response
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json
import traceback
import pandas as pd

from app.models.database import Database
from app.utils.data_helpers import date_range_to_dates
from app.utils.decorators import api_login_required

# 创建蓝图
dashboard_bp = Blueprint('dashboard_api', __name__, url_prefix='/api/dashboard')

def get_dashboard_data(start_date=None, end_date=None, date_range='week'):
    """
    获取仪表盘数据
    
    参数:
        start_date: 开始日期
        end_date: 结束日期
        date_range: 日期范围类型
        
    返回:
        包含仪表盘数据的字典
    """
    # 如果未提供日期范围，则根据date_range参数生成
    if not start_date or not end_date:
        # 根据date_range参数计算日期范围
        today = datetime.now().date()
        
        if date_range == 'today':
            start_date = today.strftime('%Y-%m-%d')
            end_date = start_date
        elif date_range == 'yesterday':
            yesterday = today - timedelta(days=1)
            start_date = yesterday.strftime('%Y-%m-%d')
            end_date = start_date
        elif date_range == 'week':
            start_date = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
        elif date_range == 'month':
            start_date = f"{today.year}-{today.month:02d}-01"
            end_date = today.strftime('%Y-%m-%d')
        elif date_range == 'quarter':
            quarter_start_month = ((today.month - 1) // 3) * 3 + 1
            start_date = f"{today.year}-{quarter_start_month:02d}-01"
            end_date = today.strftime('%Y-%m-%d')
        elif date_range == 'year':
            start_date = f"{today.year}-01-01"
            end_date = today.strftime('%Y-%m-%d')
    
    try:
        # 获取核心指标数据
        metrics = get_core_metrics(start_date, end_date)
        
        # 获取图表数据
        charts = {
            "outpatientTrend": get_outpatient_trend(start_date, end_date),
            "revenueComposition": get_revenue_composition(start_date, end_date),
            "departmentWorkload": get_department_workload(start_date, end_date),
            "inpatientDistribution": get_inpatient_distribution(start_date, end_date)
        }
        
        # 获取警报数据
        alerts = get_alerts(start_date, end_date)
        
        # 返回仪表盘完整数据
        return {
            "metrics": metrics,
            "charts": charts,
            "alerts": alerts,
            "date_range": {
                "start": start_date,
                "end": end_date,
                "type": date_range
            }
        }
    except Exception as e:
        traceback.print_exc()
        return {
            "error": f"获取仪表盘数据出错: {str(e)}",
            "metrics": {},
            "charts": {},
            "alerts": [],
            "date_range": {
                "start": start_date,
                "end": end_date,
                "type": date_range
            }
        }

def get_core_metrics(start_date, end_date):
    """获取核心指标数据"""
    try:
        # 获取就诊患者总数
        patient_query = f"""
        SELECT COUNT(*) as total 
        FROM visits 
        WHERE visit_date BETWEEN '{start_date}' AND '{end_date}'
        """
        patient_result = Database.execute_query(patient_query)
        patient_count = patient_result[0]['total'] if patient_result else 0
        
        # 获取收入总额
        revenue_query = f"""
        SELECT SUM(amount) as total 
        FROM revenue 
        WHERE date BETWEEN '{start_date}' AND '{end_date}'
        """
        revenue_result = Database.execute_query(revenue_query)
        revenue_total = revenue_result[0]['total'] if revenue_result else 0
        
        # 获取平均住院日
        los_query = f"""
        SELECT AVG(length_of_stay) as avg_los 
        FROM admissions 
        WHERE admission_date BETWEEN '{start_date}' AND '{end_date}'
        """
        los_result = Database.execute_query(los_query)
        avg_los = round(los_result[0]['avg_los'], 1) if los_result and los_result[0]['avg_los'] else 0
        
        # 获取手术台次
        surgery_query = f"""
        SELECT COUNT(*) as total 
        FROM surgeries 
        WHERE surgery_date BETWEEN '{start_date}' AND '{end_date}'
        """
        surgery_result = Database.execute_query(surgery_query)
        surgery_count = surgery_result[0]['total'] if surgery_result else 0
        
        return {
            "患者总量": f"{patient_count}人次",
            "收入总额": f"¥{revenue_total:,.2f}",
            "平均住院日": f"{avg_los}天",
            "手术台次": f"{surgery_count}台"
        }
    except Exception as e:
        print(f"获取核心指标出错: {str(e)}")
        return {
            "患者总量": "数据获取失败",
            "收入总额": "数据获取失败",
            "平均住院日": "数据获取失败",
            "手术台次": "数据获取失败"
        }

def get_outpatient_trend(start_date, end_date):
    """获取门诊量趋势数据"""
    try:
        query = f"""
        SELECT date as date, COUNT(*) as count
        FROM visits
        WHERE visit_type='门诊' AND date BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY date
        ORDER BY date
        """
        
        df = Database.query_to_dataframe(query)
        
        if df.empty:
            # 返回空数据结构
            return {"xAxis": [], "series": [{"data": []}]}
        
        # 确保日期连续
        all_dates = pd.date_range(start=start_date, end=end_date)
        date_df = pd.DataFrame({'date': all_dates})
        date_df['date'] = date_df['date'].dt.strftime('%Y-%m-%d')
        
        # 合并数据
        merged_df = pd.merge(date_df, df, on='date', how='left').fillna(0)
        
        # 转换为图表数据格式
        return {
            "xAxis": merged_df['date'].tolist(),
            "series": [{
                "name": "门诊量",
                "type": "line",
                "data": merged_df['count'].astype(int).tolist()
            }]
        }
    except Exception as e:
        print(f"获取门诊量趋势出错: {str(e)}")
        return {"xAxis": [], "series": [{"data": []}]}

def get_revenue_composition(start_date, end_date):
    """获取收入构成数据"""
    try:
        query = f"""
        SELECT revenue_type, SUM(amount) as total
        FROM revenue
        WHERE date BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY revenue_type
        ORDER BY total DESC
        """
        
        df = Database.query_to_dataframe(query)
        
        if df.empty:
            # 返回空数据结构
            return {"data": []}
        
        # 转换为图表数据格式
        data = []
        for _, row in df.iterrows():
            data.append({
                "name": row['revenue_type'],
                "value": float(row['total'])
            })
        
        return {"data": data}
    except Exception as e:
        print(f"获取收入构成出错: {str(e)}")
        return {"data": []}

def get_department_workload(start_date, end_date):
    """获取科室工作量数据"""
    try:
        query = f"""
        SELECT department, COUNT(*) as visit_count
        FROM visits
        WHERE date BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY department
        ORDER BY visit_count DESC
        LIMIT 10
        """
        
        df = Database.query_to_dataframe(query)
        
        if df.empty:
            # 返回空数据结构
            return {"yAxis": [], "series": [{"data": []}]}
        
        # 转换为图表数据格式
        return {
            "yAxis": df['department'].tolist(),
            "series": [{
                "name": "就诊量",
                "type": "bar",
                "data": df['visit_count'].astype(int).tolist()
            }]
        }
    except Exception as e:
        print(f"获取科室工作量出错: {str(e)}")
        return {"yAxis": [], "series": [{"data": []}]}

def get_inpatient_distribution(start_date, end_date):
    """获取住院患者分布数据"""
    try:
        query = f"""
        SELECT diagnosis_group, COUNT(*) as patient_count
        FROM admissions
        WHERE admission_date BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY diagnosis_group
        ORDER BY patient_count DESC
        """
        
        df = Database.query_to_dataframe(query)
        
        if df.empty:
            # 返回空数据结构
            return {"legend": [], "data": []}
        
        # 如果结果超过10个类别，合并其他类别
        if len(df) > 10:
            top_df = df.head(9)
            other_count = df.iloc[9:]['patient_count'].sum()
            
            # 添加"其他"类别
            other_row = pd.DataFrame({
                'diagnosis_group': ['其他'], 
                'patient_count': [other_count]
            })
            
            df = pd.concat([top_df, other_row])
        
        # 转换为图表数据格式
        legend = df['diagnosis_group'].tolist()
        data = []
        for _, row in df.iterrows():
            data.append({
                "name": row['diagnosis_group'],
                "value": int(row['patient_count'])
            })
        
        return {
            "legend": legend,
            "data": data
        }
    except Exception as e:
        print(f"获取住院患者分布出错: {str(e)}")
        return {"legend": [], "data": []}

def get_alerts(start_date, end_date):
    """获取警报数据"""
    try:
        query = f"""
        SELECT alert_id, alert_time, alert_type, description, status
        FROM alerts
        WHERE alert_time BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY alert_time DESC
        LIMIT 5
        """
        
        df = Database.query_to_dataframe(query)
        
        if df.empty:
            # 返回空列表
            return []
        
        # 转换状态和类型为文本
        type_map = {
            'critical': '严重',
            'warning': '警告',
            'info': '信息'
        }
        
        status_map = {
            'new': '新建',
            'processing': '处理中',
            'resolved': '已解决',
            'ignored': '已忽略'
        }
        
        # 转换为警报列表
        alerts = []
        for _, row in df.iterrows():
            alert_type = row['alert_type']
            alert_status = row['status']
            
            alerts.append({
                'id': row['alert_id'],
                'time': row['alert_time'],
                'type': alert_type,
                'typeText': type_map.get(alert_type, alert_type),
                'description': row['description'],
                'status': alert_status,
                'statusText': status_map.get(alert_status, alert_status)
            })
        
        return alerts
    except Exception as e:
        print(f"获取警报数据出错: {str(e)}")
        return []

@dashboard_bp.route('/data', methods=['GET'])
@api_login_required
def dashboard_data():
    """获取仪表盘数据接口"""
    try:
        # 获取请求参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        date_range = request.args.get('date_range', 'week')
        
        # 获取仪表盘数据
        dashboard_data = get_dashboard_data(start_date, end_date, date_range)
        
        return jsonify({
            'success': True,
            'data': dashboard_data
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f"获取仪表盘数据出错: {str(e)}"
        }), 500

@dashboard_bp.route('/export', methods=['GET'])
@api_login_required
def export_dashboard():
    """导出仪表盘报告"""
    try:
        # 获取请求参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        date_range = request.args.get('date_range', 'week')
        report_format = request.args.get('format', 'pdf').lower()
        
        # 获取仪表盘数据
        dashboard_data = get_dashboard_data(start_date, end_date, date_range)
        
        if report_format == 'pdf':
            # 导入报告生成工具
            from app.utils.report_generator import ReportGenerator
            
            # 生成PDF报告
            pdf_data = ReportGenerator.generate_dashboard_report(
                data=dashboard_data,
                title="医疗管理系统仪表盘报告",
                start_date=start_date,
                end_date=end_date
            )
            
            # 设置响应头
            filename = f"dashboard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            response = make_response(pdf_data)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            
            return response
        elif report_format == 'excel':
            # 为将来扩展提供Excel导出功能
            # TODO: 实现Excel报告生成
            return jsonify({"error": "Excel导出功能尚未实现"}), 501
        else:
            return jsonify({"error": f"不支持的格式: {report_format}"}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"导出报告出错: {str(e)}"}), 500 