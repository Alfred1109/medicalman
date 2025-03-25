"""
仪表盘路由模块 - 处理仪表盘相关的路由
"""
from flask import Blueprint, render_template, request, jsonify, make_response, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json
import traceback
import pandas as pd
import random

# 修改为使用新的数据库工具
from app.utils.database import execute_query, execute_query_to_dataframe, get_db_connection
from app.utils.utils import date_range_to_dates  # 数据帮助工具已合并到utils.py
from app.routes.auth_routes import api_login_required
from app.utils.report_generator import ReportGenerator
from app.services.chart_service import ChartService

# 导入仪表盘服务（如果需要Excel导出）
try:
    from app.services.dashboard_service import DashboardService
    dashboard_service = DashboardService()
except ImportError:
    class DashboardServiceStub:
        def export_dashboard_excel(self, data):
            raise NotImplementedError("DashboardService未实现")
    dashboard_service = DashboardServiceStub()

# 创建蓝图
dashboard_api_bp = Blueprint('dashboard_api', __name__)

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
        # 使用公共日期工具函数获取日期范围
        start_date, end_date = date_range_to_dates(date_range)
    
    try:
        # 需要获取数据库连接和游标
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 获取核心指标数据
            metrics = get_core_metrics(start_date, end_date)
            
            # 获取图表数据
            charts = {
                "outpatientTrend": get_outpatient_trend(cursor, start_date, end_date),
                "revenueComposition": get_revenue_distribution(cursor, start_date, end_date),
                "departmentWorkload": get_department_workload(cursor, start_date, end_date),
                "inpatientDistribution": get_top_admission_diagnosis(cursor, start_date, end_date)
            }
            
            # 获取警报数据
            alerts = get_alerts(cursor, 5)
        
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
        patient_result = execute_query(patient_query)
        patient_count = patient_result[0]['total'] if patient_result else 0
        
        # 获取收入总额
        revenue_query = f"""
        SELECT SUM(amount) as total 
        FROM revenue 
        WHERE date BETWEEN '{start_date}' AND '{end_date}'
        """
        revenue_result = execute_query(revenue_query)
        revenue_total = revenue_result[0]['total'] if revenue_result else 0
        
        # 获取平均住院日
        los_query = f"""
        SELECT AVG(length_of_stay) as avg_los 
        FROM admissions 
        WHERE admission_date BETWEEN '{start_date}' AND '{end_date}'
        """
        los_result = execute_query(los_query)
        avg_los = round(los_result[0]['avg_los'], 1) if los_result and los_result[0]['avg_los'] else 0
        
        # 获取手术台次
        surgery_query = f"""
        SELECT COUNT(*) as total 
        FROM surgeries 
        WHERE surgery_date BETWEEN '{start_date}' AND '{end_date}'
        """
        surgery_result = execute_query(surgery_query)
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

def get_outpatient_trend(cursor, start_date, end_date):
    """获取门诊趋势数据"""
    query = """
    SELECT visit_date as date, COUNT(*) as count 
    FROM visits 
    WHERE visit_date BETWEEN ? AND ? 
    GROUP BY visit_date 
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

def get_department_workload(cursor, start_date, end_date):
    """获取科室工作量数据（同时包含门诊、住院、手术数据）"""
    # 1. 获取门诊科室数据
    outpatient_query = """
    SELECT department, COUNT(*) as count 
    FROM visits 
    WHERE visit_date BETWEEN ? AND ? 
    GROUP BY department 
    ORDER BY count DESC
    """
    cursor.execute(outpatient_query, (start_date, end_date))
    outpatient_rows = cursor.fetchall()
    
    # 2. 获取住院科室数据
    inpatient_query = """
    SELECT department, COUNT(*) as count 
    FROM admissions 
    WHERE admission_date BETWEEN ? AND ? 
    GROUP BY department 
    ORDER BY count DESC
    """
    cursor.execute(inpatient_query, (start_date, end_date))
    inpatient_rows = cursor.fetchall()
    
    # 3. 获取手术科室数据
    surgery_query = """
    SELECT department, COUNT(*) as count 
    FROM surgeries 
    WHERE surgery_date BETWEEN ? AND ? 
    GROUP BY department 
    ORDER BY count DESC
    """
    cursor.execute(surgery_query, (start_date, end_date))
    surgery_rows = cursor.fetchall()
    
    # 4. 合并科室数据
    departments = {}
    
    # 处理门诊数据
    for row in outpatient_rows:
        dept = row[0]
        count = row[1]
        if dept not in departments:
            departments[dept] = {'outpatient': 0, 'inpatient': 0, 'surgery': 0}
        departments[dept]['outpatient'] = count
    
    # 处理住院数据
    for row in inpatient_rows:
        dept = row[0]
        count = row[1]
        if dept not in departments:
            departments[dept] = {'outpatient': 0, 'inpatient': 0, 'surgery': 0}
        departments[dept]['inpatient'] = count
    
    # 处理手术数据
    for row in surgery_rows:
        dept = row[0]
        count = row[1]
        if dept not in departments:
            departments[dept] = {'outpatient': 0, 'inpatient': 0, 'surgery': 0}
        departments[dept]['surgery'] = count
    
    # 5. 按工作量总和排序并取前10个科室
    sorted_departments = sorted(departments.items(), 
                               key=lambda x: x[1]['outpatient'] + x[1]['inpatient'] + x[1]['surgery'], 
                               reverse=True)[:10]
    
    # 6. 提取科室名称列表和各类工作量数据
    dept_names = [dept[0] for dept in sorted_departments]
    outpatient_counts = [dept[1]['outpatient'] for dept in sorted_departments]
    inpatient_counts = [dept[1]['inpatient'] for dept in sorted_departments]
    surgery_counts = [dept[1]['surgery'] for dept in sorted_departments]
    
    return {
        'departments': dept_names,
        'outpatient': outpatient_counts,
        'inpatient': inpatient_counts,
        'surgery': surgery_counts
    }

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

def get_alerts(cursor, limit=5):
    """获取最新警报数据"""
    query = """
    SELECT alert_time, alert_type, description, status
    FROM alerts
    ORDER BY alert_time DESC
    LIMIT ?
    """
    cursor.execute(query, (limit,))
    rows = cursor.fetchall()
    
    alerts = []
    for row in rows:
        alert_time = row[0]
        alert_type = row[1]
        description = row[2]
        status = row[3]
        
        # 根据类型和状态设置不同的文本和颜色
        if alert_type == "critical":
            type_text = "严重"
            type_class = "danger"
            action = "立即处理" if status == "new" else "查看详情"
        elif alert_type == "warning":
            type_text = "警告"
            type_class = "warning"
            action = "尽快处理" if status == "new" else "查看详情"
        else:  # info
            type_text = "信息"
            type_class = "info"
            action = "查看" if status == "new" else "查看详情"
        
        # 状态文本和颜色
        if status == "new":
            status_text = "新"
            status_class = "primary"
        elif status == "processing":
            status_text = "处理中"
            status_class = "warning"
        elif status == "resolved":
            status_text = "已解决"
            status_class = "success"
        else:  # ignored
            status_text = "已忽略"
            status_class = "secondary"
        
        alerts.append({
            'time': alert_time,
            'type': type_class,  # 对应前端CSS类
            'typeText': type_text,  # 显示文本
            'description': description,
            'status': status_class,  # 对应前端CSS类
            'statusText': status_text,  # 显示文本
            'action': action  # 操作按钮文本
        })
    
    return alerts

@dashboard_api_bp.route('/data', methods=['GET'])
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

@dashboard_api_bp.route('/export_dashboard', methods=['GET'])
def export_dashboard():
    """导出报表"""
    try:
        # 获取参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        date_range = request.args.get('date_range', '30days')
        report_format = request.args.get('format', 'pdf').lower()
        
        # 获取仪表盘数据
        dashboard_data = get_dashboard_data(start_date, end_date, date_range)
        
        # 根据格式导出
        if report_format == 'pdf':
            # 生成PDF报表
            pdf_data = ReportGenerator.generate_dashboard_report(
                data=dashboard_data,
                title="医疗工作量仪表盘报告",
                start_date=start_date,
                end_date=end_date
            )
            
            # 检查是否返回的是HTML（当PDF生成失败时）
            content_type = 'application/pdf'
            filename = f'dashboard_report_{datetime.now().strftime("%Y%m%d%H%M%S")}.pdf'
            
            # 检查是否为HTML内容（根据内容开头判断）
            if pdf_data.startswith(b'<') and b'</html>' in pdf_data:
                content_type = 'text/html'
                filename = f'dashboard_report_{datetime.now().strftime("%Y%m%d%H%M%S")}.html'
            
            # 返回报表
            response = make_response(pdf_data)
            response.headers['Content-Type'] = content_type
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        
        elif report_format == 'excel':
            # 导出Excel
            excel_data = dashboard_service.export_dashboard_excel(dashboard_data)
            
            # 返回Excel文件
            response = make_response(excel_data)
            response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            response.headers['Content-Disposition'] = f'attachment; filename="dashboard_report_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx"'
            return response
        
        else:
            # 不支持的格式
            return jsonify({'error': f'不支持的导出格式: {report_format}'}), 400
            
    except Exception as e:
        current_app.logger.error(f"导出报表失败: {str(e)}")
        return jsonify({'error': f'导出报表失败: {str(e)}'}), 500

@dashboard_api_bp.route('/metrics', methods=['POST'])
@api_login_required
def get_dashboard_metrics():
    """获取仪表盘指标数据"""
    try:
        # 从请求中获取日期范围参数
        data = request.get_json() or {}
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        date_range = data.get('date_range', 'week')
        
        # 根据选择的日期范围计算开始和结束日期
        if not start_date or not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            if date_range == 'today':
                start_date = end_date
            elif date_range == 'yesterday':
                start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                end_date = start_date
            elif date_range == 'week':
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            elif date_range == 'month':
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            elif date_range == 'quarter':
                start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            elif date_range == 'year':
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            else:
                # 默认最近90天
                start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        current_app.logger.debug(f"查询日期范围: {start_date} 至 {end_date}，选择的日期范围: {date_range}")
        
        # 调试日志
        current_app.logger.debug(f"开始查询仪表盘数据，日期范围: {start_date} 至 {end_date}")
        
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
        
        # 打印获取到的数据（调试用）
        current_app.logger.debug(f"获取到的门诊趋势数据: {outpatient_data}")
        current_app.logger.debug(f"获取到的收入分布数据: {revenue_data}")
        current_app.logger.debug(f"获取到的住院病种TOP10数据: {admission_diagnosis_data}")
        current_app.logger.debug(f"获取到的手术类型分布数据: {surgery_data}")
        current_app.logger.debug(f"获取到的统计数据: {stats_data}")
        current_app.logger.debug(f"获取到的科室工作量数据: {department_workload_data}")
        
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
        
        current_app.logger.debug(f"格式化后的数据: {formatted_data}")
        
        return jsonify({'success': True, 'data': formatted_data})
    
    except Exception as e:
        current_app.logger.error(f"获取仪表盘数据时出错: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取仪表盘数据失败: {str(e)}'}), 500

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
    stats = {}
    
    # 门诊总量
    query = "SELECT COUNT(*) FROM visits WHERE visit_date BETWEEN ? AND ?"
    cursor.execute(query, (start_date, end_date))
    stats['outpatient_count'] = cursor.fetchone()[0]
    
    # 住院总量
    query = "SELECT COUNT(*) FROM admissions WHERE admission_date BETWEEN ? AND ?"
    cursor.execute(query, (start_date, end_date))
    stats['inpatient_count'] = cursor.fetchone()[0]
    
    # 总收入
    query = "SELECT SUM(amount) FROM revenue WHERE date BETWEEN ? AND ?"
    cursor.execute(query, (start_date, end_date))
    total_revenue = cursor.fetchone()[0]
    stats['total_revenue'] = int(total_revenue) if total_revenue else 0
    
    return stats

def initialize_demo_data():
    """
    初始化仪表盘示例数据，包括：
    1. 门诊记录
    2. 住院记录
    3. 收入记录
    4. 手术记录
    5. 警报记录
    """
    try:
        # 获取当前日期
        today = datetime.now()
        
        # 定义一组科室名称
        departments = ['内科', '外科', '妇产科', '儿科', '骨科', '眼科', '耳鼻喉科', '神经科', '心胸外科', '皮肤科', '泌尿外科', '康复科']
        
        # 定义收入类型
        revenue_types = ['门诊收入', '住院收入', '药品收入', '检查收入', '手术收入', '其他收入']
        
        # 定义诊断组
        diagnosis_groups = ['呼吸系统疾病', '心血管系统疾病', '消化系统疾病', '泌尿系统疾病', '神经系统疾病', 
                           '内分泌系统疾病', '血液系统疾病', '肿瘤', '创伤', '感染性疾病', '先天性疾病', '其他']
        
        # 定义手术类型
        surgery_types = ['普通外科手术', '骨科手术', '神经外科手术', '心胸外科手术', '泌尿外科手术', '妇产科手术', '眼科手术', '耳鼻喉科手术', '口腔科手术', '其他']
        
        # 警报类型
        alert_types = ['critical', 'warning', 'info']
        
        # 警报状态
        alert_statuses = ['new', 'processing', 'resolved', 'ignored']
        
        # 生成过去90天的日期
        end_date = today
        start_date = end_date - timedelta(days=90)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 检查数据表是否存在，如果不存在则创建
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='visits'")
            if not cursor.fetchone():
                cursor.execute("""
                CREATE TABLE visits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    visit_date TEXT,
                    visit_type TEXT,
                    patient_id TEXT,
                    doctor_id TEXT,
                    department TEXT,
                    visit_reason TEXT,
                    diagnosis TEXT,
                    fee REAL
                )
                """)
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admissions'")
            if not cursor.fetchone():
                cursor.execute("""
                CREATE TABLE admissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admission_date TEXT,
                    discharge_date TEXT,
                    patient_id INTEGER,
                    department TEXT,
                    diagnosis_group TEXT,
                    length_of_stay INTEGER,
                    fee REAL
                )
                """)
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='revenue'")
            if not cursor.fetchone():
                cursor.execute("""
                CREATE TABLE revenue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    revenue_type TEXT,
                    amount REAL,
                    description TEXT
                )
                """)
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='surgeries'")
            if not cursor.fetchone():
                cursor.execute("""
                CREATE TABLE surgeries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    surgery_date TEXT,
                    patient_id INTEGER,
                    department TEXT,
                    surgery_type TEXT,
                    duration INTEGER,
                    fee REAL
                )
                """)
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alerts'")
            if not cursor.fetchone():
                cursor.execute("""
                CREATE TABLE alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_time TEXT,
                    alert_type TEXT,
                    description TEXT,
                    status TEXT
                )
                """)
            
            # 检查是否已有足够数据
            cursor.execute("SELECT COUNT(*) FROM visits")
            visits_count = cursor.fetchone()[0]
            
            # 如果已有足够数据，则跳过初始化
            if visits_count > 500:
                print("数据库已有足够的示例数据。")
                return
            
            print(f"开始初始化示例数据（从 {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}）...")
            
            # 生成门诊记录
            for day in range(90):
                current_date = (start_date + timedelta(days=day)).strftime('%Y-%m-%d')
                
                # 每天生成随机数量的门诊记录
                visit_count = 50 + int(random.random() * 50)  # 50-100之间的随机数
                
                # 添加一些波动和趋势，周末减少
                weekday = (start_date + timedelta(days=day)).weekday()
                if weekday >= 5:  # 周末
                    visit_count = int(visit_count * 0.6)
                
                # 趋势：随着时间增长，门诊量略有增长
                trend_factor = 1.0 + day * 0.003  # 0-0.3的增长系数
                visit_count = int(visit_count * trend_factor)
                
                for _ in range(visit_count):
                    patient_id = f"P{random.randint(1, 10000)}"
                    doctor_id = f"D{random.randint(1, 100)}"
                    department = random.choice(departments)
                    diagnosis = f"诊断{random.randint(1, 200)}"
                    visit_type = random.choice(["普通门诊", "专家门诊", "急诊", "复诊", "转诊"])
                    visit_reason = random.choice(["发热", "腹痛", "头痛", "咳嗽", "皮疹", "定期随访", "其他"])
                    
                    cursor.execute("""
                    INSERT INTO visits (date, visit_date, visit_type, department, patient_id, doctor_id, visit_reason, diagnosis)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (current_date, current_date, visit_type, department, patient_id, doctor_id, visit_reason, diagnosis))
            
            # 生成住院记录
            for day in range(90):
                current_date = (start_date + timedelta(days=day)).strftime('%Y-%m-%d')
                
                # 每天生成随机数量的住院记录
                admission_count = 10 + int(random.random() * 15)  # 10-25之间的随机数
                
                for _ in range(admission_count):
                    patient_id = random.randint(1, 5000)
                    department = random.choice(departments)
                    diagnosis_group = random.choice(diagnosis_groups)
                    length_of_stay = random.randint(1, 30)
                    discharge_date = (datetime.strptime(current_date, '%Y-%m-%d') + timedelta(days=length_of_stay)).strftime('%Y-%m-%d')
                    fee = round(5000 + random.random() * 20000, 2)  # 5000-25000之间的随机数
                    
                    cursor.execute("""
                    INSERT INTO admissions (admission_date, discharge_date, patient_id, department, diagnosis_group, length_of_stay, fee)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (current_date, discharge_date, patient_id, department, diagnosis_group, length_of_stay, fee))
            
            # 生成收入记录
            for day in range(90):
                current_date = (start_date + timedelta(days=day)).strftime('%Y-%m-%d')
                
                # 为每种收入类型生成记录
                for revenue_type in revenue_types:
                    # 基础金额
                    base_amount = {
                        '门诊收入': 30000,
                        '住院收入': 100000,
                        '药品收入': 50000,
                        '检查收入': 40000,
                        '手术收入': 80000,
                        '其他收入': 20000
                    }.get(revenue_type, 10000)
                    
                    # 添加一些随机波动
                    fluctuation = random.uniform(0.8, 1.2)
                    
                    # 周末收入减少
                    weekday = (start_date + timedelta(days=day)).weekday()
                    if weekday >= 5:  # 周末
                        fluctuation *= 0.7
                    
                    # 计算最终金额
                    amount = round(base_amount * fluctuation, 2)
                    
                    cursor.execute("""
                    INSERT INTO revenue (date, revenue_type, amount, description)
                    VALUES (?, ?, ?, ?)
                    """, (current_date, revenue_type, amount, f"{current_date} {revenue_type}"))
            
            # 生成手术记录
            for day in range(90):
                current_date = (start_date + timedelta(days=day)).strftime('%Y-%m-%d')
                
                # 每天生成随机数量的手术记录
                surgery_count = 5 + int(random.random() * 15)  # 5-20之间的随机数
                
                # 周末手术减少
                weekday = (start_date + timedelta(days=day)).weekday()
                if weekday >= 5:  # 周末
                    surgery_count = int(surgery_count * 0.5)
                
                for _ in range(surgery_count):
                    patient_id = f"P{random.randint(1, 3000)}"
                    doctor_id = f"D{random.randint(1, 100)}"
                    department = random.choice(departments)
                    surgery_type = random.choice(surgery_types)
                    duration = random.randint(30, 300)  # 30分钟到5小时
                    status = random.choice(["scheduled", "in_progress", "completed", "cancelled"])
                    complications = random.choice(["无", "轻微感染", "术中出血", "麻醉并发症", ""])
                    notes = random.choice(["手术顺利", "恢复良好", "需要特别观察", ""])
                    
                    cursor.execute("""
                    INSERT INTO surgeries (surgery_date, patient_id, doctor_id, department, surgery_type, duration, status, complications, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (current_date, patient_id, doctor_id, department, surgery_type, duration, status, complications, notes))
            
            # 生成警报记录
            for _ in range(20):  # 生成20条警报
                alert_day = random.randint(0, 89)
                alert_date = (start_date + timedelta(days=alert_day)).strftime('%Y-%m-%d')
                alert_time = f"{alert_date} {random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
                alert_type = random.choice(alert_types)
                
                # 根据警报类型生成不同的描述
                if alert_type == 'critical':
                    description = random.choice([
                        "ICU床位不足，需要紧急调配",
                        f"{random.choice(departments)}人员紧急缺勤，需要安排替补",
                        "重要医疗设备故障，需要立即维修",
                        "医院信息系统遭受网络攻击",
                        "发现医疗事故，需要立即干预"
                    ])
                elif alert_type == 'warning':
                    description = random.choice([
                        f"{random.choice(departments)}患者人数激增，可能需要增加人手",
                        "药品库存不足，需要及时补充",
                        "实验室报告异常，需要复查",
                        "病房占用率接近饱和",
                        "预约系统出现延迟"
                    ])
                else:  # info
                    description = random.choice([
                        "今日门诊量统计已完成",
                        "系统维护将在今晚进行",
                        "新版医疗指南已更新",
                        "医院例会时间已调整",
                        "新员工培训即将开始"
                    ])
                
                # 较新的警报更可能是未处理状态
                if alert_day > 70:  # 最近20天的警报
                    status = random.choices(alert_statuses, weights=[0.5, 0.3, 0.1, 0.1])[0]
                else:  # 较早的警报
                    status = random.choices(alert_statuses, weights=[0.1, 0.2, 0.5, 0.2])[0]
                
                cursor.execute("""
                INSERT INTO alerts (alert_time, alert_type, description, status)
                VALUES (?, ?, ?, ?)
                """, (alert_time, alert_type, description, status))
            
            conn.commit()
            print("示例数据初始化完成。")
    
    except Exception as e:
        print(f"初始化示例数据出错: {str(e)}")
        traceback.print_exc() 