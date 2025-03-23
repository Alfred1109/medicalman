"""
文本分析服务模块 - 处理医疗文本分析和解释
"""
import traceback
from typing import Dict, Any, Optional
import re

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
    
    def generate_sql_analysis(self, user_query: str, sql_query: str, results: list, has_chart: bool = False) -> str:
        """
        分析SQL查询结果并生成解释
        
        参数:
            user_query: 用户查询
            sql_query: 执行的SQL查询
            results: 查询结果列表
            has_chart: 是否有图表
            
        返回:
            分析结果文本
        """
        try:
            # 转换结果为可读格式
            if results and len(results) > 0:
                sample_size = min(10, len(results))  # 最多取10条数据作为样本
                results_str = str(results[:sample_size])
                total_count = len(results)
            else:
                results_str = "[]"
                total_count = 0
            
            # 构建SQL分析提示词
            prompt = f"""请分析以下SQL查询结果并生成专业、通俗易懂的解释：

用户问题：
{user_query}

执行的SQL查询：
{sql_query}

查询结果 (共{total_count}条记录，显示前{min(10, total_count)}条)：
{results_str}

{'图表已生成用于可视化这些数据。' if has_chart else '未生成图表。'}

请提供：
1. 对用户问题的直接回答
2. 对SQL查询结果的专业医学解释
3. 关键医学发现和见解
4. 结果的临床意义或管理含义
5. 如有需要，解释重要的医学术语

你的分析应当准确、客观、全面，并以清晰的医学视角进行解读。
使用专业但易于理解的语言，适合医疗管理人员阅读。
"""
            
            # 调用LLM API
            response = self.call_api(
                system_prompt="你是一位医疗数据分析专家，擅长解读SQL查询结果并提供医学见解。",
                user_message=prompt,
                temperature=0.4,
                top_p=0.9
            )
            
            if not response:
                return "无法分析查询结果，请稍后重试。"
            
            # 尝试自动生成图表配置
            if not has_chart and results and len(results) > 0:
                try:
                    charts = self.generate_auto_charts(user_query, results)
                    if charts and len(charts) > 0:
                        print(f"自动生成了{len(charts)}个图表")
                except Exception as chart_error:
                    print(f"自动生成图表时出错: {str(chart_error)}")
            
            return response
        
        except Exception as e:
            print(f"分析SQL结果时出错: {str(e)}")
            traceback.print_exc()
            return f"分析SQL结果时发生错误: {str(e)}"
    
    def generate_auto_charts(self, user_query: str, results: list) -> list:
        """
        根据查询结果自动生成适合的图表配置
        
        参数:
            user_query: 用户查询
            results: 查询结果列表
            
        返回:
            图表配置列表
        """
        try:
            if not results or len(results) == 0:
                return []
                
            charts = []
            
            # 提取数据字段
            sample = results[0]
            fields = list(sample.keys())
            
            # 检查是否有数值型和类别型字段
            numeric_fields = []
            category_fields = []
            date_fields = []
            
            for field in fields:
                values = [r.get(field) for r in results if r.get(field) is not None]
                if not values:
                    continue
                    
                # 检查是否为数值型
                if all(isinstance(v, (int, float)) for v in values):
                    numeric_fields.append(field)
                # 检查是否为日期型
                elif all(isinstance(v, str) and re.match(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', v) for v in values):
                    date_fields.append(field)
                # 检查是否为类别型
                elif len(set(values)) < len(values) * 0.5:  # 如果唯一值少于总数的一半，视为类别
                    category_fields.append(field)
            
            # 生成柱状图/折线图 (数值 vs 类别/日期)
            if numeric_fields and (category_fields or date_fields):
                # 选择X轴（优先使用日期，其次使用类别）
                x_field = date_fields[0] if date_fields else category_fields[0]
                # 选择Y轴（数值）
                y_field = numeric_fields[0]
                
                # 提取并聚合数据
                x_values = []
                y_values = []
                
                # 简单数据预处理
                data_map = {}
                for r in results:
                    x_val = r.get(x_field)
                    y_val = r.get(y_field)
                    if x_val is not None and y_val is not None:
                        if x_val in data_map:
                            data_map[x_val] += y_val
                        else:
                            data_map[x_val] = y_val
                
                # 转换为数组
                for x, y in data_map.items():
                    x_values.append(str(x))
                    y_values.append(y)
                
                # 对日期或数字类型的X值进行排序
                if x_values and len(x_values) > 0:
                    try:
                        # 检查是否为日期格式
                        if date_fields and all(re.match(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', x) for x in x_values):
                            # 日期排序
                            sorted_data = sorted(zip(x_values, y_values), 
                                                key=lambda item: [int(n) for n in re.split(r'[-/]', item[0])])
                            x_values = [item[0] for item in sorted_data]
                            y_values = [item[1] for item in sorted_data]
                        # 检查是否为月份格式 (例如: "1月", "2月"...)
                        elif all(re.match(r'(\d+)月?', x) for x in x_values):
                            # 月份排序
                            sorted_data = sorted(zip(x_values, y_values), 
                                                key=lambda item: int(re.match(r'(\d+)月?', item[0]).group(1)))
                            x_values = [item[0] for item in sorted_data]
                            y_values = [item[1] for item in sorted_data]
                        # 检查是否为纯数字
                        elif all(re.match(r'^\d+$', x) for x in x_values):
                            # 数字排序
                            sorted_data = sorted(zip(x_values, y_values), key=lambda item: int(item[0]))
                            x_values = [item[0] for item in sorted_data]
                            y_values = [item[1] for item in sorted_data]
                    except Exception as sort_error:
                        print(f"排序X轴数据时出错: {str(sort_error)}")
                
                # 创建图表配置
                chart_type = "line" if date_fields else "bar"
                chart = {
                    "title": f"{y_field} vs {x_field}",
                    "type": chart_type,
                    "xAxis": {
                        "type": "category",
                        "data": x_values,
                        "name": x_field
                    },
                    "yAxis": {
                        "type": "value",
                        "name": y_field
                    },
                    "series": [
                        {
                            "name": y_field,
                            "data": y_values,
                            "type": chart_type
                        }
                    ]
                }
                
                charts.append(chart)
            
            # 如果有多个数值字段，为每个字段创建一个图表
            if len(numeric_fields) > 1 and (category_fields or date_fields):
                x_field = date_fields[0] if date_fields else category_fields[0]
                
                for y_field in numeric_fields[1:2]:  # 最多再添加一个图表
                    # 提取并聚合数据
                    data_map = {}
                    for r in results:
                        x_val = r.get(x_field)
                        y_val = r.get(y_field)
                        if x_val is not None and y_val is not None:
                            if x_val in data_map:
                                data_map[x_val] += y_val
                            else:
                                data_map[x_val] = y_val
                    
                    # 转换为数组
                    x_values = []
                    y_values = []
                    for x, y in data_map.items():
                        x_values.append(str(x))
                        y_values.append(y)
                    
                    # 对日期或数字类型的X值进行排序
                    if x_values and len(x_values) > 0:
                        try:
                            # 检查是否为日期格式
                            if date_fields and all(re.match(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', x) for x in x_values):
                                # 日期排序
                                sorted_data = sorted(zip(x_values, y_values), 
                                                    key=lambda item: [int(n) for n in re.split(r'[-/]', item[0])])
                                x_values = [item[0] for item in sorted_data]
                                y_values = [item[1] for item in sorted_data]
                            # 检查是否为月份格式 (例如: "1月", "2月"...)
                            elif all(re.match(r'(\d+)月?', x) for x in x_values):
                                # 月份排序
                                sorted_data = sorted(zip(x_values, y_values), 
                                                    key=lambda item: int(re.match(r'(\d+)月?', item[0]).group(1)))
                                x_values = [item[0] for item in sorted_data]
                                y_values = [item[1] for item in sorted_data]
                            # 检查是否为纯数字
                            elif all(re.match(r'^\d+$', x) for x in x_values):
                                # 数字排序
                                sorted_data = sorted(zip(x_values, y_values), key=lambda item: int(item[0]))
                                x_values = [item[0] for item in sorted_data]
                                y_values = [item[1] for item in sorted_data]
                        except Exception as sort_error:
                            print(f"排序X轴数据时出错: {str(sort_error)}")
                    
                    # 创建图表配置
                    chart_type = "line" if date_fields else "bar"
                    chart = {
                        "title": f"{y_field} vs {x_field}",
                        "type": chart_type,
                        "xAxis": {
                            "type": "category",
                            "data": x_values,
                            "name": x_field
                        },
                        "yAxis": {
                            "type": "value",
                            "name": y_field
                        },
                        "series": [
                            {
                                "name": y_field,
                                "data": y_values,
                                "type": chart_type
                            }
                        ]
                    }
                    
                    charts.append(chart)
            
            # 饼图（如果只有一个数值字段和一个类别字段，且类别不超过10个）
            if len(numeric_fields) == 1 and len(category_fields) == 1:
                category_field = category_fields[0]
                value_field = numeric_fields[0]
                
                # 提取并聚合数据
                data_map = {}
                for r in results:
                    cat = r.get(category_field)
                    val = r.get(value_field)
                    if cat is not None and val is not None:
                        if cat in data_map:
                            data_map[cat] += val
                        else:
                            data_map[cat] = val
                
                # 如果类别数量合适，创建饼图
                if len(data_map) <= 10:
                    pie_data = []
                    for cat, val in data_map.items():
                        pie_data.append({"name": str(cat), "value": val})
                    
                    chart = {
                        "title": f"{value_field} 按 {category_field} 分布",
                        "type": "pie",
                        "series": [
                            {
                                "type": "pie",
                                "radius": "60%",
                                "data": pie_data
                            }
                        ]
                    }
                    
                    charts.append(chart)
            
            return charts
            
        except Exception as e:
            print(f"自动生成图表配置时出错: {str(e)}")
            traceback.print_exc()
            return []
    
    def generate_text_response(self, user_query: str) -> str:
        """
        生成文本响应，当无法执行SQL查询时使用
        
        参数:
            user_query: 用户查询
            
        返回:
            响应文本
        """
        try:
            # 构建提示词
            prompt = f"""请回答以下医疗相关问题：

问题：{user_query}

请提供：
1. 准确、专业的回答
2. 如有必要，解释相关医学术语
3. 以清晰、易于理解的方式表达

如果问题超出你的知识范围，请诚实地表明并提供可能的参考来源。
"""
            
            # 调用LLM API
            response = self.call_api(
                system_prompt="你是一位专业的医疗助手，擅长回答医疗相关问题。你的回答应当准确、全面、易于理解。",
                user_message=prompt,
                temperature=0.5,
                top_p=0.9
            )
            
            if not response:
                return "无法生成回答，请稍后重试。"
            
            return response
        
        except Exception as e:
            print(f"生成文本响应时出错: {str(e)}")
            traceback.print_exc()
            return f"生成回答时发生错误: {str(e)}"
    
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