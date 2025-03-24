"""
AI聊天路由模块 - 处理AI智能助手相关功能
"""
from flask import Blueprint, render_template, request, jsonify, current_app, session
import json
import traceback
import time

from app.services.query_service import process_user_query
from app.services.chart_service import ChartService
from app.utils.logger import log_user_query
from app.utils.json_helper import safe_json_dumps
from app.routes.auth_routes import login_required, api_login_required

# 创建蓝图
ai_chat_bp = Blueprint('ai_chat', __name__, url_prefix='/chat')

@ai_chat_bp.route('/')
@login_required
def index():
    """AI聊天首页"""
    return render_template('ai_chat/index.html')

@ai_chat_bp.route('/query', methods=['POST'])
@api_login_required
def process_query():
    """处理用户查询"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        query = data.get('query') or data.get('message')  # 兼容前端可能发送的message参数
        knowledge_settings = data.get('knowledge_settings', {}) or {'data_source': data.get('data_source', 'auto')}  # 兼容旧的data_source参数
        
        if not query:
            return jsonify({'error': '查询内容为空'}), 400
        
        # 记录用户查询
        username = session.get('username', 'guest')
        log_user_query(username, query)
        
        # 处理查询
        start_time = time.time()
        result = process_user_query(query, knowledge_settings)
        process_time = time.time() - start_time
        
        # 记录处理时间
        current_app.logger.info(f"查询处理完成，耗时: {process_time:.2f}秒")
        
        # 使用安全的JSON序列化
        if result.get('success'):
            # 直接返回安全处理后的JSON响应字符串
            return safe_json_dumps(result), 200, {'Content-Type': 'application/json'}
        else:
            # 错误响应也需要安全处理
            error_response = {
                'success': False,
                'message': result.get('message', '处理查询时出错')
            }
            return safe_json_dumps(error_response), 500, {'Content-Type': 'application/json'}
    except Exception as e:
        traceback.print_exc()
        error_response = {
            'success': False,
            'message': f'处理查询失败: {str(e)}'
        }
        return safe_json_dumps(error_response), 500, {'Content-Type': 'application/json'}

@ai_chat_bp.route('/render-chart', methods=['POST'])
@api_login_required
def render_chart():
    """渲染图表"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        chart_config = data.get('chart_config')
        
        if not chart_config:
            return jsonify({'error': '图表配置为空'}), 400
            
        chart_service = ChartService()
        
        # 验证图表配置
        chart_config = chart_service._validate_chart_config(chart_config)
        
        return jsonify({
            'success': True,
            'chart_config': chart_config
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'渲染图表失败: {str(e)}'
        }), 500

@ai_chat_bp.route('/debug-charts', methods=['GET'])
@login_required
def debug_charts():
    """调试图表渲染功能"""
    # 创建测试图表数据
    test_charts = [
        {
            "title": "测试柱状图",
            "type": "bar",
            "xAxis": {
                "type": "category",
                "data": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            },
            "yAxis": {
                "type": "value"
            },
            "series": [{
                "data": [120, 132, 101, 134, 90, 230, 210],
                "type": "bar"
            }]
        },
        {
            "title": "测试折线图",
            "type": "line",
            "xAxis": {
                "type": "category",
                "data": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            },
            "yAxis": {
                "type": "value"
            },
            "series": [{
                "data": [150, 230, 224, 218, 135, 147, 260],
                "type": "line"
            }]
        }
    ]
    
    # 尝试使用ChartService生成图表
    try:
        chart_service = ChartService()
        test_data = [
            {"日期": "周一", "门诊量": 120, "住院量": 56},
            {"日期": "周二", "门诊量": 132, "住院量": 61},
            {"日期": "周三", "门诊量": 101, "住院量": 42},
            {"日期": "周四", "门诊量": 134, "住院量": 67},
            {"日期": "周五", "门诊量": 90, "住院量": 43},
            {"日期": "周六", "门诊量": 230, "住院量": 78},
            {"日期": "周日", "门诊量": 210, "住院量": 65}
        ]
        
        # 记录详细日志
        current_app.logger.info("开始测试ChartService图表生成功能")
        
        # 将测试数据转换为JSON字符串
        structured_data = json.dumps(test_data, ensure_ascii=False)
        current_app.logger.info(f"测试数据: {structured_data[:200]}...")
        
        # 测试查询
        test_query = "分析一周内的门诊量和住院量变化趋势"
        
        # 调用服务生成图表配置
        chart_config = chart_service.generate_chart_config(test_query, structured_data)
        current_app.logger.info(f"生成的图表配置: {json.dumps(chart_config, ensure_ascii=False)}")
        
        # 如果生成了有效的图表配置，添加到展示列表
        if chart_config and 'charts' in chart_config and chart_config['charts']:
            test_charts.extend(chart_config['charts'])
            current_app.logger.info(f"成功添加 {len(chart_config['charts'])} 个自动生成的图表")
    except Exception as e:
        current_app.logger.error(f"测试ChartService时出错: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
    
    # 渲染调试页面
    return render_template('ai_chat/debug_charts.html', charts=test_charts) 