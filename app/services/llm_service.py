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
from app.prompts.database import DATABASE_SYSTEM_PROMPT, DATABASE_USER_PROMPT

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
                user_query=user_message,
                database_schema=schema
            )
            
            # 调用LLM
            response = LLMService.call_llm_api(DATABASE_SYSTEM_PROMPT, formatted_user_prompt)
            
            if not response:
                print("LLM回复为空")
                return None
            
            # 尝试从回复中提取JSON
            try:
                # 查找JSON内容的模式 - 匹配 ```json ... ``` 或 { ... }
                json_match = re.search(r'```(?:json)?\s*({.*?})\s*```|({.*})', response, re.DOTALL)
                
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
                    print("LLM回复中没有找到JSON格式的内容")
                    return None
                    
            except json.JSONDecodeError:
                print("JSON解析错误")
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
            
            # 系统提示词
            system_prompt = """
            你是一个专业的医疗数据分析助手，擅长分析医疗数据并提供见解。
            请根据提供的数据和用户的问题，生成详细的分析报告。
            
            分析报告应包括：
            1. 数据概述：简要描述数据内容和结构
            2. 关键发现：指出数据中的主要趋势、模式和异常
            3. 详细分析：深入分析数据，提供具体的见解和解释
            4. 建议：基于分析结果提供实用的建议
            
            请确保分析准确、专业，并使用医疗行业的专业术语。
            """
            
            # 用户消息
            user_message = f"""
            用户问题：{user_query}
            
            数据：{data_json}
            
            请分析上述数据并回答用户问题。
            """
            
            # 调用大模型API
            analysis_result = LLMService.call_llm_api(system_prompt, user_message)
            
            if analysis_result:
                return {
                    'analysis': analysis_result,
                    'original_data': data,
                    'query': user_query
                }
            
            return None
            
        except Exception as e:
            print(f"生成数据分析时出错: {str(e)}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def generate_text_analysis(text_content: str, user_query: str) -> Optional[str]:
        """
        生成文本分析结果
        
        参数:
            text_content: 文本内容
            user_query: 用户查询
            
        返回:
            分析结果，如果失败则返回None
        """
        # 系统提示词
        system_prompt = """
        你是一个专业的医疗文档分析助手，擅长分析医疗文档并提取关键信息。
        请根据提供的文档内容和用户的问题，生成详细的分析报告。
        
        请确保分析准确、专业，并使用医疗行业的专业术语。
        """
        
        # 用户消息
        user_message = f"""
        用户问题：{user_query}
        
        文档内容：
        {text_content}
        
        请分析上述文档并回答用户问题。
        """
        
        # 调用大模型API
        return LLMService.call_llm_api(system_prompt, user_message) 