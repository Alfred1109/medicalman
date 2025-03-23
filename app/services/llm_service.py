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

class LLMService:
    """大模型服务类"""
    
    @staticmethod
    def call_llm_api(system_prompt: str, user_message: str) -> Optional[str]:
        """
        调用大模型API
        
        参数:
            system_prompt: 系统提示词
            user_message: 用户消息
            
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
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 50
            }
            
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
            
            # 构建提示词
            formatted_user_prompt = DATABASE_USER_PROMPT.format(
                request=user_message,
                schema_info=schema
            )
            
            # 调用LLM
            response = LLMService.call_llm_api(DATABASE_SYSTEM_PROMPT, formatted_user_prompt)
            
            if not response:
                print("LLM回复为空")
                return None
            
            # 优化JSON内容匹配模式 - 支持更多格式
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```|(\{.*?\})', response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1) or json_match.group(2)
                result = json.loads(json_str)
                
                # 验证JSON格式是否符合预期
                if "sql" in result:
                    return result
                else:
                    print("JSON中没有找到sql字段")
                    return None
            else:
                # 尝试直接从文本中提取JSON格式 - 使用更强大的匹配模式
                # 改进正则表达式以更好地处理嵌套结构
                try:
                    # 首先尝试是否整个响应就是一个有效的JSON
                    try:
                        result = json.loads(response)
                        if "sql" in result:
                            return result
                    except:
                        pass
                    
                    # 使用更复杂的模式匹配嵌套JSON
                    # 寻找可能的JSON对象起始位置
                    start_pos = response.find('{')
                    if start_pos >= 0:
                        # 从找到的起始位置开始，尝试不同长度的子串
                        for end_pos in range(len(response), start_pos, -1):
                            try:
                                substr = response[start_pos:end_pos]
                                # 确保花括号是匹配的
                                if substr.count('{') == substr.count('}'):
                                    result = json.loads(substr)
                                    if "sql" in result:
                                        return result
                            except:
                                continue
                
                    # 如果所有尝试都失败
                    print("LLM回复中没有找到JSON格式的内容")
                    print(f"原始回复: {response}")  # 打印完整回复用于调试
                    return None
                except Exception as json_ex:
                    print(f"JSON提取过程出错: {str(json_ex)}")
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
                        chart_data = json.loads(json_str)
                        
                        if "charts" in chart_data:
                            charts = chart_data["charts"]
                    else:
                        # 尝试直接从文本中提取JSON格式 - 使用更强大的匹配模式
                        try:
                            # 首先尝试是否整个响应就是一个有效的JSON
                            try:
                                chart_data = json.loads(analysis_result)
                                if "charts" in chart_data:
                                    charts = chart_data["charts"]
                            except:
                                pass
                            
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
                                            chart_data = json.loads(substr)
                                            if "charts" in chart_data:
                                                charts = chart_data["charts"]
                                                break
                                    except:
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
                user_prompt=parsing_user_prompt,
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
                user_prompt=analysis_user_prompt,
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
            user_prompt=response_user_prompt,
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
            user_prompt=query_user_prompt,
            temperature=0.2
        ) 