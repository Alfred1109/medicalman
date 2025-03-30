"""
主路由模块 - 处理网站主要页面路由
"""
from flask import Blueprint, render_template, redirect, url_for, current_app, jsonify, session, request, flash
import sqlite3
import datetime
from app.routes.auth_routes import login_required, api_login_required
from app.config import config

# 创建蓝图
main_bp = Blueprint('main', __name__)  # 移除URL前缀,因为这是主蓝图
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')  # 添加URL前缀

@main_bp.route('/')
def index():
    """主页 - 重定向到仪表盘"""
    if 'user_id' not in session:
        # 将当前URL作为next参数传递给登录页面
        next_url = request.url
        if not next_url.startswith('/'):
            next_url = '/'
        return redirect(url_for('auth.login', next=next_url))
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/')
@login_required
def index():
    """仪表盘首页"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login', next=request.url))
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

@main_bp.route('/about')
def about():
    return render_template('main/about.html')

@main_bp.route('/api/dates')
@api_login_required
def get_dates():
    """获取所有日期"""
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
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
        conn = sqlite3.connect(config.DATABASE_PATH)
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
        conn = sqlite3.connect(config.DATABASE_PATH)
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
        conn = sqlite3.connect(config.DATABASE_PATH)
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

@main_bp.route('/api/data', methods=['GET'])
def get_data():
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM 门诊量")
        data = cursor.fetchall()
        conn.close()
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"获取数据失败: {str(e)}")
        return jsonify([])

@main_bp.route('/api/analysis', methods=['GET'])
def get_analysis():
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM 门诊量")
        data = cursor.fetchall()
        conn.close()
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"获取分析数据失败: {str(e)}")
        return jsonify([])

@main_bp.route('/api/charts', methods=['GET'])
def get_charts():
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM 门诊量")
        data = cursor.fetchall()
        conn.close()
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"获取图表数据失败: {str(e)}")
        return jsonify([])

@main_bp.route('/api/reports', methods=['GET'])
def get_reports():
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM 门诊量")
        data = cursor.fetchall()
        conn.close()
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"获取报告数据失败: {str(e)}")
        return jsonify([])

@main_bp.route('/test-api')
def test_api():
    """API测试页面"""
    return render_template('test-api.html')

@main_bp.route('/test_chat')
def test_chat():
    """测试聊天气泡页面"""
    return render_template('test_chat.html') 