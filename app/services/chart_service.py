"""
图表服务模块 - 处理医疗数据图表生成和解析
"""
import json
import re
import traceback
from typing import Dict, Any, Optional, List
import copy

from app.services.base_llm_service import BaseLLMService
from app.utils.json_helper import robust_json_parser

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
            
            return True
            
        except Exception as e:
            print(f"验证图表配置时出错: {str(e)}")
            traceback.print_exc()
            return False
    
    def _generate_chart_prompt(self, user_query, structured_data):
        """
        生成用于图表分析的提示
        
        参数:
            user_query: 用户查询
            structured_data: 结构化数据
            
        返回:
            生成的提示词
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