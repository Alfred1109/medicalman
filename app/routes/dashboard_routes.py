"""
仪表盘路由模块 - 处理仪表盘相关的路由
"""
from flask import Blueprint, render_template, request, jsonify, make_response, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json
import traceback
import random
from flask_wtf import CSRFProtect
from app import csrf  # 导入app/__init__.py中定义的csrf实例

from app.utils.database import execute_query, get_db_connection
from app.utils.utils import date_range_to_dates
from app.routes.auth_routes import api_login_required
from app.utils.report_generator import ReportGenerator
from app.utils.error_handler import api_error_handler, ApiError

# 创建蓝图
dashboard_api_bp = Blueprint('dashboard_api', __name__)

# 不再创建新的CSRF保护实例，使用app/__init__.py中定义的实例

# ============== 核心数据获取函数 ==============

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
        current_app.logger.error(f"获取仪表盘数据出错: {str(e)}")
        # 生成完整的备用数据结构
        fallback_metrics = generate_fallback_metrics()
        fallback_charts = generate_fallback_charts()
        
        return {
            "error": f"获取仪表盘数据出错: {str(e)}",
            "metrics": fallback_metrics,
            "charts": fallback_charts,
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
        revenue_total = revenue_result[0]['total'] if revenue_result and revenue_result[0]['total'] is not None else 0
        
        # 获取平均住院日
        los_query = f"""
        SELECT AVG(length_of_stay) as avg_los 
        FROM admissions 
        WHERE admission_date BETWEEN '{start_date}' AND '{end_date}'
        """
        los_result = execute_query(los_query)
        avg_los = round(los_result[0]['avg_los'], 1) if los_result and los_result[0]['avg_los'] is not None else 0
        
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
        current_app.logger.error(f"获取核心指标出错: {str(e)}")
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
    """获取科室工作量数据"""
    # 获取科室列表
    dept_query = """
    SELECT DISTINCT department 
    FROM visits 
    WHERE visit_date BETWEEN ? AND ? 
    ORDER BY department
    """
    cursor.execute(dept_query, (start_date, end_date))
    departments = [row[0] for row in cursor.fetchall()]
    
    # 如果没有科室数据，返回空结果
    if not departments:
        return {"departments": [], "outpatient": [], "inpatient": [], "surgery": []}
    
    # 获取各科室门诊量
    outpatient_query = """
    SELECT department, COUNT(*) as count 
    FROM visits 
    WHERE visit_date BETWEEN ? AND ? 
    GROUP BY department
    """
    cursor.execute(outpatient_query, (start_date, end_date))
    outpatient_data = {row[0]: row[1] for row in cursor.fetchall()}
    
    # 获取各科室住院量
    inpatient_query = """
    SELECT department, COUNT(*) as count 
    FROM admissions 
    WHERE admission_date BETWEEN ? AND ? 
    GROUP BY department
    """
    cursor.execute(inpatient_query, (start_date, end_date))
    inpatient_data = {row[0]: row[1] for row in cursor.fetchall()}
    
    # 获取各科室手术量
    surgery_query = """
    SELECT department, COUNT(*) as count 
    FROM surgeries 
    WHERE surgery_date BETWEEN ? AND ? 
    GROUP BY department
    """
    cursor.execute(surgery_query, (start_date, end_date))
    surgery_data = {row[0]: row[1] for row in cursor.fetchall()}
    
    # 构建结果
    outpatient_counts = [outpatient_data.get(dept, 0) for dept in departments]
    inpatient_counts = [inpatient_data.get(dept, 0) for dept in departments]
    surgery_counts = [surgery_data.get(dept, 0) for dept in departments]
    
    result = {
        "departments": departments,
        "outpatient": outpatient_counts,
        "inpatient": inpatient_counts,
        "surgery": surgery_counts
    }
    
    return result

def get_top_admission_diagnosis(cursor, start_date, end_date, limit=5):
    """获取住院诊断分布数据"""
    query = """
    SELECT diagnosis_group, COUNT(*) as count 
    FROM admissions 
    WHERE admission_date BETWEEN ? AND ? 
    GROUP BY diagnosis_group 
    ORDER BY count DESC 
    LIMIT ?
    """
    cursor.execute(query, (start_date, end_date, limit))
    rows = cursor.fetchall()
    
    result = [{'diagnosis_group': row[0], 'count': row[1]} for row in rows]
    return result

def get_alerts(cursor, limit=5):
    """获取警报数据"""
    query = """
    SELECT id, alert_type, description, status, alert_time 
    FROM alerts 
    ORDER BY alert_time DESC 
    LIMIT ?
    """
    cursor.execute(query, (limit,))
    rows = cursor.fetchall()
    
    # 返回格式化后的警报数据，以数组的形式
    alerts = []
    for row in rows:
        alerts.append([
            row[0],                 # id
            row[1],                 # alert_type (显示为title)
            row[2],                 # description (显示为message)
            row[3],                 # status (显示为level)
            '查看详情',              # 操作按钮文本
            str(row[0])             # 警报ID (用于操作)
        ])
    
    return alerts

# ============== 数据格式化函数 ==============

def format_dashboard_data(dashboard_data):
    """格式化仪表盘数据为前端期望的结构"""
    # 如果dashboard_data为None或不是字典类型，使用空字典
    if not dashboard_data or not isinstance(dashboard_data, dict):
        dashboard_data = {}
    
    # 获取数据，如果不存在则使用默认值
    metrics = dashboard_data.get("metrics", {})
    if not metrics or not isinstance(metrics, dict):
        metrics = {}
        
    charts = dashboard_data.get("charts", {})
    if not charts or not isinstance(charts, dict):
        charts = {}
        
    alerts = dashboard_data.get("alerts", [])
    if not alerts or not isinstance(alerts, list):
        alerts = []
    
    # 格式化数据
    try:
        stats = format_stats(metrics)
    except Exception as e:
        current_app.logger.error(f"格式化统计数据失败: {str(e)}")
        stats = generate_fallback_metrics()
    
    try:
        formatted_charts = {
            'outpatientTrend': format_outpatient_trend(charts.get('outpatientTrend', [])),
            'revenueComposition': format_revenue_composition(charts.get('revenueComposition', [])),
            'departmentWorkload': format_department_workload(charts.get('departmentWorkload', {})),
            'inpatientDistribution': format_inpatient_distribution(charts.get('inpatientDistribution', []))
        }
    except Exception as e:
        current_app.logger.error(f"格式化图表数据失败: {str(e)}")
        formatted_charts = generate_fallback_charts()
    
    # 确保每个图表都有完整结构
    for key in formatted_charts:
        if key not in charts:
            current_app.logger.warning(f"图表 {key} 数据缺失，使用默认格式")
    
    return {
        "stats": stats,
        "charts": formatted_charts, 
        "alerts": alerts
    }

def format_stats(metrics):
    """格式化统计数据为前端期望的格式"""
    try:
        # 检查metrics是否为空或非字典类型
        if not metrics or not isinstance(metrics, dict):
            return generate_fallback_metrics()
            
        # 从metrics中提取数据，这里使用中文键名
        outpatient_count = metrics.get("患者总量", "0人次").replace("人次", "")
        revenue = metrics.get("收入总额", "¥0.00")
        avg_los = metrics.get("平均住院日", "0天").replace("天", "")
        surgery_count = metrics.get("手术台次", "0台").replace("台", "")
        
        # 模拟一些变化率
        outpatient_change = random.uniform(-10, 10)
        revenue_change = random.uniform(-5, 15)
        avg_los_change = random.uniform(-8, 8)
        bed_usage_change = random.uniform(-5, 5)
        
        # 生成随机床位使用率
        bed_usage_rate = random.randint(65, 95)
        
        # 构建前端期望的格式 - 同时包含两种前端需要的字段名
        # 同时包含两种不同的字段名(value/count/amount/rate)，以适应不同的前端实现
        return {
            'outpatient': {
                'value': outpatient_count,
                'count': outpatient_count,
                'change': round(outpatient_change, 1)
            },
            'inpatient': {
                'value': avg_los,
                'count': avg_los,
                'change': round(avg_los_change, 1)
            },
            'revenue': {
                'value': revenue,
                'amount': revenue,
                'change': round(revenue_change, 1)
            },
            'bedUsage': {
                'value': f"{bed_usage_rate}%",
                'rate': str(bed_usage_rate),
                'change': round(bed_usage_change, 1)
            }
        }
    except Exception as e:
        current_app.logger.error(f"格式化统计数据出错: {str(e)}")
        traceback.print_exc()  # 打印详细的错误堆栈
        return generate_fallback_metrics()

def format_outpatient_trend(trend_data):
    """格式化门诊趋势数据"""
    if not trend_data:
        return {
            'xAxis': {
                'data': []
            },
            'series': [{
                'name': '门诊量',
                'type': 'line',
                'data': []
            }]
        }
    
    dates = [item.get('date', '') for item in trend_data]
    counts = [item.get('count', 0) for item in trend_data]
    
    return {
        'xAxis': {
            'data': dates
        },
        'series': [{
            'name': '门诊量',
            'type': 'line',
            'data': counts
        }]
    }

def format_revenue_composition(revenue_data):
    """格式化收入构成数据"""
    if not revenue_data:
        return {'data': []}
    
    pie_data = [{'name': item.get('revenue_type', ''), 'value': item.get('amount', 0) or 0} for item in revenue_data]
    
    return {'data': pie_data}

def format_department_workload(workload_data):
    """格式化科室工作量数据"""
    if not workload_data or not isinstance(workload_data, dict) or 'departments' not in workload_data:
        return {
            'yAxis': {
                'data': []
            },
            'series': [
                {'name': '门诊量', 'type': 'bar', 'data': [], 'itemStyle': {'color': '#5470c6'}},
                {'name': '住院量', 'type': 'bar', 'data': [], 'itemStyle': {'color': '#91cc75'}},
                {'name': '手术量', 'type': 'bar', 'data': [], 'itemStyle': {'color': '#fac858'}}
            ]
        }
    
    # 确保数据是安全的
    departments = workload_data.get('departments', [])
    outpatient = workload_data.get('outpatient', [0] * len(departments))
    inpatient = workload_data.get('inpatient', [0] * len(departments))
    surgery = workload_data.get('surgery', [0] * len(departments))
    
    # 确保所有列表长度一致
    max_length = max(len(departments), len(outpatient), len(inpatient), len(surgery))
    departments = departments + [''] * (max_length - len(departments))
    outpatient = outpatient + [0] * (max_length - len(outpatient))
    inpatient = inpatient + [0] * (max_length - len(inpatient))
    surgery = surgery + [0] * (max_length - len(surgery))
    
    return {
        'yAxis': {
            'data': departments
        },
        'series': [
            {
                'name': '门诊量',
                'type': 'bar',
                'data': outpatient,
                'itemStyle': {
                    'color': '#5470c6'
                }
            },
            {
                'name': '住院量',
                'type': 'bar',
                'data': inpatient,
                'itemStyle': {
                    'color': '#91cc75'
                }
            },
            {
                'name': '手术量',
                'type': 'bar',
                'data': surgery,
                'itemStyle': {
                    'color': '#fac858'
                }
            }
        ]
    }

def format_inpatient_distribution(diagnosis_data):
    """格式化住院分布数据"""
    if not diagnosis_data:
        return {
            'legend': [],
            'data': []
        }
    
    # 提取诊断组和计数，确保值为数字
    legend = [item.get('diagnosis_group', '') for item in diagnosis_data]
    data = [{'name': item.get('diagnosis_group', ''), 'value': item.get('count', 0) or 0} for item in diagnosis_data]
    
    return {
        'legend': legend,
        'data': data
    }

# ============== 备用数据生成函数 ==============

def generate_fallback_metrics():
    """生成备用的指标数据"""
    return {
        'outpatient': {
            'value': '0', 
            'count': '0',
            'change': 0
        },
        'inpatient': {
            'value': '0', 
            'count': '0',
            'change': 0
        },
        'revenue': {
            'value': '¥0.00', 
            'amount': '¥0.00',
            'change': 0
        },
        'bedUsage': {
            'value': '0%', 
            'rate': '0',
            'change': 0
        }
    }

def generate_fallback_charts():
    """生成备用的图表数据"""
    return {
        'outpatientTrend': {
            'xAxis': {
                'data': []
            },
            'series': [{
                'name': '门诊量', 
                'type': 'line', 
                'data': []
            }]
        },
        'revenueComposition': {'data': []},
        'departmentWorkload': {
            'yAxis': {
                'data': []
            },
            'series': [
                {'name': '门诊量', 'type': 'bar', 'data': [], 'itemStyle': {'color': '#5470c6'}},
                {'name': '住院量', 'type': 'bar', 'data': [], 'itemStyle': {'color': '#91cc75'}},
                {'name': '手术量', 'type': 'bar', 'data': [], 'itemStyle': {'color': '#fac858'}}
            ]
        },
        'inpatientDistribution': {'legend': [], 'data': []}
    }

def generate_fallback_dashboard_data():
    """生成备用仪表盘数据，当数据获取或处理出错时使用"""
    return {
        "stats": generate_fallback_metrics(),
        "charts": generate_fallback_charts(),
        "alerts": []
    }

# ============== API路由 ==============

@dashboard_api_bp.route('/metrics', methods=['GET', 'POST'])
@csrf.exempt
@api_error_handler
def get_dashboard_metrics():
    """获取仪表盘指标数据 - 统一GET和POST请求处理"""
    try:
        # 获取请求参数，同时支持GET和POST
        if request.method == 'POST':
            data = request.get_json() or {}
            date_range = data.get('date_range', 'week')
            start_date = data.get('start_date')
            end_date = data.get('end_date')
        else:  # GET请求
            date_range = request.args.get('date_range', 'week')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
        
        # 验证日期参数
        if date_range == 'custom' and (not start_date or not end_date):
            current_app.logger.warning("自定义日期范围需要提供开始和结束日期")
            fallback_data = generate_fallback_dashboard_data()
            return jsonify({
                "success": False,
                "error": "自定义日期范围需要提供开始和结束日期",
                "error_code": "INVALID_DATE_PARAMS",
                "data": fallback_data,
                "date_range": {
                    "start": start_date or "",
                    "end": end_date or "",
                    "type": date_range
                }
            }), 400
        
        # 如果没有提供日期范围，则根据date_range使用工具函数生成
        if (not start_date or not end_date) and date_range != 'custom':
            start_date, end_date = date_range_to_dates(date_range)
            current_app.logger.debug(f"使用date_range_to_dates生成日期范围: {start_date} 至 {end_date}")
        
        current_app.logger.info(f"获取仪表盘数据: date_range={date_range}, start_date={start_date}, end_date={end_date}")
        
        # 获取仪表盘数据
        dashboard_data = get_dashboard_data(start_date, end_date, date_range)
        
        # 如果数据获取出错
        if "error" in dashboard_data:
            current_app.logger.error(dashboard_data["error"])
            # 生成一个完整的数据结构，而不是仅返回错误
            formatted_data = format_dashboard_data({
                "metrics": dashboard_data.get("metrics", generate_fallback_metrics()),
                "charts": dashboard_data.get("charts", generate_fallback_charts()),
                "alerts": dashboard_data.get("alerts", [])
            })
            
            return jsonify({
                "success": False,
                "error": dashboard_data["error"],
                "error_code": "DATA_FETCH_ERROR",
                "data": formatted_data,
                "date_range": dashboard_data["date_range"]
            }), 500
        
        # 格式化数据以符合前端期望的结构
        try:
            # 不要直接使用format_stats，而是通过format_dashboard_data处理整个数据
            formatted_data = format_dashboard_data(dashboard_data)
        except Exception as e:
            current_app.logger.error(f"格式化仪表盘数据出错: {str(e)}")
            # 使用预定义的备用数据生成函数
            formatted_data = generate_fallback_dashboard_data()
        
        # 返回成功响应
        return jsonify({
            "success": True,
            "data": formatted_data,
            "date_range": dashboard_data["date_range"]
        })
    
    except Exception as e:
        current_app.logger.error(f"处理仪表盘请求时出错: {str(e)}")
        traceback.print_exc()
        
        # 生成完整的备用数据
        fallback_data = generate_fallback_dashboard_data()
        
        # 返回错误响应，但包含备用数据
        return jsonify({
            "success": False,
            "error": f"服务器内部错误: {str(e)}",
            "error_code": "INTERNAL_SERVER_ERROR",
            "data": fallback_data,
            "date_range": {
                "start": start_date or "",
                "end": end_date or "",
                "type": date_range or "week"
            }
        }), 500

@dashboard_api_bp.route('/metrics_get', methods=['GET'])
@csrf.exempt
@api_error_handler
def get_dashboard_metrics_get():
    """获取仪表盘指标数据(兼容旧版本GET接口) - 转发到统一处理函数"""
    return get_dashboard_metrics()

@dashboard_api_bp.route('/export_report', methods=['GET'])
@csrf.exempt
def export_dashboard_report():
    """导出仪表盘报表"""
    try:
        # 获取请求参数
        report_format = request.args.get('format', 'pdf')
        date_range = request.args.get('date_range', 'week')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 生成日期范围
        if not start_date or not end_date:
            start_date, end_date = date_range_to_dates(date_range)
        
        # 获取数据
        dashboard_data = get_dashboard_data(start_date, end_date, date_range)
        
        # 根据格式生成报表
        if report_format == 'pdf':
            # 创建报表生成器并生成PDF
            report_generator = ReportGenerator()
            pdf_data = report_generator.generate_dashboard_pdf(dashboard_data)
            
            # 返回报表
            response = make_response(pdf_data)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename="dashboard_report_{datetime.now().strftime("%Y%m%d%H%M%S")}.pdf"'
            return response
        
        else:
            # 不支持的格式
            return jsonify({'error': f'不支持的导出格式: {report_format}'}), 400
            
    except Exception as e:
        current_app.logger.error(f"导出报表失败: {str(e)}")
        return jsonify({'error': f'导出报表失败: {str(e)}'}), 500

# ============== 演示数据生成函数 ==============

def initialize_demo_data(force=False):
    """初始化仪表盘演示数据"""
    try:
        print("初始化仪表盘演示数据...")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 创建必要的表
            tables = {
                'visits': '''
                    CREATE TABLE IF NOT EXISTS visits (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        visit_date TEXT NOT NULL,
                        visit_type TEXT NOT NULL,
                        department TEXT NOT NULL,
                        patient_id TEXT,
                        doctor_id TEXT,
                        visit_reason TEXT,
                        diagnosis TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''',
                'admissions': '''
                    CREATE TABLE IF NOT EXISTS admissions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        patient_id TEXT NOT NULL,
                        admission_date TEXT NOT NULL,
                        discharge_date TEXT,
                        length_of_stay INTEGER,
                        department TEXT NOT NULL,
                        diagnosis_group TEXT,
                        doctor_id TEXT,
                        status TEXT DEFAULT 'active',
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''',
                'revenue': '''
                    CREATE TABLE IF NOT EXISTS revenue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        revenue_type TEXT NOT NULL,
                        amount REAL NOT NULL,
                        department TEXT,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''',
                'surgeries': '''
                    CREATE TABLE IF NOT EXISTS surgeries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        surgery_date TEXT NOT NULL,
                        patient_id TEXT NOT NULL,
                        doctor_id TEXT NOT NULL,
                        department TEXT NOT NULL,
                        surgery_type TEXT NOT NULL,
                        duration INTEGER,
                        status TEXT DEFAULT 'completed',
                        complications TEXT,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''',
                'alerts': '''
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_time TEXT NOT NULL,
                        alert_type TEXT NOT NULL,
                        description TEXT NOT NULL,
                        status TEXT DEFAULT 'new',
                        related_entity TEXT,
                        related_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                '''
            }
            
            for table_name, schema in tables.items():
                # 如果强制重建，先删除现有表
                if force:
                    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                
                # 创建表
                cursor.execute(schema)
            
            # 检查是否需要生成数据（如果表为空或强制重建）
            for table_name in tables.keys():
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                
                if count == 0 or force:
                    print(f"生成{table_name}演示数据...")
                    # 生成日期范围（过去3个月的数据）
                    current_date = datetime.now()
                    start_date = datetime(current_date.year, 1, 1).strftime('%Y-%m-%d')  # 当年1月1日开始
                    end_date = current_date.strftime('%Y-%m-%d')
                    
                    # 根据表名生成不同的数据
                    if table_name == 'visits':
                        generate_visit_data(cursor, start_date, end_date)
                    elif table_name == 'admissions':
                        generate_admission_data(cursor, start_date, end_date)
                    elif table_name == 'revenue':
                        generate_revenue_data(cursor, start_date, end_date)
                    elif table_name == 'surgeries':
                        generate_surgery_data(cursor, start_date, end_date)
                    elif table_name == 'alerts':
                        generate_alert_data(cursor)
                    
                    print(f"{table_name}演示数据生成完成")
                else:
                    print(f"{table_name}表已有{count}条记录，跳过生成")
        
        print("仪表盘演示数据初始化完成！")
        return True
    
    except Exception as e:
        print(f"初始化仪表盘演示数据出错: {str(e)}")
        traceback.print_exc()
        return False

def generate_visit_data(cursor, start_date, end_date):
    """生成门诊就诊数据"""
    departments = ['内科', '外科', '妇产科', '儿科', '骨科', '眼科', '耳鼻喉科', '神经科', '口腔科', '皮肤科']
    visit_types = ['普通门诊', '专家门诊', '急诊', '复诊', '转诊']
    
    # 将日期字符串转换为datetime对象
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    days = (end - start).days + 1
    
    # 为每个科室每天生成数据
    for dept in departments:
        # 每个科室的基准日均就诊量，随机生成，范围20-100
        base_daily_visits = random.randint(20, 100)
        
        for i in range(days):
            # 当前日期
            current_date = (start + timedelta(days=i)).strftime('%Y-%m-%d')
            
            # 根据星期几调整就诊量（周末减少）
            weekday = (start + timedelta(days=i)).weekday()
            multiplier = 0.7 if weekday >= 5 else 1.0  # 周末减少30%
            
            # 添加随机波动 (±20%)
            daily_fluctuation = random.uniform(0.8, 1.2)
            
            # 计算当天就诊量
            daily_visits = int(base_daily_visits * multiplier * daily_fluctuation)
            
            # 为每次就诊生成记录
            for _ in range(daily_visits):
                # 随机选择就诊类型
                visit_type = random.choice(visit_types)
                
                # 随机生成患者ID和医生ID
                patient_id = f'P{random.randint(10000, 99999)}'
                doctor_id = f'D{random.randint(100, 999)}'
                
                # 插入数据
                cursor.execute(
                    'INSERT INTO visits (date, visit_date, visit_type, department, patient_id, doctor_id) VALUES (?, ?, ?, ?, ?, ?)',
                    (current_date, current_date, visit_type, dept, patient_id, doctor_id)
                )

def generate_admission_data(cursor, start_date, end_date):
    """生成住院数据"""
    departments = ['内科', '外科', '妇产科', '儿科', '骨科', '神经科']
    diagnosis_groups = ['心血管疾病', '呼吸系统疾病', '消化系统疾病', '神经系统疾病', '骨科疾病', 
                        '内分泌疾病', '感染性疾病', '肿瘤', '妇产科疾病', '儿科疾病']
    
    # 将日期字符串转换为datetime对象
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    days = (end - start).days + 1
    
    # 为每个科室每天生成数据
    for dept in departments:
        # 每个科室的基准日均住院量，随机生成，范围2-10
        base_daily_admissions = random.randint(2, 10)
        
        for i in range(days):
            # 当前日期
            admission_date = (start + timedelta(days=i)).strftime('%Y-%m-%d')
            
            # 添加随机波动 (±30%)
            daily_fluctuation = random.uniform(0.7, 1.3)
            
            # 计算当天住院量
            daily_admissions = int(base_daily_admissions * daily_fluctuation)
            
            # 为每次住院生成记录
            for _ in range(daily_admissions):
                # 随机生成患者ID和医生ID
                patient_id = f'P{random.randint(10000, 99999)}'
                doctor_id = f'D{random.randint(100, 999)}'
                
                # 随机选择诊断组
                diagnosis_group = random.choice(diagnosis_groups)
                
                # 随机住院天数（1-30天）
                length_of_stay = random.randint(1, 30)
                
                # 计算出院日期（如果已出院）
                admission_date_obj = datetime.strptime(admission_date, '%Y-%m-%d')
                discharge_date_obj = admission_date_obj + timedelta(days=length_of_stay)
                
                # 如果出院日期在当前日期之前，则已出院，否则仍在住院
                if discharge_date_obj <= end:
                    discharge_date = discharge_date_obj.strftime('%Y-%m-%d')
                    status = 'discharged'
                else:
                    discharge_date = None
                    status = 'active'
                    # 调整住院天数为当前已住天数
                    length_of_stay = (end - admission_date_obj).days
                
                # 插入数据
                cursor.execute(
                    'INSERT INTO admissions (patient_id, admission_date, discharge_date, length_of_stay, department, diagnosis_group, doctor_id, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    (patient_id, admission_date, discharge_date, length_of_stay, dept, diagnosis_group, doctor_id, status)
                )

def generate_revenue_data(cursor, start_date, end_date):
    """生成收入数据"""
    departments = ['内科', '外科', '妇产科', '儿科', '骨科', '眼科', '耳鼻喉科', '神经科', '口腔科', '皮肤科']
    revenue_types = ['门诊', '住院', '药房', '检查', '手术', '其他']
    
    # 将日期字符串转换为datetime对象
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    days = (end - start).days + 1
    
    # 每个科室的基准日收入（元）
    department_base_daily_revenues = {
        '内科': random.randint(20000, 50000),
        '外科': random.randint(30000, 70000),
        '妇产科': random.randint(25000, 60000),
        '儿科': random.randint(15000, 40000),
        '骨科': random.randint(30000, 65000),
        '眼科': random.randint(20000, 45000),
        '耳鼻喉科': random.randint(15000, 35000),
        '神经科': random.randint(25000, 55000),
        '口腔科': random.randint(18000, 40000),
        '皮肤科': random.randint(12000, 30000)
    }
    
    # 每种收入类型的比例
    revenue_type_proportions = {
        '门诊': 0.25,
        '住院': 0.35,
        '药房': 0.15,
        '检查': 0.12,
        '手术': 0.10,
        '其他': 0.03
    }
    
    # 为每个科室每天生成数据
    for dept in departments:
        base_daily_revenue = department_base_daily_revenues[dept]
        
        for i in range(days):
            # 当前日期
            revenue_date = (start + timedelta(days=i)).strftime('%Y-%m-%d')
            
            # 根据星期几调整收入（周末减少）
            weekday = (start + timedelta(days=i)).weekday()
            multiplier = 0.8 if weekday >= 5 else 1.0  # 周末减少20%
            
            # 添加随机波动 (±20%)
            daily_fluctuation = random.uniform(0.8, 1.2)
            
            # 计算当天总收入
            daily_total_revenue = base_daily_revenue * multiplier * daily_fluctuation
            
            # 为每种收入类型生成记录
            for revenue_type, proportion in revenue_type_proportions.items():
                # 计算该类型的收入
                type_revenue = daily_total_revenue * proportion
                
                # 添加随机波动 (±10%)
                type_revenue *= random.uniform(0.9, 1.1)
                
                # 描述
                description = f"{dept}{revenue_type}收入"
                
                # 插入数据
                cursor.execute(
                    'INSERT INTO revenue (date, revenue_type, amount, department, description) VALUES (?, ?, ?, ?, ?)',
                    (revenue_date, revenue_type, round(type_revenue, 2), dept, description)
                )

def generate_surgery_data(cursor, start_date, end_date):
    """生成手术数据"""
    departments = ['外科', '骨科', '神经科', '妇产科', '眼科', '耳鼻喉科', '口腔科']
    surgery_types = ['普通外科手术', '骨科手术', '心脏手术', '神经外科手术', '眼科手术', 
                    '耳鼻喉科手术', '妇产科手术', '泌尿外科手术', '整形外科手术', '微创手术']
    complications = [None, None, None, None, '出血', '感染', '过敏反应', '麻醉并发症', '心律失常', '伤口裂开']
    statuses = ['scheduled', 'in_progress', 'completed', 'cancelled']
    
    # 将日期字符串转换为datetime对象
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    days = (end - start).days + 1
    
    # 为每个科室每天生成数据
    for dept in departments:
        # 每个科室的基准日均手术量，随机生成，范围1-8
        base_daily_surgeries = random.randint(1, 8)
        
        for i in range(days):
            # 当前日期
            surgery_date = (start + timedelta(days=i)).strftime('%Y-%m-%d')
            
            # 根据星期几调整手术量（周末减少）
            weekday = (start + timedelta(days=i)).weekday()
            multiplier = 0.5 if weekday >= 5 else 1.0  # 周末减少50%
            
            # 添加随机波动 (±30%)
            daily_fluctuation = random.uniform(0.7, 1.3)
            
            # 计算当天手术量
            daily_surgeries = int(base_daily_surgeries * multiplier * daily_fluctuation)
            
            # 为每台手术生成记录
            for _ in range(daily_surgeries):
                # 随机生成患者ID和医生ID
                patient_id = f'P{random.randint(10000, 99999)}'
                doctor_id = f'D{random.randint(100, 999)}'
                
                # 随机选择手术类型
                surgery_type = random.choice(surgery_types)
                
                # 随机手术时长（30分钟到5小时）
                duration = random.randint(30, 300)
                
                # 随机状态
                status = random.choice(statuses)
                
                # 随机并发症
                complication = random.choice(complications)
                
                # 随机备注
                notes = f'患者{patient_id}的{surgery_type}' if random.random() < 0.3 else None
                
                # 插入数据
                cursor.execute(
                    'INSERT INTO surgeries (surgery_date, patient_id, doctor_id, department, surgery_type, duration, status, complications, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (surgery_date, patient_id, doctor_id, dept, surgery_type, duration, status, complication, notes)
                )

def generate_alert_data(cursor):
    """生成警报数据"""
    alert_types = ['critical', 'warning', 'info']
    alert_statuses = ['new', 'processing', 'resolved', 'ignored']
    alert_descriptions = [
        'ICU床位使用率超过95%',
        '心内科门诊量异常增加',
        '系统维护通知',
        '药品库存不足警告',
        '设备维护提醒',
        '人员配置警告',
        '门诊等待时间过长',
        '收入异常波动',
        '患者满意度降低',
        '急诊科负荷过高'
    ]
    
    # 获取当前日期
    current_date = datetime.now()
    
    # 生成50个警报
    for i in range(50):
        # 随机日期（过去7天内）
        days_ago = random.randint(0, 7)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        alert_time = (current_date - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)).strftime('%Y-%m-%d %H:%M:%S')
        
        # 随机警报类型和状态
        alert_type = random.choice(alert_types)
        status = random.choice(alert_statuses)
        
        # 随机描述
        description = random.choice(alert_descriptions)
        
        # 随机关联实体
        related_entity = random.choice(['department', 'patient', 'system', None])
        related_id = random.randint(1, 100) if related_entity else None
        
        # 插入数据
        cursor.execute(
            'INSERT INTO alerts (alert_time, alert_type, description, status, related_entity, related_id) VALUES (?, ?, ?, ?, ?, ?)',
            (alert_time, alert_type, description, status, related_entity, related_id)
        ) 