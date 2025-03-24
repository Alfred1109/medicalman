"""
API路由模块 - 处理API请求
"""
from flask import Blueprint, request, jsonify
import json
from app.services.llm_service import LLMServiceFactory
from app.routes.auth_routes import api_login_required

# 创建蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/analyze', methods=['POST'])
@api_login_required
def analyze():
    """分析用户查询"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        user_query = data.get('query')
        
        if not user_query:
            return jsonify({'error': '查询内容为空'}), 400
        
        # 使用工厂方法获取SQL服务
        sql_service = LLMServiceFactory.get_sql_service()
        
        # 生成SQL查询
        sql_result = sql_service.generate_sql(user_query)
        
        if not sql_result:
            return jsonify({'error': '生成SQL查询失败'}), 500
        
        sql_query = sql_result.get('sql')
        explanation = sql_result.get('explanation')
        
        # 执行SQL查询
        from app.models.database import Database
        results = Database.execute_query(sql_query)
        
        if results is None:
            return jsonify({'error': '执行SQL查询失败'}), 500
            
        # 格式化结果
        formatted_results = []
        for row in results:
            formatted_results.append(dict(row))
        
        # 生成图表配置
        chart_service = LLMServiceFactory.get_chart_service()
        chart_result = chart_service.generate_chart_config(user_query, json.dumps(formatted_results, ensure_ascii=False))
        
        # 使用文本分析服务生成最终响应
        text_service = LLMServiceFactory.get_text_analysis_service()
        final_response = text_service.generate_modular_response(
            user_query=user_query,
            sql_query=sql_query,
            sql_results=json.dumps(formatted_results, ensure_ascii=False, indent=2),
            chart_configs=json.dumps(chart_result, ensure_ascii=False, indent=2) if chart_result else None
        )
        
        # 返回结果
        return jsonify({
            'success': True,
            'query': user_query,
            'sql': sql_query,
            'explanation': explanation,
            'results': formatted_results,
            'chart_config': chart_result,
            'response': final_response
        })
    except Exception as e:
        return jsonify({'error': f'分析请求出错: {str(e)}'}), 500

@api_bp.route('/generate_chart', methods=['POST'])
@api_login_required
def generate_chart():
    """根据用户查询和数据生成图表配置"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        user_query = data.get('query')
        data = data.get('data')
        
        if not user_query or not data:
            return jsonify({'error': '查询内容或数据为空'}), 400
        
        # 使用图表服务生成图表配置
        chart_service = LLMServiceFactory.get_chart_service()
        result = chart_service.generate_chart_config(user_query, json.dumps(data, ensure_ascii=False))
        
        return jsonify({
            'success': True,
            'chart_config': result
        })
    except Exception as e:
        return jsonify({'error': f'生成图表配置出错: {str(e)}'}), 500

@api_bp.route('/departments', methods=['GET'])
@api_login_required
def get_departments():
    """获取所有科室"""
    try:
        # 引入db工具函数
        from app.utils.db import connect_db
        
        conn = connect_db()
        cursor = conn.cursor()
        
        # 查询门诊量表中的所有科室
        cursor.execute("SELECT DISTINCT 科室 FROM 门诊量 ORDER BY 科室")
        departments = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify(departments)
    except Exception as e:
        return jsonify({'error': f'获取科室列表失败: {str(e)}'}), 500

@api_bp.route('/specialties', methods=['GET'])
@api_login_required
def get_specialties():
    """获取所有专科"""
    try:
        # 引入db工具函数
        from app.utils.db import connect_db
        
        conn = connect_db()
        cursor = conn.cursor()
        
        # 查询门诊量表中的所有专科
        cursor.execute("SELECT DISTINCT 专科 FROM 门诊量 ORDER BY 专科")
        specialties = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify(specialties)
    except Exception as e:
        return jsonify({'error': f'获取专科列表失败: {str(e)}'}), 500

@api_bp.route('/specialties-by-department', methods=['GET'])
@api_login_required
def get_specialties_by_department():
    """获取指定科室下的专科"""
    try:
        department = request.args.get('department')
        
        if not department:
            return jsonify({'error': '科室参数为空'}), 400
            
        # 引入db工具函数
        from app.utils.db import connect_db
        
        conn = connect_db()
        cursor = conn.cursor()
        
        # 查询指定科室下的所有专科
        cursor.execute("SELECT DISTINCT 专科 FROM 门诊量 WHERE 科室=? ORDER BY 专科", (department,))
        specialties = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify(specialties)
    except Exception as e:
        return jsonify({'error': f'获取科室专科列表失败: {str(e)}'}), 500 