"""
查询服务模块 - 处理用户查询并返回结果
"""
import re
import json
import traceback
import os
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from app.utils.database import execute_query, execute_query_to_dataframe
from app.services.llm_service import LLMServiceFactory
from app.utils.utils import safe_json_dumps
from app.services.prompts import (
    DATA_ANALYSIS_SYSTEM_PROMPT,
    RESPONSE_SYSTEM_PROMPT,
    RESPONSE_USER_PROMPT
)

# 统一的响应格式
def create_response(success: bool, message: str, data: Any = None, error: str = None) -> Dict[str, Any]:
    """
    创建标准格式的响应
    
    参数:
        success: 操作是否成功
        message: 消息内容
        data: 响应数据
        error: 错误消息
        
    返回:
        格式化的响应字典
    """
    response = {
        "success": success,
        "message": message,
        "process_time": f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    }
    
    if data is not None:
        response["data"] = data
        
    if error is not None:
        response["error"] = error
        
    return response

def execute_sql_query(sql: str) -> pd.DataFrame:
    """
    执行SQL查询并返回DataFrame结果
    
    参数:
        sql: SQL查询语句
        
    返回:
        查询结果DataFrame
    """
    try:
        # 使用新的数据库工具函数
        return execute_query_to_dataframe(sql)
    except Exception as e:
        print(f"执行SQL查询时出错: {str(e)}")
        traceback.print_exc()
        raise e  # 向上抛出异常以便更好地处理

def process_user_query(user_message: str, knowledge_settings: Dict = None) -> Dict[str, Any]:
    """
    处理用户查询并返回结果
    
    参数:
        user_message: 用户查询消息
        knowledge_settings: 知识库查询设置
        
    返回:
        包含处理结果的字典
    """
    if not knowledge_settings:
        knowledge_settings = {}
    
    # 数据源选择，默认为'general'
    data_source = knowledge_settings.get('data_source', 'general')
    
    start_time = datetime.now()
    
    try:
        # 根据数据源选择查询处理方式
        print(f"处理用户查询，使用数据源: {data_source}")
        
        if data_source == 'database':
            # 数据库查询处理
            result = process_database_query(user_message)
        elif data_source == 'knowledge_base':
            # 知识库查询处理
            result = process_knowledge_query(user_message, knowledge_settings)
        elif data_source == 'file':
            # 文件分析查询处理
            result = process_file_query(user_message, knowledge_settings)
        else:
            # 通用查询处理
            result = process_general_query(user_message)
        
        # 处理完成时间
        end_time = datetime.now()
        process_time = (end_time - start_time).total_seconds()
        
        # 添加处理时间到结果
        if isinstance(result, dict):
            result['process_time'] = f"{process_time:.2f}秒"
            
            # 确保响应中包含表格数据（如果有）
            if 'structured_result' in result and isinstance(result['structured_result'], dict):
                if 'tables' in result['structured_result']:
                    # 确保表格数据传递到前端
                    result['tables'] = result['structured_result']['tables']
        
        return result
    except Exception as e:
        print(f"处理查询时出错: {str(e)}")
        traceback.print_exc()
        
        return create_response(
            success=False, 
            message=f"处理查询时出错: {str(e)}",
            error=str(e)
        )

def process_database_query(user_message: str) -> Dict[str, Any]:
    """
    处理数据库查询
    
    参数:
        user_message: 用户查询消息
        
    返回:
        包含处理结果的字典
    """
    try:
        print(f"开始处理数据库查询: {user_message}")
        
        # 使用LLM生成SQL
        sql_service = LLMServiceFactory.get_sql_service()
        sql_result = sql_service.generate_sql(user_message)
        
        if not sql_result or 'sql' not in sql_result:
            print("无法生成有效的SQL查询")
            return create_response(
                success=False,
                message="无法生成有效的SQL查询，请尝试重新表述您的问题。"
            )
        
        sql = sql_result['sql']
        explanation = sql_result.get('explanation', '未提供解释')
        
        print(f"生成的SQL查询: {sql}")
        print(f"查询解释: {explanation}")
        
        # 执行SQL查询
        try:
            print("开始执行SQL查询...")
            df = execute_sql_query(sql)
            
            if df.empty:
                print("查询执行成功，但未找到符合条件的数据")
                return create_response(
                    success=True,
                    message="查询执行成功，但未找到符合条件的数据。",
                    data={
                        "sql": sql,
                        "explanation": explanation
                    }
                )
                
            print(f"查询成功，返回了 {len(df)} 行数据")
            
            # 将DataFrame转换为字典列表
            data_list = df.to_dict(orient='records')
            
            # 使用ChartService生成图表
            print("使用ChartService生成动态图表...")
            chart_service = LLMServiceFactory.get_chart_service()
            chart_result = chart_service.generate_chart_config(
                user_message, 
                json.dumps(data_list, ensure_ascii=False)
            )
            
            charts = chart_result.get('charts', []) if chart_result else []
            if charts:
                print(f"成功生成 {len(charts)} 个图表")
            else:
                print("未能生成有效的图表配置")
                charts = []
            
            # 检查数据表格结构
            columns = df.columns.tolist()
            print(f"数据表列: {columns}")
            print(f"数据示例: {df.head(2).to_dict(orient='records')}")
            
            # 构建结构化结果
            structured_result = {
                "data": data_list,
                "charts": charts,
                "tables": [
                    {
                        "type": "detail",
                        "title": "查询结果数据",
                        "headers": df.columns.tolist(),
                        "rows": df.values.tolist(),
                        "description": "SQL查询的详细结果数据"
                    }
                ]
            }
            
            # 使用LLM服务对查询结果进行丰富的解释和分析
            try:
                print("开始使用LLM进行结果分析...")
                base_service = LLMServiceFactory.get_base_service()
                
                # 将DataFrame转换为描述性文本
                df_summary = f"查询数据包含{len(df)}行，{len(df.columns)}列。\n"
                df_summary += f"列名: {', '.join(df.columns.tolist())}\n"
                df_summary += f"数据样例（前5行）:\n{df.head(5).to_string(index=False)}\n"
                
                # 添加一些基本统计信息
                try:
                    df_summary += "\n基本统计:\n"
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    if numeric_cols:
                        df_summary += f"数值列统计:\n{df[numeric_cols].describe().to_string()}\n"
                except Exception as stats_err:
                    print(f"生成统计信息时出错: {str(stats_err)}")
                
                # 准备用户分析请求
                analysis_request = f"请对以下查询和结果进行专业的分析和解读:\n\n"
                analysis_request += f"用户查询: {user_message}\n\n"
                analysis_request += f"SQL查询: {sql}\n\n"
                analysis_request += f"数据结果: {df_summary}"
                
                # 如果有图表，添加图表描述
                if charts:
                    chart_types = [chart.get('type', 'unknown') for chart in charts]
                    analysis_request += f"\n\n图表类型: {', '.join(chart_types)}"
                
                # 请求详细的分析和解读
                analysis_request += "\n\n请提供详细的数据分析、关键发现、趋势解读、专业建议等，使回答更加完整和有深度。包括对数据的医学意义的解释，以及可能的下一步行动建议。"
                
                # 调用LLM进行分析
                print("请求LLM对查询结果进行专业分析...")
                llm_analysis = base_service.call_api(DATA_ANALYSIS_SYSTEM_PROMPT, analysis_request)
                
                analysis_message = llm_analysis if llm_analysis else "查询执行成功，但未能生成详细分析。"
                    
            except Exception as analysis_err:
                print(f"生成分析时出错: {str(analysis_err)}")
                traceback.print_exc()
                analysis_message = "查询执行成功。" 
                
            # 构建返回结果
            return create_response(
                success=True,
                message=analysis_message,
                data={
                    "sql": sql,
                    "explanation": explanation,
                    "structured_result": structured_result,
                    "charts": charts
                }
            )
                
        except Exception as exec_err:
            print(f"执行SQL查询时出错: {str(exec_err)}")
            traceback.print_exc()
            
            # 检查错误类型，提供更具体的错误消息
            error_message = f"执行SQL查询时出错: {str(exec_err)}"
            
            # 检查常见的SQL错误
            if "no such table" in str(exec_err).lower():
                table_match = re.search(r"no such table: (\w+)", str(exec_err).lower())
                if table_match:
                    table_name = table_match.group(1)
                    error_message = f"数据库中不存在表 '{table_name}'。请确认表名是否正确，或查询其他可用表。"
            elif "no such column" in str(exec_err).lower():
                column_match = re.search(r"no such column: (\w+)", str(exec_err).lower())
                if column_match:
                    column_name = column_match.group(1)
                    error_message = f"数据库中不存在列 '{column_name}'。请确认列名是否正确，或查询其他可用列。"
            elif "syntax error" in str(exec_err).lower():
                error_message = "SQL语法错误。请尝试简化您的查询或使用其他方式表述。"
            
            return create_response(
                success=False,
                message=error_message,
                data={"sql": sql, "explanation": explanation},
                error=str(exec_err)
            )
    
    except Exception as e:
        print(f"处理数据库查询时出错: {str(e)}")
        traceback.print_exc()
        return create_response(
            success=False,
            message=f"处理数据库查询时出错: {str(e)}",
            error=str(e)
        )

def process_knowledge_query(user_message: str, knowledge_settings: Dict = None) -> Dict[str, Any]:
    """
    处理知识库查询
    
    参数:
        user_message: 用户查询消息
        knowledge_settings: 知识库设置
        
    返回:
        包含处理结果的字典
    """
    try:
        print(f"开始处理知识库查询: {user_message}")
        
        # 获取知识库服务
        kb_service = LLMServiceFactory.get_knowledge_service()
        
        # 使用知识库服务处理查询
        response = kb_service.query(user_message, knowledge_settings)
        
        if not response:
            return create_response(
                success=False,
                message="无法从知识库获取有效回复，请尝试重新表述您的问题。"
            )
        
        # 处理结果
        return create_response(
            success=True,
            message=response,
            data={"source": "knowledge_base"}
        )
    
    except Exception as e:
        print(f"处理知识库查询时出错: {str(e)}")
        traceback.print_exc()
        return create_response(
            success=False,
            message=f"处理知识库查询时出错: {str(e)}",
            error=str(e)
        )

def get_latest_excel_file() -> Optional[Tuple[str, pd.DataFrame]]:
    """
    获取最新上传的Excel文件并读取为DataFrame
    
    返回:
        元组 (文件名, DataFrame) 或 None (如果没有找到文件或读取失败)
    """
    try:
        from app.utils.files import get_latest_file
        
        # 设置上传文件的目录
        upload_dir = 'static/uploads/documents'
        
        # 获取最新的文件
        latest_file = get_latest_file(upload_dir)
        
        if not latest_file:
            print("未找到任何文件")
            return None
        
        # 检查文件是否为Excel或CSV文件
        if not latest_file.lower().endswith(('.xlsx', '.xls', '.csv')):
            print(f"文件类型不支持: {latest_file}")
            return None
        
        # 构建完整文件路径
        file_path = os.path.join(upload_dir, latest_file)
        print(f"找到最新文件: {file_path}")
        
        # 根据文件类型读取数据
        if latest_file.lower().endswith(('.xlsx', '.xls')):
            try:
                # 尝试读取Excel文件
                print(f"尝试读取Excel文件: {file_path}")
                df = pd.read_excel(file_path)
                print(f"成功读取Excel文件，包含 {len(df)} 行数据")
                return (latest_file, df)
            except Exception as e:
                print(f"读取Excel文件失败: {str(e)}")
                traceback.print_exc()
                return None
        elif latest_file.lower().endswith('.csv'):
            try:
                # 尝试读取CSV文件
                print(f"尝试读取CSV文件: {file_path}")
                df = pd.read_csv(file_path)
                print(f"成功读取CSV文件，包含 {len(df)} 行数据")
                return (latest_file, df)
            except Exception as e:
                print(f"读取CSV文件失败: {str(e)}")
                traceback.print_exc()
                return None
        else:
            print(f"文件类型不支持: {latest_file}")
            return None
    except Exception as e:
        print(f"获取最新Excel文件时出错: {str(e)}")
        traceback.print_exc()
        return None

def process_file_query(user_message: str, settings: Dict = None) -> Dict[str, Any]:
    """
    处理文件分析查询
    
    参数:
        user_message: 用户查询消息
        settings: 文件分析设置
        
    返回:
        包含处理结果的字典
    """
    try:
        print(f"开始处理文件分析查询: {user_message}")
        
        # 获取最新的Excel文件
        file_data = get_latest_excel_file()
        
        if not file_data:
            return create_response(
                success=False,
                message="未找到可分析的Excel文件，请先上传文件。"
            )
        
        file_name, df = file_data
        
        # 准备文件内容摘要
        if len(df) > 100:
            df_sample = df.head(100)  # 只取前100行作为样本
            file_summary = f"文件名: {file_name}\n总行数: {len(df)}\n前100行样本数据:\n{df_sample.to_string()}"
        else:
            file_summary = f"文件名: {file_name}\n总行数: {len(df)}\n全部数据:\n{df.to_string()}"
        
        # 使用LLM分析文件
        base_service = LLMServiceFactory.get_base_service()
        
        # 准备提示词
        analysis_prompt = f"""你是一个专业的医疗数据分析师。请根据以下用户查询和文件内容提供详细分析:

用户查询: {user_message}

文件内容摘要:
{file_summary}

请提供:
1. 对文件内容的总体概括
2. 针对用户查询的具体分析
3. 关键发现和洞察
4. 如有可能，提供数据趋势和模式
5. 专业的医学建议或下一步行动建议
"""
        
        # 调用LLM API
        analysis_result = base_service.call_api(
            "你是一个专业的医疗数据分析师，擅长分析Excel文件数据并提供医学见解。",
            analysis_prompt
        )
        
        if not analysis_result:
            return create_response(
                success=False,
                message="无法分析文件内容，请稍后重试。"
            )
        
        # 尝试提取表格数据用于前端显示
        try:
            # 转换为HTML表格
            html_table = df.head(50).to_html(index=False)
            
            # 提取列名和行数据
            headers = df.columns.tolist()
            rows = df.head(50).values.tolist()
            
            # 构建表格结构
            table_data = {
                "type": "detail",
                "title": f"文件数据: {file_name}",
                "headers": headers,
                "rows": rows,
                "description": f"显示文件中的前50行数据(共{len(df)}行)"
            }
            
            # 尝试自动生成图表
            chart_service = LLMServiceFactory.get_chart_service()
            chart_data = chart_service.generate_chart_config(
                user_message, 
                json.dumps(df.head(200).to_dict(orient='records'), ensure_ascii=False)
            )
            
            charts = chart_data.get('charts', []) if chart_data else []
            
            return create_response(
                success=True,
                message=analysis_result,
                data={
                    "file_name": file_name,
                    "tables": [table_data],
                    "charts": charts,
                    "row_count": len(df)
                }
            )
            
        except Exception as table_err:
            print(f"生成表格数据时出错: {str(table_err)}")
            traceback.print_exc()
            
            # 即使表格生成失败，仍返回分析结果
            return create_response(
                success=True,
                message=analysis_result,
                data={"file_name": file_name}
            )
        
    except Exception as e:
        print(f"处理文件查询时出错: {str(e)}")
        traceback.print_exc()
        return create_response(
            success=False,
            message=f"处理文件查询时出错: {str(e)}",
            error=str(e)
        )

def process_general_query(user_message: str) -> Dict[str, Any]:
    """
    处理通用查询
    
    参数:
        user_message: 用户查询消息
        
    返回:
        包含处理结果的字典
    """
    try:
        print(f"开始处理通用查询: {user_message}")
        
        # 使用基本服务获取回复
        service = LLMServiceFactory.get_base_service()
        
        # 构建提示
        system_prompt = RESPONSE_SYSTEM_PROMPT
        user_prompt = RESPONSE_USER_PROMPT.format(
            analysis_type="通用",
            analysis_results="",
            user_query=user_message
        )
        
        # 调用LLM获取回复
        response = service.call_api(system_prompt, user_prompt)
        
        if not response:
            return create_response(
                success=False,
                message="无法获取有效回复，请尝试重新表述您的问题。"
            )
        
        # 处理结果
        return create_response(
            success=True,
            message=response,
            data={"source": "general_query"}
        )
    
    except Exception as e:
        print(f"处理通用查询时出错: {str(e)}")
        traceback.print_exc()
        return create_response(
            success=False,
            message=f"处理通用查询时出错: {str(e)}",
            error=str(e)
        ) 