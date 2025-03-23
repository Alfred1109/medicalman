"""
文本分析服务模块 - 处理医疗文本分析和解释
"""
import traceback
from typing import Dict, Any, Optional

from app.services.base_llm_service import BaseLLMService

class TextAnalysisService(BaseLLMService):
    """
    文本分析服务类，处理医疗文本分析和解释
    """
    
    def __init__(self, model_name=None, api_key=None, api_url=None):
        """
        初始化文本分析服务
        
        参数:
            model_name: 模型名称，默认使用环境变量中的设置
            api_key: API密钥，默认使用环境变量中的设置
            api_url: API端点URL，默认使用环境变量中的设置
        """
        super().__init__(model_name, api_key, api_url)
        print(f"初始化TextAnalysisService，使用模型: {self.model_name}")
    
    def generate_text_analysis(self, user_query: str, context_data: str) -> str:
        """
        生成文本分析结果
        
        参数:
            user_query: 用户查询
            context_data: 上下文数据或分析背景
            
        返回:
            分析结果文本
        """
        try:
            # 构建分析提示词
            prompt = self._generate_analysis_prompt(user_query, context_data)
            
            # 调用LLM API
            response = self.call_api(
                system_prompt="你是一位医疗专家，擅长从医疗数据中提取见解并用通俗易懂的语言解释医学概念。",
                user_message=prompt,
                temperature=0.5,
                top_p=0.9
            )
            
            if not response:
                return "无法生成分析结果，请稍后重试。"
            
            return response
        
        except Exception as e:
            print(f"生成文本分析时出错: {str(e)}")
            traceback.print_exc()
            return f"分析过程中发生错误: {str(e)}"
    
    def generate_modular_response(self, 
                                user_query: str, 
                                sql_query: Optional[str] = None,
                                sql_results: Optional[str] = None,
                                chart_configs: Optional[str] = None) -> Dict[str, Any]:
        """
        生成模块化响应，整合SQL查询、数据分析和图表配置
        
        参数:
            user_query: 用户查询
            sql_query: SQL查询语句（可选）
            sql_results: SQL查询结果（可选）
            chart_configs: 图表配置（可选）
            
        返回:
            整合后的模块化响应
        """
        try:
            # 构建提示词，包含所有可用信息
            components = []
            
            components.append(f"用户问题: {user_query}")
            
            if sql_query:
                components.append(f"执行的SQL查询:\n{sql_query}")
            
            if sql_results:
                components.append(f"查询结果:\n{sql_results}")
            
            if chart_configs:
                components.append(f"生成的图表配置:\n{chart_configs}")
            
            prompt = "请对以下医疗数据进行综合分析并生成一个结构化的响应。\n\n" + "\n\n".join(components)
            
            # 附加具体的输出要求
            prompt += """

请生成以下结构的响应:
1. 摘要: 对用户问题的简洁回答（1-2句话）
2. 关键发现: 列出数据分析中的主要发现（最多5点）
3. 详细分析: 对数据的深入解释
4. 医学建议: 根据数据提供的医学建议或解释
5. 后续分析: 可能的进一步分析方向
"""
            
            # 调用LLM API
            response = self.call_api(
                system_prompt="你是一位医疗数据专家，擅长分析医疗数据并提供易于理解的见解。",
                user_message=prompt,
                temperature=0.4,
                top_p=0.9
            )
            
            if not response:
                return {
                    "摘要": "无法生成分析结果",
                    "关键发现": ["分析生成过程中出现问题"],
                    "详细分析": "服务暂时不可用，请稍后重试",
                    "医学建议": "请咨询医疗专业人员获取准确建议",
                    "后续分析": ["请稍后重试"]
                }
            
            # 尝试将响应解析为结构化格式
            result = self._parse_structured_response(response)
            return result
        
        except Exception as e:
            print(f"生成模块化响应时出错: {str(e)}")
            traceback.print_exc()
            return {
                "摘要": f"处理请求时出错: {str(e)}",
                "关键发现": ["处理过程中发生错误"],
                "详细分析": "无法完成分析",
                "医学建议": "请咨询医疗专业人员获取准确建议",
                "后续分析": ["系统恢复后重试"]
            }
    
    def _generate_analysis_prompt(self, user_query: str, context_data: str) -> str:
        """
        生成用于文本分析的提示词
        
        参数:
            user_query: 用户查询
            context_data: 上下文数据
            
        返回:
            生成的提示词
        """
        return f"""请分析以下医疗数据，并提供专业但通俗易懂的解释：

用户问题：
{user_query}

相关数据：
{context_data}

请提供：
1. 对数据的专业解释
2. 关键医学发现和见解
3. 可能的医学建议（如适用）
4. 使用通俗易懂的语言，避免过多专业术语
5. 如有需要，解释重要的医学术语

分析结果应当准确、客观、全面，并直接回答用户问题。"""
    
    def _parse_structured_response(self, response: str) -> Dict[str, Any]:
        """
        将LLM响应解析为结构化格式
        
        参数:
            response: LLM响应文本
            
        返回:
            结构化的响应字典
        """
        result = {
            "摘要": "",
            "关键发现": [],
            "详细分析": "",
            "医学建议": "",
            "后续分析": []
        }
        
        # 简单的基于标题的解析
        current_section = None
        section_content = []
        
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # 检测部分标题
            if line.startswith('摘要') or '摘要:' in line or '摘要：' in line:
                current_section = "摘要"
                # 提取冒号后面的内容
                if ':' in line or '：' in line:
                    content = line.split(':', 1)[1].strip() if ':' in line else line.split('：', 1)[1].strip()
                    section_content.append(content)
            elif line.startswith('关键发现') or '关键发现:' in line or '关键发现：' in line:
                # 保存前一部分内容
                if current_section and section_content:
                    if current_section == "摘要":
                        result[current_section] = ' '.join(section_content)
                    section_content = []
                current_section = "关键发现"
            elif line.startswith('详细分析') or '详细分析:' in line or '详细分析：' in line:
                # 保存前一部分内容
                if current_section and section_content:
                    if current_section == "关键发现":
                        result[current_section] = [item.strip('- ') for item in section_content if item.strip('- ')]
                    section_content = []
                current_section = "详细分析"
            elif line.startswith('医学建议') or '医学建议:' in line or '医学建议：' in line:
                # 保存前一部分内容
                if current_section and section_content:
                    if current_section == "详细分析":
                        result[current_section] = '\n'.join(section_content)
                    section_content = []
                current_section = "医学建议"
            elif line.startswith('后续分析') or '后续分析:' in line or '后续分析：' in line:
                # 保存前一部分内容
                if current_section and section_content:
                    if current_section == "医学建议":
                        result[current_section] = '\n'.join(section_content)
                    section_content = []
                current_section = "后续分析"
            # 列表项处理
            elif current_section and (line.startswith('-') or line.startswith('*') or line[0].isdigit() and line[1:3] in ('. ', '、')):
                section_content.append(line)
            # 普通文本内容
            elif current_section:
                section_content.append(line)
        
        # 处理最后一个部分
        if current_section and section_content:
            if current_section == "后续分析":
                result[current_section] = [item.strip('- ') for item in section_content if item.strip('- ')]
            elif current_section == "关键发现":
                result[current_section] = [item.strip('- ') for item in section_content if item.strip('- ')]
            elif current_section in ["摘要", "详细分析", "医学建议"]:
                result[current_section] = '\n'.join(section_content)
        
        return result 