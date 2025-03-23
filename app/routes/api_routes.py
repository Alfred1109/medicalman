from app.services.llm_service import LLMServiceFactory

@bp.route('/analyze', methods=['POST'])
def analyze():
    # ... existing code ...
    
    # 使用工厂方法获取SQL服务
    sql_service = LLMServiceFactory.get_sql_service()
    
    # 生成SQL查询
    sql_result = sql_service.generate_sql(user_query)
    
    # ... existing code ...
    
    # 使用文本分析服务生成最终响应
    text_service = LLMServiceFactory.get_text_analysis_service()
    final_response = text_service.generate_modular_response(
        user_query=user_query,
        sql_query=sql_query,
        sql_results=json.dumps(formatted_results, ensure_ascii=False, indent=2),
        chart_configs=json.dumps(chart_result, ensure_ascii=False, indent=2) if chart_result else None
    )
    
    # ... existing code ...

@bp.route('/generate_chart', methods=['POST'])
def generate_chart():
    # ... existing code ...
    
    # 使用图表服务生成图表配置
    chart_service = LLMServiceFactory.get_chart_service()
    result = chart_service.generate_chart_config(user_query, json.dumps(data, ensure_ascii=False))
    
    # ... existing code ... 