"""
大模型服务模块
"""
import json
import requests
import time
import traceback
import re
import os
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from dotenv import load_dotenv

# 获取项目根目录的绝对路径
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = ROOT_DIR / '.env'

# 明确指定.env文件路径
print(f"加载环境变量文件: {ENV_FILE}")
load_dotenv(dotenv_path=ENV_FILE)

# 直接设置API密钥，不依赖环境变量
VOLCENGINE_API_KEY = "3470059d-f774-4302-81e0-50fa017fea38"
VOLCENGINE_API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
VOLCENGINE_MODEL = "deepseek-v3-241226"
REQUEST_TIMEOUT = 30
MAX_RETRIES = 2
RETRY_DELAY = 1

from app.utils.db import get_database_schema
from app.prompts import (
    DATABASE_SYSTEM_PROMPT, DATABASE_USER_PROMPT,
    DATA_ANALYSIS_SYSTEM_PROMPT, DATA_ANALYSIS_USER_PROMPT,
    TEXT_ANALYSIS_SYSTEM_PROMPT, TEXT_ANALYSIS_USER_PROMPT,
    EXCEL_ANALYSIS_SYSTEM_PROMPT, EXCEL_ANALYSIS_USER_PROMPT,
    # 直接从app.prompts导入模块化提示词
    PARSING_SYSTEM_PROMPT, PARSING_USER_PROMPT,
    QUERY_SYSTEM_PROMPT, QUERY_USER_PROMPT,
    ANALYSIS_SYSTEM_PROMPT, ANALYSIS_USER_PROMPT,
    RESPONSE_SYSTEM_PROMPT, RESPONSE_USER_PROMPT
)
from app.utils.json_helper import robust_json_parser

class LLMService:
    """大模型服务类"""
    
    def __init__(self):
        """初始化LLMService"""
        # 设置模型名称
        self.sql_model = VOLCENGINE_MODEL  # 使用全局变量中定义的模型
        self.chart_model = VOLCENGINE_MODEL  # 使用同一个模型进行图表生成
        print(f"初始化LLMService，使用SQL模型: {self.sql_model}, 图表模型: {self.chart_model}")
    
    @staticmethod
    def call_llm_api(system_prompt: str, user_message: str, temperature=0.7, top_p=0.8, top_k=50, max_tokens=None) -> Optional[str]:
        """
        调用大模型API
        
        参数:
            system_prompt: 系统提示词
            user_message: 用户消息
            temperature: 温度参数，控制随机性
            top_p: 核采样概率
            top_k: 考虑的最高概率词汇数量
            max_tokens: 最大生成令牌数
            
        返回:
            AI的回复，如果失败则返回None
        """
        try:
            # 使用从环境变量加载的值
            api_key = VOLCENGINE_API_KEY
            api_url = VOLCENGINE_API_URL
            model = VOLCENGINE_MODEL
            timeout = REQUEST_TIMEOUT
            max_retries = MAX_RETRIES
            retry_delay = RETRY_DELAY
            
            print(f"使用API密钥: {api_key[:5]}...{api_key[-5:]}")
            print(f"使用API端点: {api_url}")
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k
            }
            
            # 如果提供了max_tokens，则添加到payload中
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            
            # 实现重试逻辑
            for attempt in range(max_retries + 1):
                try:
                    response = requests.post(
                        api_url,
                        headers=headers,
                        json=payload,
                        timeout=timeout
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        
                        if "choices" in response_data and len(response_data["choices"]) > 0:
                            return response_data["choices"][0]["message"]["content"]
                        else:
                            print(f"警告: API响应没有包含有效的选择: {response_data}")
                            return None
                    else:
                        print(f"警告: API返回状态码 {response.status_code}: {response.text}")
                        
                        # 如果不是最后一次尝试，则等待后重试
                        if attempt < max_retries:
                            time.sleep(retry_delay)
                            continue
                        else:
                            return None
                
                except requests.exceptions.RequestException as e:
                    print(f"API请求异常: {str(e)}")
                    
                    # 如果不是最后一次尝试，则等待后重试
                    if attempt < max_retries:
                        time.sleep(retry_delay)
                        continue
                    else:
                        return None
            
            return None
        
        except Exception as e:
            print(f"调用LLM API时发生错误: {str(e)}")
            print(f"错误堆栈: {traceback.format_exc()}")
            return None

    @staticmethod
    def analyze_user_query_and_generate_sql(user_message: str) -> Optional[Dict[str, Any]]:
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
            
            # 使用自定义SQL查询提示词，避免格式化问题
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
            
            # 使用更安全的字符串替换方式，确保替换的是完整的占位符
            formatted_user_prompt = prompt_template.replace("{request}", user_message).replace("{schema_info}", schema)
            
            # 调用LLM
            response = LLMService.call_llm_api(DATABASE_SYSTEM_PROMPT, formatted_user_prompt)
            
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
                                print(f"第一次修复失败，尝试更复杂的修复: {str(second_je)}")
                                # 尝试识别特定模式的错误
                                if '"name":' in json_str[max(0, error_pos-30):error_pos]:
                                    print("检测到name字段后可能缺少逗号，尝试更精确的修复")
                                    # 查找name字段所在的行
                                    lines = json_str.split('\n')
                                    fixed_lines = []
                                    for line in lines:
                                        if '"name":' in line and ',' not in line:
                                            fixed_lines.append(line + ',')
                                        else:
                                            fixed_lines.append(line)
                                    fixed_json = '\n'.join(fixed_lines)
                                    try:
                                        result = json.loads(fixed_json)
                                        if "sql" in result:
                                            print("通过修复name字段后缺少的逗号成功解析SQL JSON")
                                            return result
                                    except:
                                        print("修复name字段后依然解析失败")
                            except:
                                print("修复逗号后仍然解析失败")
                        # 2. 处理末尾多余逗号
                        elif "Expecting property name" in str(je) or "Expecting value" in str(je):
                            # 移除尾部逗号
                            fixed_json = re.sub(r',\s*}', '}', json_str)
                            fixed_json = re.sub(r',\s*]', ']', fixed_json)
                            try:
                                result = json.loads(fixed_json)
                                if "sql" in result:
                                    print("修复了多余逗号的SQL JSON")
                                    return result
                                else:
                                    print("修复后的JSON中没有sql字段")
                            except:
                                print("修复多余逗号后仍然解析失败")
                        else:
                            # 尝试通用修复方法
                            print("尝试通用JSON修复方法")
                            try:
                                # 使用正则表达式查找所有可能缺少逗号的位置
                                # 典型模式: 属性值后面直接跟着另一个属性名而没有逗号
                                fixed_json = re.sub(r'(\w"|\d|true|false|\])(\s*[{\[])', r'\1,\2', json_str)
                                fixed_json = re.sub(r'(\w"|\d|true|false|\])(\s*")', r'\1,\2', fixed_json)
                                
                                # 修复花引号不匹配的情况
                                quote_count = fixed_json.count('"')
                                if quote_count % 2 != 0:
                                    print(f"发现不匹配的引号，总数: {quote_count}")
                                    # 寻找可能缺少右引号的位置
                                    fixed_json = re.sub(r'([^\\])"([^"]*)([\s,}\]])', r'\1"\2"\3', fixed_json)
                                
                                try:
                                    result = json.loads(fixed_json)
                                    if "sql" in result:
                                        print("通过通用修复成功解析SQL JSON")
                                        return result
                                except:
                                    print("通用修复方法失败")
                            except Exception as general_ex:
                                print(f"通用修复方法异常: {str(general_ex)}")
                            
                            # 如果无法识别具体错误类型，回退到默认处理
                            print("无法修复JSON格式错误，尝试其他方法")
                else:
                    # 尝试直接从文本中提取JSON格式
                    # 首先尝试整个响应是否是有效的JSON
                    try:
                        result = json.loads(response)
                        if "sql" in result:
                            print("整个响应是有效的SQL JSON")
                            return result
                    except:
                        pass
                    
                    # 尝试使用正则匹配更复杂的模式
                    json_pattern = re.compile(r'{(?:[^{}]|"(?:\\.|[^"\\])*"|\[(?:[^\[\]]|"(?:\\.|[^"\\])*")*\])*}', re.DOTALL)
                    matches = json_pattern.findall(response)
                    
                    if matches:
                        for match in matches:
                            try:
                                result = json.loads(match)
                                if "sql" in result:
                                    print("从正则匹配中找到有效的SQL JSON")
                                    return result
                            except json.JSONDecodeError as je:
                                # 尝试修复此匹配的JSON
                                if "Expecting ',' delimiter" in str(je):
                                    error_pos = je.pos
                                    fixed_json = match[:error_pos] + "," + match[error_pos:]
                                    try:
                                        result = json.loads(fixed_json)
                                        if "sql" in result:
                                            print("修复了正则匹配JSON中缺少的逗号")
                                            return result
                                    except:
                                        pass
                            except:
                                continue
                    
                    # 如果所有尝试都失败，尝试使用花括号计数法
                    start_pos = response.find('{')
                    if start_pos >= 0:
                        for end_pos in range(len(response), start_pos, -1):
                            try:
                                substr = response[start_pos:end_pos]
                                if substr.count('{') == substr.count('}'):
                                    try:
                                        result = json.loads(substr)
                                        if "sql" in result:
                                            print("使用花括号计数法找到有效的SQL JSON")
                                            return result
                                    except json.JSONDecodeError as je:
                                        if "Expecting ',' delimiter" in str(je):
                                            error_pos = je.pos
                                            fixed_json = substr[:error_pos] + "," + substr[error_pos:]
                                            try:
                                                result = json.loads(fixed_json)
                                                if "sql" in result:
                                                    print("修复了子串中缺少的逗号")
                                                    return result
                                            except:
                                                pass
                                    except:
                                        continue
                            except:
                                continue
                    
                    # 如果所有尝试都失败
                    print("LLM回复中没有找到JSON格式的内容")
                    print(f"原始回复: {response}")  # 打印完整回复用于调试
                    return None
                    
            except Exception as e:
                print(f"分析用户查询时出错: {str(e)}")
                print(f"错误堆栈: {traceback.format_exc()}")
                return None
                
        except Exception as e:
            print(f"分析用户查询时出错: {str(e)}")
            print(f"错误堆栈: {traceback.format_exc()}")
            return None

    @staticmethod
    def generate_data_analysis(data: Dict[str, Any], user_query: str) -> Optional[Dict[str, Any]]:
        """
        生成数据分析结果
        
        参数:
            data: 数据
            user_query: 用户查询
            
        返回:
            分析结果，如果失败则返回None
        """
        try:
            # 将数据转换为JSON字符串
            data_json = json.dumps(data, ensure_ascii=False)
            
            # 使用预定义的提示词模板
            formatted_user_prompt = DATA_ANALYSIS_USER_PROMPT.format(
                user_query=user_query,
                data_json=data_json
            )
            
            # 调用大模型API
            analysis_result = LLMService.call_llm_api(DATA_ANALYSIS_SYSTEM_PROMPT, formatted_user_prompt)
            
            if analysis_result:
                # 尝试提取JSON格式的图表建议
                charts = []
                
                try:
                    # 查找JSON内容的模式 - 匹配 ```json ... ``` 或 { ... }
                    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```|(\{.*?\})', analysis_result, re.DOTALL)
                    
                    if json_match:
                        json_str = json_match.group(1) or json_match.group(2)
                        # 记录原始JSON字符串，帮助调试
                        print(f"找到的JSON字符串: {json_str[:200]}...")
                        
                        # 尝试修复常见的JSON格式错误
                        try:
                            chart_data = json.loads(json_str)
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
                                    chart_data = json.loads(fixed_json)
                                    print("修复了缺少逗号的JSON")
                                except:
                                    print("修复逗号后仍然解析失败")
                                    chart_data = None
                            # 2. 处理末尾多余逗号
                            elif "Expecting property name" in str(je) or "Expecting value" in str(je):
                                # 移除尾部逗号
                                fixed_json = re.sub(r',\s*}', '}', json_str)
                                fixed_json = re.sub(r',\s*]', ']', fixed_json)
                                try:
                                    chart_data = json.loads(fixed_json)
                                    print("修复了多余逗号的JSON")
                                except:
                                    print("修复多余逗号后仍然解析失败")
                                    chart_data = None
                            else:
                                # 如果无法识别具体错误类型，进行启发式修复
                                print("尝试通用JSON修复")
                                try:
                                    import ast
                                    # 尝试将字符串字面量解析为字典，然后转回JSON
                                    ast_dict = ast.literal_eval(json_str)
                                    chart_data = ast_dict
                                    print("使用AST成功解析JSON")
                                except:
                                    # 如果所有修复都失败，则返回空结果
                                    print("无法修复JSON格式错误")
                                    chart_data = None
                        
                        if chart_data and "charts" in chart_data:
                            charts = chart_data["charts"]
                            # 验证charts结构的正确性
                            if charts and isinstance(charts, list):
                                valid_charts = []
                                for chart in charts:
                                    if isinstance(chart, dict) and "type" in chart:
                                        # 确保必要的字段存在
                                        if "xAxis" not in chart:
                                            chart["xAxis"] = {"data": [], "name": ""}
                                        if "yAxis" not in chart:
                                            chart["yAxis"] = {"name": ""}
                                        if "series" not in chart or not chart["series"]:
                                            chart["series"] = [{"name": "数据", "data": [], "type": chart["type"]}]
                                        valid_charts.append(chart)
                                charts = valid_charts
                                print(f"成功解析 {len(charts)} 个有效图表配置")
                    
                    else:
                        # 尝试直接从文本中提取JSON格式 - 使用更强大的匹配模式
                        try:
                            # 使用更复杂的模式匹配嵌套JSON
                            # 寻找可能的JSON对象起始位置
                            start_pos = analysis_result.find('{')
                            if start_pos >= 0 and not charts:
                                # 从找到的起始位置开始，尝试不同长度的子串
                                for end_pos in range(len(analysis_result), start_pos, -1):
                                    try:
                                        substr = analysis_result[start_pos:end_pos]
                                        # 确保花括号是匹配的
                                        if substr.count('{') == substr.count('}'):
                                            # 记录尝试解析的子串
                                            print(f"尝试解析JSON子串 (长度: {len(substr)}): {substr[:100]}...")
                                            
                                            try:
                                                chart_data = json.loads(substr)
                                            except json.JSONDecodeError as je:
                                                # 记录错误信息
                                                print(f"子串JSON解析错误: {str(je)}")
                                                error_pos = je.pos
                                                context_start = max(0, error_pos - 20)
                                                context_end = min(len(substr), error_pos + 20)
                                                print(f"错误上下文: ...{substr[context_start:error_pos]}>>>HERE>>>{substr[error_pos:context_end]}...")
                                                
                                                # 应用相同的修复逻辑
                                                if "Expecting ',' delimiter" in str(je):
                                                    fixed_json = substr[:error_pos] + "," + substr[error_pos:]
                                                    try:
                                                        chart_data = json.loads(fixed_json)
                                                        print("修复了子串中缺少逗号的JSON")
                                                    except:
                                                        print("修复逗号后仍然解析失败")
                                                        chart_data = None
                                                        continue
                                                elif "Expecting property name" in str(je) or "Expecting value" in str(je):
                                                    fixed_json = re.sub(r',\s*}', '}', substr)
                                                    fixed_json = re.sub(r',\s*]', ']', fixed_json)
                                                    try:
                                                        chart_data = json.loads(fixed_json)
                                                        print("修复了子串中多余逗号的JSON")
                                                    except:
                                                        print("修复多余逗号后仍然解析失败")
                                                        chart_data = None
                                                        continue
                                                else:
                                                    # 其他类型的错误，继续尝试下一个长度
                                                    continue
                                            
                                            if chart_data and "charts" in chart_data:
                                                # 验证charts结构
                                                potential_charts = chart_data["charts"]
                                                if potential_charts and isinstance(potential_charts, list):
                                                    valid_charts = []
                                                    for chart in potential_charts:
                                                        if isinstance(chart, dict) and "type" in chart:
                                                            # 确保必要的字段存在
                                                            if "xAxis" not in chart:
                                                                chart["xAxis"] = {"data": [], "name": ""}
                                                            if "yAxis" not in chart:
                                                                chart["yAxis"] = {"name": ""}
                                                            if "series" not in chart or not chart["series"]:
                                                                chart["series"] = [{"name": "数据", "data": [], "type": chart["type"]}]
                                                            valid_charts.append(chart)
                                                    
                                                    if valid_charts:
                                                        charts = valid_charts
                                                        print(f"从子串中成功解析 {len(charts)} 个有效图表配置")
                                        break
                                    except Exception as parse_ex:
                                        # 这里捕获除了JSON解析错误以外的其他异常
                                        print(f"从子串中解析图表时出现错误，尝试继续解析")
                                        print(f"图表解析错误详情: {str(parse_ex)}")
                                        print(f"当前图表子串: {substr[:200]}...")
                                        continue
                        except Exception as json_ex:
                            print(f"图表JSON提取过程出错: {str(json_ex)}")
                except Exception as e:
                    print(f"解析图表JSON时出错: {str(e)}")
                    print(f"分析结果前100个字符: {analysis_result[:100]}...")
                
                # 清除分析文本中的JSON部分，避免在UI中显示原始JSON
                analysis_text = re.sub(r'```(?:json)?\s*{.*?}\s*```', '', analysis_result, flags=re.DOTALL)
                analysis_text = re.sub(r'{.*"charts":\s*\[.*\].*}', '', analysis_text, flags=re.DOTALL)
                
                return {
                    'analysis': analysis_text.strip(),
                    'original_data': data,
                    'query': user_query,
                    'charts': charts
                }
            
            return None
            
        except Exception as e:
            print(f"生成数据分析时出错: {str(e)}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def generate_text_analysis(text_content: str, user_query: str, metadata=None, structured_data=None, file_type="文本文件", file_name="未命名文件") -> Optional[str]:
        """
        根据文本内容和用户查询生成分析结果
        
        参数:
            text_content: 要分析的文本内容
            user_query: 用户查询
            metadata: 文件元数据（可选）
            structured_data: 结构化数据（可选）
            file_type: 文件类型（可选）
            file_name: 文件名称（可选）
            
        返回:
            分析结果
        """
        from app.prompts.file_analysis import FILE_ANALYSIS_SYSTEM_PROMPT, FILE_ANALYSIS_USER_PROMPT
        
        # 如果文本内容太长，则截断（避免超出token限制）
        max_text_length = 10000
        if len(text_content) > max_text_length:
            truncated_text = text_content[:max_text_length] + f"\n\n[注意：原文档内容过长，已截断。总长度：{len(text_content)}字符]"
        else:
            truncated_text = text_content
            
        # 准备结构化数据信息
        structured_data_info = ""
        if structured_data:
            if isinstance(structured_data, dict) and 'type' in structured_data:
                if structured_data['type'] == 'dataframe':
                    table_info = f"文件包含表格数据（共{structured_data.get('total_rows', '未知')}行数据，字段包括：{', '.join(structured_data.get('columns', []))}）"
                    structured_data_info = f"文件包含结构化数据：\n{table_info}"
                elif structured_data['type'] == 'json':
                    structured_data_info = "文件包含JSON格式的结构化数据"
            else:
                structured_data_info = "文件包含部分结构化数据"
        
        # 准备元数据信息
        metadata_str = "无可用元数据"
        if metadata and isinstance(metadata, dict):
            metadata_parts = []
            # 提取关键元数据
            for key in ['size', 'created', 'modified', 'page_count', 'author', 'rows', 'sheet_count', 'paragraph_count', 'document_info']:
                if key in metadata:
                    if key == 'size':
                        size_kb = metadata[key] / 1024
                        metadata_parts.append(f"大小: {size_kb:.1f}KB")
                    elif key == 'document_info' and isinstance(metadata[key], dict):
                        doc_info = metadata[key]
                        for doc_key in ['author', 'title', 'created', 'modified']:
                            if doc_key in doc_info:
                                metadata_parts.append(f"{doc_key}: {doc_info[doc_key]}")
                    else:
                        metadata_parts.append(f"{key}: {metadata[key]}")
            
            if metadata_parts:
                metadata_str = ", ".join(metadata_parts)
        
        # 填充提示模板
        user_prompt = FILE_ANALYSIS_USER_PROMPT.format(
            file_content=truncated_text,
            user_query=user_query,
            file_type=file_type,
            file_name=file_name,
            metadata=metadata_str,
            structured_data_info=structured_data_info
        )
        
        # 调用LLM API
        response = LLMService.call_llm_api(
            system_prompt=FILE_ANALYSIS_SYSTEM_PROMPT,
            user_message=user_prompt,
            temperature=0.3,
            top_p=0.95,
            max_tokens=1500
        )
        
        return response 

    def generate_modular_response(self, content_type, content, query, analysis_type=None, analysis_results=None):
        """
        使用模块化提示词生成回复
        
        根据提供的内容类型和分析类型，选择合适的模块组合生成回复
        
        Args:
            content_type: 内容类型 (如 "文档", "数据", "查询结果")
            content: 待处理的内容
            query: 用户查询
            analysis_type: 分析类型 (如 "医疗文档", "临床数据", "统计结果")  
            analysis_results: 分析结果（如果已有）
            
        Returns:
            生成的回复
        """
        # 如果需要解析和分析
        if analysis_results is None and content:
            # 首先解析内容
            parsing_user_prompt = PARSING_USER_PROMPT.format(
                content_type=content_type,
                content=content
            )
            
            parsed_result = self.call_llm_api(
                system_prompt=PARSING_SYSTEM_PROMPT,
                user_message=parsing_user_prompt,
                temperature=0.2
            )
            
            # 然后分析解析结果
            analysis_user_prompt = ANALYSIS_USER_PROMPT.format(
                data_type=content_type,
                data=parsed_result,
                analysis_request=query
            )
            
            analysis_results = self.call_llm_api(
                system_prompt=ANALYSIS_SYSTEM_PROMPT,
                user_message=analysis_user_prompt,
                temperature=0.3
            )
        
        # 最后生成回复
        response_user_prompt = RESPONSE_USER_PROMPT.format(
            analysis_type=analysis_type or content_type,
            analysis_results=analysis_results or content,
            user_query=query
        )
        
        return self.call_llm_api(
            system_prompt=RESPONSE_SYSTEM_PROMPT,
            user_message=response_user_prompt,
            temperature=0.5
        )

    def generate_query(self, query_type, request, schema_info=""):
        """
        生成查询语句
        
        Args:
            query_type: 查询类型 (如 "SQL", "知识库", "文档检索")
            request: 查询请求
            schema_info: 数据库结构信息（对SQL查询） 
            
        Returns:
            生成的查询语句
        """
        query_user_prompt = QUERY_USER_PROMPT.format(
            query_type=query_type,
            request=request,
            schema_info=schema_info
        )
        
        return self.call_llm_api(
            system_prompt=QUERY_SYSTEM_PROMPT,
            user_message=query_user_prompt,
            temperature=0.2
        ) 

    def extract_chart_configs(self, content: str) -> list:
        """
        从LLM响应中提取图表配置
        
        参数:
            content: LLM响应内容
            
        返回:
            提取的图表配置列表
        """
        chart_configs = []
        
        # 尝试直接解析整个响应内容
        try:
            # 首先清理响应，移除Markdown代码块标记和其他非JSON内容
            print(f"原始响应内容 (前200字符): {content[:200]}...")
            
            # 尝试提取JSON代码块
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
            cleaned_content = json_match.group(1) if json_match else content
            
            # 移除可能的前导和尾随文本，只保留JSON部分
            json_start = cleaned_content.find('{')
            if json_start >= 0:
                # 尝试找到匹配的右大括号
                open_count = 1
                for i in range(json_start + 1, len(cleaned_content)):
                    if cleaned_content[i] == '{':
                        open_count += 1
                    elif cleaned_content[i] == '}':
                        open_count -= 1
                    if open_count == 0:
                        # 找到匹配的结束括号
                        json_str = cleaned_content[json_start:i+1]
                        break
            
            # 使用健壮的JSON解析器处理可能的格式问题
            print(f"尝试解析JSON: {cleaned_content[:200]}...")
            json_obj = robust_json_parser(cleaned_content)
            
            if json_obj:
                # 如果整个响应是有效的JSON，尝试提取charts字段
                if isinstance(json_obj, dict) and 'charts' in json_obj:
                    charts = json_obj.get('charts', [])
                    if charts and isinstance(charts, list):
                        for chart in charts:
                            # 确保chart是有效的配置
                            if self._validate_chart_config(chart):
                                chart_configs.append(chart)
                # 如果整个响应是一个图表数组
                elif isinstance(json_obj, list):
                    for chart in json_obj:
                        if self._validate_chart_config(chart):
                            chart_configs.append(chart)
                # 如果整个响应本身就是一个单一图表
                elif isinstance(json_obj, dict) and self._validate_chart_config(json_obj):
                    chart_configs.append(json_obj)
            
            # 打印判断结果
            if chart_configs:
                print(f"成功提取了 {len(chart_configs)} 个图表配置")
            else:
                print("未能从JSON中提取到有效的图表配置")
                
        except Exception as e:
            # 记录解析错误
            print(f"从整个响应提取图表配置失败: {str(e)}")
            traceback.print_exc()
        
        # 如果通过健壮解析器无法获取有效配置，则使用更严格的提取方法
        if not chart_configs:
            print("尝试使用备用方法提取图表配置...")
            try:
                # 尝试找到charts数组的定义部分
                charts_match = re.search(r'"charts"\s*:\s*\[([\s\S]*?)\]', content)
                if charts_match:
                    charts_str = charts_match.group(1)
                    # 提取单个图表对象
                    chart_objects = []
                    bracket_count = 0
                    start_pos = None
                    
                    for i, char in enumerate(charts_str):
                        if char == '{' and bracket_count == 0:
                            start_pos = i
                            bracket_count += 1
                        elif char == '{':
                            bracket_count += 1
                        elif char == '}':
                            bracket_count -= 1
                            if bracket_count == 0 and start_pos is not None:
                                chart_objects.append(charts_str[start_pos:i+1])
                                start_pos = None
                    
                    # 使用robust_json_parser处理每个图表对象
                    for chart_str in chart_objects:
                        try:
                            chart = robust_json_parser("{" + chart_str + "}")
                            if chart and self._validate_chart_config(chart):
                                chart_configs.append(chart)
                        except Exception as chart_e:
                            print(f"解析单个图表时出错: {str(chart_e)}")
                
                # 如果仍未提取到图表，尝试其他方法
                if not chart_configs:
                    # 查找可能的图表定义模式
                    chart_pattern = r'{\s*"title"[^}]*"type"[^}]*"xAxis"[^}]*"yAxis"[^}]*"series"[^}]*}'
                    chart_matches = re.findall(chart_pattern, content, re.DOTALL)
                    
                    for chart_str in chart_matches:
                        try:
                            chart = robust_json_parser(chart_str)
                            if chart and self._validate_chart_config(chart):
                                chart_configs.append(chart)
                        except Exception as chart_e:
                            print(f"解析匹配的图表时出错: {str(chart_e)}")
            
            except Exception as e:
                print(f"备用提取方法失败: {str(e)}")
                traceback.print_exc()
        
        return chart_configs

    def _validate_chart_config(self, chart: dict) -> bool:
        """
        验证图表配置的有效性并修复简单问题
        
        参数:
            chart: 图表配置字典
            
        返回:
            如果配置有效则返回True，否则返回False
        """
        try:
            if not isinstance(chart, dict):
                print(f"图表配置不是有效的字典对象: {type(chart)}")
                return False
            
            # 检查必要字段
            required_fields = ['type', 'series']
            if not all(field in chart for field in required_fields):
                missing = [field for field in required_fields if field not in chart]
                print(f"图表配置缺少必要字段: {missing}")
                return False
            
            # 确保有标题，如果没有则添加默认标题
            if 'title' not in chart:
                chart['title'] = "数据分析图表"
                print("添加了默认标题")
            
            # 检查图表类型是否为支持的类型
            supported_types = ['line', 'bar', 'pie', 'scatter', 'radar', 'funnel', 'gauge', 'heatmap']
            if chart['type'] not in supported_types:
                print(f"不支持的图表类型 '{chart.get('type')}'，使用默认的'bar'类型")
                chart['type'] = 'bar'  # 使用默认的柱状图类型
            
            # 检查series是否为列表且不为空
            if not isinstance(chart.get('series'), list):
                print("series不是列表类型")
                return False
            
            if not chart.get('series'):
                print("series列表为空")
                return False
            
            # 验证并修复xAxis
            if 'xAxis' not in chart:
                print("添加默认xAxis配置")
                chart['xAxis'] = {"data": [], "name": "X轴"}
            elif not isinstance(chart['xAxis'], dict):
                print("xAxis不是字典类型，使用默认配置")
                chart['xAxis'] = {"data": [], "name": "X轴"}
            else:
                # 确保xAxis有正确的属性
                if 'data' not in chart['xAxis']:
                    chart['xAxis']['data'] = []
                    print("在xAxis中添加了空的data数组")
                
                if 'name' not in chart['xAxis']:
                    chart['xAxis']['name'] = "X轴"
                    print("在xAxis中添加了默认name")
                
                # 确保xAxis中的data是列表
                if not isinstance(chart['xAxis'].get('data'), list):
                    print("xAxis中的data不是列表，使用空列表替代")
                    chart['xAxis']['data'] = []
            
            # 验证并修复yAxis
            if 'yAxis' not in chart:
                print("添加默认yAxis配置")
                chart['yAxis'] = {"name": "Y轴"}
            elif not isinstance(chart['yAxis'], dict):
                print("yAxis不是字典类型，使用默认配置")
                chart['yAxis'] = {"name": "Y轴"}
            else:
                # 确保yAxis有正确的属性
                if 'name' not in chart['yAxis']:
                    chart['yAxis']['name'] = "Y轴"
                    print("在yAxis中添加了默认name")
            
            # 验证并修复series中的每个项目
            valid_series = []
            for i, item in enumerate(chart.get('series', [])):
                if not isinstance(item, dict):
                    print(f"series中的第{i+1}项不是字典对象，已跳过")
                    continue
                
                # 确保series项中有name和data
                if 'name' not in item:
                    item['name'] = f"数据系列{i+1}"
                    print(f"为series中的第{i+1}项添加了默认name")
                
                if 'data' not in item:
                    item['data'] = []
                    print(f"为series中的第{i+1}项添加了空的data数组")
                
                # 确保data是列表类型
                if not isinstance(item.get('data'), list):
                    print(f"series中第{i+1}项的data不是列表，使用空列表替代")
                    item['data'] = []
                
                # 确保有type字段，且与chart.type一致
                if 'type' not in item:
                    item['type'] = chart['type']
                    print(f"为series中的第{i+1}项添加了type: {chart['type']}")
                
                valid_series.append(item)
            
            # 更新series数组
            if valid_series:
                chart['series'] = valid_series
            else:
                print("没有有效的series项")
                return False
            
            # 确保其他需要的属性存在且类型正确
            for field, value in chart.items():
                if field not in ['title', 'type', 'xAxis', 'yAxis', 'series']:
                    # 验证其他可选字段的类型
                    if not isinstance(value, (str, int, float, bool, list, dict)):
                        print(f"字段{field}的值类型无效: {type(value)}")
                        return False
            
            return True
            
        except Exception as e:
            print(f"验证图表配置时出错: {str(e)}")
            traceback.print_exc()
            return False

    def analyze_data_and_generate_chart(self, user_query, headers, data):
        """
        分析数据并生成图表
        """
        try:
            # 准备提示
            structured_data = self._format_data_for_analysis(headers, data)
            prompt = self._generate_chart_prompt(user_query, structured_data)
            
            # 使用LLM进行分析
            analysis_result = self._call_llm_with_retry(prompt, self.chart_model, max_tokens=4000)
            
            if not analysis_result:
                print("LLM返回空结果")
                return None
            
            # 提取图表配置
            chart_configs = self.extract_chart_configs(analysis_result)
            
            if not chart_configs:
                print("未能提取图表配置")
                print(f"原始分析结果: {analysis_result}")
                return None
            
            print(f"提取到的图表配置: {json.dumps(chart_configs, ensure_ascii=False)[:200]}...")
            return chart_configs
            
        except Exception as e:
            print(f"分析数据生成图表时出错: {str(e)}")
            print(traceback.format_exc())
            return None
    
    def _format_data_for_analysis(self, headers, data):
        """
        将数据格式化为分析所需的结构
        """
        if not headers or not data:
            return "[]"
        
        try:
            # 将数据转换为字典列表格式
            structured_data = []
            for row in data:
                item = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        item[header] = row[i]
                    else:
                        item[header] = ""
                structured_data.append(item)
            
            # 转换为JSON字符串
            return json.dumps(structured_data, ensure_ascii=False)
        except Exception as e:
            print(f"格式化数据时出错: {str(e)}")
            return "[]"
    
    def _generate_chart_prompt(self, user_query, structured_data):
        """
        生成用于图表分析的提示
        """
        return f"""你是一个专业的医疗数据分析师，现在需要根据以下数据和用户查询生成合适的图表配置。你必须返回格式严格正确的JSON，没有任何格式错误。

用户查询: {user_query}

数据:
{structured_data}

你的任务是生成一个严格有效的JSON对象，其中包含一个名为"charts"的数组。这个JSON必须能被Python的json.loads()函数直接解析，不能有任何格式错误！

【极其重要的格式规则】
1. 所有JSON对象的属性必须用逗号分隔，最后一个属性后不能有逗号
2. 所有数组元素必须用逗号分隔，最后一个元素后不能有逗号
3. 所有属性名和字符串值必须使用双引号，不能用单引号
4. 必须严格遵循以下固定模板结构，不能改变基本格式

【图表JSON模板】 - 请严格按照此模板格式：
{{
  "charts": [
    {{
      "title": "图表标题",
      "type": "图表类型",
      "xAxis": {{
        "type": "category",
        "data": ["数据1", "数据2", "数据3"],
        "name": "横轴名称"
      }},
      "yAxis": {{
        "type": "value",
        "name": "纵轴名称"
      }},
      "series": [
        {{
          "name": "数据系列名称",
          "data": [值1, 值2, 值3],
          "type": "系列类型"
        }}
      ]
    }}
  ]
}}

【必须注意的关键点】
1. 所有属性之后都必须有逗号，除了对象或数组的最后一个属性
2. 每个对象的结束花括号后，如果还有下一个属性，必须加逗号
3. "xAxis"对象的结束花括号后面必须有逗号，再写"yAxis"属性
4. "name": "月份"后面必须有逗号（这是最容易错的地方）

【错误模式1】: 最常见的错误是"name": "月份"后缺少逗号
错误:
```json
{{
  "xAxis": {{
    "type": "category",
    "data": ["1月", "2月", "3月"],
    "name": "月份"
  }}
  "yAxis": {{...}}
}}
```

正确:
```json
{{
  "xAxis": {{
    "type": "category",
    "data": ["1月", "2月", "3月"],
    "name": "月份"
  }},
  "yAxis": {{...}}
}}
```

【错误模式2】: 对象属性之间缺少逗号
错误:
```json
{{
  "xAxis": {{...}}
  "yAxis": {{...}}
  "series": [...]
}}
```

正确:
```json
{{
  "xAxis": {{...}},
  "yAxis": {{...}},
  "series": [...]
}}
```

【错误模式3】: 以下这种格式(缺少逗号)绝对会导致JSON解析错误，必须避免！
错误：
```json
  "xAxis": {{
    "type": "category",
    "data": ["1月", "2月", "3月"],
    "name": "月份"
  }}
  "yAxis": {{
    "type": "value",
    "name": "指标"
  }}
```

正确：
```json
  "xAxis": {{
    "type": "category",
    "data": ["1月", "2月", "3月"],
    "name": "月份"
  }},
  "yAxis": {{
    "type": "value",
    "name": "指标"
  }}
```

【生成步骤】
1. 分析数据结构和用户查询
2. 选择适合的图表类型
3. 按照模板格式生成JSON，确保句法完全正确
4. 检查每个对象和属性后是否需要添加逗号
5. 特别检查中文属性值后面是否有逗号

请生成符合要求的JSON图表配置："""
    
    def _call_llm_with_retry(self, prompt, model_name, max_tokens=2000, retry_count=3):
        """
        调用LLM并实现重试逻辑
        """
        attempts = 0
        while attempts < retry_count:
            try:
                # 使用火山引擎API，与call_llm_api方法相似
                api_key = VOLCENGINE_API_KEY
                api_url = VOLCENGINE_API_URL
                timeout = REQUEST_TIMEOUT
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
                
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": "你是一个专业的数据分析师助手，擅长根据数据生成图表配置。"},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.2,
                    "top_p": 0.8,
                    "top_k": 50
                }
                
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    if "choices" in response_data and len(response_data["choices"]) > 0:
                        return response_data["choices"][0]["message"]["content"]
                    else:
                        print(f"警告: API响应没有包含有效的选择: {response_data}")
                else:
                    print(f"警告: API返回状态码 {response.status_code}: {response.text}")
                    
                attempts += 1
                if attempts >= retry_count:
                    print("已达到最大重试次数，放弃调用")
                    return None
                time.sleep(RETRY_DELAY)  # 使用全局定义的重试延迟
                
            except Exception as e:
                attempts += 1
                print(f"LLM调用失败 (尝试 {attempts}/{retry_count}): {str(e)}")
                if attempts >= retry_count:
                    print("已达到最大重试次数，放弃调用")
                    return None
                time.sleep(RETRY_DELAY)  # 使用全局定义的重试延迟 

    def generate_chart_config(self, user_query, structured_data):
        """
        根据用户查询和结构化数据生成图表配置
        
        参数:
            user_query: 用户查询
            structured_data: 结构化数据（JSON格式）
            
        返回:
            图表配置（JSON格式）
        """
        try:
            # 生成提示词
            prompt = self._generate_chart_prompt(user_query, structured_data)
            
            # 设置更高的温度以确保更确定性的输出
            # 调用大模型，将温度设置更低以减少随机性
            response = self._call_llm_with_retry(prompt, self.chart_model, temperature=0.1)
            
            if not response:
                print("生成图表配置时大模型返回为空")
                return {"charts": []}
            
            print(f"LLM原始响应 (截断至200字符): {response[:200]}...")
            
            # 尝试提取JSON部分
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
            if json_match:
                json_content = json_match.group(1)
                print("成功从Markdown代码块中提取JSON内容")
            else:
                # 如果没有代码块，尝试直接找到JSON对象
                start = response.find('{')
                if start >= 0:
                    json_content = response[start:]
                    print("从原始响应中直接提取JSON内容")
                else:
                    json_content = response
                    print("未找到JSON开始标记，使用完整响应")
            
            # 预处理JSON字符串，修复常见格式问题
            # 1. 修复月份相关的常见错误
            if '"name": "月份"' in json_content:
                pattern = r'"name":\s*"月份"\s*}\s*"yAxis"'
                if re.search(pattern, json_content):
                    json_content = re.sub(pattern, '"name": "月份" },\n"yAxis"', json_content)
                    print("预处理：修复了'月份'属性后缺少逗号的问题")
            
            # 2. 修复xAxis和yAxis之间缺少逗号的问题
            if '"xAxis":' in json_content and '"yAxis":' in json_content:
                pattern = r'(}")\s*("yAxis")'
                if re.search(pattern, json_content):
                    json_content = re.sub(pattern, r'},\n\2', json_content)
                    print("预处理：修复了xAxis和yAxis之间缺少逗号的问题")
            
            # 尝试使用健壮的JSON解析器
            result = robust_json_parser(json_content)
            
            if result:
                print("成功解析图表配置JSON")
                # 验证结果的结构
                if isinstance(result, dict) and 'charts' in result:
                    # 确保每个图表配置有必要的字段
                    charts = result['charts']
                    if isinstance(charts, list):
                        valid_charts = []
                        for chart in charts:
                            if self._validate_chart_config(chart):
                                valid_charts.append(chart)
                            else:
                                print(f"图表配置无效，已跳过: {chart}")
                        if valid_charts:
                            result['charts'] = valid_charts
                            return result
                        else:
                            print("所有图表配置都无效")
                            return {"charts": []}
                    else:
                        print("'charts'字段不是列表")
                        return {"charts": []}
                else:
                    # 如果结果是单个图表配置对象，则包装它
                    if isinstance(result, dict) and self._validate_chart_config(result):
                        return {"charts": [result]}
                    else:
                        print("JSON不是有效的图表配置")
                        return {"charts": []}
            else:
                print("无法从LLM响应中解析有效的JSON")
                
                # 尝试从响应中提取图表配置
                print("尝试使用提取方法获取图表配置...")
                chart_configs = self.extract_chart_configs(response)
                if chart_configs:
                    return {"charts": chart_configs}
                
                return {"charts": []}
        
        except Exception as e:
            print(f"生成图表配置时发生错误: {str(e)}")
            traceback.print_exc()
            return {"charts": []} 