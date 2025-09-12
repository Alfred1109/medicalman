"""
图表服务模块 - 处理医疗数据图表生成和解析 (Vega-Lite)
"""
import json
import re
import traceback
import copy
from typing import Dict, Any, Optional, List

from app.services.base_llm_service import BaseLLMService
from app.utils.utils import robust_json_parser, safe_json_dumps, extract_json_object
from app.config import config

class ChartService(BaseLLMService):
    """
    Vega-Lite 图表服务类，处理图表配置生成和解析
    """
    
    def __init__(self, model_name=None, api_key=None, api_url=None):
        """
        初始化 Vega-Lite 图表服务
        
        参数:
            model_name: 模型名称，默认使用环境变量中的设置
            api_key: API密钥，默认使用环境变量中的设置
            api_url: API端点URL，默认使用环境变量中的设置
        """
        super().__init__(model_name, api_key, api_url)
        print(f"初始化ChartService (Vega-Lite)，使用模型: {self.model_name}")
    
    def generate_chart_config(self, user_query: str, structured_data: str) -> Dict[str, Any]:
        """
        根据用户查询和结构化数据生成Vega-Lite图表配置
        
        参数:
            user_query: 用户查询
            structured_data: 结构化数据（JSON格式）
            
        返回:
            Vega-Lite图表配置（JSON格式）
        """
        try:
            # 先尝试智能数据分析生成图表
            auto_charts = self._generate_smart_vega_charts(structured_data, user_query)
            if auto_charts:
                return {"charts": auto_charts}
            
            # 如果自动生成失败，使用LLM生成
            prompt = self._build_vega_generation_prompt(user_query, structured_data)
            
            # 调用大模型，将温度设置更低以减少随机性
            response = self.call_api(
                system_prompt=self._get_vega_system_prompt(),
                user_message=prompt,
                temperature=0.1,
                top_p=0.9
            )
            
            if not response:
                print("生成Vega-Lite图表配置时大模型返回为空")
                return {"charts": []}
            
            # 解析响应
            result = self.parse_llm_response(response)
            
            # 检查结果并增强图表质量
            if result and 'charts' in result and isinstance(result['charts'], list) and len(result['charts']) > 0:
                # 增强图表配置
                enhanced_charts = self._enhance_vega_configs(result['charts'], user_query)
                print(f"成功生成并增强 {len(enhanced_charts)} 个Vega-Lite图表配置")
                return {"charts": enhanced_charts}
            else:
                print("未能生成有效的Vega-Lite图表配置")
                return {"charts": []}
        
        except Exception as e:
            print(f"生成Vega-Lite图表配置时出错: {str(e)}")
            traceback.print_exc()
            return {"charts": []}
    
    def _get_vega_system_prompt(self) -> str:
        """获取Vega-Lite系统提示词"""
        return """你是一个专业的医疗数据分析师助手，擅长根据数据生成Vega-Lite图表配置。
请根据用户查询和数据结构，生成最适合的Vega-Lite图表配置。

Vega-Lite的核心概念：
1. mark: 图形标记类型 (point, line, bar, area, rect, circle等)
2. encoding: 数据到视觉属性的映射
   - x: 横轴映射
   - y: 纵轴映射  
   - color: 颜色映射
   - size: 大小映射
   - opacity: 透明度映射

数据类型：
- quantitative: 数值型数据
- ordinal: 有序分类数据
- nominal: 无序分类数据
- temporal: 时间数据

你应当特别关注：
- 数据的时间序列特征 → temporal类型
- 分类数据的分布情况 → nominal/ordinal类型
- 数值数据的统计特征 → quantitative类型
- 多维度数据的关联关系 → 多重编码
- 异常值和趋势的展示 → 合适的mark类型

返回标准的Vega-Lite规范JSON格式。
"""
    
    def _build_vega_generation_prompt(self, user_query: str, structured_data: str) -> str:
        """构建Vega-Lite生成提示词"""
        return f"""
请根据以下数据生成合适的Vega-Lite图表配置：

用户查询：{user_query}

数据结构：
{structured_data}

要求：
1. 根据用户查询需求选择合适的mark类型
2. 设计合理的encoding映射
3. 使用适当的数据类型 (quantitative, ordinal, nominal, temporal)
4. 添加必要的标题和说明
5. 确保图表清晰易读
6. 返回标准JSON格式的Vega-Lite规范

Vega-Lite配置格式示例：
{{
  "charts": [
    {{
      "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
      "title": "图表标题",
      "mark": "图形标记类型",
      "data": {{"values": [...]}},
      "encoding": {{
        "x": {{"field": "字段名", "type": "数据类型", "title": "轴标题"}},
        "y": {{"field": "字段名", "type": "数据类型", "title": "轴标题"}},
        "color": {{"field": "分类字段", "type": "nominal"}}
      }},
      "width": 400,
      "height": 300
    }}
  ]
}}

请确保返回的JSON格式正确，且包含完整的Vega-Lite规范参数。
"""
    
    def parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        解析LLM响应，提取Vega-Lite图表配置
        
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
    
    def _generate_smart_vega_charts(self, structured_data: str, user_query: str) -> List[Dict[str, Any]]:
        """
        智能数据分析生成Vega-Lite图表
        
        参数:
            structured_data: 结构化数据字符串
            user_query: 用户查询
            
        返回:
            Vega-Lite图表配置列表
        """
        try:
            # 解析结构化数据
            try:
                data = json.loads(structured_data)
            except json.JSONDecodeError:
                print("无法解析结构化数据为JSON")
                return []
            
            # 如果数据是列表且不为空
            if isinstance(data, list) and len(data) > 0:
                return self._analyze_data_for_vega_charts(data, user_query)
            
            # 如果数据是字典且包含results
            elif isinstance(data, dict) and 'results' in data:
                return self._analyze_data_for_vega_charts(data['results'], user_query)
            
            return []
            
        except Exception as e:
            print(f"智能Vega-Lite图表生成失败: {str(e)}")
            return []
    
    def _analyze_data_for_vega_charts(self, data: List[Dict], user_query: str) -> List[Dict[str, Any]]:
        """
        分析数据生成Vega-Lite图表
        
        参数:
            data: 数据列表
            user_query: 用户查询
            
        返回:
            Vega-Lite图表配置列表
        """
        if not data or len(data) == 0:
            return []
        
        try:
            charts = []
            sample = data[0]
            fields = list(sample.keys())
            
            # 分析字段类型
            field_types = self._analyze_field_types_for_vega(data, fields)
            
            print(f"字段类型分析: {field_types}")
            
            # 生成时间序列图表
            time_charts = self._generate_vega_time_series_charts(data, field_types, user_query)
            charts.extend(time_charts)
            
            # 生成分类统计图表
            category_charts = self._generate_vega_category_charts(data, field_types, user_query)
            charts.extend(category_charts)
            
            # 生成分布图表
            distribution_charts = self._generate_vega_distribution_charts(data, field_types, user_query)
            charts.extend(distribution_charts)
            
            # 生成对比图表
            comparison_charts = self._generate_vega_comparison_charts(data, field_types, user_query)
            charts.extend(comparison_charts)
            
            print(f"智能生成了 {len(charts)} 个Vega-Lite图表")
            return charts[:3]  # 限制最多3个图表
            
        except Exception as e:
            print(f"分析数据生成Vega-Lite图表失败: {str(e)}")
            return []
    
    def _analyze_field_types_for_vega(self, data: List[Dict], fields: List[str]) -> Dict[str, str]:
        """
        分析字段类型（针对Vega-Lite）
        
        参数:
            data: 数据列表
            fields: 字段列表
            
        返回:
            字段类型字典 {field: vega_type}
        """
        field_types = {}
        
        for field in fields:
            values = [item.get(field) for item in data if item.get(field) is not None]
            
            if not values:
                field_types[field] = 'nominal'
                continue
            
            # 判断是否为数字类型 → quantitative
            if all(isinstance(v, (int, float)) for v in values):
                field_types[field] = 'quantitative'
            # 判断是否为日期类型 → temporal
            elif all(isinstance(v, str) and self._is_date_string(v) for v in values):
                field_types[field] = 'temporal'
            # 判断是否为有序分类类型 → ordinal
            elif self._is_ordinal_field(field, values):
                field_types[field] = 'ordinal'
            # 判断是否为无序分类类型 → nominal
            elif len(set(str(v) for v in values)) <= min(10, len(values) * 0.5):
                field_types[field] = 'nominal'
            else:
                field_types[field] = 'nominal'
        
        return field_types
    
    def _is_date_string(self, value: str) -> bool:
        """判断字符串是否为日期格式"""
        date_patterns = [
            r'^\d{4}-\d{1,2}-\d{1,2}$',  # YYYY-MM-DD
            r'^\d{4}/\d{1,2}/\d{1,2}$',  # YYYY/MM/DD
            r'^\d{1,2}-\d{1,2}-\d{4}$',  # DD-MM-YYYY
            r'^\d{1,2}/\d{1,2}/\d{4}$',  # DD/MM/YYYY
            r'^\d{4}\.\d{1,2}\.\d{1,2}$' # YYYY.MM.DD
        ]
        return any(re.match(pattern, value) for pattern in date_patterns)
    
    def _is_ordinal_field(self, field: str, values: List) -> bool:
        """判断字段是否为有序分类"""
        ordinal_patterns = [
            ['高', '中', '低'],
            ['优秀', '良好', '一般', '差'],
            ['一级', '二级', '三级', '四级'],
            ['轻度', '中度', '重度'],
            ['早期', '中期', '晚期']
        ]
        
        unique_values = set(str(v) for v in values)
        for pattern in ordinal_patterns:
            if unique_values.issubset(set(pattern)):
                return True
        return False
    
    def _generate_vega_time_series_charts(self, data: List[Dict], field_types: Dict, user_query: str) -> List[Dict[str, Any]]:
        """生成Vega-Lite时间序列图表"""
        charts = []
        
        # 找到时间字段和数值字段
        time_fields = [field for field, ftype in field_types.items() if ftype == 'temporal']
        numeric_fields = [field for field, ftype in field_types.items() if ftype == 'quantitative']
        
        if time_fields and numeric_fields:
            time_field = time_fields[0]
            value_field = numeric_fields[0]
            
            # 按时间排序数据
            sorted_data = sorted(data, key=lambda x: str(x.get(time_field, '')))
            
            chart = {
                "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                "title": {
                    "text": f"{value_field}随时间变化趋势",
                    "fontSize": 16,
                    "fontWeight": "bold",
                    "color": "#333"
                },
                "mark": {
                    "type": "line",
                    "point": True,
                    "interpolate": "monotone",
                    "strokeWidth": 2
                },
                "data": {"values": sorted_data},
                "encoding": {
                    "x": {
                        "field": time_field,
                        "type": "temporal",
                        "title": time_field,
                        "axis": {
                            "format": "%Y-%m-%d",
                            "labelAngle": -45
                        }
                    },
                    "y": {
                        "field": value_field,
                        "type": "quantitative",
                        "title": value_field,
                        "scale": {"zero": False}
                    },
                    "color": {"value": "#4A90E2"},
                    "tooltip": [
                        {"field": time_field, "type": "temporal", "format": "%Y-%m-%d"},
                        {"field": value_field, "type": "quantitative"}
                    ]
                },
                "width": 500,
                "height": 300
            }
            
            charts.append(chart)
        
        return charts
    
    def _generate_vega_category_charts(self, data: List[Dict], field_types: Dict, user_query: str) -> List[Dict[str, Any]]:
        """生成Vega-Lite分类统计图表"""
        charts = []
        
        category_fields = [field for field, ftype in field_types.items() if ftype in ['nominal', 'ordinal']]
        numeric_fields = [field for field, ftype in field_types.items() if ftype == 'quantitative']
        
        if category_fields and numeric_fields:
            category_field = category_fields[0]
            value_field = numeric_fields[0]
            
            # 统计分类数据
            category_stats = {}
            for item in data:
                cat = str(item.get(category_field, '未知'))
                val = item.get(value_field, 0)
                
                if cat in category_stats:
                    category_stats[cat] += val
                else:
                    category_stats[cat] = val
            
            # 转换为图表数据
            chart_data = [{"category": cat, "value": val} for cat, val in category_stats.items()]
            chart_data = sorted(chart_data, key=lambda x: x["value"], reverse=True)[:10]  # 最多10个类别
            
            # 如果类别少于等于6个，生成饼图；否则生成柱状图
            if len(chart_data) <= 6:
                # 饼图
                chart = {
                    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                    "title": {
                        "text": f"{value_field}按{category_field}分布",
                        "fontSize": 16,
                        "fontWeight": "bold"
                    },
                    "mark": {"type": "arc", "innerRadius": 50, "outerRadius": 120},
                    "data": {"values": chart_data},
                    "encoding": {
                        "theta": {"field": "value", "type": "quantitative"},
                        "color": {
                            "field": "category", 
                            "type": "nominal",
                            "scale": {
                                "range": ["#4A90E2", "#7ED321", "#F5A623", "#D0021B", "#9013FE", "#50E3C2"]
                            }
                        },
                        "tooltip": [
                            {"field": "category", "type": "nominal"},
                            {"field": "value", "type": "quantitative"}
                        ]
                    },
                    "width": 300,
                    "height": 300
                }
            else:
                # 柱状图
                chart = {
                    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                    "title": {
                        "text": f"{value_field}按{category_field}统计",
                        "fontSize": 16,
                        "fontWeight": "bold"
                    },
                    "mark": {"type": "bar", "color": "#4A90E2"},
                    "data": {"values": chart_data},
                    "encoding": {
                        "x": {
                            "field": "category",
                            "type": field_types.get(category_field, "nominal"),
                            "title": category_field,
                            "axis": {"labelAngle": -45}
                        },
                        "y": {
                            "field": "value",
                            "type": "quantitative",
                            "title": value_field
                        },
                        "tooltip": [
                            {"field": "category", "type": "nominal"},
                            {"field": "value", "type": "quantitative"}
                        ]
                    },
                    "width": 400,
                    "height": 300
                }
            
            charts.append(chart)
        
        return charts
    
    def _generate_vega_distribution_charts(self, data: List[Dict], field_types: Dict, user_query: str) -> List[Dict[str, Any]]:
        """生成Vega-Lite分布图表"""
        charts = []
        
        numeric_fields = [field for field, ftype in field_types.items() if ftype == 'quantitative']
        
        # 如果有多个数值字段，生成散点图
        if len(numeric_fields) >= 2:
            x_field = numeric_fields[0]
            y_field = numeric_fields[1]
            
            chart = {
                "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                "title": {
                    "text": f"{x_field} vs {y_field} 散点分布",
                    "fontSize": 16,
                    "fontWeight": "bold"
                },
                "mark": {"type": "point", "filled": True, "size": 100, "opacity": 0.7},
                "data": {"values": data},
                "encoding": {
                    "x": {
                        "field": x_field,
                        "type": "quantitative",
                        "title": x_field
                    },
                    "y": {
                        "field": y_field,
                        "type": "quantitative",
                        "title": y_field
                    },
                    "color": {"value": "#4A90E2"},
                    "tooltip": [
                        {"field": x_field, "type": "quantitative"},
                        {"field": y_field, "type": "quantitative"}
                    ]
                },
                "width": 400,
                "height": 300
            }
            
            charts.append(chart)
        
        return charts
    
    def _generate_vega_comparison_charts(self, data: List[Dict], field_types: Dict, user_query: str) -> List[Dict[str, Any]]:
        """生成Vega-Lite对比图表"""
        charts = []
        
        # 如果查询中包含对比关键词
        comparison_keywords = ['对比', '比较', '差异', 'vs', '相比']
        if any(keyword in user_query for keyword in comparison_keywords):
            category_fields = [field for field, ftype in field_types.items() if ftype in ['nominal', 'ordinal']]
            numeric_fields = [field for field, ftype in field_types.items() if ftype == 'quantitative']
            
            if category_fields and len(numeric_fields) >= 2:
                category_field = category_fields[0]
                
                # 准备多指标对比数据
                comparison_data = []
                categories = list(set(str(item.get(category_field, '')) for item in data))[:5]
                
                for category in categories:
                    cat_items = [item for item in data if str(item.get(category_field, '')) == category]
                    for numeric_field in numeric_fields[:3]:  # 最多3个指标
                        values = [item.get(numeric_field, 0) for item in cat_items]
                        avg_value = sum(values) / len(values) if values else 0
                        comparison_data.append({
                            "category": category,
                            "metric": numeric_field,
                            "value": avg_value
                        })
                
                chart = {
                    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                    "title": {
                        "text": "多指标对比分析",
                        "fontSize": 16,
                        "fontWeight": "bold"
                    },
                    "mark": "bar",
                    "data": {"values": comparison_data},
                    "encoding": {
                        "x": {
                            "field": "category",
                            "type": field_types.get(category_field, "nominal"),
                            "title": category_field,
                            "axis": {"labelAngle": -45}
                        },
                        "y": {
                            "field": "value",
                            "type": "quantitative",
                            "title": "数值"
                        },
                        "color": {
                            "field": "metric",
                            "type": "nominal",
                            "title": "指标",
                            "scale": {
                                "range": ["#4A90E2", "#7ED321", "#F5A623"]
                            }
                        },
                        "xOffset": {"field": "metric"},
                        "tooltip": [
                            {"field": "category", "type": "nominal"},
                            {"field": "metric", "type": "nominal"},
                            {"field": "value", "type": "quantitative"}
                        ]
                    },
                    "width": 500,
                    "height": 300
                }
                
                charts.append(chart)
        
        return charts
    
    def _enhance_vega_configs(self, charts: List[Dict[str, Any]], user_query: str) -> List[Dict[str, Any]]:
        """
        增强Vega-Lite图表配置
        
        参数:
            charts: 原始图表配置列表
            user_query: 用户查询
            
        返回:
            增强后的图表配置列表
        """
        enhanced_charts = []
        
        for chart in charts:
            if not isinstance(chart, dict):
                continue
            
            # 深拷贝避免修改原配置
            enhanced = copy.deepcopy(chart)
            
            # 确保有schema
            if "$schema" not in enhanced:
                enhanced["$schema"] = "https://vega.github.io/schema/vega-lite/v5.json"
            
            # 增强配置项
            enhanced = self._add_vega_medical_theme(enhanced)
            enhanced = self._add_vega_interactions(enhanced)
            enhanced = self._add_vega_accessibility(enhanced)
            
            enhanced_charts.append(enhanced)
        
        return enhanced_charts
    
    def _add_vega_medical_theme(self, chart: Dict[str, Any]) -> Dict[str, Any]:
        """添加医疗主题"""
        # 医疗主题配色方案
        medical_colors = ["#4A90E2", "#7ED321", "#F5A623", "#D0021B", "#9013FE", "#50E3C2", "#B8E986", "#4A4A4A"]
        
        # 如果有颜色编码且没有指定颜色范围
        if "encoding" in chart and "color" in chart["encoding"]:
            if "scale" not in chart["encoding"]["color"]:
                chart["encoding"]["color"]["scale"] = {"range": medical_colors}
        
        # 添加医疗主题配置
        chart["config"] = {
            "axis": {
                "labelFontSize": 11,
                "titleFontSize": 12,
                "titleFontWeight": "bold"
            },
            "title": {
                "fontSize": 16,
                "fontWeight": "bold",
                "color": "#333"
            },
            "legend": {
                "labelFontSize": 11,
                "titleFontSize": 12
            }
        }
        
        return chart
    
    def _add_vega_interactions(self, chart: Dict[str, Any]) -> Dict[str, Any]:
        """添加Vega-Lite交互功能"""
        # 添加选择交互
        chart["params"] = [
            {
                "name": "hover",
                "select": {"type": "point", "on": "mouseover"}
            }
        ]
        
        # 为mark添加交互效果
        if isinstance(chart.get("mark"), str):
            chart["mark"] = {
                "type": chart["mark"],
                "cursor": "pointer"
            }
        elif isinstance(chart.get("mark"), dict):
            chart["mark"]["cursor"] = "pointer"
        
        return chart
    
    def _add_vega_accessibility(self, chart: Dict[str, Any]) -> Dict[str, Any]:
        """添加可访问性支持"""
        # 确保有描述
        if "description" not in chart:
            chart["description"] = "医疗数据可视化图表"
        
        # 确保有合适的宽高比
        if "width" not in chart:
            chart["width"] = 400
        if "height" not in chart:
            chart["height"] = 300
        
        return chart
    
    # 保持向后兼容的方法名
    def extract_chart_configs(self, content: str) -> List[Dict[str, Any]]:
        """向后兼容：从响应中提取图表配置"""
        result = self.parse_llm_response(content)
        return result.get('charts', []) if result else []
    
    def _generate_chart_prompt(self, user_query: str, structured_data: str) -> str:
        """向后兼容：生成图表配置的提示词"""
        return self._build_vega_generation_prompt(user_query, structured_data)