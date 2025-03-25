from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import os
import re
from datetime import datetime
import json
import traceback
import sqlite3
from pathlib import Path

# 获取项目根目录的绝对路径
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# 使用app配置中的数据库路径，而不是直接设置
# DATABASE_PATH = str(ROOT_DIR / 'medical_workload.db')

from app.utils.db import execute_query_to_dataframe
from app.services.llm_service import LLMServiceFactory
from app.utils.chart import generate_dynamic_charts
from app.utils.files import get_latest_file, analyze_text_content
from app.models.database import Database

# 导入提示词
from app.prompts import (
    DATABASE_SCHEMA_PROMPT, DATABASE_USER_PROMPT,
    RESPONSE_SYSTEM_PROMPT, RESPONSE_USER_PROMPT,
    EXCEL_ANALYSIS_SYSTEM_PROMPT, EXCEL_ANALYSIS_USER_PROMPT,
    TEXT_ANALYSIS_SYSTEM_PROMPT, TEXT_ANALYSIS_USER_PROMPT,
    KNOWLEDGE_BASE_SYSTEM_PROMPT, KNOWLEDGE_BASE_USER_PROMPT,
    FILE_ANALYSIS_SYSTEM_PROMPT, FILE_ANALYSIS_USER_PROMPT,
    DATA_ANALYSIS_SYSTEM_PROMPT, DATA_ANALYSIS_USER_PROMPT,
    SQL_META_PROMPT
)

# 数据库元数据缓存
DB_METADATA_CACHE = None
DB_METADATA_CACHE_TIME = 0

def get_db_metadata(force_refresh=False):
    """
    获取数据库的元数据信息，包括所有表和字段
    
    参数:
        force_refresh: 是否强制刷新缓存
        
    返回:
        包含表和字段详细信息的字典
    """
    global DB_METADATA_CACHE, DB_METADATA_CACHE_TIME
    
    # 如果缓存存在且未过期（30分钟）且不强制刷新，直接返回缓存
    current_time = pd.Timestamp.now().timestamp()
    if DB_METADATA_CACHE and (current_time - DB_METADATA_CACHE_TIME < 1800) and not force_refresh:
        return DB_METADATA_CACHE
    
    # 初始化元数据结构
    metadata = {
        'tables': [],
        'table_details': {},
        'column_details': {},
        'relationships': []
    }
    
    try:
        # 获取数据库连接
        conn = Database.get_connection()
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        metadata['tables'] = tables
        
        # 获取每个表的结构
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            table_info = {
                'name': table,
                'columns': []
            }
            
            for col in columns:
                col_id, col_name, col_type, col_notnull, col_default, col_pk = col
                
                # 添加列信息
                column_info = {
                    'name': col_name,
                    'type': col_type,
                    'is_primary_key': col_pk == 1,
                    'not_null': col_notnull == 1,
                    'default': col_default
                }
                
                table_info['columns'].append(col_name)
                metadata['column_details'][f"{table}.{col_name}"] = column_info
            
            # 获取表中的前10行数据作为示例
            try:
                cursor.execute(f"SELECT * FROM {table} LIMIT 10")
                sample_data = cursor.fetchall()
                
                if sample_data and len(sample_data) > 0:
                    # 获取列名
                    col_names = [description[0] for description in cursor.description]
                    
                    # 将样例数据转换为列表的字典
                    sample_rows = []
                    for row in sample_data:
                        sample_row = {}
                        for i, col_name in enumerate(col_names):
                            sample_row[col_name] = row[i]
                        sample_rows.append(sample_row)
                    
                    table_info['sample_data'] = sample_rows
            except Exception as e:
                print(f"获取表 {table} 的样例数据失败: {str(e)}")
                table_info['sample_data'] = []
            
            metadata['table_details'][table] = table_info
            
        # 更新缓存
        DB_METADATA_CACHE = metadata
        DB_METADATA_CACHE_TIME = current_time
        
        return metadata
    except Exception as e:
        print(f"获取数据库元数据失败: {str(e)}")
        return None
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def generate_schema_prompt():
    """
    生成描述数据库架构的提示，用于帮助LLM理解数据库结构
    
    返回:
        描述数据库结构的字符串
    """
    metadata = get_db_metadata()
    
    if not metadata:
        return "无法获取数据库结构信息。"
    
    prompt_parts = ["以下是数据库的结构信息："]
    
    # 添加表信息
    prompt_parts.append("\n## 数据库表\n")
    for table in metadata['tables']:
        table_info = metadata['table_details'][table]
        columns = table_info['columns']
        prompt_parts.append(f"- 表名: `{table}`")
        prompt_parts.append(f"  - 列: {', '.join([f'`{col}`' for col in columns])}")
        
        # 添加样例数据（如果有）
        if 'sample_data' in table_info and table_info['sample_data']:
            prompt_parts.append(f"  - 样例数据 (前几行):")
            
            # 如果有多于5行，仅显示前5行
            sample_data = table_info['sample_data'][:5]
            
            # 格式化为简单的表格形式
            for row in sample_data:
                row_str = ", ".join([f"{k}: {v}" for k, v in row.items()])
                prompt_parts.append(f"    * {row_str}")
    
    # 添加列详细信息
    prompt_parts.append("\n## 列详细信息\n")
    for table in metadata['tables']:
        prompt_parts.append(f"### 表 `{table}`")
        table_info = metadata['table_details'][table]
        for col_name in table_info['columns']:
            col_info = metadata['column_details'][f"{table}.{col_name}"]
            prompt_parts.append(f"- `{col_name}`: 类型={col_info['type']}, 主键={col_info['is_primary_key']}, 非空={col_info['not_null']}")
    
    return "\n".join(prompt_parts)

def generate_sql_from_metadata(user_message):
    """
    使用数据库元数据帮助LLM生成更准确的SQL查询
    
    参数:
        user_message: 用户的查询消息
        
    返回:
        包含生成的SQL和说明的字典
    """
    # 获取数据库结构
    schema_prompt = generate_schema_prompt()
    
    # 结合数据库结构和用户查询创建提示
    formatted_prompt = SQL_META_PROMPT.format(schema_prompt=schema_prompt)
    
    user_prompt = f"请为以下问题生成SQL查询：{user_message}"
    
    # 使用基础服务调用LLM API
    base_service = LLMServiceFactory.get_base_service()
    llm_response = base_service.call_api(formatted_prompt, user_prompt)
    
    # 解析LLM的回答，提取JSON部分
    if llm_response:
        # 尝试从回答中提取JSON
        json_match = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', llm_response)
        if json_match:
            try:
                result = json.loads(json_match.group(1))
                # 确保结果包含必要的字段
                if 'sql' in result and 'explanation' in result:
                    return result
            except json.JSONDecodeError:
                pass
        
        # 如果无法提取JSON或格式不正确，尝试直接从回答中提取SQL和解释
        sql_match = re.search(r'```sql\s*([\s\S]*?)\s*```', llm_response)
        explanation_match = re.search(r'解释[：:]\s*([\s\S]*?)(?=$|\n\n|\Z)', llm_response)
        
        if sql_match:
            sql = sql_match.group(1).strip()
            explanation = explanation_match.group(1).strip() if explanation_match else "无解释提供"
            return {
                "sql": sql,
                "explanation": explanation
            }
    
    # 如果无法获取有效响应或解析失败
    return None

def analyze_user_query_and_generate_sql(user_message):
    """
    分析用户查询并生成SQL
    
    参数:
        user_message: 用户的查询消息
        
    返回:
        包含生成的SQL和说明的字典，如果失败则返回None
    """
    try:
        # 使用数据库元数据生成SQL
        sql_result = generate_sql_from_metadata(user_message)
        
        if sql_result and 'sql' in sql_result:
            return sql_result
        
        # 如果使用元数据方法失败，则使用LLM服务生成SQL
        sql_service = LLMServiceFactory.get_sql_service()
        return sql_service.generate_sql(user_message)
    except Exception as e:
        print(f"生成SQL时出错: {str(e)}")
        traceback.print_exc()
        return None

def execute_sql_query(sql_query):
    """
    执行SQL查询并返回结果
    
    参数:
        sql_query: SQL查询字符串
        
    返回:
        查询结果的数据帧
    """
    try:
        return execute_query_to_dataframe(sql_query)
    except Exception as e:
        print(f"SQL查询执行错误: {str(e)}")
        # 添加更多有用的上下文信息，帮助诊断问题
        print(f"执行的SQL查询: {sql_query}")
        traceback.print_exc()  # 打印完整的堆栈跟踪
        raise e

def get_latest_excel_file(directory: str = 'static/uploads/documents') -> Optional[Tuple[str, pd.DataFrame]]:
    """
    获取最新上传的Excel文件及其数据
    
    参数:
        directory: 文件目录
        
    返回:
        元组 (文件名, 数据帧) 或 None
    """
    latest_file = get_latest_file(directory)
    
    if not latest_file:
        return None
        
    file_path = os.path.join(directory, latest_file)
    
    # 检查是否是Excel文件
    if latest_file.endswith(('.xlsx', '.xls', '.xlsm', '.ods')):
        try:
            # 尝试读取Excel文件
            df = pd.read_excel(file_path)
            return (latest_file, df)
        except Exception as e:
            print(f"读取Excel文件失败: {str(e)}")
            return None
    
    return None

# 添加直接执行查询的函数
def execute_sql_query(sql: str) -> pd.DataFrame:
    """
    执行SQL查询并返回DataFrame结果
    
    参数:
        sql: SQL查询语句
        
    返回:
        查询结果DataFrame
    """
    try:
        # 使用Database类获取连接而不是直接使用路径
        conn = Database.get_connection()
        df = pd.read_sql_query(sql, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"执行SQL查询时出错: {str(e)}")
        return pd.DataFrame()

# 添加LangChain查询处理函数
def process_query_with_langchain(user_message: str) -> Dict[str, Any]:
    """
    使用LangChain处理用户查询并生成SQL
    
    参数:
        user_message: 用户查询信息
        
    返回:
        包含SQL和解释的结果
    """
    try:
        # 获取SQL服务实例
        sql_service = LLMServiceFactory.get_sql_service()
        
        # 使用LangChain生成SQL
        sql_result = sql_service.generate_sql_with_langchain(user_message)
        
        if not sql_result:
            print("LangChain SQL生成失败")
            return None
            
        return sql_result
        
    except Exception as e:
        print(f"LangChain处理查询出错: {str(e)}")
        traceback.print_exc()
        return None

# 使用改进后的方法处理用户查询
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
    
    # 数据源选择，默认为'auto'
    data_source = knowledge_settings.get('data_source', 'auto')
    
    start_time = datetime.now()
    
    try:
        # 根据数据源选择查询处理方式
        if data_source == 'database' or (data_source == 'auto' and looks_like_database_query(user_message)):
            # 数据库查询处理
            result = process_database_query(user_message)
        elif data_source == 'knowledge_base' or (data_source == 'auto' and is_medical_knowledge_query(user_message)):
            # 知识库查询处理
            result = process_knowledge_query(user_message, knowledge_settings)
        elif data_source == 'file' or (data_source == 'auto' and is_file_analysis_query(user_message)):
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
        
        return {
            "success": False,
            "message": f"处理查询时出错: {str(e)}",
            "process_time": f"{(datetime.now() - start_time).total_seconds():.2f}秒"
        } 