"""
SQL服务模块 - 处理数据库查询和SQL生成
"""
import json
import re
import traceback
import logging
from typing import Dict, Any, Optional, List
from flask import current_app
import sqlite3
from functools import lru_cache
import hashlib
from datetime import datetime

from app.services.base_llm_service import BaseLLMService
from app.utils.database import get_database_schema, execute_query, validate_sql_query
from app.utils.utils import safe_json_dumps
from app.prompts import DATABASE_SYSTEM_PROMPT
from app.prompts.querying import (
    SQL_QUERY_SYSTEM_PROMPT,
    SQL_QUERY_USER_PROMPT,
    SQL_OPTIMIZATION_SYSTEM_PROMPT,
    SQL_OPTIMIZATION_USER_PROMPT,
    SQL_RESULT_ANALYSIS_SYSTEM_PROMPT,
    SQL_RESULT_ANALYSIS_USER_PROMPT,
    DATABASE_SCHEMA_PROMPT,
    SQL_META_PROMPT,
    SQL_GENERATION_TEMPLATE,
    SQL_EXPLANATION_PROMPT
)
from app.prompts.responding import (
    KB_RESPONSE_SYSTEM_PROMPT,
    KB_RESPONSE_USER_PROMPT
)
from app.config import config

# 初始化日志
logger = logging.getLogger(__name__)

# SQL状态码
SQL_STATUS_CODES = {
    'success': 'success',
    'error': 'error',
    'warning': 'warning',
    'info': 'info'
}

# SQL错误消息
SQL_ERROR_MESSAGES = {
    'invalid_query': '无效的SQL查询',
    'unsafe_query': '不安全的SQL查询，仅支持SELECT语句',
    'processing_failed': '处理SQL查询失败: {}',
    'execution_failed': '执行SQL查询失败: {}',
    'optimization_failed': '优化SQL查询失败: {}',
    'analysis_failed': '分析SQL查询结果失败: {}',
    'select_only': '仅支持SELECT语句',
    'validation_success': 'SQL查询验证通过',
    'validation_failed': 'SQL查询验证失败: {}'
}

# 导入LangChain相关库
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

class SQLQueryCache:
    """SQL查询缓存类"""
    def __init__(self):
        self.cache = {}
    
    def get(self, key: str) -> Optional[str]:
        """获取缓存的查询"""
        return self.cache.get(key)
    
    def set(self, key: str, value: str):
        """设置缓存的查询"""
        self.cache[key] = value
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()

class SQLQueryOptimizer:
    """
    SQL查询优化器类，用于智能生成和优化SQL查询
    """
    def __init__(self, llm_service):
        self.llm_service = llm_service
        
    def optimize_query(self, sql_query: str, schema_info: str) -> Dict[str, Any]:
        """优化SQL查询"""
        try:
            # 使用SQL优化提示词
            response = self.llm_service.generate_response(
                system_prompt=SQL_OPTIMIZATION_SYSTEM_PROMPT,
                user_prompt=SQL_OPTIMIZATION_USER_PROMPT.format(
                    sql_query=sql_query,
                    schema_info=schema_info
                )
            )
            return json.loads(response)
        except Exception as e:
            logger.error(f"SQL查询优化失败: {str(e)}")
            return {"error": str(e)}

class SQLService(BaseLLMService):
    """
    SQL服务类，处理SQL查询生成和分析
    """
    
    def __init__(self, db_path: str):
        super().__init__()
        self.db_path = db_path
        self._init_db()
        self._init_langchain_db()
        
    def _init_db(self):
        """初始化数据库连接和表名映射"""
        try:
            self.query_cache = SQLQueryCache()
            self.query_optimizer = SQLQueryOptimizer(self)
            
            # 设置中文表名到英文表名的映射
            self.table_name_mapping = {
                '门诊记录': 'outpatient_records', 
                '医生信息': 'doctor_info',
                '患者信息': 'patient_info',
                '医院科室': 'hospital_departments',
                '疾病信息': 'disease_info',
                '处方记录': 'prescription_records',
                '治疗方案': 'treatment_plans',
                '检查结果': 'examination_results',
                '手术记录': 'surgery_records',
                '医疗费用': 'medical_expenses'
            }
            
            # 建立反向映射
            self.reverse_mapping = {v: k for k, v in self.table_name_mapping.items()}
            
            print(f"数据库初始化成功: {self.db_path}")
            print(f"表名映射: {self.table_name_mapping}")
        except Exception as e:
            print(f"初始化数据库连接时出错: {str(e)}")
            traceback.print_exc()
        
    def _init_langchain_db(self):
        """初始化LangChain SQLDatabase对象"""
        try:
            db_path = current_app.config.get('DATABASE_PATH', config.DATABASE_PATH)
            self.langchain_db = SQLDatabase.from_uri(f"sqlite:///{db_path}", 
                                                     include_tables=list(self.table_name_mapping.values()))
            print(f"LangChain SQLDatabase初始化成功: {db_path}")
        except Exception as e:
            print(f"LangChain SQLDatabase初始化失败: {str(e)}")
            self.langchain_db = None
        
    def generate_sql(self, user_message: str) -> Optional[Dict[str, Any]]:
        """生成SQL查询"""
        try:
            # 获取数据库结构信息
            schema_info = get_database_schema(self.db_path)
            
            # 使用SQL查询提示词
            response = self.generate_response(
                system_prompt=SQL_QUERY_SYSTEM_PROMPT,
                user_prompt=SQL_QUERY_USER_PROMPT.format(
                    request=user_message,
                    schema_info=schema_info
                )
            )
            
            # 解析响应
            result = json.loads(response)
            
            # 验证SQL安全性
            if not result.get('sql') or not result['sql'].strip().upper().startswith('SELECT'):
                return {
                    'status': SQL_STATUS_CODES['error'],
                    'message': SQL_ERROR_MESSAGES['invalid_query']
                }
            
            # 优化查询
            optimization_result = self.query_optimizer.optimize_query(
                sql_query=result['sql'],
                schema_info=schema_info
            )
            
            if 'error' in optimization_result:
                return {
                    'status': SQL_STATUS_CODES['error'],
                    'message': SQL_ERROR_MESSAGES['optimization_failed'].format(optimization_result["error"])
                }
            
            return {
                'status': SQL_STATUS_CODES['success'],
                'sql': optimization_result.get('sql', result['sql']),
                'explanation': optimization_result.get('explanation', result.get('explanation')),
                'purpose': optimization_result.get('purpose', result.get('purpose')),
                'recommendations': optimization_result.get('recommendations', result.get('recommendations', []))
            }
            
        except Exception as e:
            logger.error(f"生成SQL查询失败: {str(e)}")
            return {
                'status': SQL_STATUS_CODES['error'],
                'message': SQL_ERROR_MESSAGES['processing_failed'].format(str(e))
            }
    
    def execute_query(self, sql: str) -> Optional[Dict[str, Any]]:
        """执行SQL查询"""
        try:
            # 验证SQL安全性
            if not validate_sql_query(sql):
                return {
                    'status': SQL_STATUS_CODES['error'],
                    'message': SQL_ERROR_MESSAGES['unsafe_query']
                }
            
            # 执行查询
            results = execute_query(self.db_path, sql)
            
            # 分析结果
            analysis_result = self.analyze_query_results(sql, results)
            
            if 'error' in analysis_result:
                return {
                    'status': SQL_STATUS_CODES['error'],
                    'message': SQL_ERROR_MESSAGES['analysis_failed'].format(analysis_result["error"])
                }
            
            return {
                'status': SQL_STATUS_CODES['success'],
                'results': results,
                'analysis': analysis_result
            }
            
        except Exception as e:
            logger.error(f"执行SQL查询失败: {str(e)}")
            return {
                'status': SQL_STATUS_CODES['error'],
                'message': SQL_ERROR_MESSAGES['execution_failed'].format(str(e))
            }
    
    def process_query(self, user_message: str) -> Optional[Dict[str, Any]]:
        """处理用户查询"""
        try:
            # 获取create_response函数
            from app.services.query_service import create_response
            
            # 生成SQL
            sql_result = self.generate_sql(user_message)
            if sql_result['status'] == 'error':
                return create_response(
                    success=False,
                    message=sql_result.get('message', '生成SQL失败'),
                    error=sql_result.get('message', '生成SQL失败'),
                    data={
                        'status': 'error',
                        'sql': sql_result.get('sql', ''),
                        'explanation': sql_result.get('explanation', '')
                    }
                )
            
            # 执行查询
            query_result = self.execute_query(sql_result['sql'])
            if query_result['status'] == 'error':
                return create_response(
                    success=False,
                    message=query_result.get('message', '执行SQL失败'),
                    error=query_result.get('message', '执行SQL失败'), 
                    data={
                        'status': 'error',
                        'sql': sql_result['sql'],
                        'explanation': sql_result.get('explanation', '')
                    }
                )
            
            # 构建成功响应
            formatted_response = f"""
查询结果:
{query_result.get('analysis', '')}

执行的SQL语句:
{sql_result['sql']}

{sql_result.get('explanation', '')}
            """
            
            # 使用create_response函数创建标准格式响应
            return create_response(
                success=True,
                message=formatted_response,
                data={
                    'status': 'success',
                    'sql': sql_result['sql'],
                    'explanation': sql_result.get('explanation'),
                    'purpose': sql_result.get('purpose'),
                    'recommendations': sql_result.get('recommendations', []),
                    'results': query_result['results'],
                    'analysis': query_result['analysis']
                },
                tables=query_result.get('tables'),
                charts=query_result.get('charts')
            )
            
        except Exception as e:
            logger.error(f"处理查询失败: {str(e)}")
            from app.services.query_service import create_response
            return create_response(
                success=False,
                message=f'处理查询失败: {str(e)}',
                error=str(e)
            )
    
    def validate_sql(self, sql_query: str) -> Dict[str, Any]:
        """
        验证SQL查询
        
        参数:
            sql_query: SQL查询语句
            
        返回:
            验证结果字典
        """
        try:
            # 验证SQL语法
            if not sql_query.strip().upper().startswith('SELECT'):
                return {
                    'status': SQL_STATUS_CODES['error'],
                    'message': SQL_ERROR_MESSAGES['select_only']
                }
            
            # 验证SQL安全性
            if not validate_sql_query(sql_query):
                return {
                    'status': SQL_STATUS_CODES['error'],
                    'message': SQL_ERROR_MESSAGES['unsafe_query']
                }
            
            return {
                'status': SQL_STATUS_CODES['success'],
                'message': SQL_ERROR_MESSAGES['validation_success']
            }
        except Exception as e:
            return {
                'status': SQL_STATUS_CODES['error'],
                'message': SQL_ERROR_MESSAGES['validation_failed'].format(str(e))
            }
    
    def analyze_query_results(self, sql_query: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析SQL查询结果"""
        try:
            # 使用SQL结果分析提示词
            response = self.generate_response(
                system_prompt=SQL_RESULT_ANALYSIS_SYSTEM_PROMPT,
                user_prompt=SQL_RESULT_ANALYSIS_USER_PROMPT.format(
                    sql_query=sql_query,
                    query_results=json.dumps(results, ensure_ascii=False)
                )
            )
            return json.loads(response)
        except Exception as e:
            logger.error(f"SQL结果分析失败: {str(e)}")
            return {"error": str(e)}
    
    def generate_sql_with_langchain(self, user_message: str) -> Optional[Dict[str, Any]]:
        """
        使用LangChain生成SQL查询
        
        参数:
            user_message: 用户消息
            
        返回:
            包含SQL查询和解释的字典，如果失败则返回None
        """
        try:
            if self.langchain_db is None:
                self._init_langchain_db()
                if self.langchain_db is None:
                    print("LangChain数据库初始化失败，回退到普通方法")
                    return self.generate_sql(user_message)
            
            # 创建SQL生成链
            prompt = ChatPromptTemplate.from_template(SQL_GENERATION_TEMPLATE)
            
            # 创建查询链
            chain = (
                prompt | 
                self._langchain_llm_invoke |
                StrOutputParser() 
            )
            
            # 执行链
            sql_query = chain.invoke({
                "schema": self.langchain_db.get_table_info(),
                "question": user_message
            })
            
            # 清理SQL查询
            sql_query = sql_query.strip()
            
            # 尝试从可能的JSON或Markdown格式中提取纯SQL
            if sql_query.startswith("```") or "{" in sql_query:
                # 尝试从Markdown代码块中提取
                md_match = re.search(r'```(?:sql)?\s*(.*?)\s*```', sql_query, re.DOTALL)
                if md_match:
                    sql_query = md_match.group(1).strip()
                
                # 尝试从JSON中提取
                json_match = re.search(r'"sql":\s*"(.*?)"', sql_query, re.DOTALL)
                if json_match:
                    sql_query = json_match.group(1).strip()
                    # 替换转义的引号
                    sql_query = sql_query.replace('\\"', '"')
                
                print(f"从复杂输出中提取SQL: {sql_query[:100]}...")
            
            # 最后验证是否为有效SQL
            if not sql_query.upper().startswith(("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER")):
                print(f"提取的SQL无效: {sql_query}")
                return None
            
            # 生成解释
            explanation = self._generate_sql_explanation(sql_query, user_message)
            
            return {
                "sql": sql_query,
                "explanation": explanation,
                "purpose": f"解答用户的问题：{user_message}",
                "recommendations": ["可以进一步按需求细化查询"]
            }
        
        except Exception as e:
            print(f"使用LangChain生成SQL时出错: {str(e)}")
            traceback.print_exc()
            return self.generate_sql(user_message)  # 回退到普通生成方法
    
    def _langchain_llm_invoke(self, prompt):
        """为LangChain链调用LLM"""
        try:
            # 确保prompt是字符串
            if not isinstance(prompt, str):
                # 尝试转换为字符串
                if hasattr(prompt, 'to_string'):
                    prompt = prompt.to_string()
                elif hasattr(prompt, 'to_messages'):
                    # 如果是ChatPromptValue，尝试获取消息
                    messages = prompt.to_messages()
                    prompt_text = ""
                    for msg in messages:
                        role = getattr(msg, 'type', 'unknown')
                        content = getattr(msg, 'content', '')
                        prompt_text += f"{role}: {content}\n"
                    prompt = prompt_text
                else:
                    prompt = str(prompt)
            
            response = self.call_api(
                system_prompt=DATABASE_SYSTEM_PROMPT,
                user_message=prompt,
                temperature=0.3,
                top_p=0.9
            )
            return response
        except Exception as e:
            print(f"LangChain LLM调用失败: {str(e)}")
            return f"系统发生错误: {str(e)}"
    
    def _generate_sql_explanation(self, sql_query: str, user_message: str) -> str:
        """生成SQL查询的解释"""
        try:
            # 使用LLM生成解释
            explanation = self.call_api(
                system_prompt=SQL_META_PROMPT,
                user_message=SQL_EXPLANATION_PROMPT.format(
                    user_message=user_message,
                    sql_query=sql_query
                ),
                temperature=0.3,
                max_tokens=150
            )
            
            return explanation
        except Exception as e:
            print(f"生成SQL解释时出错: {str(e)}")
            return f"此查询用于分析{user_message}相关的数据。" 