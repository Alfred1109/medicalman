"""
SQL服务模块 - 处理SQL查询生成和分析
"""
import json
import re
import traceback
from typing import Dict, Any, Optional
from flask import current_app
import sqlite3

from app.services.base_llm_service import BaseLLMService
from app.utils.database import get_database_schema
from app.prompts import DATABASE_SYSTEM_PROMPT

# 导入LangChain相关库
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

class SQLService(BaseLLMService):
    """
    SQL服务类，处理SQL查询生成和分析
    """
    
    def __init__(self, model_name=None, api_key=None, api_url=None):
        """
        初始化SQL服务
        
        参数:
            model_name: 模型名称，默认使用环境变量中的设置
            api_key: API密钥，默认使用环境变量中的设置
            api_url: API端点URL，默认使用环境变量中的设置
        """
        super().__init__(model_name, api_key, api_url)
        print(f"初始化SQLService，使用模型: {self.model_name}")
        
        # 初始化表名映射字典
        self.table_name_mapping = {
            "outpatient": "门诊量",
            "target": "目标值",
            "drg_records": "drg_records"
        }
        
        # 初始化LangChain SQLDatabase对象
        self._init_langchain_db()
    
    def _init_langchain_db(self):
        """初始化LangChain SQLDatabase对象"""
        try:
            db_path = current_app.config.get('DATABASE_PATH', 'medical_workload.db')
            self.langchain_db = SQLDatabase.from_uri(f"sqlite:///{db_path}", 
                                                     include_tables=list(self.table_name_mapping.values()))
            print(f"LangChain SQLDatabase初始化成功: {db_path}")
        except Exception as e:
            print(f"LangChain SQLDatabase初始化失败: {str(e)}")
            self.langchain_db = None
    
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
            template = """
            你是一个医疗数据库专家，需要将用户问题转换为SQL查询。
            
            数据库信息:
            {schema}
            
            注意: 
            1. 请使用中文表名和字段名。我们的表名是中文，如"门诊量"、"目标值"等。
            2. 在SQLite中，使用strftime('%Y-%m', 日期)来格式化日期。
            3. 确保生成的SQL语法正确且满足用户需求。
            
            用户问题: {question}
            
            必须仅返回有效的SQL查询语句，不要添加解释或其他文本。
            """
            
            prompt = ChatPromptTemplate.from_template(template)
            
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
            prompt = f"""
            请解释以下SQL查询的含义和目的:
            
            用户问题: {user_message}
            
            SQL查询:
            {sql_query}
            
            请给出简明的解释，说明查询的目的和结果含义。
            """
            
            explanation = self.call_api(
                system_prompt="你是一个医疗数据专家，擅长解释SQL查询的含义。",
                user_message=prompt,
                temperature=0.3,
                max_tokens=150
            )
            
            return explanation
        except Exception as e:
            print(f"生成SQL解释时出错: {str(e)}")
            return f"此查询用于分析{user_message}相关的数据。"
    
    def generate_sql(self, user_message: str) -> Optional[Dict[str, Any]]:
        """
        分析用户查询并生成SQL
        
        参数:
            user_message: 用户消息
            
        返回:
            包含SQL查询和解释的字典，如果失败则返回None
        """
        # 尝试使用LangChain方法
        result = self.generate_sql_with_langchain(user_message)
        if result:
            return result
            
        # 以下为原始生成方法，作为备用
        try:
            # 获取数据库模式
            schema = get_database_schema()
            
            # 使用自定义SQL查询提示词
            prompt_template = """
请根据以下医疗数据需求，设计精确的SQL查询并以JSON格式返回：

数据需求：{request}

数据库结构信息：
{schema_info}

常用查询示例：
1. 查询门诊量的月度趋势：
   SELECT strftime('%Y-%m', 日期) as 月份, SUM(数量) as 总门诊量 
   FROM 门诊量 
   GROUP BY strftime('%Y-%m', 日期) 
   ORDER BY 月份

2. 查询各科室的门诊量趋势：
   SELECT 科室, strftime('%Y-%m', 日期) as 月份, SUM(数量) as 门诊量 
   FROM 门诊量 
   GROUP BY 科室, strftime('%Y-%m', 日期) 
   ORDER BY 科室, 月份

3. 查询门诊量与目标的完成情况：
   SELECT a.科室, a.专科, strftime('%Y-%m', a.日期) as 月份, 
          SUM(a.数量) as 实际量, b.目标值,
          ROUND(SUM(a.数量)*100.0/b.目标值, 2) as 完成率
   FROM 门诊量 a
   JOIN 目标值 b ON a.科室=b.科室 AND a.专科=b.专科
   WHERE strftime('%Y',a.日期)=b.年 AND strftime('%m',a.日期)=b.月
   GROUP BY a.科室, a.专科, 月份

要求：
1. 设计能够准确回答上述需求的SQL查询语句
2. 提供查询设计的医学解释
3. 说明查询结果的预期用途和解读方法
4. 如有必要，建议后续优化或扩展查询的方向

返回格式必须是严格的JSON格式，示例如下：
```json
{
  "sql": "SELECT strftime('%Y-%m', 日期) as 月份, SUM(数量) as 总门诊量 FROM 门诊量 GROUP BY strftime('%Y-%m', 日期) ORDER BY 月份",
  "explanation": "此查询计算每个月的总门诊人次，按月份排序，用于分析门诊量的时间趋势",
  "purpose": "用于了解医院门诊量的月度变化趋势，帮助医院进行资源规划和绩效评估",
  "recommendations": [
    "可进一步按科室分组，分析不同科室的门诊趋势",
    "可与目标值表联合查询，分析完成率情况"
  ]
}
```

请仅返回JSON格式的响应，不要添加任何其他文本或标记。确保JSON格式严格正确，所有属性名和字符串值使用双引号，数组元素用逗号分隔，没有多余的逗号。

对于门诊趋势分析，请确保查询能够按照日期进行分组和排序，以便展示随时间的变化情况。
"""
            
            # 使用更安全的字符串替换方式
            formatted_user_prompt = prompt_template.replace("{request}", user_message).replace("{schema_info}", schema)
            
            # 调用LLM
            response = self.call_api(
                system_prompt=DATABASE_SYSTEM_PROMPT,
                user_message=formatted_user_prompt,
                temperature=0.3,
                top_p=0.9
            )
            
            if not response:
                print("LLM回复为空")
                return None
            
            # 尝试从回复中提取JSON
            try:
                # 优化JSON内容匹配模式 - 支持更多格式
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```|(\{.*?\})', response, re.DOTALL)
                
                if json_match:
                    json_str = json_match.group(1) or json_match.group(2)
                    print(f"找到的JSON字符串: {json_str[:100]}...")
                    
                    try:
                        result = json.loads(json_str)
                        
                        # 验证JSON格式是否符合预期
                        if "sql" in result:
                            return result
                        else:
                            print("JSON中没有找到sql字段")
                            return None
                    except json.JSONDecodeError as je:
                        # 记录详细的错误信息
                        print(f"JSON解析错误: {str(je)}")
                        error_pos = je.pos
                        context_start = max(0, error_pos - 20)
                        context_end = min(len(json_str), error_pos + 20)
                        print(f"错误上下文: ...{json_str[context_start:error_pos]}>>>HERE>>>{json_str[error_pos:context_end]}...")
                        
                        # 尝试修复常见错误
                        # 1. 缺少逗号的情况
                        if "Expecting ',' delimiter" in str(je):
                            # 在错误位置插入逗号并尝试重新解析
                            fixed_json = json_str[:error_pos] + "," + json_str[error_pos:]
                            try:
                                result = json.loads(fixed_json)
                                if "sql" in result:
                                    print("修复了缺少逗号的SQL JSON")
                                    return result
                                else:
                                    print("修复后的JSON中没有sql字段")
                            except json.JSONDecodeError as second_je:
                                print(f"第一次修复失败: {str(second_je)}")
                                return None
                        return None
                else:
                    print("未能在回复中找到JSON内容")
                    return None
            except Exception as e:
                print(f"处理回复时出错: {str(e)}")
                traceback.print_exc()
                return None
        
        except Exception as e:
            print(f"生成SQL时发生错误: {str(e)}")
            traceback.print_exc()
            return None
    
    def validate_sql(self, sql_query: str) -> Dict[str, Any]:
        """
        验证SQL查询是否有效且安全
        
        参数:
            sql_query: 要验证的SQL查询
            
        返回:
            包含验证结果的字典
        """
        try:
            # 简单的SQL注入检测
            dangerous_patterns = [
                r'--', r';.*DROP', r';.*DELETE', r';.*UPDATE',
                r'UNION.*SELECT', r'INTO OUTFILE', r'INFORMATION_SCHEMA',
                r'EXEC\s+\w+', r'xp_cmdshell'
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, sql_query, re.IGNORECASE):
                    return {
                        "valid": False,
                        "safe": False,
                        "error": "查询可能包含SQL注入攻击模式",
                        "detected_pattern": pattern
                    }
            
            # 这里可以添加更多复杂的SQL验证逻辑
            # 例如检查表名和字段名是否存在于数据库模式中
            
            return {
                "valid": True,
                "safe": True
            }
        
        except Exception as e:
            print(f"验证SQL时出错: {str(e)}")
            return {
                "valid": False,
                "safe": False,
                "error": f"验证过程出错: {str(e)}"
            }
    
    def analyze_sql_results(self, sql_query: str, results: list, user_query: str) -> str:
        """
        分析SQL查询结果，提供解释和见解
        
        参数:
            sql_query: 执行的SQL查询
            results: 查询结果列表
            user_query: 原始用户查询
            
        返回:
            对结果的分析和解释
        """
        try:
            # 准备查询结果的摘要
            result_summary = f"查询返回了 {len(results)} 条记录。"
            
            # 准备样本数据（最多5条）
            sample_data = results[:5] if results else []
            sample_json = json.dumps(sample_data, ensure_ascii=False)
            
            # 创建提示词
            prompt = f"""
请分析以下SQL查询及其结果，并提供医学见解：

用户原始问题：
{user_query}

执行的SQL查询：
{sql_query}

查询结果摘要：
{result_summary}

结果样本（最多5条）：
{sample_json}

请提供：
1. 对查询结果的医学解读
2. 关键发现和趋势
3. 医学建议和后续分析方向
4. 结果如何回答用户的原始问题
"""
            
            # 调用LLM分析结果
            analysis = self.call_api(
                system_prompt="你是一位医疗数据分析专家，擅长解读SQL查询结果并提供医学见解。",
                user_message=prompt,
                temperature=0.4,
                top_p=0.9
            )
            
            return analysis or "无法分析查询结果。"
        
        except Exception as e:
            print(f"分析SQL结果时出错: {str(e)}")
            traceback.print_exc()
            return f"分析结果时发生错误: {str(e)}" 