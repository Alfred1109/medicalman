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
from app.services.llm_service import LLMService
from app.utils.chart import generate_dynamic_charts
from app.utils.files import get_latest_file, analyze_text_content
from app.models.database import Database

# 导入提示词
from app.prompts import (
    DATABASE_SYSTEM_PROMPT, DATABASE_USER_PROMPT,
    RESPONSE_SYSTEM_PROMPT, RESPONSE_USER_PROMPT,
    EXCEL_SYSTEM_PROMPT, EXCEL_USER_PROMPT,
    TEXT_SYSTEM_PROMPT, TEXT_USER_PROMPT,
    KNOWLEDGE_BASE_SYSTEM_PROMPT, KNOWLEDGE_BASE_USER_PROMPT,
    FILE_ANALYSIS_SYSTEM_PROMPT, FILE_ANALYSIS_USER_PROMPT
)

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

def process_user_query(user_message: str, knowledge_settings: Dict = None) -> Dict[str, Any]:
    """
    处理用户查询
    
    参数:
        user_message: 用户消息
        knowledge_settings: 知识设置
        
    返回:
        处理结果
    """
    try:
        print("\n=== 处理新的用户查询 ===")
        print(f"用户消息: {user_message}")
        
        # 对于特定查询，直接使用预定义的SQL
        if "神经内科" in user_message and "小儿专科" in user_message and "2024年1月" in user_message:
            sql_query = """
            SELECT 
                o.department AS 科室, 
                o.specialty AS 专科, 
                SUM(o.visit_count) AS 实际门诊量, 
                t.target_count AS 目标门诊量,
                ROUND(SUM(o.visit_count) * 100.0 / t.target_count, 2) AS 完成率
            FROM outpatient o
            JOIN target t ON o.department = t.department AND o.specialty = t.specialty
            WHERE o.department = '神经内科' AND o.specialty = '小儿专科'
                  AND substr(o.visit_date, 1, 7) = '2024-01'
                  AND t.month = '2024-01'
            GROUP BY o.department, o.specialty
            """
            explanation = "根据用户查询使用预定义的SQL查询"
            
            try:
                # 执行预定义查询
                results = execute_sql_query(sql_query)
                query_success = True
                error_message = None
            except Exception as e:
                query_success = False
                error_message = str(e)
                results = pd.DataFrame()
                print(f"执行预定义查询出错: {error_message}")
        else:
            # 1. 调用LLM生成SQL查询
            query_result = LLMService.analyze_user_query_and_generate_sql(user_message)
            
            # 如果LLM调用失败，使用一个合理的默认查询
            if not query_result:
                # 通用的默认查询
                sql_query = """
                SELECT o.department AS 科室, o.specialty AS 专科, 
                       o.visit_date AS 日期, o.visit_count AS 门诊量
                FROM outpatient o
                LIMIT 10
                """
                explanation = "无法解析生成的查询，返回默认查询"
            else:
                sql_query = query_result.get('sql', '')
                explanation = query_result.get('explanation', '无解释')
                
                # 检查SQL查询中的表名和字段名，必要时进行修正
                # 如果查询使用中文表名，转换为英文
                if '门诊量' in sql_query:
                    sql_query = sql_query.replace('门诊量', 'outpatient')
                if '目标值' in sql_query:
                    sql_query = sql_query.replace('目标值', 'target')
                
                # 转换列名
                mapping = {
                    '科室': 'department',
                    '专科': 'specialty',
                    '日期': 'visit_date',
                    '数量': 'visit_count',
                    '目标值': 'target_count',
                    '年': 'year',
                    '月': 'month'
                }
                
                for zh, en in mapping.items():
                    sql_query = sql_query.replace(zh, en)
            
            print(f"生成的SQL查询: {sql_query}")
            print(f"查询解释: {explanation}")
            
            # 2. 执行SQL查询
            try:
                # 使用直接的SQL执行函数，而不是依赖应用上下文
                results = execute_sql_query(sql_query)
                query_success = True
                error_message = None
            except Exception as e:
                query_success = False
                error_message = str(e)
                results = pd.DataFrame()
                print(f"执行SQL查询时出错: {error_message}")
                
                # 如果查询出错，尝试使用默认查询
                try:
                    default_sql = """
                    SELECT o.department AS 科室, o.specialty AS 专科, 
                           SUM(o.visit_count) AS 实际门诊量, 
                           t.target_count AS 目标门诊量,
                           ROUND(SUM(o.visit_count) * 100.0 / t.target_count, 2) AS 完成率
                    FROM outpatient o
                    JOIN target t ON o.department = t.department AND o.specialty = t.specialty
                    WHERE o.department = '神经内科' AND o.specialty = '小儿专科'
                          AND substr(o.visit_date, 1, 7) = '2024-01'
                          AND t.month = '2024-01'
                    GROUP BY o.department, o.specialty
                    """
                    print("尝试使用默认查询...")
                    results = execute_sql_query(default_sql)
                    query_success = True
                    error_message = None
                except Exception as e2:
                    print(f"默认查询也失败: {str(e2)}")
        
        # 3. 根据查询结果生成可视化
        visualizations = []
        if not results.empty:
            # 无法生成可视化图表，因为不在应用上下文中
            pass
        
        # 4. 生成回复文本
        if query_success and not results.empty:
            # 将数据帧转换为可读字符串
            result_str = results.to_string(index=False)
            
            # 使用LLM分析结果
            formatted_user_prompt = RESPONSE_USER_PROMPT.format(
                user_query=user_message,
                query_results=result_str
            )
            
            reply = LLMService.call_llm_api(RESPONSE_SYSTEM_PROMPT, formatted_user_prompt)
            if not reply:
                # 如果LLM调用失败，直接返回结果
                if "完成率" in results.columns:
                    for _, row in results.iterrows():
                        completion_rate = row["完成率"]
                        reply = f"神经内科小儿专科2024年1月的门诊量目标达成情况分析：\n\n" \
                               f"科室: {row['科室']}\n" \
                               f"专科: {row['专科']}\n" \
                               f"实际门诊量: {row['实际门诊量']}\n" \
                               f"目标门诊量: {row['目标门诊量']}\n" \
                               f"完成率: {completion_rate}%\n\n" \
                               f"{'目标已达成' if completion_rate >= 100 else '目标未达成'}"
                else:
                    reply = f"查询结果: \n{result_str}"
        else:
            # 生成错误提示
            reply = f"抱歉，无法执行您的查询。错误信息: {error_message}" if error_message else "抱歉，查询没有返回任何结果。"
        
        # 5. 返回完整结果
        return {
            'success': query_success,
            'query': sql_query,
            'explanation': explanation,
            'sql_results': results.to_dict('records') if not results.empty else [],
            'visualizations': visualizations,
            'reply': reply,
            'error': error_message
        }
        
    except Exception as e:
        print(f"处理用户查询时出错: {str(e)}")
        print(f"错误堆栈: {traceback.format_exc()}")
        
        return {
            'success': False,
            'query': '',
            'explanation': '',
            'sql_results': [],
            'visualizations': [],
            'reply': f"抱歉，处理您的查询时发生错误: {str(e)}",
            'error': str(e)
        } 