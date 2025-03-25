"""
图表服务模块 - 处理医疗数据图表生成和解析
"""
import json
import re
import traceback
from typing import Dict, Any, Optional, List
import copy

from app.services.base_llm_service import BaseLLMService
from app.utils.utils import robust_json_parser, safe_json_dumps, extract_json_object
from app.prompts.visualization import (
    CHART_GENERATION_SYSTEM_PROMPT,
    CHART_GENERATION_USER_PROMPT,
    CHART_PARSING_SYSTEM_PROMPT,
    CHART_PARSING_USER_PROMPT
)
from app.config import config

class ChartService(BaseLLMService):
    """
    图表服务类，处理图表配置生成和解析
    """
    
    def __init__(self, model_name=None, api_key=None, api_url=None):
        """
        初始化图表服务
        
        参数:
            model_name: 模型名称，默认使用环境变量中的设置
            api_key: API密钥，默认使用环境变量中的设置
            api_url: API端点URL，默认使用环境变量中的设置
        """
        super().__init__(model_name, api_key, api_url)
        print(f"初始化ChartService，使用模型: {self.model_name}")
    
    def generate_chart_config(self, user_query: str, structured_data: str) -> Dict[str, Any]:
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
            prompt = CHART_GENERATION_USER_PROMPT.format(
                user_query=user_query,
                structured_data=structured_data
            )
            
            # 调用大模型，将温度设置更低以减少随机性
            response = self.call_api(
                system_prompt=CHART_GENERATION_SYSTEM_PROMPT,
                user_message=prompt,
                temperature=0.1,
                top_p=0.9
            )
            
            if not response:
                print("生成图表配置时大模型返回为空")
                return {"charts": []}
            
            # 使用新的解析方法处理响应
            result = self.parse_llm_response(response)
            
            # 检查结果
            if result and 'charts' in result and isinstance(result['charts'], list) and len(result['charts']) > 0:
                print(f"成功生成 {len(result['charts'])} 个图表配置")
                return result
            else:
                print("未能生成有效的图表配置")
                return {"charts": []}
        
        except Exception as e:
            print(f"生成图表配置时出错: {str(e)}")
            traceback.print_exc()
            return {"charts": []}
    
    def extract_chart_configs(self, content: str) -> List[Dict[str, Any]]:
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
                            json_str = cleaned_content[json_start:i+1]
                            try:
                                config = json.loads(json_str)
                                if isinstance(config, dict) and 'charts' in config:
                                    chart_configs.extend(config['charts'])
                            except json.JSONDecodeError:
                                print(f"JSON解析失败: {json_str[:100]}...")
            
            # 如果没有找到完整的JSON，尝试提取部分配置
            if not chart_configs:
                # 使用正则表达式提取可能的图表配置片段
                chart_patterns = [
                    r'"type"\s*:\s*"([^"]+)"',  # 图表类型
                    r'"title"\s*:\s*"([^"]+)"',  # 图表标题
                    r'"data"\s*:\s*\[([^\]]+)\]',  # 数据数组
                    r'"name"\s*:\s*"([^"]+)"'  # 名称
                ]
                
                for pattern in chart_patterns:
                    matches = re.finditer(pattern, cleaned_content)
                    for match in matches:
                        try:
                            # 尝试构建基本的图表配置
                            chart_config = {
                                "type": config.CHART_DEFAULT_TYPE,
                                "title": match.group(1) if pattern == r'"title"\s*:\s*"([^"]+)"' else config.CHART_DEFAULT_TITLE,
                                "data": json.loads(f"[{match.group(1)}]") if pattern == r'"data"\s*:\s*\[([^\]]+)\]' else [],
                                "name": match.group(1) if pattern == r'"name"\s*:\s*"([^"]+)"' else config.CHART_DEFAULT_SERIES_NAME
                            }
                            chart_configs.append(chart_config)
                        except:
                            continue
            
            # 验证提取的配置
            if chart_configs:
                # 使用LLM验证配置
                validation_prompt = CHART_PARSING_USER_PROMPT.format(
                    chart_config=json.dumps({"charts": chart_configs}, ensure_ascii=False)
                )
                
                validation_response = self.call_api(
                    system_prompt=CHART_PARSING_SYSTEM_PROMPT,
                    user_message=validation_prompt,
                    temperature=0.1
                )
                
                if validation_response:
                    try:
                        validation_result = json.loads(validation_response)
                        if validation_result.get("is_valid"):
                            chart_configs = validation_result.get("validated_config", {}).get("charts", chart_configs)
                        else:
                            print(f"配置验证发现问题: {validation_result.get('issues')}")
                    except:
                        print("配置验证结果解析失败")
            
            return chart_configs
            
        except Exception as e:
            print(f"提取图表配置时出错: {str(e)}")
            traceback.print_exc()
            return []
    
    def parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        解析LLM响应，提取图表配置
        
        参数:
            response: LLM响应内容
            
        返回:
            解析后的图表配置字典
        """
        try:
            # 首先尝试直接解析JSON
            try:
                return json.loads(response)
            except:
                pass
            
            # 尝试提取JSON代码块
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except:
                    pass
            
            # 尝试提取JSON对象
            json_obj = extract_json_object(response)
            if json_obj:
                return json_obj
            
            # 如果都失败了，返回空配置
            return {"charts": []}
            
        except Exception as e:
            print(f"解析LLM响应时出错: {str(e)}")
            traceback.print_exc()
            return {"charts": []}
    
    def _generate_chart_prompt(self, user_query: str, structured_data: str) -> str:
        """
        生成图表配置的提示词
        
        参数:
            user_query: 用户查询
            structured_data: 结构化数据
            
        返回:
            生成的提示词
        """
        return CHART_GENERATION_USER_PROMPT.format(
            user_query=user_query,
            structured_data=structured_data
        ) 