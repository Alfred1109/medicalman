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
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))  # 增加到60秒
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))  # 增加到3次
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "2"))  # 增加到2秒

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
            # 记录开始调用API的时间
            start_time = time.time()
            print(f"开始调用LLM API - 时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 检查并确保输入是字符串类型
            if isinstance(system_prompt, str) and isinstance(user_message, str):
                print(f"系统提示长度: {len(system_prompt)}, 用户消息长度: {len(user_message)}")
            else:
                # 处理非字符串类型
                if not isinstance(system_prompt, str):
                    system_prompt = str(system_prompt) if system_prompt is not None else ""
                if not isinstance(user_message, str):
                    if hasattr(user_message, 'to_string'):
                        user_message = user_message.to_string()
                    elif hasattr(user_message, '__str__'):
                        user_message = str(user_message)
                    else:
                        user_message = "无法转换的用户消息"
                print(f"系统提示类型转换为字符串, 用户消息类型转换为字符串")
            
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
                    print(f"API尝试 {attempt+1}/{retries+1}")
                    
                    try:
                        response = requests.post(
                            self.api_url,
                            headers=headers,
                            json=payload,
                            timeout=self.timeout
                        )
                        
                        # 记录API响应时间
                        response_time = time.time() - start_time
                        print(f"API响应耗时: {response_time:.2f}秒")
                        
                        if response.status_code == 200:
                            response_data = response.json()
                            
                            if "choices" in response_data and len(response_data["choices"]) > 0:
                                # 记录成功
                                print(f"API调用成功 - 状态码: 200, 耗时: {response_time:.2f}秒")
                                return response_data["choices"][0]["message"]["content"]
                            else:
                                print(f"警告: API响应没有包含有效的选择: {json.dumps(response_data, ensure_ascii=False)[:200]}...")
                                # 如果不是最后一次尝试，则继续重试
                                if attempt < retries:
                                    print(f"等待 {self.retry_delay} 秒后重试...")
                                    time.sleep(self.retry_delay)
                                    continue
                                return None
                        else:
                            print(f"警告: API返回状态码 {response.status_code}")
                            print(f"响应详情: {response.text[:500]}...")
                            
                            # 如果是4xx错误(客户端错误)，可以输出更详细的请求信息以便调试
                            if 400 <= response.status_code < 500:
                                print(f"API请求详情:")
                                print(f"- URL: {self.api_url}")
                                print(f"- Model: {self.model_name}")
                                print(f"- 系统提示长度: {len(system_prompt)}")
                                print(f"- 用户消息长度: {len(user_message)}")
                                print(f"- Temperature: {temperature}")
                            
                            # 如果不是最后一次尝试，则等待后重试
                            if attempt < retries:
                                print(f"等待 {self.retry_delay} 秒后重试...")
                                time.sleep(self.retry_delay)
                                continue
                            else:
                                return None
                    
                    except requests.exceptions.Timeout:
                        print(f"API请求超时 (尝试 {attempt+1}/{retries+1}): 超过了 {self.timeout} 秒")
                        # 增加超时时间进行重试
                        if attempt < retries:
                            self.timeout += 30  # 每次重试增加30秒超时时间
                            print(f"增加超时时间到 {self.timeout} 秒并重试...")
                            time.sleep(self.retry_delay)
                            continue
                        else:
                            return "API请求超时，请稍后再试或简化您的问题。"
                    
                    except requests.exceptions.RequestException as e:
                        print(f"API请求异常 (尝试 {attempt+1}/{retries+1}): {str(e)}")
                        
                        # 如果不是最后一次尝试，则等待后重试
                        if attempt < retries:
                            print(f"等待 {self.retry_delay} 秒后重试...")
                            time.sleep(self.retry_delay)
                            continue
                        else:
                            return "API连接异常，请检查网络连接后重试。"
                
                except Exception as inner_e:
                    print(f"API请求处理异常: {str(inner_e)}")
                    print(traceback.format_exc())
                    
                    if attempt < retries:
                        print(f"等待 {self.retry_delay} 秒后重试...")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        return "处理请求时出现异常，请稍后重试。"
            
            # 如果所有重试都失败，返回一个有用的错误消息而不是None
            return "无法从AI服务获取响应，请稍后重试。"
        
        except Exception as e:
            print(f"调用LLM API时发生错误: {str(e)}")
            print(f"错误堆栈: {traceback.format_exc()}")
            # 返回错误消息而不是None，这样用户会看到具体原因而不是无限等待
            return f"系统发生错误: {str(e)}" 