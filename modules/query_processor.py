from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import os
import re
from datetime import datetime
import numpy as np
import json
import sqlite3
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from sklearn.linear_model import LinearRegression
import traceback  # 添加traceback模块

from .db_connection import get_database_schema, execute_safe_query, validate_sql_query
from .llm_interface import analyze_user_query_and_generate_sql, generate_data_analysis, generate_text_analysis, call_llm_api
from .chart_generator import generate_dynamic_charts
from .response_generator import generate_response
from .file_processor import get_latest_file, analyze_text_content

# 导入新的提示词
from .prompts.excel_prompt import EXCEL_SYSTEM_PROMPT, EXCEL_USER_PROMPT
from .prompts.text_prompt import TEXT_SYSTEM_PROMPT, TEXT_USER_PROMPT
from .prompts.database_prompt import DATABASE_SYSTEM_PROMPT, DATABASE_USER_PROMPT
from .prompts.knowledge_base_prompt import KNOWLEDGE_BASE_SYSTEM_PROMPT, KNOWLEDGE_BASE_USER_PROMPT
from .prompts.response_generator_prompt import RESPONSE_SYSTEM_PROMPT, RESPONSE_USER_PROMPT

def get_latest_excel_file(directory: str = 'static/uploads/documents') -> Optional[Tuple[str, pd.DataFrame]]:
    """
    获取最新上传的Excel文件及其数据
    
    参数:
        directory: 文件目录
        
    返回:
        Optional[Tuple[str, pd.DataFrame]]: 文件名和DataFrame的元组，如果没有文件则返回None
    """
    try:
        # 使用新的文件处理模块获取最新文件
        file_info = get_latest_file(directory)
        
        # 如果没有文件或文件类型不是Excel/CSV，返回None
        if file_info is None:
            print(f"未找到有效的Excel文件")
            return None
            
        filename, content, file_type = file_info
        
        # 只处理Excel和CSV文件
        if file_type in ['excel', 'csv']:
            return (filename, content)
        else:
            print(f"最新文件不是Excel格式: {filename}, 类型: {file_type}")
            return None
        
    except Exception as e:
        print(f"获取最新Excel文件时出错: {str(e)}")
        return None

def analyze_uploaded_data(df: pd.DataFrame, user_message: str) -> str:
    """
    通用化分析上传的Excel数据
    
    参数:
        df: DataFrame对象，包含上传的Excel数据
        user_message: 用户的问题
        
    返回:
        str: 分析结果的文本描述
    """
    try:
        print(f"开始分析上传数据，用户消息: '{user_message}'")
        
        # 1. 数据预处理
        print(f"原始数据形状: {df.shape}")
        print("原始数据列:", df.columns.tolist())
        df = df.dropna(axis=1, how='all').dropna(how='all')
        print(f"预处理后数据形状: {df.shape}")
        print("预处理后数据列:", df.columns.tolist())
        
        # 检查是否要显示前几行数据
        if any(keyword in user_message.lower() for keyword in ['前', '前几行', '开头', '列出']):
            print("检测到用户要求显示前几行数据")
            num_rows = 3  # 默认显示3行
            for num in re.findall(r'前(\d+)行', user_message):
                num_rows = int(num)
                print(f"用户指定显示前{num_rows}行")
            
            result = f"以下是数据的前{num_rows}行内容：\n\n"
            # 将DataFrame的前几行转换为字符串格式
            df_head = df.head(num_rows)
            # 格式化输出，确保对齐
            result += df_head.to_string(index=False) + "\n\n"
            result += f"总共有 {len(df)} 条记录。\n\n"
            print("返回前几行数据结果")
            return result
        
        # 如果用户消息很简短（如"分析下我上传的文件"），提供基本数据概览
        if len(user_message) < 15 or re.search(r'^(分析|查看|浏览|显示|看下|查询|打开|了解)(下|一下|下载|看看)?(上传|我的|刚刚的|这个|最新)?(文件|表格|excel|xlsx|xls|csv|pdf|文档|内容|数据|资料|报表|报告|表单)', user_message):
            print("用户请求简单，提供基本数据概览")
            
            # 生成基本数据概览
            result = f"## 上传文件数据概览\n\n"
            result += f"- **总行数**: {len(df)}\n"
            result += f"- **总列数**: {len(df.columns)}\n\n"
            
            # 显示前5行数据
            result += "### 数据预览（前5行）\n\n"
            result += df.head(5).to_markdown(index=False) + "\n\n"
            
            # 显示数据类型
            result += "### 数据列类型\n\n"
            dtypes_df = pd.DataFrame({
                '列名': df.columns,
                '数据类型': df.dtypes.astype(str),
                '非空值数量': df.count().values,
                '空值数量': df.isna().sum().values,
                '唯一值数量': [df[col].nunique() for col in df.columns]
            })
            result += dtypes_df.to_markdown(index=False) + "\n\n"
            
            # 如果有数值列，添加基本统计信息
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                result += "### 数值列统计\n\n"
                stats = df[numeric_cols].describe().T
                result += stats.to_markdown() + "\n\n"
            
            # 如果有日期列，添加时间范围信息
            date_cols = df.select_dtypes(include=['datetime']).columns
            if len(date_cols) > 0:
                result += "### 日期列范围\n\n"
                for col in date_cols:
                    min_date = df[col].min()
                    max_date = df[col].max()
                    result += f"- **{col}**: 从 {min_date} 到 {max_date}\n"
                result += "\n"
            
            # 添加进一步分析的提示
            result += "### 进一步分析\n\n"
            result += "您可以通过以下方式获取更详细的分析：\n\n"
            result += "1. 询问特定列的分析，例如：'分析[列名]的分布情况'\n"
            result += "2. 询问数据趋势，例如：'分析销售额随时间的变化趋势'\n"
            result += "3. 询问特定统计信息，例如：'计算各部门的平均销售额'\n"
            
            print("返回基本数据概览结果")
            return result
            
        # 2. 智能识别数据类型
        print("开始识别数据类型")
        column_types = {}
        date_pattern = r'\d{4}[-/年]\d{1,2}[-/月]'
        numeric_pattern = r'^\d+\.?\d*$'
        
        for col in df.columns:
            # 日期类型识别
            if df[col].dtype == 'datetime64[ns]':
                column_types[col] = 'date'
            elif isinstance(df[col].iloc[0], str) and re.search(date_pattern, str(df[col].iloc[0])):
                try:
                    df[col] = pd.to_datetime(df[col])
                    column_types[col] = 'date'
                except:
                    column_types[col] = 'text'
            # 数值类型识别
            elif df[col].dtype in ['int64', 'float64']:
                column_types[col] = 'numeric'
            elif isinstance(df[col].iloc[0], str) and re.search(numeric_pattern, str(df[col].iloc[0])):
                try:
                    df[col] = pd.to_numeric(df[col])
                    column_types[col] = 'numeric'
                except:
                    column_types[col] = 'text'
            else:
                column_types[col] = 'text'
        
        print(f"列类型识别结果: {column_types}")
        
        # 3. 基于用户问题的关键词提取
        keywords = extract_keywords_from_message(user_message)
        print(f"从用户消息中提取的关键词: {keywords}")
        
        # 4. 相关列识别
        relevant_cols = find_relevant_columns(df, keywords)
        print(f"识别到的相关列: {relevant_cols}")
        
        # 5. 使用LLM生成分析结果
        print("调用LLM生成分析结果")
        result = generate_data_analysis(df, column_types, relevant_cols, keywords, user_message)
        print("LLM分析完成")
        
        return result
        
    except Exception as e:
        print(f"分析上传数据时出错: {str(e)}")
        traceback.print_exc()
        return f"分析数据时遇到错误: {str(e)}"

def extract_keywords_from_message(message: str) -> List[str]:
    """
    从用户消息中提取关键词
    
    参数:
        message: 用户消息
        
    返回:
        List[str]: 关键词列表
    """
    # 医疗领域关键词
    medical_keywords = ['门诊', '住院', '患者', '医生', '科室', '病例', '诊断', '治疗', 
                       '手术', '药品', '医院', '病人', '床位', '挂号', '就诊', '医保']
    
    # 电商领域关键词
    ecommerce_keywords = ['销售', '商品', '订单', '客户', '价格', '库存', '产品', 
                         '交易', '购买', '店铺', '主播', '直播', '流量', '转化率']
    
    # 通用分析关键词
    analysis_keywords = ['分析', '统计', '趋势', '对比', '比较', '排名', '排序', 
                        '最高', '最低', '平均', '总计', '汇总', '预测']
    
    # 时间相关关键词
    time_keywords = ['今天', '昨天', '本周', '上周', '本月', '上月', '今年', '去年', 
                    '季度', '年度', '日', '周', '月', '年']
    
    # 合并所有关键词
    all_keywords = medical_keywords + ecommerce_keywords + analysis_keywords + time_keywords
    
    # 从消息中提取关键词
    extracted_keywords = []
    for keyword in all_keywords:
        if keyword in message:
            extracted_keywords.append(keyword)
    
    # 如果没有提取到关键词，则使用消息中的所有词作为关键词
    if not extracted_keywords:
        # 简单分词，按空格和标点符号分割
        words = re.findall(r'\w+', message)
        extracted_keywords = [word for word in words if len(word) > 1]
    
    return extracted_keywords

def find_relevant_columns(df: pd.DataFrame, keywords: List[str]) -> List[str]:
    """
    根据关键词找出相关的列
    
    参数:
        df: DataFrame对象
        keywords: 关键词列表
        
    返回:
        List[str]: 相关列名列表
    """
    relevant_cols = []
    
    # 将列名转换为字符串
    str_columns = [str(col) for col in df.columns]
    
    # 对每个关键词，找出包含该关键词的列
    for keyword in keywords:
        for col in str_columns:
            # 检查列名是否包含关键词（不区分大小写）
            if keyword.lower() in col.lower() and col not in relevant_cols:
                relevant_cols.append(col)
    
    # 如果没有找到相关列，则返回所有数值列作为相关列
    if not relevant_cols:
        # 尝试识别数值列
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if numeric_cols:
            return numeric_cols
        # 如果没有数值列，则返回前5列
        else:
            return df.columns[:5].tolist()
    
    return relevant_cols

def determine_data_source(user_message: str, has_excel: bool) -> str:
    """
    根据用户消息智能判断用户想要查询的数据源
    
    参数:
        user_message: 用户消息
        has_excel: 是否有上传的Excel文件
        
    返回:
        str: 数据源偏好，'file'（上传文件）, 'database'（数据库）, 'both'（两者都查）
    """
    # 如果没有上传Excel文件，只能查询数据库
    if not has_excel:
        return 'database'
    
    # 检查用户消息中是否明确指定了数据源
    file_keywords = ['上传', '文件', '表格', 'excel', '电子表格', '刚刚上传', '我的文件']
    db_keywords = ['数据库', '系统数据', '历史数据', '系统', '医院数据']
    
    has_file_keywords = any(keyword in user_message.lower() for keyword in file_keywords)
    has_db_keywords = any(keyword in user_message.lower() for keyword in db_keywords)
    
    # 如果用户明确指定了数据源
    if has_file_keywords and not has_db_keywords:
        return 'file'
    elif has_db_keywords and not has_file_keywords:
        return 'database'
    elif has_file_keywords and has_db_keywords:
        return 'both'
    
    # 如果用户没有明确指定数据源，默认查询上传的文件
    return 'file'

def generate_response_from_sql_results(user_message: str, sql_query: str, results: pd.DataFrame) -> str:
    """
    根据SQL查询结果生成自然语言回复
    
    参数:
        user_message: 用户消息
        sql_query: 执行的SQL查询
        results: 查询结果DataFrame
        
    返回:
        str: 自然语言回复
    """
    # 如果没有结果
    if results.empty:
        return "抱歉，没有找到与您查询相关的数据。"
    
    # 提取查询中的关键信息
    keywords = extract_keywords_from_message(user_message)
    
    # 生成回复
    reply = "## 查询结果\n\n"
    
    # 添加结果概述
    reply += f"共找到 {len(results)} 条记录。\n\n"
    
    # 如果结果较少，直接显示所有结果
    if len(results) <= 10:
        # 将DataFrame转换为Markdown表格
        table = results.to_markdown(index=False)
        reply += table + "\n\n"
    else:
        # 显示前5行
        table = results.head(5).to_markdown(index=False)
        reply += "以下是前5条记录：\n\n" + table + "\n\n"
    
    # 如果有数值列，添加统计信息
    numeric_cols = results.select_dtypes(include=['number']).columns
    if not numeric_cols.empty:
        reply += "### 统计信息\n\n"
        stats = results[numeric_cols].describe().T[['count', 'mean', 'min', 'max']]
        stats_table = stats.to_markdown()
        reply += stats_table + "\n\n"
    
    # 添加SQL查询（可选，取决于是否需要向用户展示）
    # reply += f"### 执行的SQL查询\n\n```sql\n{sql_query}\n```\n\n"
    
    return reply

def process_user_query(user_message: str, data_source_preference: str = None):
    """
    处理用户查询并生成响应
    
    参数:
        user_message: 用户的问题
        data_source_preference: 用户偏好的数据源（如果有）
        
    返回:
        dict: 包含响应类型和内容的字典
    """
    try:
        print(f"开始处理用户查询: '{user_message}'")
        
        # 检查是否是查看文件内容的请求
        is_view_file_content = re.search(r'(查看|浏览|显示|看下|查询|打开)(上传|文件|文档|表格|内容)', user_message.lower()) and not re.search(r'(分析|统计|计算|对比|比较)', user_message.lower())
        
        # 检查是否是分析文件内容的请求
        is_analyze_file_content = re.search(r'(分析|统计|计算|对比|比较)(上传|文件|文档|表格|内容|数据)', user_message.lower())
        
        # 获取最新上传的文件
        latest_file_info = get_latest_file('static/uploads/documents')
        
        # 如果有文件且是查看或分析文件的请求
        if latest_file_info and (is_view_file_content or is_analyze_file_content):
            file_path, file_type, file_content = latest_file_info
            filename = os.path.basename(file_path)
            
            # 处理查看文件内容的请求
            if is_view_file_content:
                from .prompts.file_analysis_prompt import FILE_CONTENT_PROMPT
                
                # 构建提示词
                prompt = FILE_CONTENT_PROMPT.format(
                    filename=filename,
                    file_type=file_type,
                    file_path=file_path,
                    file_size=os.path.getsize(file_path),
                    content_preview=str(file_content)[:1000] + "..." if len(str(file_content)) > 1000 else str(file_content),
                    user_message=user_message
                )
                
                # 调用LLM生成回复
                response = call_llm_api(FILE_CONTENT_PROMPT, prompt)
                
                if not response:
                    return {
                        'type': 'error',
                        'content': '无法生成文件内容分析，请重试。'
                    }
                
                # 格式化响应
                formatted_response = call_llm_api(
                    RESPONSE_SYSTEM_PROMPT,
                    RESPONSE_USER_PROMPT.format(
                        analysis_result=response,
                        data_source='file',
                        analysis_type='file_content'
                    )
                )
                
                return {
                    'type': 'knowledge_base',
                    'content': formatted_response or response,
                    'file_name': filename
                }
            
            # 处理分析文件内容的请求
            elif is_analyze_file_content:
                if file_type in ['xlsx', 'xls', 'xlsm', 'ods', 'csv']:
                    try:
                        # 分析Excel数据
                        analysis_result = analyze_uploaded_data(file_content, user_message)
                        
                        # 格式化响应
                        formatted_response = call_llm_api(
                            RESPONSE_SYSTEM_PROMPT,
                            RESPONSE_USER_PROMPT.format(
                                analysis_result=analysis_result,
                                data_source='excel',
                                analysis_type='data_analysis'
                            )
                        )
                        
                        return {
                            'type': 'excel_analysis',
                            'content': formatted_response or analysis_result,
                            'file_name': filename
                        }
                    except Exception as e:
                        print(f"分析Excel数据时出错: {str(e)}")
                        return {
                            'type': 'error',
                            'content': f"分析Excel数据时出错: {str(e)}"
                        }
                elif file_type in ['pdf', 'docx', 'txt']:
                    if file_content:
                        # 使用LLM分析文本内容
                        analysis_result = generate_text_analysis(file_content, user_message)
                        
                        # 格式化响应
                        formatted_response = call_llm_api(
                            RESPONSE_SYSTEM_PROMPT,
                            RESPONSE_USER_PROMPT.format(
                                analysis_result=analysis_result,
                                data_source='text',
                                analysis_type='text_analysis'
                            )
                        )
                        
                        return {
                            'type': 'text_analysis',
                            'content': formatted_response or analysis_result,
                            'file_name': filename
                        }
                    else:
                        return {
                            'type': 'error',
                            'content': f"无法从{file_type}文件中提取内容，请检查文件是否有效。"
                        }
        
        # 如果没有文件或不是文件相关的请求，使用知识库
        # 使用大模型生成回复
        from .prompts.knowledge_base_prompt import KNOWLEDGE_BASE_SYSTEM_PROMPT, KNOWLEDGE_BASE_USER_PROMPT
        
        # 构建用户提示词
        prompt = KNOWLEDGE_BASE_USER_PROMPT.format(user_message=user_message)
        
        # 调用大模型生成回复
        response = call_llm_api(KNOWLEDGE_BASE_SYSTEM_PROMPT, prompt)
        
        if not response:
            return {
                'type': 'error',
                'content': '无法生成回复，请重试。'
            }
        
        # 格式化响应
        formatted_response = call_llm_api(
            RESPONSE_SYSTEM_PROMPT,
            RESPONSE_USER_PROMPT.format(
                analysis_result=response,
                data_source='knowledge_base',
                analysis_type='general'
            )
        )
        
        return {
            'type': 'knowledge_base',
            'content': formatted_response or response
        }
        
    except Exception as e:
        print(f"处理用户查询时出错: {str(e)}")
        traceback.print_exc()
        return {
            'type': 'error',
            'content': f"处理您的问题时出错: {str(e)}"
        }

def generate_sql_query(user_message: str, db_schema: Dict) -> str:
    """
    根据用户消息和数据库模式生成SQL查询
    
    参数:
        user_message: 用户消息
        db_schema: 数据库模式信息
        
    返回:
        str: 生成的SQL查询
    """
    # 这里是一个简化的实现，实际应用中可能需要更复杂的逻辑
    # 例如使用NLP技术或规则引擎来生成更准确的SQL查询
    
    # 提取关键词
    keywords = extract_keywords_from_message(user_message)
    print(f"提取的关键词: {keywords}")
    
    # 根据关键词找出相关表
    relevant_tables = []
    for table_name, table_info in db_schema.items():
        # 检查表名是否包含关键词
        if any(keyword in table_name.lower() for keyword in keywords):
            relevant_tables.append(table_name)
            continue
        
        # 检查列名是否包含关键词
        for column in table_info['columns']:
            if any(keyword in column.lower() for keyword in keywords):
                relevant_tables.append(table_name)
                break
    
    print(f"相关表: {relevant_tables}")
    
    # 如果没有找到相关表，使用默认查询
    if not relevant_tables:
        # 默认查询第一个表的前10行
        default_table = list(db_schema.keys())[0] if db_schema else 'unknown_table'
        return f"SELECT * FROM {default_table} LIMIT 10"
    
    # 生成查询
    table_name = relevant_tables[0]
    columns = db_schema[table_name]['columns']
    
    # 检查是否有聚合函数关键词
    has_aggregation = any(kw in user_message.lower() for kw in ['平均', '总计', '最大', '最小', '统计', '汇总'])
    
    # 检查是否有分组关键词
    has_groupby = any(kw in user_message.lower() for kw in ['按', '分组', '分类', '每个'])
    
    # 检查是否有排序关键词
    has_orderby = any(kw in user_message.lower() for kw in ['排序', '从高到低', '从低到高', '升序', '降序'])
    
    # 检查是否有限制关键词
    has_limit = any(kw in user_message.lower() for kw in ['前', '最多', '限制'])
    
    # 构建查询
    if has_aggregation:
        # 找出可能的聚合列（数值列）
        numeric_cols = [col for col in columns if 'int' in db_schema[table_name]['column_types'].get(col, '').lower() or 'float' in db_schema[table_name]['column_types'].get(col, '').lower()]
        
        if not numeric_cols:
            # 如果没有数值列，使用COUNT(*)
            select_clause = "COUNT(*) as count"
        else:
            # 使用第一个数值列进行聚合
            agg_col = numeric_cols[0]
            
            if '平均' in user_message:
                select_clause = f"AVG({agg_col}) as average_{agg_col}"
            elif '总计' in user_message or '汇总' in user_message:
                select_clause = f"SUM({agg_col}) as total_{agg_col}"
            elif '最大' in user_message:
                select_clause = f"MAX({agg_col}) as max_{agg_col}"
            elif '最小' in user_message:
                select_clause = f"MIN({agg_col}) as min_{agg_col}"
            else:
                select_clause = f"COUNT(*) as count, SUM({agg_col}) as total_{agg_col}, AVG({agg_col}) as average_{agg_col}"
        
        # 如果有分组，添加分组列
        if has_groupby:
            # 找出可能的分组列（非数值列）
            non_numeric_cols = [col for col in columns if col not in numeric_cols]
            
            if non_numeric_cols:
                # 使用第一个非数值列进行分组
                group_col = non_numeric_cols[0]
                select_clause = f"{group_col}, {select_clause}"
                query = f"SELECT {select_clause} FROM {table_name} GROUP BY {group_col}"
            else:
                # 如果没有非数值列，不使用分组
                query = f"SELECT {select_clause} FROM {table_name}"
        else:
            query = f"SELECT {select_clause} FROM {table_name}"
    else:
        # 普通查询，选择所有列
        query = f"SELECT * FROM {table_name}"
    
    # 添加排序
    if has_orderby:
        # 找出可能的排序列
        if has_aggregation and not has_groupby:
            # 如果有聚合但没有分组，不添加排序
            pass
        elif has_aggregation and has_groupby:
            # 如果有聚合和分组，按聚合结果排序
            if '平均' in user_message:
                query += f" ORDER BY average_{agg_col} DESC"
            elif '总计' in user_message or '汇总' in user_message:
                query += f" ORDER BY total_{agg_col} DESC"
            elif '最大' in user_message:
                query += f" ORDER BY max_{agg_col} DESC"
            elif '最小' in user_message:
                query += f" ORDER BY min_{agg_col} DESC"
            else:
                query += f" ORDER BY count DESC"
        else:
            # 普通查询，使用第一个列排序
            order_col = columns[0]
            if '降序' in user_message or '从高到低' in user_message:
                query += f" ORDER BY {order_col} DESC"
            else:
                query += f" ORDER BY {order_col} ASC"
    
    # 添加限制
    if has_limit:
        # 提取数字
        limit_numbers = re.findall(r'\d+', user_message)
        limit = int(limit_numbers[0]) if limit_numbers else 10
        query += f" LIMIT {limit}"
    else:
        # 默认限制为100行
        query += " LIMIT 100"
    
    return query 

def process_knowledge_base_query(user_message: str) -> Dict[str, Any]:
    """
    处理基于知识库的查询
    
    参数:
        user_message: 用户消息
        
    返回:
        包含回复内容的字典
    """
    try:
        # 获取数据库结构信息
        schema_info = get_database_schema()
        
        # 如果是查询门诊目标达成情况
        if "门诊目标" in user_message or "目标达成" in user_message:
            # 生成SQL查询
            sql_result = analyze_user_query_and_generate_sql(user_message, schema_info)
            
            if sql_result and "sql_queries" in sql_result:
                queries = []
                results = {}
                
                # 执行所有SQL查询
                for i, query in enumerate(sql_result["sql_queries"]):
                    if validate_sql_query(query):
                        df = execute_safe_query(query)
                        if not df.empty:
                            query_name = f"查询{i+1}"
                            results[query_name] = df
                            queries.append({"name": query_name, "sql": query})
                
                # 生成可视化方案
                charts = []
                if "visualization_plan" in sql_result:
                    for plan in sql_result["visualization_plan"]:
                        if isinstance(plan, dict):
                            charts.append(plan)
                
                # 生成最终响应
                response = generate_response(
                    user_message=user_message,
                    query_results=results,
                    charts=charts,
                    explanation=sql_result.get("explanation", "")
                )
                
                return {
                    "type": "database_query",
                    "content": response,
                    "sql_results": results,
                    "charts": charts
                }
            
            return {
                "type": "error",
                "content": "抱歉,生成SQL查询时出错,请稍后重试。"
            }
            
        # 检查是否有关于查看文件内容的查询
        elif re.search(r'(查看|浏览|显示|看下|查询|打开)(上传|文件|文档|表格|内容)', user_message):
            # 先检查是否有上传的文件
            latest_file_info = get_latest_file('static/uploads/documents')
            
            if not latest_file_info:
                # 如果没有上传文件，返回提示信息
                return {
                    'type': 'knowledge_base',
                    'content': f"""
## 查看上传文件内容

很抱歉，系统中没有找到任何上传的文件。

您需要先上传文件，然后才能查看文件内容。您可以：

1. 点击上传按钮上传文件（支持Excel、CSV、PDF、Word、文本和图像文件）
2. 上传完成后，再次询问"查看上传文件内容"

如果您已经上传了文件但系统未能识别，可能是因为：
- 文件格式不受支持
- 上传过程中出现错误
- 文件已被删除

请尝试重新上传文件，或联系系统管理员获取帮助。
"""
                }
            
            # 如果有上传文件，获取文件信息
            file_path, file_type, file_content = latest_file_info
            filename = os.path.basename(file_path)
            
            # 根据文件类型返回不同的回复
            if file_type in ['xlsx', 'xls', 'xlsm', 'ods', 'csv']:
                file_type_desc = "Excel/CSV表格文件"
            elif file_type in ['pdf', 'docx', 'txt']:
                file_type_desc = "文本文档"
            elif file_type in ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif']:
                file_type_desc = "图像文件"
            else:
                file_type_desc = f"{file_type}类型文件"
            
            # 使用大模型生成文件内容查看的回复
            from .llm_interface import call_llm_api
            
            # 构建用户提示词
            user_prompt = f"""
用户询问了查看上传文件的内容。

文件信息:
- 文件名: {filename}
- 文件类型: {file_type_desc}
- 文件路径: {file_path}

请生成一个友好、专业的回复，告知用户如何查看和分析这个文件的内容。
回复应包括：
1. 确认已找到的文件信息
2. 查看文件内容的不同方式（API、聊天询问等）
3. 根据文件类型提供的不同功能说明
4. 鼓励用户进一步探索文件内容的建议

请使用Markdown格式组织回复。
"""
            
            # 调用大模型生成回复
            llm_response = call_llm_api(FILE_CONTENT_PROMPT, user_prompt)
            
            if llm_response:
                return {
                    'type': 'knowledge_base',
                    'content': llm_response
                }
            else:
                # 如果大模型调用失败，使用备用回复
                return {
                    'type': 'knowledge_base',
                    'content': f"""
## 查看上传文件内容

系统检测到您已上传了一个{file_type_desc}：**{filename}**

您可以通过以下方式查看该文件内容：

1. **直接访问查看文件API**：
   - 访问 `/view_document` 接口可以查看该文件的内容
   - 该接口会返回文件的基本信息和内容预览

2. **在AI聊天中询问**：
   - 您可以直接询问"分析我上传的文件"或"查看我的{file_type}数据"
   - 系统会自动处理您上传的文件并返回分析结果

3. **文件类型支持**：
   - Excel/CSV文件：显示表格数据和基本统计信息
   - PDF/Word/文本文件：显示文本内容
   - 图像文件：提供图像预览链接

需要更详细的分析吗？请告诉我您想了解文件的哪些具体方面。
"""
                }
        
        # 其他知识库查询
        else:
            return {
                "type": "knowledge_base",
                "content": "抱歉,我暂时无法理解您的问题。请尝试用不同的方式提问,或者提供更多细节。"
            }
            
    except Exception as e:
        print(f"处理知识库查询时出错: {str(e)}")
        return {
            "type": "error", 
            "content": f"处理查询时发生错误: {str(e)}"
        } 