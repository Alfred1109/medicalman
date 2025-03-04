import json
import requests
import time
import re
import traceback
from typing import Dict, Any, Optional
from .config import (
    VOLCENGINE_API_KEY,
    VOLCENGINE_API_URL,
    VOLCENGINE_MODEL,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY
)
from .prompts.database_prompt import DATABASE_SYSTEM_PROMPT, DATABASE_USER_PROMPT
from .prompts.response_generator_prompt import RESPONSE_SYSTEM_PROMPT, RESPONSE_USER_PROMPT
from .prompts.excel_prompt import EXCEL_SYSTEM_PROMPT, EXCEL_USER_PROMPT
from .prompts.text_prompt import TEXT_SYSTEM_PROMPT, TEXT_USER_PROMPT

def call_llm_api(system_prompt: str, user_message: str) -> Optional[str]:
    """
    调用大模型API
    
    参数:
        system_prompt: 系统提示词
        user_message: 用户消息
        
    返回:
        str: AI的回复
    """
    try:
        # 准备请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {VOLCENGINE_API_KEY}"
        }
        
        # 准备请求体
        payload = {
            "model": VOLCENGINE_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "temperature": 0.7,
            "top_p": 0.8,
            "stream": False
        }
        
        print(f"正在调用LLM API，模型: {VOLCENGINE_MODEL}")
        print(f"API URL: {VOLCENGINE_API_URL}")
        print(f"API KEY: {VOLCENGINE_API_KEY[:5]}...{VOLCENGINE_API_KEY[-5:]}")
        print(f"系统提示词: {system_prompt[:200]}...")
        print(f"用户消息: {user_message[:200]}...")
        print(f"完整请求体: {json.dumps(payload, ensure_ascii=False)[:500]}...")
        
        # 发送请求，带重试机制
        for attempt in range(MAX_RETRIES):
            try:
                print(f"尝试 {attempt+1}/{MAX_RETRIES}")
                
                # 设置超时
                response = requests.post(
                    VOLCENGINE_API_URL, 
                    headers=headers, 
                    json=payload, 
                    timeout=REQUEST_TIMEOUT
                )
                
                # 打印响应状态和内容预览
                print(f"API响应状态码: {response.status_code}")
                print(f"API响应内容预览: {response.text[:500] if response.text else '空响应'}...")
                
                # 检查响应状态
                response.raise_for_status()
                
                # 解析JSON响应
                result = response.json()
                print(f"API响应JSON: {json.dumps(result, ensure_ascii=False)[:500]}...")
                
                # 提取AI回复
                if 'choices' in result and len(result['choices']) > 0:
                    if 'message' in result['choices'][0] and 'content' in result['choices'][0]['message']:
                        ai_message = result['choices'][0]['message']['content'].strip()
                        if ai_message:
                            print(f"成功获取AI回复，长度: {len(ai_message)}")
                            print(f"AI回复预览: {ai_message[:200]}...")
                            return ai_message
                        else:
                            print("API返回了空的回复内容")
                    else:
                        print("API响应格式不符合预期，找不到message.content字段")
                        print(f"实际响应结构: {result['choices'][0] if 'choices' in result and len(result['choices']) > 0 else '无choices'}")
                else:
                    print("API响应格式不符合预期，找不到choices字段")
                    print(f"实际响应结构: {list(result.keys()) if result else '空结果'}")
                
                # 如果提取失败但还有重试机会，继续重试
                if attempt < MAX_RETRIES - 1:
                    print(f"等待 {RETRY_DELAY} 秒后重试...")
                    time.sleep(RETRY_DELAY)
                    continue
                    
            except requests.exceptions.Timeout:
                print(f"API请求超时 (超过 {REQUEST_TIMEOUT} 秒)")
                if attempt < MAX_RETRIES - 1:
                    print(f"等待 {RETRY_DELAY} 秒后重试...")
                    time.sleep(RETRY_DELAY)
                    continue
                    
            except requests.exceptions.RequestException as e:
                print(f"API请求失败: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    print(f"等待 {RETRY_DELAY} 秒后重试...")
                    time.sleep(RETRY_DELAY)
                    continue
                    
            except Exception as e:
                print(f"调用API时发生未预期错误: {str(e)}")
                print(f"错误类型: {type(e)}")
                print(f"错误堆栈: {traceback.format_exc()}")
                if attempt < MAX_RETRIES - 1:
                    print(f"等待 {RETRY_DELAY} 秒后重试...")
                    time.sleep(RETRY_DELAY)
                    continue
        
        # 如果所有重试都失败
        print("所有重试都失败，返回默认错误消息")
        return "抱歉，我暂时无法回答您的问题，请稍后再试。"
        
    except Exception as e:
        print(f"调用LLM API时发生错误: {str(e)}")
        print(f"错误类型: {type(e)}")
        print(f"错误堆栈: {traceback.format_exc()}")
        return "抱歉，调用AI服务时发生错误，请稍后再试。"

def analyze_user_query_and_generate_sql(user_message: str, schema_info: str) -> Dict[str, Any]:
    """
    分析用户查询并生成SQL
    
    参数:
        user_message: 用户消息
        schema_info: 数据库结构信息
        
    返回:
        Dict: 包含分析结果和SQL查询的字典
    """
    try:
        # 构建提示词
        prompt = DATABASE_USER_PROMPT.format(
            db_schema=schema_info,
            user_message=user_message
        )
        
        # 调用LLM API生成SQL查询
        raw_response = call_llm_api(DATABASE_SYSTEM_PROMPT, prompt)
        
        if not raw_response:
            return {
                "analysis": "无法处理查询",
                "sql_queries": [],
                "visualization_plan": [],
                "explanation": "调用API失败"
            }
            
        # 解析JSON响应
        try:
            result = json.loads(raw_response)
            if all(key in result for key in ["analysis", "sql_queries", "visualization_plan", "explanation"]):
                # 使用response_generator格式化输出
                formatted_response = call_llm_api(
                    RESPONSE_SYSTEM_PROMPT,
                    RESPONSE_USER_PROMPT.format(
                        analysis_result=json.dumps(result, ensure_ascii=False, indent=2),
                        data_source='database',
                        analysis_type='sql_analysis'
                    )
                )
                
                if formatted_response:
                    result["formatted_response"] = formatted_response
                
                return result
        except json.JSONDecodeError:
            print("无法解析SQL生成结果为JSON格式")
        except Exception as e:
            print(f"处理SQL生成结果时出错: {str(e)}")
            
        # 如果解析失败，返回原始响应
        return {
            "analysis": raw_response,
            "sql_queries": [],
            "visualization_plan": [],
            "explanation": "无法解析为标准格式，返回原始响应"
        }
        
    except Exception as e:
        print(f"分析查询时出错: {str(e)}")
        traceback.print_exc()
        return {
            "analysis": "处理查询时出错",
            "sql_queries": [],
            "visualization_plan": [],
            "explanation": f"处理查询时发生错误: {str(e)}"
        }

def generate_data_analysis(df, column_types, relevant_cols, keywords, user_message):
    """
    使用LLM生成数据分析结果
    
    参数:
        df: DataFrame对象，包含上传的Excel数据
        column_types: 列类型字典
        relevant_cols: 与用户问题相关的列
        keywords: 从用户问题中提取的关键词
        user_message: 用户的问题
        
    返回:
        str: 分析结果的文本描述
    """
    try:
        # 准备数据概览
        data_overview = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "column_types": column_types,
            "relevant_columns": relevant_cols
        }
        
        # 准备数据样本（前5行）
        sample_data = df.head(5).to_dict(orient='records')
        
        # 构建提示词
        prompt = EXCEL_USER_PROMPT.format(
            total_rows=data_overview['total_rows'],
            total_columns=data_overview['total_columns'],
            column_types=json.dumps(data_overview['column_types'], ensure_ascii=False),
            relevant_columns=json.dumps(data_overview['relevant_columns'], ensure_ascii=False),
            sample_data=json.dumps(sample_data, ensure_ascii=False, indent=2),
            user_message=user_message
        )
        
        # 调用LLM API
        raw_response = call_llm_api(EXCEL_SYSTEM_PROMPT, prompt)
        
        if not raw_response:
            return "无法生成数据分析结果，请重试。"
            
        # 使用response_generator格式化输出
        formatted_response = call_llm_api(
            RESPONSE_SYSTEM_PROMPT,
            RESPONSE_USER_PROMPT.format(
                analysis_result=raw_response,
                data_source='excel',
                analysis_type='data_analysis'
            )
        )
        
        return formatted_response or raw_response
        
    except Exception as e:
        print(f"生成数据分析结果时出错: {str(e)}")
        traceback.print_exc()
        return f"生成数据分析结果时出错: {str(e)}"

def generate_text_analysis(text, user_message):
    """
    使用LLM分析文本内容
    
    参数:
        text: 文本内容
        user_message: 用户的问题
        
    返回:
        str: 分析结果的文本描述
    """
    try:
        # 准备文本概览
        total_chars = len(text)
        total_words = len(text.split())
        total_lines = len(text.split('\n'))
        text_preview = text[:1000] + "..." if len(text) > 1000 else text
        
        # 构建提示词
        prompt = TEXT_USER_PROMPT.format(
            total_chars=total_chars,
            total_words=total_words,
            total_lines=total_lines,
            file_type='text',
            text_preview=text_preview,
            user_message=user_message
        )
        
        # 调用LLM API
        raw_response = call_llm_api(TEXT_SYSTEM_PROMPT, prompt)
        
        if not raw_response:
            return "无法生成文本分析结果，请重试。"
            
        # 使用response_generator格式化输出
        formatted_response = call_llm_api(
            RESPONSE_SYSTEM_PROMPT,
            RESPONSE_USER_PROMPT.format(
                analysis_result=raw_response,
                data_source='text',
                analysis_type='text_analysis'
            )
        )
        
        return formatted_response or raw_response
        
    except Exception as e:
        print(f"生成文本分析结果时出错: {str(e)}")
        traceback.print_exc()
        return f"生成文本分析结果时出错: {str(e)}" 