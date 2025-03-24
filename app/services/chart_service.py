"""
图表服务模块 - 处理医疗数据图表生成和解析
"""
import json
import re
import traceback
from typing import Dict, Any, Optional, List
import copy

from app.services.base_llm_service import BaseLLMService
from app.utils.json_helper import robust_json_parser, aggressive_json_fix, extract_json_object

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
            prompt = self._generate_chart_prompt(user_query, structured_data)
            
            # 调用大模型，将温度设置更低以减少随机性
            response = self.call_api(
                system_prompt="你是一个专业的医疗数据分析师助手，擅长根据数据生成图表配置。",
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
    
    def _validate_chart_config(self, chart: Dict[str, Any]) -> bool:
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
            
            # 检查必要字段 - 更宽松的验证方式
            if 'type' not in chart:
                # 尝试从series[0].type获取类型
                if 'series' in chart and isinstance(chart['series'], list) and len(chart['series']) > 0:
                    if isinstance(chart['series'][0], dict) and 'type' in chart['series'][0]:
                        chart['type'] = chart['series'][0]['type']
                        print(f"从series[0].type获取图表类型: {chart['type']}")
                    else:
                        chart['type'] = 'bar'  # 默认类型
                        print("未找到图表类型，使用默认的'bar'类型")
                else:
                    chart['type'] = 'bar'  # 默认类型
                    print("未找到图表类型，使用默认的'bar'类型")
                
            # 检查series
            if 'series' not in chart:
                # 没有series时，看是否有数据可以构建
                if 'data' in chart and isinstance(chart['data'], list):
                    chart['series'] = [{'data': chart['data'], 'type': chart['type']}]
                    print("从chart.data构建series")
                else:
                    print("图表配置缺少series且无法从数据构建")
                    return False
            elif not isinstance(chart['series'], list):
                if isinstance(chart['series'], dict):
                    # 将单个series对象转换为数组
                    chart['series'] = [chart['series']]
                    print("将单个series对象转换为数组")
                else:
                    print("series不是列表类型")
                    return False
            
            # 确保series不为空
            if not chart.get('series'):
                print("series列表为空")
                return False
            
            # 确保每个series都有类型和数据
            for i, series in enumerate(chart['series']):
                if not isinstance(series, dict):
                    print(f"series[{i}]不是字典类型")
                    return False
                
                if 'type' not in series:
                    series['type'] = chart['type']
                    print(f"为series[{i}]设置类型: {chart['type']}")
                
                if 'data' not in series:
                    print(f"series[{i}]缺少data字段")
                return False
            
            # 确保有标题，如果没有则添加默认标题
            if 'title' not in chart:
                chart['title'] = {"text": "数据分析图表", "left": "center"}
                print("添加了默认标题")
            elif isinstance(chart['title'], str):
                # 将字符串标题转换为对象格式
                title_text = chart['title']
                chart['title'] = {"text": title_text, "left": "center"}
                print(f"将字符串标题 '{title_text}' 转换为对象格式")
            
            # 检查图表类型是否为支持的类型
            supported_types = ['line', 'bar', 'pie', 'scatter', 'radar', 'funnel', 'gauge', 'heatmap']
            if chart['type'] not in supported_types:
                print(f"不支持的图表类型 '{chart.get('type')}'，使用默认的'bar'类型")
                chart['type'] = 'bar'  # 使用默认的柱状图类型
            
            # 处理饼图特殊情况
            if chart['type'] == 'pie':
                # 饼图不需要xAxis和yAxis
                return True
            
            # 验证并修复xAxis
            if 'xAxis' not in chart:
                # 尝试从系列数据中推断x轴数据
                if chart['series'] and 'data' in chart['series'][0]:
                    # 如果series[0].data是对象数组，尝试提取名称
                    series_data = chart['series'][0]['data']
                    if isinstance(series_data, list) and len(series_data) > 0:
                        if isinstance(series_data[0], dict) and 'name' in series_data[0]:
                            x_data = [item['name'] for item in series_data if isinstance(item, dict) and 'name' in item]
                            chart['xAxis'] = {"type": "category", "data": x_data}
                            print("从series[0].data中的name字段构建xAxis.data")
                        else:
                            # 默认x轴
                            chart['xAxis'] = {"type": "category", "data": []}
                            print("添加默认xAxis配置")
                    else:
                        chart['xAxis'] = {"type": "category", "data": []}
                        print("添加默认xAxis配置")
                else:
                    chart['xAxis'] = {"type": "category", "data": []}
                print("添加默认xAxis配置")
            elif not isinstance(chart['xAxis'], dict):
                if isinstance(chart['xAxis'], list):
                    # ECharts支持多x轴，保留列表格式
                    pass
                else:
                    print("xAxis不是字典类型，使用默认配置")
                    chart['xAxis'] = {"type": "category", "data": []}
            
            # 验证并修复yAxis
            if 'yAxis' not in chart:
                print("添加默认yAxis配置")
                chart['yAxis'] = {"type": "value"}
            elif not isinstance(chart['yAxis'], dict):
                if isinstance(chart['yAxis'], list):
                    # ECharts支持多y轴，保留列表格式
                    pass
                else:
                    print("yAxis不是字典类型，使用默认配置")
                    chart['yAxis'] = {"type": "value"}
            
            return True
        except Exception as e:
            print(f"验证图表配置时出错: {str(e)}")
            return False
    
    def _generate_chart_prompt(self, user_query: str, structured_data: str) -> str:
        """
        生成用于请求图表配置的提示词
        
        参数:
            user_query: 用户查询
            structured_data: 结构化数据（JSON格式）
            
        返回:
            提示词
        """
        return f"""
请分析以下用户查询和数据，生成2-3个最合适的图表配置，用于可视化分析结果。

用户查询:
{user_query}

数据（JSON格式）:
{structured_data}

请使用标准的ECharts配置格式，生成一个包含"charts"数组的JSON对象。每个图表对象必须包含：
- type: 图表类型（例如：bar, line, pie 等）
- title: 图表标题
- xAxis: 横轴配置 (包含data数组)
- yAxis: 纵轴配置
- series: 系列数组，每个系列包含data字段

请务必遵循以下规则：
1. 返回的必须是完全有效的JSON对象，严格检查格式正确性
2. 确保所有大括号和中括号正确闭合，属性名使用双引号
3. 属性之间使用逗号分隔，最后一个属性后不要加逗号
4. 所有字段名使用英文，值可以使用中文
5. 针对用户查询提供最有信息量的可视化
6. 简单、清晰的图表比复杂的更好
7. 返回的格式必须是带有"charts"数组的JSON对象

示例格式：
```json
{{
  "charts": [
    {{
      "type": "bar",
      "title": {{
        "text": "门诊量趋势分析",
        "left": "center"
      }},
      "xAxis": {{
        "type": "category",
        "data": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
      }},
      "yAxis": {{
        "type": "value",
        "name": "门诊量"
      }},
      "series": [
        {{
          "data": [120, 200, 150, 80, 70, 110, 130],
          "type": "bar"
        }}
      ]
    }},
    {{
      "type": "line",
      "title": {{
        "text": "同环比分析",
        "left": "center"
      }},
      "xAxis": {{
        "type": "category",
        "data": ["1月", "2月", "3月", "4月", "5月", "6月"]
      }},
      "yAxis": {{
        "type": "value",
        "name": "增长率%"
      }},
      "series": [
        {{
          "name": "同比增长",
          "data": [10, -2, 5, 8, -4, 6],
          "type": "line"
        }},
        {{
          "name": "环比增长",
          "data": [5, 3, -1, 4, -2, 3],
          "type": "line"
        }}
      ]
    }}
  ]
}}
```

只返回符合要求的JSON对象，不要有其他文字说明，确保图表配置完全符合ECharts格式规范。
""" 

    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        解析LLM响应中的图表配置JSON
        
        参数:
            response: LLM响应文本
            
        返回:
            解析后的图表配置
        """
        try:
            if not response or not isinstance(response, str):
                print("LLM响应为空或非字符串类型")
                return {"charts": []}
            
            print(f"LLM原始响应 (截断至200字符): {response[:200]}...")
            
            # 1. 首先尝试提取Markdown代码块
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
            if json_match:
                extracted_json = json_match.group(1).strip()
                print("成功从Markdown代码块中提取JSON内容")
            else:
                # 2. 尝试提取大括号内容
                json_start = response.find('{')
                json_end = response.rfind('}')
                if json_start >= 0 and json_end > json_start:
                    extracted_json = response[json_start:json_end+1].strip()
                    print(f"从原始响应中提取JSON内容，长度为 {len(extracted_json)}")
                else:
                    extracted_json = response
                    print("未找到JSON标记，使用完整响应")
                
            # 安全解析部分
            result = None
            try:
                result = robust_json_parser(extracted_json)
                if not result:
                    print("使用健壮JSON解析器无法获取有效图表配置")
            except Exception as e:
                print(f"使用健壮JSON解析器时出错: {str(e)}")
                result = None
            
            # 如果健壮解析器无法解析，尝试更激进的修复
            if not result:
                try:
                    # 尝试修复JSON
                    fixed_json = aggressive_json_fix(extracted_json)
                    if fixed_json:
                        result = json.loads(fixed_json)
                except Exception as e:
                    print(f"使用激进JSON修复时出错: {str(e)}")
                    result = None
                
                # 如果激进修复失败，尝试提取JSON对象
                if not result:
                    try:
                        json_obj = extract_json_object(extracted_json)
                        if json_obj:
                            result = json.loads(json_obj)
                    except Exception as e:
                        print(f"提取JSON对象时出错: {str(e)}")
                        result = None
            
            # 处理解析结果
            if result:
                # 处理包含charts数组的对象
                if isinstance(result, dict) and 'charts' in result:
                    charts = result['charts']
                    if isinstance(charts, list):
                        valid_charts = []
                        for chart in charts:
                            if self._validate_chart_config(chart):
                                self._add_field_mapping(chart)
                                valid_charts.append(chart)
                        
                        if valid_charts:
                            print(f"成功验证 {len(valid_charts)} 个有效图表配置")
                            result['charts'] = valid_charts
                            return result
                        else:
                            print("所有图表配置都无效")
                            return {"charts": []}
                
                # 处理单个图表对象
                elif isinstance(result, dict) and self._validate_chart_config(result):
                    print("发现单个图表配置，封装到charts数组中")
                    self._add_field_mapping(result)
                    return {"charts": [result]}
                
                # 处理图表配置数组
                elif isinstance(result, list):
                    valid_charts = []
                    for chart in result:
                        if isinstance(chart, dict) and self._validate_chart_config(chart):
                            self._add_field_mapping(chart)
                            valid_charts.append(chart)
                    
                    if valid_charts:
                        print(f"从数组中提取 {len(valid_charts)} 个有效图表配置")
                        return {"charts": valid_charts}
            
            # 如果所有尝试都失败
            print("无法提取有效的图表配置")
            return {"charts": []}
        
        except Exception as e:
            print(f"解析LLM响应时出错: {str(e)}")
            traceback.print_exc()
            return {"charts": []}
    
    def _add_field_mapping(self, chart: Dict[str, Any]) -> None:
        """
        为图表配置添加必要的字段映射
        
        参数:
            chart: 图表配置字典
        """
        if 'field_mapping' not in chart or not chart['field_mapping']:
            chart_type = chart.get('type', '')
            field_mapping = {}
            
            # 从图表配置中推断字段映射
            if chart_type in ['bar', 'line']:
                # 从xAxis和series中获取实际字段名
                if 'xAxis' in chart and isinstance(chart['xAxis'], dict) and 'data' in chart['xAxis']:
                    # 如果xAxis数据是一个列表，通常是直接的类别值而不是字段引用
                    # 我们需要找出这是哪个字段的值，暂时使用通用字段名
                    field_mapping['x'] = chart.get('xAxis', {}).get('name', '日期')
                
                # 获取y轴数据
                if 'series' in chart and isinstance(chart['series'], list):
                    if len(chart['series']) == 1:
                        # 单系列
                        series = chart['series'][0]
                        field_name = series.get('name')
                        # 使用series名称作为字段名，如果没有则使用通用名称
                        field_mapping['y'] = field_name if field_name else '数值'
                    else:
                        # 多系列，每个系列使用自己的名称
                        series_names = []
                        for s in chart['series']:
                            name = s.get('name')
                            if name:
                                series_names.append(name)
                            else:
                                # 如果没有名称，使用索引
                                series_names.append(f'系列{len(series_names)+1}')
                        
                        field_mapping['y'] = series_names
            
            elif chart_type == 'pie':
                # 饼图默认字段映射
                field_mapping = {
                    'name': '类别',
                    'value': '数值'
                }
                
            elif chart_type == 'scatter':
                # 散点图默认字段映射
                field_mapping = {
                    'x': 'x轴',
                    'y': 'y轴'
                }
            
            # 添加字段映射到图表配置
            chart['field_mapping'] = field_mapping
            print(f"为 {chart.get('title', chart_type)} 图表添加了默认字段映射: {field_mapping}") 