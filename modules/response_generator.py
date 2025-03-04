import json
from typing import Dict, List, Any
import pandas as pd
from .llm_interface import call_llm_api
from .prompts.response_generator_prompt import RESPONSE_SYSTEM_PROMPT as SYSTEM_PROMPT, RESPONSE_USER_PROMPT

def format_query_results(query_results: Dict[str, Any]) -> str:
    """
    将查询结果格式化为文本
    
    参数:
        query_results: 查询结果字典
        
    返回:
        str: 格式化的文本
    """
    formatted_text = ""
    
    for name, df in query_results.items():
        if df is not None:
            # 处理DataFrame类型
            if isinstance(df, pd.DataFrame) and not df.empty:
                formatted_text += f"\n查询 {name}:\n{df.to_string()}\n\n"
            # 处理列表类型
            elif isinstance(df, list) and len(df) > 0:
                formatted_text += f"\n查询 {name}:\n"
                for item in df:
                    formatted_text += f"{str(item)}\n"
                formatted_text += "\n"
            # 处理其他类型
            else:
                formatted_text += f"\n查询 {name}: {str(df)}\n\n"
    
    return formatted_text

def generate_response(user_message: str, query_results: Dict[str, Any], 
                     charts: List[Dict[str, Any]], explanation: str) -> str:
    """
    生成最终响应
    
    参数:
        user_message: 用户消息
        query_results: 查询结果
        charts: 生成的图表
        explanation: 查询逻辑解释
        
    返回:
        str: 最终响应
    """
    try:
        # 打印调试信息
        print(f"\n=== 生成响应 ===")
        print(f"收到图表数量: {len(charts)}")
        for i, chart in enumerate(charts):
            print(f"图表 {i+1}:")
            print(f"- 标题: {chart.get('title', '无标题')}")
            print(f"- 配置: {json.dumps(chart.get('config', {}), ensure_ascii=False)[:200]}...")
        
        # 准备上下文
        formatted_results = format_query_results(query_results)
        
        # 构建提示词
        prompt = RESPONSE_USER_PROMPT.format(
            analysis_result=formatted_results,
            data_source='database',
            analysis_type='sql_analysis'
        )
        
        # 调用大模型生成响应
        response = call_llm_api(SYSTEM_PROMPT, prompt)
        if not response:
            return "抱歉，我无法生成分析响应。请稍后再试。"
        
        print("\n=== 收到LLM响应 ===")
        print(response[:200], "...")
        
        # 处理响应文本，确保格式正确
        response_lines = response.strip().split('\n')
        formatted_response = []
        current_section = None
        
        # 处理每一行，确保Markdown格式正确
        for line in response_lines:
            line = line.strip()
            # 处理标题行
            if line.startswith('#'):
                if current_section != 'title':
                    formatted_response.extend(['', line, ''])
                else:
                    formatted_response.append(line)
                current_section = 'title'
            # 处理列表项
            elif line.startswith('- ') or line.startswith('* '):
                if current_section != 'list':
                    formatted_response.append('')
                formatted_response.append(line)
                current_section = 'list'
            # 处理普通段落
            elif line:
                if current_section != 'paragraph':
                    formatted_response.append('')
                formatted_response.append(line)
                current_section = 'paragraph'
            # 处理空行
            else:
                if formatted_response and formatted_response[-1]:
                    formatted_response.append(line)
                current_section = None
        
        # 合并处理后的响应
        final_response = '\n'.join(formatted_response)
        
        # 如果响应中没有一级标题，添加一个
        if not any(line.startswith('# ') for line in response_lines):
            final_response = f"# 分析结果\n\n{final_response}"
        
        # 如果响应中没有总结部分，添加一个
        if not any(line.startswith('## 总结') for line in response_lines):
            final_response += "\n\n## 总结\n\n"
            final_response += "以上是本次分析的主要发现和建议。如果您需要更详细的分析或有其他问题，请随时询问。"
        
        print("\n=== 添加图表 ===")
        # 添加图表
        if charts:
            final_response += "\n\n## 数据可视化\n\n"
            for chart in charts:
                title = chart.get('title', '')
                config = chart.get('config', {})
                print(f"处理图表: {title}")
                
                if not title.endswith("图表"):
                    title = title.replace("图表", "") + "图表"
                
                if config:
                    chart_data = f"\n\n### {title}\n\n```chart\n{json.dumps(config, ensure_ascii=False, indent=2)}\n```\n"
                    final_response += chart_data
                    print(f"已添加图表: {title}")
                else:
                    print(f"警告：图表 '{title}' 缺少配置信息")
        
        print("\n=== 最终响应长度 ===")
        print(f"响应长度: {len(final_response)} 字符")
        
        return final_response
        
    except Exception as e:
        print(f"生成响应时出错: {str(e)}")
        print(f"错误类型: {type(e)}")
        print(f"错误堆栈: {traceback.format_exc()}")
        return "抱歉，生成分析响应时发生错误。请稍后再试。" 