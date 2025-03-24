"""
数据分析路由模块
提供数据分析和可视化API
"""
from flask import Blueprint, request, jsonify, render_template, current_app
import json
import pandas as pd
import traceback

from app.utils.data_analysis import DataAnalyzer, DataVisualizer, generate_plotly_chart_for_sql
from app.models.database import Database
from app.routes.auth_routes import login_required, api_login_required

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

@analytics_bp.route('/outpatient')
@login_required
def outpatient_analysis():
    """门诊量分析页面"""
    return render_template('analytics/outpatient.html')

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
        
        # 引入db工具函数
        from app.utils.db import get_outpatient_data
        
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
        
        # 引入db工具函数
        from app.utils.db import get_completion_rate
        
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
        
        # 引入db工具函数
        from app.utils.db import get_outpatient_data
        
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
    """测试LangChain集成功能的页面"""
    return render_template('test/langchain.html')

# 多维度分析相关路由 (整合自analysis_routes.py)
@analytics_bp.route('/analysis')
@login_required
def analysis_home():
    """分析总览页面"""
    return render_template('analysis/analysis.html')

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