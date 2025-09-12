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
            response = self.llm_service.call_api(
                system_prompt=SQL_OPTIMIZATION_SYSTEM_PROMPT,
                user_message=SQL_OPTIMIZATION_USER_PROMPT.format(
                    sql_query=sql_query,
                    schema_info=schema_info
                )
            )
            
            print(f"优化查询LLM响应: {response}")
            
            try:
                # 尝试直接解析
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                print(f"JSON解析失败，尝试提取JSON部分...")
                # 尝试从响应中提取JSON部分
                json_match = re.search(r'(\{.*\})', response, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group(1))
                        print(f"成功从响应中提取JSON: {result}")
                        return result
                    except:
                        print("提取的内容不是有效JSON")
                else:
                    print("未找到JSON结构")
                
                # 返回原始SQL
                return {"sql": sql_query, "explanation": "优化失败，使用原始SQL"}
        except Exception as e:
            logger.error(f"SQL查询优化失败: {str(e)}")
            return {"error": str(e), "sql": sql_query}

class SQLService(BaseLLMService):
    """
    SQL服务类，处理SQL查询生成和分析
    """
    
    def __init__(self, db_path: str):
        super().__init__()
        self.db_path = db_path
        self._init_db()
        self._init_langchain_db()
        
        # 智能查询代理已移除，改为使用标准LangChain Agent架构
        
    def _init_db(self):
        """初始化数据库连接和表名映射"""
        try:
            self.query_cache = SQLQueryCache()
            self.query_optimizer = SQLQueryOptimizer(self)
            
            # 设置中文表名到英文表名的映射（基于实际数据库表结构）
            self.table_name_mapping = {
                '门诊记录': 'visits',
                '门诊量': 'visits', 
                '住院记录': 'admissions',
                '住院量': 'admissions',
                '手术记录': 'surgeries',
                '手术量': 'surgeries',
                '收入记录': 'revenue',
                '医疗收入': 'revenue',
                '警报信息': 'alerts',
                '科室工作量': 'department_workload',
                '科室效率': 'department_efficiency', 
                '科室资源': 'department_resources',
                '科室收入': 'department_revenue',
                '财务摘要': 'finance_summary',
                '用户信息': 'users',
                # 保留原有映射以防兼容性问题
                '医生信息': 'users',
                '患者信息': 'users', 
                '医院科室': 'department_workload',
                '疾病信息': 'admissions',
                '处方记录': 'visits',
                '治疗方案': 'visits',
                '检查结果': 'visits',
                '医疗费用': 'revenue'
            }
            
            # 建立反向映射
            self.reverse_mapping = {v: k for k, v in self.table_name_mapping.items()}
            
            print(f"数据库初始化成功: {self.db_path}")
            print(f"表名映射: {self.table_name_mapping}")
        except Exception as e:
            print(f"初始化数据库连接时出错: {str(e)}")
            traceback.print_exc()
    
    def map_table_names_in_sql(self, sql_query: str) -> str:
        """
        将SQL查询中的中文表名映射为实际的英文表名
        
        参数:
            sql_query: 包含中文表名的SQL查询
            
        返回:
            映射后的SQL查询
        """
        mapped_sql = sql_query
        for chinese_name, english_name in self.table_name_mapping.items():
            # 使用正则表达式来精确匹配表名，避免部分匹配
            import re
            pattern = r'\b' + re.escape(chinese_name) + r'\b'
            mapped_sql = re.sub(pattern, english_name, mapped_sql)
        
        print(f"SQL映射前: {sql_query}")
        print(f"SQL映射后: {mapped_sql}")
        return mapped_sql
        
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
            
            print(f"处理SQL查询: {user_message}")
            print(f"表名映射: {self.table_name_mapping}")
            
            # 通用数据库内容查询
            if any(keyword in user_message.lower() for keyword in ["看看数据库", "数据库有什么", "查看数据库"]):
                print("检测到查看数据库内容请求，使用预定义SQL")
                sql = "SELECT name FROM sqlite_master WHERE type='table'"
                explanation = "这个查询会列出数据库中所有的表"
                return {
                    'status': SQL_STATUS_CODES['success'],
                    'sql': sql,
                    'explanation': explanation,
                    'purpose': "查询数据库中包含的表",
                    'recommendations': []
                }
            
            # 检查特定表的查询
            if "门诊量" in user_message:
                print("检测到对门诊量表的查询")
                # 使用表名映射获取实际表名
                actual_table = self.table_name_mapping.get('门诊量', 'visits')
                sql = f"SELECT department, visit_type, DATE(visit_date) as date, COUNT(*) as count FROM {actual_table} GROUP BY department, visit_type, DATE(visit_date) LIMIT 10"
                explanation = f"这个查询会返回{actual_table}表中按科室和日期分组的门诊量统计"
                return {
                    'status': SQL_STATUS_CODES['success'],
                    'sql': sql,
                    'explanation': explanation,
                    'purpose': "查询门诊量数据统计",
                    'recommendations': []
                }
            
            if "目标值" in user_message:
                print("检测到对目标值表的查询")
                sql = "SELECT * FROM 目标值 LIMIT 10"
                explanation = "这个查询会返回目标值表中的前10条记录"
                return {
                    'status': SQL_STATUS_CODES['success'],
                    'sql': sql,
                    'explanation': explanation,
                    'purpose': "查询目标值表的数据",
                    'recommendations': []
                }
            
            # 如果是关于数据库表的基本查询，直接使用预定义的SQL
            if any(keyword in user_message.lower() for keyword in ["表", "tables", "数据库里有什么", "数据库结构"]):
                print("检测到基本数据库结构查询，使用预定义SQL")
                sql = "SELECT name FROM sqlite_master WHERE type='table'"
                explanation = "这个查询会列出数据库中所有的表"
                return {
                    'status': SQL_STATUS_CODES['success'],
                    'sql': sql,
                    'explanation': explanation,
                    'purpose': "查询数据库表结构",
                    'recommendations': []
                }
            
            # 使用SQL查询提示词
            prompt = f"""
请根据用户的请求和数据库结构生成一个SQL查询。

用户请求: {user_message}

数据库结构:
{schema_info}

请生成一个SQL查询来满足用户请求。只返回SQL查询语句，不要有其他任何内容。
注意：不要使用UNION或UNION ALL来合并不同结构的表。
"""
            
            # 调用LLM
            response = self.call_api(
                system_prompt="你是一个SQL专家，擅长将自然语言查询转换为精确的SQL语句。请只返回SQL查询语句，不要包含解释或其他内容。不要使用UNION或UNION ALL来合并不同结构的表。",
                user_message=prompt
            )
            
            print(f"LLM返回的SQL查询: {response}")
            
            # 清理响应，提取SQL
            sql = response.strip()
            
            # 移除可能的代码块标记
            sql = re.sub(r'```sql|```', '', sql).strip()
            
            # 验证SQL安全性
            if not sql or not sql.upper().startswith('SELECT'):
                return {
                    'status': SQL_STATUS_CODES['error'],
                    'message': SQL_ERROR_MESSAGES['invalid_query']
                }
            
            # 额外检查UNION ALL，避免表结构不一致的错误
            if "UNION ALL" in sql.upper() or "UNION" in sql.upper():
                print("检测到UNION操作，可能有风险，改为基本查询")
                return {
                    'status': SQL_STATUS_CODES['error'],
                    'message': "不支持UNION操作查询多个表，请分别查询每个表"
                }
            
            # 生成解释
            explanation_prompt = f"""
请解释以下SQL查询的含义:

SQL查询: {sql}

用户请求: {user_message}

请提供简洁的解释，说明这个SQL查询的作用和它如何满足用户的请求。
"""
            explanation = self.call_api(
                system_prompt="你是一个SQL专家，擅长解释SQL查询的含义。",
                user_message=explanation_prompt
            )
            
            return {
                'status': SQL_STATUS_CODES['success'],
                'sql': sql,
                'explanation': explanation,
                'purpose': f"满足用户请求: {user_message}",
                'recommendations': []
            }
            
        except Exception as e:
            logger.error(f"生成SQL查询失败: {str(e)}")
            traceback.print_exc()
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
            try:
                results = execute_query(sql)
                print(f"SQL查询执行结果: {results}")
            except Exception as query_error:
                print(f"执行SQL查询失败: {str(query_error)}")
                traceback.print_exc()
                return {
                    'status': SQL_STATUS_CODES['error'],
                    'message': SQL_ERROR_MESSAGES['execution_failed'].format(str(query_error))
                }
            
            # 分析结果
            analysis_result = {
                'analysis': f"查询返回了 {len(results) if results else 0} 条记录",
                'summary': self._generate_result_summary(sql, results)
            }
            
            return {
                'status': SQL_STATUS_CODES['success'],
                'results': results,
                'analysis': analysis_result
            }
            
        except Exception as e:
            logger.error(f"执行SQL查询失败: {str(e)}")
            traceback.print_exc()
            return {
                'status': SQL_STATUS_CODES['error'],
                'message': SQL_ERROR_MESSAGES['execution_failed'].format(str(e))
            }
    
    def _generate_result_summary(self, sql: str, results: List[Dict[str, Any]]) -> str:
        """生成结果摘要"""
        try:
            if not results:
                return "查询没有返回任何结果。"
            
            # 特殊处理表名查询
            if "sqlite_master" in sql and "type='table'" in sql:
                tables = [row.get('name', '') for row in results if row.get('name')]
                chinese_names = []
                for table in tables:
                    if table in self.reverse_mapping:
                        chinese_names.append(f"{table} ({self.reverse_mapping[table]})")
                    else:
                        chinese_names.append(table)
                
                return f"数据库中包含以下表: {', '.join(chinese_names)}"
            
            # 常规结果摘要
            columns = list(results[0].keys()) if results else []
            summary = f"查询返回了 {len(results)} 条记录，包含以下字段: {', '.join(columns)}。\n"
            
            # 添加简短的样本数据
            if len(results) > 0:
                sample = results[0]
                sample_str = ", ".join([f"{k}: {v}" for k, v in sample.items()])
                summary += f"数据样例: {sample_str}"
            
            return summary
        except Exception as e:
            print(f"生成结果摘要失败: {str(e)}")
            return f"查询返回了 {len(results) if results else 0} 条记录。"
    
    def process_query(self, user_message: str) -> Optional[Dict[str, Any]]:
        """处理用户查询"""
        try:
            from app.services.query_service import create_response
            
            print("使用标准SQL生成方法...")
            
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
            response = self.call_api(
                system_prompt=SQL_RESULT_ANALYSIS_SYSTEM_PROMPT,
                user_message=SQL_RESULT_ANALYSIS_USER_PROMPT.format(
                    sql_query=sql_query,
                    query_results=json.dumps(results, ensure_ascii=False)
                )
            )
            
            print(f"分析结果LLM响应: {response}")
            
            try:
                # 尝试直接解析
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                print(f"JSON解析失败，尝试提取JSON部分...")
                # 尝试从响应中提取JSON部分
                json_match = re.search(r'(\{.*\})', response, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group(1))
                        print(f"成功从响应中提取JSON: {result}")
                        return result
                    except:
                        print("提取的内容不是有效JSON")
                else:
                    print("未找到JSON结构")
                
                # 创建简单的分析结果
                return {
                    "analysis": f"查询返回了 {len(results)} 条记录",
                    "summary": response
                }
        except Exception as e:
            logger.error(f"SQL结果分析失败: {str(e)}")
            return {"error": str(e), "analysis": f"查询返回了 {len(results)} 条记录"}
    
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