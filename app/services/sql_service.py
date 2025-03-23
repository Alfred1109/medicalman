"""
SQL服务模块 - 处理SQL查询生成和分析
"""
import json
import re
import traceback
from typing import Dict, Any, Optional

from app.services.base_llm_service import BaseLLMService
from app.utils.db import get_database_schema
from app.prompts import DATABASE_SYSTEM_PROMPT

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
    
    def generate_sql(self, user_message: str) -> Optional[Dict[str, Any]]:
        """
        分析用户查询并生成SQL
        
        参数:
            user_message: 用户消息
            
        返回:
            包含SQL查询和解释的字典，如果失败则返回None
        """
        try:
            # 获取数据库模式
            schema = get_database_schema()
            
            # 使用自定义SQL查询提示词
            prompt_template = """
请根据以下医疗数据需求，设计精确的SQL查询并以JSON格式返回：

数据需求：{request}

数据库结构信息：
{schema_info}

要求：
1. 设计能够准确回答上述需求的SQL查询语句
2. 提供查询设计的医学解释
3. 说明查询结果的预期用途和解读方法
4. 如有必要，建议后续优化或扩展查询的方向

返回格式必须是严格的JSON格式，示例如下：
```json
{
  "sql": "SELECT patient_id, diagnosis, treatment_date FROM patients WHERE age > 60 ORDER BY treatment_date DESC",
  "explanation": "此查询筛选出60岁以上患者的诊断和治疗日期信息，按治疗日期降序排列",
  "purpose": "用于分析老年患者的诊断分布和治疗时间趋势",
  "recommendations": [
    "可考虑按性别分组进行进一步分析",
    "建议增加对治疗效果的统计分析"
  ]
}
```

请仅返回JSON格式的响应，不要添加任何其他文本或标记。确保JSON格式严格正确，所有属性名和字符串值使用双引号，数组元素用逗号分隔，没有多余的逗号。
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