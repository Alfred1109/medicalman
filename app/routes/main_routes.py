"""
主路由模块 - 处理网站主要页面路由
"""
from flask import Blueprint, render_template, redirect, url_for, current_app, jsonify, session
import sqlite3
import datetime
from app.routes.auth_routes import login_required, api_login_required

# 创建蓝图
main_bp = Blueprint('main', __name__)

# 为了兼容之前的模板，添加额外的蓝图
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/', endpoint='index')
@login_required
def dashboard_index():
    """仪表盘首页"""
    return render_template('dashboard/dashboard.html')

@dashboard_bp.route('/alerts')
@login_required
def alerts():
    """预警通知页面"""
    return render_template('dashboard/alerts.html', alerts=[
        {
            'id': 1,
            'title': '内科就诊量异常',
            'description': '内科昨日就诊量较上周同期下降30%，请关注原因',
            'severity': 'high',
            'date': '2025-03-23'
        },
        {
            'id': 2,
            'title': '目标完成提醒',
            'description': '外科本月就诊量已完成月度目标的90%',
            'severity': 'medium',
            'date': '2025-03-22'
        }
    ])

@dashboard_bp.route('/workload')
@login_required
def workload_analysis():
    """工作量分析页面"""
    return render_template('dashboard/workloadanlysis.html')

@main_bp.route('/')
@login_required
def index():
    """主页 - 重定向到仪表盘"""
    return redirect(url_for('dashboard.index'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """仪表盘页面"""
    return render_template('dashboard.html')

@main_bp.route('/about')
def about():
    """关于页面"""
    return render_template('about.html')

@main_bp.route('/api/dates')
@api_login_required
def get_dates():
    """获取所有日期"""
    try:
        conn = sqlite3.connect(current_app.config.get('DATABASE_PATH', 'instance/medical_workload.db'))
        cursor = conn.cursor()
        
        # 查询门诊量表中的所有日期
        cursor.execute("SELECT DISTINCT 日期 FROM 门诊量 ORDER BY 日期")
        dates = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify(dates)
    except Exception as e:
        current_app.logger.error(f"获取日期列表失败: {str(e)}")
        return jsonify([])

@main_bp.route('/api/stats/department')
@api_login_required
def get_department_stats():
    """获取科室统计数据"""
    try:
        conn = sqlite3.connect(current_app.config.get('DATABASE_PATH', 'instance/medical_workload.db'))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询科室统计数据
        cursor.execute("""
            SELECT 科室, COUNT(*) as 记录数, SUM(数量) as 总数量, AVG(数量) as 平均数量
            FROM 门诊量
            GROUP BY 科室
            ORDER BY 总数量 DESC
        """)
        
        results = []
        for row in cursor.fetchall():
            results.append(dict(row))
        
        conn.close()
        
        return jsonify(results)
    except Exception as e:
        current_app.logger.error(f"获取科室统计数据失败: {str(e)}")
        return jsonify([])

@main_bp.route('/api/stats/specialty')
@api_login_required
def get_specialty_stats():
    """获取专科统计数据"""
    try:
        conn = sqlite3.connect(current_app.config.get('DATABASE_PATH', 'instance/medical_workload.db'))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询专科统计数据
        cursor.execute("""
            SELECT 专科, COUNT(*) as 记录数, SUM(数量) as 总数量, AVG(数量) as 平均数量
            FROM 门诊量
            GROUP BY 专科
            ORDER BY 总数量 DESC
        """)
        
        results = []
        for row in cursor.fetchall():
            results.append(dict(row))
        
        conn.close()
        
        return jsonify(results)
    except Exception as e:
        current_app.logger.error(f"获取专科统计数据失败: {str(e)}")
        return jsonify([])

@main_bp.route('/api/stats/date')
@api_login_required
def get_date_stats():
    """获取日期统计数据"""
    try:
        conn = sqlite3.connect(current_app.config.get('DATABASE_PATH', 'instance/medical_workload.db'))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询日期统计数据
        cursor.execute("""
            SELECT 日期, COUNT(*) as 记录数, SUM(数量) as 总数量
            FROM 门诊量
            GROUP BY 日期
            ORDER BY 日期
        """)
        
        results = []
        for row in cursor.fetchall():
            results.append(dict(row))
        
        conn.close()
        
        return jsonify(results)
    except Exception as e:
        current_app.logger.error(f"获取日期统计数据失败: {str(e)}")
        return jsonify([]) 