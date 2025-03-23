"""
基础大模型服务模块 - 提供通用的LLM API调用功能
"""
import json
import requests
import time
import traceback
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from dotenv import load_dotenv

# 获取项目根目录的绝对路径
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = ROOT_DIR / '.env'

# 明确指定.env文件路径
print(f"加载环境变量文件: {ENV_FILE}")
load_dotenv(dotenv_path=ENV_FILE)

# 从环境变量加载配置，避免硬编码
VOLCENGINE_API_KEY = os.getenv("VOLCENGINE_API_KEY", "3470059d-f774-4302-81e0-50fa017fea38")
VOLCENGINE_API_URL = os.getenv("VOLCENGINE_API_URL", "https://ark.cn-beijing.volces.com/api/v3/chat/completions")
VOLCENGINE_MODEL = os.getenv("VOLCENGINE_MODEL", "deepseek-v3-241226")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "1"))

class BaseLLMService:
    """
    基础大模型服务类
    提供通用的大模型API调用功能，包括重试机制和错误处理
    """
    
    def __init__(self, model_name=None, api_key=None, api_url=None):
        """
        初始化基础LLM服务
        
        参数:
            model_name: 模型名称，默认使用环境变量中的设置
            api_key: API密钥，默认使用环境变量中的设置
            api_url: API端点URL，默认使用环境变量中的设置
        """
        self.model_name = model_name or VOLCENGINE_MODEL
        self.api_key = api_key or VOLCENGINE_API_KEY
        self.api_url = api_url or VOLCENGINE_API_URL
        self.timeout = REQUEST_TIMEOUT
        self.max_retries = MAX_RETRIES
        self.retry_delay = RETRY_DELAY
        
        print(f"初始化BaseLLMService，使用模型: {self.model_name}")
        print(f"API密钥: {self.api_key[:5]}...{self.api_key[-5:]}")
        print(f"API端点: {self.api_url}")
    
    def call_api(self, system_prompt: str, user_message: str, 
                temperature=0.7, top_p=0.8, top_k=50, 
                max_tokens=None, retry_count=None) -> Optional[str]:
        """
        调用大模型API并处理重试逻辑
        
        参数:
            system_prompt: 系统提示词
            user_message: 用户消息
            temperature: 温度参数，控制随机性
            top_p: 核采样概率
            top_k: 考虑的最高概率词汇数量
            max_tokens: 最大生成令牌数
            retry_count: 重试次数，None表示使用默认设置
            
        返回:
            AI的回复，如果失败则返回None
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model_name,
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
            
            # 使用用户指定的重试次数或默认值
            retries = retry_count if retry_count is not None else self.max_retries
            
            # 实现重试逻辑
            for attempt in range(retries + 1):
                try:
                    response = requests.post(
                        self.api_url,
                        headers=headers,
                        json=payload,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        
                        if "choices" in response_data and len(response_data["choices"]) > 0:
                            return response_data["choices"][0]["message"]["content"]
                        else:
                            print(f"警告: API响应没有包含有效的选择: {response_data}")
                            # 如果不是最后一次尝试，则继续重试
                            if attempt < retries:
                                time.sleep(self.retry_delay)
                                continue
                            return None
                    else:
                        print(f"警告: API返回状态码 {response.status_code}: {response.text}")
                        
                        # 如果不是最后一次尝试，则等待后重试
                        if attempt < retries:
                            time.sleep(self.retry_delay)
                            continue
                        else:
                            return None
                
                except requests.exceptions.RequestException as e:
                    print(f"API请求异常 (尝试 {attempt+1}/{retries+1}): {str(e)}")
                    
                    # 如果不是最后一次尝试，则等待后重试
                    if attempt < retries:
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        return None
            
            return None
        
        except Exception as e:
            print(f"调用LLM API时发生错误: {str(e)}")
            print(f"错误堆栈: {traceback.format_exc()}")
            return None 