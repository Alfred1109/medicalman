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
from app.prompts.querying import (
    QUERY_SYSTEM_PROMPT,
    QUERY_USER_PROMPT,
    KB_QUERY_SYSTEM_PROMPT,
    KB_QUERY_USER_PROMPT,
    TEXT_QUERY_SYSTEM_PROMPT,
    TEXT_QUERY_USER_PROMPT,
    QUERY_ANALYSIS_PROMPT,
    QUERY_ERROR_PROMPT
)
from app.prompts.analyzing import (
    KB_ANALYSIS_SYSTEM_PROMPT,
    KB_ANALYSIS_USER_PROMPT,
    FILE_ANALYSIS_SYSTEM_PROMPT,
    FILE_ANALYSIS_USER_PROMPT
)
from app.prompts.responding import (
    KB_RESPONSE_SYSTEM_PROMPT,
    KB_RESPONSE_USER_PROMPT,
    COMPREHENSIVE_RESPONSE_SYSTEM_PROMPT,
    COMPREHENSIVE_RESPONSE_USER_PROMPT
)
from app.config import (
    DATA_ANALYSIS_KEYWORDS,
    UPLOAD_FOLDER,
    ALLOWED_EXTENSIONS
)

# 统一的响应格式
def create_response(success: bool, message: str, data: Any = None, error: str = None, charts: List = None, tables: List = None) -> Dict[str, Any]:
    """
    创建标准格式的响应
    
    参数:
        success: 操作是否成功
        message: 消息内容
        data: 响应数据
        error: 错误消息
        charts: 图表数据
        tables: 表格数据
        
    返回:
        格式化的响应字典
    """
    # 基本响应结构
    response = {
        "success": success,
        "message": message,
        "answer": message,  # 前端使用answer字段显示回复
        "process_time": f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    }
    
    # 直接在根级别添加图表和表格数据（前端可能直接访问）
    if charts:
        response["charts"] = charts
        
    if tables:
        response["tables"] = tables
    
    # 结构化数据放在data字段中（集中管理）
    if data is not None:
        response["data"] = data
        
        # 同时在data中也包含图表和表格数据（如果有）
        if charts and "charts" not in data:
            if isinstance(data, dict):
                data["charts"] = charts
                
        if tables and "tables" not in data:
            if isinstance(data, dict):
                data["tables"] = tables
        
    # 错误信息
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

def analyze_query_intent(user_message: str) -> Dict[str, Any]:
    """
    使用LLM分析用户查询意图
    
    参数:
        user_message: 用户查询消息
        
    返回:
        包含查询意图分析的字典
    """
    try:
        print(f"开始分析查询意图: {user_message}")
        
        # 获取LLM服务
        base_service = LLMServiceFactory.get_base_service()
        
        # 构建系统提示词
        system_prompt = """你是一位医疗信息系统查询意图分析专家。你的任务是分析用户查询的意图，并将其分类为以下类型之一:

1. DATABASE_QUERY: 请求查询数据库中的数据、统计、表格结构，或与系统存储的数据相关的信息
2. KNOWLEDGE_QUERY: 请求医学知识、概念解释、疾病信息等知识库内容
3. FILE_ANALYSIS: 请求分析文件内容或处理上传的文档
4. GENERAL_QUERY: 一般问题，不需要访问数据库或特定资源

请以JSON格式返回，包含以下字段:
- intent: 查询意图类型(上述四种之一)
- confidence: 置信度(0-1)
- explanation: 简短解释
- requires_data: 是否需要访问数据(布尔值)

只返回JSON格式的结果，不要包含其他解释文本。"""
        
        # 构建用户提示词
        user_prompt = f"""请分析以下医疗系统用户查询的意图:

用户查询: "{user_message}"

请注意:
- 如果查询涉及"数据库内容"、"表格结构"、"系统数据"等，应该归类为DATABASE_QUERY
- 如果查询要求统计分析、趋势、数量等，应该归类为DATABASE_QUERY
- 任何提及系统存储数据的查询都应归类为DATABASE_QUERY"""
        
        # 调用LLM
        response = base_service.call_api(system_prompt, user_prompt)
        
        # 解析JSON响应
        try:
            import json
            result = json.loads(response)
            print(f"查询意图分析结果: {result}")
            return result
        except json.JSONDecodeError:
            print(f"LLM返回的意图分析无法解析为JSON: {response}")
            # 尝试提取JSON部分
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group(0))
                    print(f"提取的JSON结果: {result}")
                    return result
                except:
                    pass
            
            # 返回默认分析结果
            return {
                "intent": "GENERAL_QUERY",
                "confidence": 0.5,
                "explanation": "无法解析LLM响应，默认为一般查询",
                "requires_data": False
            }
    
    except Exception as e:
        print(f"分析查询意图时出错: {str(e)}")
        traceback.print_exc()
        # 返回默认的意图
        return {
            "intent": "GENERAL_QUERY",
            "confidence": 0.5,
            "explanation": f"分析查询意图时出错: {str(e)}",
            "requires_data": False
        }

def process_user_query(user_message: str, knowledge_settings: Dict = None, attachments: List = None) -> Dict[str, Any]:
    """
    处理用户查询并返回结果
    
    参数:
        user_message: 用户查询消息
        knowledge_settings: 知识库查询设置
        attachments: 用户上传的附件列表
        
    返回:
        包含处理结果的字典
    """
    if not knowledge_settings:
        knowledge_settings = {}
    
    if not attachments:
        attachments = []
    
    # 默认数据源
    data_source = knowledge_settings.get('data_source', 'auto')
    
    # 如果有附件，优先使用文件查询处理
    if attachments and len(attachments) > 0:
        print(f"检测到用户上传的附件: {attachments}，使用文件查询处理")
        data_source = 'file'
        knowledge_settings['attachments'] = attachments
    
    start_time = datetime.now()
    
    try:
        # 使用LLM分析用户查询意图
        if data_source == 'auto':
            intent_analysis = analyze_query_intent(user_message)
            print(f"LLM分析查询意图结果: {intent_analysis}")
            
            # 根据意图分析结果选择处理方式
            if intent_analysis.get("intent") == "DATABASE_QUERY":
                print(f"基于意图分析，使用数据库查询处理")
                result = process_database_query(user_message)
            elif intent_analysis.get("intent") == "KNOWLEDGE_QUERY":
                print(f"基于意图分析，使用知识库查询处理")
                result = process_knowledge_query(user_message, knowledge_settings)
            elif intent_analysis.get("intent") == "FILE_ANALYSIS":
                print(f"基于意图分析，使用文件查询处理")
                result = process_file_query(user_message, knowledge_settings)
            else:
                # 默认为通用查询
                print(f"基于意图分析，使用通用查询处理")
                result = process_general_query(user_message)
        else:
            # 使用指定的数据源处理方式
            print(f"使用指定的数据源: {data_source}")
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
        # 获取SQL服务实例
        sql_service = LLMServiceFactory.get_sql_service()
        
        # 生成并执行SQL查询
        print("生成SQL查询...")
        sql_response = sql_service.process_query(user_message)
        print(f"SQL服务响应: {sql_response}")
        
        # 检查是否成功执行
        if isinstance(sql_response, dict) and sql_response.get('success') is False:
            error_message = sql_response.get('message', '无法生成有效的SQL查询，请尝试重新表述您的问题。')
            return create_response(
                success=False,
                message=error_message,
                error=sql_response.get('error')
            )
        
        return sql_response
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
    获取最新的Excel文件及其内容
    
    返回:
        元组 (文件名, DataFrame) 或 None
    """
    try:
        # 获取上传目录中的所有文件
        files = [f for f in os.listdir(UPLOAD_FOLDER) 
                if os.path.isfile(os.path.join(UPLOAD_FOLDER, f)) 
                and f.lower().endswith(tuple(ALLOWED_EXTENSIONS))]
        
        if not files:
            print("未找到Excel文件")
            return None
            
        # 按修改时间排序，获取最新的文件
        latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(UPLOAD_FOLDER, x)))
        file_path = os.path.join(UPLOAD_FOLDER, latest_file)
        
        print(f"找到最新的Excel文件: {latest_file}")
        
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        return latest_file, df
        
    except Exception as e:
        print(f"获取最新Excel文件时出错: {str(e)}")
        traceback.print_exc()
        return None

def process_file_query(user_message: str, knowledge_settings: Dict = None) -> Dict[str, Any]:
    """
    处理文件分析查询
    
    参数:
        user_message: 用户查询消息
        knowledge_settings: 知识库查询设置，包含附件信息
        
    返回:
        包含处理结果的字典
    """
    try:
        print(f"处理文件分析查询: {user_message}")
        
        # 获取附件
        attachments = knowledge_settings.get('attachments', []) if knowledge_settings else []
        
        if not attachments or len(attachments) == 0:
            return create_response(
                success=False,
                message="未提供文件进行分析",
                error="文件分析需要上传文件"
            )
        
        # 这里添加文件分析逻辑
        # 可以调用LLM服务来分析文件内容
        
        # 暂时使用通用查询处理返回简单响应
        return process_general_query(user_message)
        
    except Exception as e:
        print(f"处理文件分析查询时出错: {str(e)}")
        traceback.print_exc()
        
        return create_response(
            success=False,
            message=f"处理文件分析查询时出错: {str(e)}",
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
        system_prompt = KB_RESPONSE_SYSTEM_PROMPT
        user_prompt = KB_RESPONSE_USER_PROMPT.format(
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