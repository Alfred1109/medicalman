"""
数据分析路由模块
提供数据分析和可视化API
"""
from flask import Blueprint, request, jsonify, render_template, current_app
import json
import pandas as pd
import traceback

from app.utils.data_analysis import DataAnalyzer, DataVisualizer, generate_plotly_chart_for_sql
from app.routes.auth_routes import login_required, api_login_required
from app.utils.database import get_outpatient_data, get_completion_rate, get_db_connection

# 创建蓝图
analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/')
@login_required
def analytics_home():
    """数据分析首页"""
    return render_template('analytics/index.html')

@analytics_bp.route('/profile-report', methods=['POST'])
@api_login_required
def generate_profile_report():
    """生成数据概览报告"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        query = data.get('query')
        title = data.get('title', '数据分析报告')
        minimal = data.get('minimal', False)
        
        if not query:
            return jsonify({'error': '查询语句为空'}), 400
            
        # 生成报告
        report_html = DataAnalyzer.generate_profile_report_for_query(
            query=query,
            title=title,
            minimal=minimal
        )
        
        return jsonify({
            'success': True,
            'report_html': report_html
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'生成报告出错: {str(e)}'}), 500

@analytics_bp.route('/chart', methods=['POST'])
@api_login_required
def generate_chart():
    """生成图表"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        query = data.get('query')
        chart_type = data.get('chart_type', 'line')
        x = data.get('x')
        y = data.get('y')
        title = data.get('title')
        color = data.get('color')
        additional_params = data.get('params', {})
        
        if not query:
            return jsonify({'error': '查询语句为空'}), 400
            
        # 生成图表
        chart_json = generate_plotly_chart_for_sql(
            query=query,
            chart_type=chart_type,
            x=x,
            y=y,
            title=title,
            color=color,
            **additional_params
        )
        
        if not chart_json:
            return jsonify({'error': '生成图表失败'}), 500
            
        return jsonify({
            'success': True,
            'chart_data': json.loads(chart_json)
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'生成图表出错: {str(e)}'}), 500

@analytics_bp.route('/pivot-table', methods=['POST'])
@api_login_required
def create_pivot_table():
    """创建数据透视表"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        query = data.get('query')
        index = data.get('index')
        columns = data.get('columns')
        values = data.get('values')
        aggfunc = data.get('aggfunc', 'mean')
        
        if not query or not index or not values:
            return jsonify({'error': '参数不完整'}), 400
            
        # 执行查询
        df = Database.query_to_dataframe(query)
        
        if df.empty:
            return jsonify({'error': '查询结果为空'}), 400
            
        # 创建透视表
        pivot_df = DataAnalyzer.create_pivot_table(
            df=df,
            index=index,
            columns=columns,
            values=values,
            aggfunc=aggfunc
        )
        
        # 转换为JSON
        pivot_data = pivot_df.reset_index().to_dict(orient='records')
        columns = pivot_df.reset_index().columns.tolist()
        
        return jsonify({
            'success': True,
            'pivot_data': pivot_data,
            'columns': columns
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'创建数据透视表出错: {str(e)}'}), 500

@analytics_bp.route('/correlation', methods=['POST'])
@api_login_required
def generate_correlation():
    """生成相关性矩阵"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        query = data.get('query')
        method = data.get('method', 'pearson')
        
        if not query:
            return jsonify({'error': '查询语句为空'}), 400
            
        # 执行查询
        df = Database.query_to_dataframe(query)
        
        if df.empty:
            return jsonify({'error': '查询结果为空'}), 400
            
        # 计算相关性
        fig = DataAnalyzer.create_correlation_heatmap(df, method=method)
        
        if fig is None:
            return jsonify({'error': '生成相关性热图失败'}), 500
            
        return jsonify({
            'success': True,
            'correlation_data': json.loads(fig.to_json())
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'生成相关性矩阵出错: {str(e)}'}), 500

@analytics_bp.route('/dashboard', methods=['POST'])
@api_login_required
def generate_dashboard():
    """生成仪表板"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        query = data.get('query')
        title = data.get('title', '数据分析仪表板')
        
        if not query:
            return jsonify({'error': '查询语句为空'}), 400
            
        # 执行查询
        df = Database.query_to_dataframe(query)
        
        if df.empty:
            return jsonify({'error': '查询结果为空'}), 400
            
        # 生成仪表板
        fig = DataVisualizer.create_dashboard(df, title=title)
        
        if fig is None:
            return jsonify({'error': '生成仪表板失败'}), 500
            
        return jsonify({
            'success': True,
            'dashboard_data': json.loads(fig.to_json())
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'生成仪表板出错: {str(e)}'}), 500

@analytics_bp.route('/analytics')
@login_required
def analytics_index():
    return render_template('analysis/analytics-dashboard.html')

@analytics_bp.route('/outpatient')
@login_required
def outpatient_analysis():
    return render_template('analysis/outpatient-analysis.html')

@analytics_bp.route('/api/outpatient/trends', methods=['POST'])
@api_login_required
def get_outpatient_trends():
    """获取门诊量趋势分析"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        department = data.get('department')
        specialty = data.get('specialty')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # 获取门诊量数据
        df = get_outpatient_data(
            department=department,
            specialty=specialty,
            start_date=start_date,
            end_date=end_date
        )
        
        if df.empty:
            return jsonify({'error': '未找到符合条件的数据'}), 404
            
        # 分析门诊量趋势
        groupby_column = None
        if data.get('group_by'):
            groupby_column = data.get('group_by')
            
        analysis_result = DataAnalyzer.analyze_outpatient_trends(
            df=df,
            time_column='日期',
            value_column='数量',
            groupby_column=groupby_column
        )
        
        # 生成趋势图
        fig = DataVisualizer.create_outpatient_trend_chart(
            df=df,
            x='日期',
            y='数量',
            color=groupby_column,
            title="门诊量趋势分析"
        )
        
        return jsonify({
            'success': True,
            'analysis': analysis_result,
            'chart_data': json.loads(fig.to_json()) if fig else None
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'门诊量趋势分析出错: {str(e)}'}), 500

@analytics_bp.route('/api/outpatient/completion-rate', methods=['POST'])
@api_login_required
def get_completion_rate():
    """获取目标完成率分析"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        year = data.get('year')
        month = data.get('month')
        
        # 获取目标完成率数据
        df = get_completion_rate(year=year, month=month)
        
        if df.empty:
            return jsonify({'error': '未找到符合条件的数据'}), 404
            
        # 分析目标完成率
        groupby_column = None
        if data.get('group_by'):
            groupby_column = data.get('group_by')
            
        analysis_result = DataAnalyzer.analyze_completion_rate(
            df=df,
            actual_column='实际量',
            target_column='目标值',
            rate_column='完成率',
            groupby_column=groupby_column
        )
        
        # 生成完成率图表
        fig = DataVisualizer.create_completion_rate_chart(
            df=df,
            x='科室' if groupby_column != '科室' else '专科',
            y='完成率',
            target_column='目标值',
            actual_column='实际量',
            title="目标完成率分析"
        )
        
        return jsonify({
            'success': True,
            'analysis': analysis_result,
            'chart_data': json.loads(fig.to_json()) if fig else None
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'目标完成率分析出错: {str(e)}'}), 500

@analytics_bp.route('/api/outpatient/department-comparison', methods=['POST'])
@api_login_required
def get_department_comparison():
    """获取科室对比分析"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # 获取门诊量数据
        df = get_outpatient_data(
            start_date=start_date,
            end_date=end_date
        )
        
        if df.empty:
            return jsonify({'error': '未找到符合条件的数据'}), 404
            
        # 生成科室对比图表
        fig = DataVisualizer.create_department_comparison_chart(
            df=df,
            department_column='科室',
            value_column='数量',
            title="科室门诊量对比"
        )
        
        # 按科室汇总数据
        dept_summary = df.groupby('科室')['数量'].sum().reset_index()
        dept_summary = dept_summary.sort_values(by='数量', ascending=False)
        
        return jsonify({
            'success': True,
            'summary_data': dept_summary.to_dict('records'),
            'chart_data': json.loads(fig.to_json()) if fig else None
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'科室对比分析出错: {str(e)}'}), 500

@analytics_bp.route('/api/test-langchain', methods=['POST'])
@api_login_required
def test_langchain():
    """测试LangChain集成功能"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        query = data.get('query', '分析门诊量趋势')
        
        # 使用LangChain生成SQL
        from app.services.query_service import process_query_with_langchain
        
        # 获取SQL服务实例并测试查询处理
        result = process_query_with_langchain(query)
        
        # 返回结果
        return jsonify({
            'success': True,
            'result': result,
            'table_mapping': {
                '门诊量': 'outpatient',
                '目标值': 'target',
                'drg_records': 'drg_records'
            },
            'message': '测试完成'
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'测试LangChain集成出错: {str(e)}', 
            'traceback': traceback.format_exc()
        }), 500

@analytics_bp.route('/test/langchain')
@login_required
def test_langchain_page():
    return render_template('test/langchain.html')

# 多维度分析相关路由 (整合自analysis_routes.py)
@analytics_bp.route('/analysis')
@login_required
def analysis():
    return render_template('analysis/index.html')

@analytics_bp.route('/analysis/department')
@login_required
def department_analysis():
    """科室分析页面"""
    return render_template('analysis/department-analysis.html')

@analytics_bp.route('/analysis/doctor')
@login_required
def doctor_performance():
    """医生绩效页面"""
    return render_template('analysis/doctor-performance.html')

@analytics_bp.route('/analysis/patient')
@login_required
def patient_analysis():
    """患者分析页面"""
    return render_template('analysis/patient-analysis.html')

@analytics_bp.route('/analysis/financial')
@login_required
def financial_analysis():
    """财务分析页面"""
    return render_template('analysis/financial-analysis.html')

@analytics_bp.route('/analysis/drg')
@login_required
def drg_analysis():
    """DRG分析页面"""
    return render_template('analysis/drg-analysis.html')

# 科室分析API路由
@analytics_bp.route('/api/department/workload', methods=['POST'])
@api_login_required
def get_department_workload():
    """获取科室工作量数据"""
    try:
        data = request.get_json() or {}
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        departments = data.get('departments', [])  # 可选择特定科室
        
        # 构建查询
        query = """
        SELECT date, department, outpatient_count, inpatient_count, 
               surgery_count, emergency_count, consultation_count, total_count
        FROM department_workload
        WHERE date BETWEEN ? AND ?
        """
        
        params = [start_date, end_date]
        
        # 如果指定了科室，添加科室过滤条件
        if departments:
            placeholders = ','.join(['?'] * len(departments))
            query += f" AND department IN ({placeholders})"
            params.extend(departments)
            
        query += " ORDER BY date, department"
        
        # 执行查询
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
        # 格式化数据
        result = []
        for row in rows:
            result.append({
                'date': row[0],
                'department': row[1],
                'outpatient_count': row[2],
                'inpatient_count': row[3],
                'surgery_count': row[4],
                'emergency_count': row[5],
                'consultation_count': row[6],
                'total_count': row[7]
            })
            
        return jsonify({'success': True, 'data': result})
    
    except Exception as e:
        current_app.logger.error(f"获取科室工作量数据时出错: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取科室工作量数据时出错: {str(e)}'}), 500

@analytics_bp.route('/api/department/efficiency', methods=['POST'])
@api_login_required
def get_department_efficiency():
    """获取科室效率数据"""
    try:
        data = request.get_json() or {}
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        departments = data.get('departments', [])  # 可选择特定科室
        
        # 构建查询
        query = """
        SELECT date, department, avg_treatment_time, avg_waiting_time, 
               bed_turnover_rate, bed_occupancy_rate, avg_los, readmission_rate
        FROM department_efficiency
        WHERE date BETWEEN ? AND ?
        """
        
        params = [start_date, end_date]
        
        # 如果指定了科室，添加科室过滤条件
        if departments:
            placeholders = ','.join(['?'] * len(departments))
            query += f" AND department IN ({placeholders})"
            params.extend(departments)
            
        query += " ORDER BY date, department"
        
        # 执行查询
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
        # 格式化数据
        result = []
        for row in rows:
            result.append({
                'date': row[0],
                'department': row[1],
                'avg_treatment_time': row[2],
                'avg_waiting_time': row[3],
                'bed_turnover_rate': row[4],
                'bed_occupancy_rate': row[5],
                'avg_los': row[6],
                'readmission_rate': row[7]
            })
            
        return jsonify({'success': True, 'data': result})
    
    except Exception as e:
        current_app.logger.error(f"获取科室效率数据时出错: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取科室效率数据时出错: {str(e)}'}), 500

@analytics_bp.route('/api/department/resources', methods=['POST'])
@api_login_required
def get_department_resources():
    """获取科室资源数据"""
    try:
        data = request.get_json() or {}
        date = data.get('date')  # 特定日期（如 '2025Q1'）
        departments = data.get('departments', [])  # 可选择特定科室
        
        # 构建查询
        query = """
        SELECT date, department, doctor_count, nurse_count, 
               bed_count, equipment_count, room_count, space_square_meters
        FROM department_resources
        """
        
        params = []
        conditions = []
        
        # 添加日期过滤
        if date:
            conditions.append("date = ?")
            params.append(date)
        
        # 添加科室过滤
        if departments:
            placeholders = ','.join(['?'] * len(departments))
            conditions.append(f"department IN ({placeholders})")
            params.extend(departments)
        
        # 组合条件
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " ORDER BY date, department"
        
        # 执行查询
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
        # 格式化数据
        result = []
        for row in rows:
            result.append({
                'date': row[0],
                'department': row[1],
                'doctor_count': row[2],
                'nurse_count': row[3],
                'bed_count': row[4],
                'equipment_count': row[5],
                'room_count': row[6],
                'space_square_meters': row[7]
            })
            
        return jsonify({'success': True, 'data': result})
    
    except Exception as e:
        current_app.logger.error(f"获取科室资源数据时出错: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取科室资源数据时出错: {str(e)}'}), 500

@analytics_bp.route('/api/department/revenue', methods=['POST'])
@api_login_required
def get_department_revenue():
    """获取科室收入数据"""
    try:
        data = request.get_json() or {}
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        departments = data.get('departments', [])  # 可选择特定科室
        
        # 构建查询
        query = """
        SELECT date, department, outpatient_income, inpatient_income, 
               drug_income, material_income, examination_income, 
               surgery_income, other_income, total_income
        FROM department_revenue
        WHERE date BETWEEN ? AND ?
        """
        
        params = [start_date, end_date]
        
        # 如果指定了科室，添加科室过滤条件
        if departments:
            placeholders = ','.join(['?'] * len(departments))
            query += f" AND department IN ({placeholders})"
            params.extend(departments)
            
        query += " ORDER BY date, department"
        
        # 执行查询
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
        # 格式化数据
        result = []
        for row in rows:
            result.append({
                'date': row[0],
                'department': row[1],
                'outpatient_income': row[2],
                'inpatient_income': row[3],
                'drug_income': row[4],
                'material_income': row[5],
                'examination_income': row[6],
                'surgery_income': row[7],
                'other_income': row[8],
                'total_income': row[9]
            })
            
        return jsonify({'success': True, 'data': result})
    
    except Exception as e:
        current_app.logger.error(f"获取科室收入数据时出错: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取科室收入数据时出错: {str(e)}'}), 500

@analytics_bp.route('/api/department/list', methods=['GET'])
@api_login_required
def get_department_list():
    """获取科室列表"""
    try:
        # 构建查询
        query = """
        SELECT DISTINCT department
        FROM department_workload
        ORDER BY department
        """
        
        # 执行查询
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            
        # 格式化数据
        departments = [row[0] for row in rows]
            
        return jsonify({'success': True, 'data': departments})
    
    except Exception as e:
        current_app.logger.error(f"获取科室列表时出错: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取科室列表时出错: {str(e)}'}), 500

# 财务分析API路由
@analytics_bp.route('/api/finance/summary', methods=['POST'])
@api_login_required
def get_finance_summary():
    """获取财务汇总数据"""
    try:
        data = request.get_json() or {}
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # 构建查询
        query = """
        SELECT date, type, amount
        FROM finance_summary
        WHERE date BETWEEN ? AND ?
        ORDER BY date
        """
        
        params = [start_date, end_date]
        
        # 执行查询
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # 检查表是否存在，如果不存在则创建示例数据
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='finance_summary'
            """)
            
            if not cursor.fetchone():
                # 创建表并插入示例数据
                current_app.logger.info("创建finance_summary表并插入示例数据")
                cursor.execute("""
                    CREATE TABLE finance_summary (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        type TEXT NOT NULL,
                        amount REAL NOT NULL
                    )
                """)
                
                # 生成示例数据 - 最近12个月的收入和支出
                import random
                from datetime import datetime, timedelta
                
                end = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.now()
                for i in range(12):
                    month_date = end - timedelta(days=30*i)
                    date_str = month_date.strftime('%Y-%m-%d')
                    
                    # 收入 - 基础值300万，波动±20%
                    income_base = 3000000
                    income = income_base * (0.8 + 0.4 * random.random())
                    
                    # 支出 - 收入的60-80%
                    expense = income * (0.6 + 0.2 * random.random())
                    
                    cursor.execute(
                        "INSERT INTO finance_summary (date, type, amount) VALUES (?, ?, ?)",
                        (date_str, "income", income)
                    )
                    cursor.execute(
                        "INSERT INTO finance_summary (date, type, amount) VALUES (?, ?, ?)",
                        (date_str, "expense", expense)
                    )
                
                conn.commit()
            
            # 查询数据
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
        # 格式化数据
        result = []
        for row in rows:
            result.append({
                'date': row[0],
                'type': row[1],
                'amount': row[2]
            })
            
        return jsonify({'success': True, 'data': result})
    
    except Exception as e:
        current_app.logger.error(f"获取财务汇总数据时出错: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取财务汇总数据时出错: {str(e)}'}), 500
        
@analytics_bp.route('/api/finance/composition', methods=['POST'])
@api_login_required
def get_finance_composition():
    """获取收入构成数据"""
    try:
        data = request.get_json() or {}
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # 构建查询获取所有科室的收入并按类型分组
        query = """
        SELECT 
            SUM(outpatient_income) as outpatient,
            SUM(inpatient_income) as inpatient,
            SUM(drug_income) as drug,
            SUM(examination_income) as examination,
            SUM(surgery_income) as surgery,
            SUM(other_income) as other
        FROM department_revenue
        WHERE date BETWEEN ? AND ?
        """
        
        params = [start_date, end_date]
        
        # 执行查询
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            
        # 检查是否有数据返回
        if not row or all(x is None for x in row):
            # 如果没有数据，生成模拟数据
            result = {
                'outpatient': 1200000,
                'inpatient': 1800000,
                'drug': 850000,
                'examination': 650000,
                'surgery': 750000,
                'other': 350000
            }
        else:
            # 格式化数据
            result = {
                'outpatient': row[0] or 0,
                'inpatient': row[1] or 0,
                'drug': row[2] or 0,
                'examination': row[3] or 0,
                'surgery': row[4] or 0,
                'other': row[5] or 0
            }
            
        return jsonify({'success': True, 'data': result})
    
    except Exception as e:
        current_app.logger.error(f"获取收入构成数据时出错: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取收入构成数据时出错: {str(e)}'}), 500 