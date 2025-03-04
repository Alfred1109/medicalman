import random
from typing import List, Dict, Any
import pandas as pd

def generate_random_colors(count: int) -> List[str]:
    """生成随机颜色"""
    colors = []
    for _ in range(count):
        r = random.randint(100, 200)
        g = random.randint(100, 200)
        b = random.randint(100, 200)
        colors.append(f'rgba({r}, {g}, {b}, 0.7)')
    return colors

def generate_chart_data(df: pd.DataFrame, chart_type: str, x_field: str, y_field: str, title: str) -> Dict[str, Any]:
    """
    根据数据生成Chart.js图表配置
    
    参数:
        df: 数据框
        chart_type: 图表类型 (bar/line/pie)
        x_field: X轴字段
        y_field: Y轴字段
        title: 图表标题
        
    返回:
        Dict: Chart.js配置
    """
    if df is None or df.empty:
        return None
    
    labels = df[x_field].tolist()
    data = df[y_field].tolist()
    
    # 生成随机颜色
    colors = generate_random_colors(len(labels))
    
    chart_config = {
        'type': chart_type,
        'data': {
            'labels': labels,
            'datasets': [{
                'label': y_field,
                'data': data,
                'backgroundColor': colors if chart_type in ['bar', 'pie', 'doughnut'] else 'rgba(75, 192, 192, 0.2)',
                'borderColor': 'rgba(75, 192, 192, 1)' if chart_type == 'line' else colors,
                'borderWidth': 1
            }]
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'title': {
                    'display': True,
                    'text': title
                },
                'legend': {
                    'display': True,
                    'position': 'top'
                }
            }
        }
    }
    
    return chart_config

def generate_dynamic_charts(query_results: Dict[str, pd.DataFrame], visualization_plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    根据查询结果和可视化计划生成图表
    
    参数:
        query_results: 查询结果字典
        visualization_plan: 可视化计划列表
        
    返回:
        List[Dict]: 图表配置列表
    """
    charts = []
    
    try:
        print("\n=== 开始生成图表 ===")
        print(f"可视化计划数量: {len(visualization_plan)}")
        
        for i, viz in enumerate(visualization_plan):
            print(f"\n处理图表 {i+1}:")
            print(f"类型: {viz.get('type')}")
            print(f"字段映射: {viz.get('field_mapping')}")
            
            data_source = f"query_{viz['data_source']}"
            if data_source not in query_results:
                print(f"找不到数据源: {data_source}")
                continue
                
            df = query_results[data_source]
            if df.empty:
                print(f"数据源为空: {data_source}")
                continue
                
            print(f"数据源行数: {len(df)}")
            
            if viz['type'] == 'mixed':
                # 处理混合图表（柱状图+折线图）
                field_mapping = viz['field_mapping']
                x_field = field_mapping.get('x')
                y1_field = field_mapping.get('y1')
                y2_field = field_mapping.get('y2')
                
                if not all([x_field, y1_field, y2_field]):
                    print("混合图表缺少必要的字段映射")
                    continue
                    
                if not all(field in df.columns for field in [x_field, y1_field, y2_field]):
                    print("数据中缺少必要的字段")
                    continue
                
                labels = df[x_field].tolist()
                colors = viz.get('style', {}).get('colors', ['#4e79a7', '#e15759'])
                
                chart_config = {
                    'type': 'mixed',
                    'data': {
                        'labels': labels,
                        'datasets': [
                            {
                                'type': 'bar',
                                'label': y1_field,
                                'data': df[y1_field].tolist(),
                                'backgroundColor': colors[0],
                                'borderColor': colors[0],
                                'borderWidth': 1,
                                'order': 1
                            },
                            {
                                'type': 'line',
                                'label': y2_field,
                                'data': df[y2_field].tolist(),
                                'borderColor': colors[1],
                                'backgroundColor': 'transparent',
                                'borderWidth': 2,
                                'order': 0
                            }
                        ]
                    },
                    'options': {
                        'responsive': True,
                        'maintainAspectRatio': False,
                        'plugins': {
                            'title': {
                                'display': True,
                                'text': viz['title']
                            },
                            'legend': {
                                'display': True,
                                'position': 'top'
                            }
                        }
                    }
                }
                charts.append({"title": viz['title'], "config": chart_config})
                print(f"成功生成混合图表: {viz['title']}")
                
            elif viz['type'] == 'scatter':
                # 处理散点图
                field_mapping = viz['field_mapping']
                x_field = field_mapping.get('x')
                y_field = field_mapping.get('y')
                size_field = field_mapping.get('size')
                color_field = field_mapping.get('color')
                
                if not all([x_field, y_field]):
                    print("散点图缺少必要的字段映射")
                    continue
                    
                if not all(field in df.columns for field in [x_field, y_field]):
                    print("数据中缺少必要的字段")
                    continue
                
                # 生成散点图数据
                data = []
                categories = df[color_field].unique() if color_field else [None]
                colors = generate_random_colors(len(categories))
                
                for i, category in enumerate(categories):
                    mask = df[color_field] == category if color_field else pd.Series([True] * len(df))
                    cat_data = {
                        'label': str(category) if category is not None else '数据点',
                        'data': [
                            {
                                'x': x,
                                'y': y,
                                'r': s/100 if size_field else 5  # 调整大小比例
                            }
                            for x, y, s in zip(
                                df[mask][x_field],
                                df[mask][y_field],
                                df[mask][size_field] if size_field else [500] * len(df[mask])
                            )
                        ],
                        'backgroundColor': colors[i],
                        'borderColor': colors[i],
                        'borderWidth': 1
                    }
                    data.append(cat_data)
                
                chart_config = {
                    'type': 'scatter',
                    'data': {
                        'datasets': data
                    },
                    'options': {
                        'responsive': True,
                        'maintainAspectRatio': False,
                        'plugins': {
                            'title': {
                                'display': True,
                                'text': viz['title']
                            },
                            'legend': {
                                'display': bool(color_field),
                                'position': 'top'
                            }
                        },
                        'scales': {
                            'x': {
                                'title': {
                                    'display': True,
                                    'text': x_field
                                }
                            },
                            'y': {
                                'title': {
                                    'display': True,
                                    'text': y_field
                                }
                            }
                        }
                    }
                }
                charts.append({"title": viz['title'], "config": chart_config})
                print(f"成功生成散点图: {viz['title']}")
                
            else:
                # 处理基本图表类型
                field_mapping = viz['field_mapping']
                x_field = field_mapping.get('x')
                y_field = field_mapping.get('y')
                
                if not all([x_field, y_field]):
                    print(f"图表缺少必要的字段映射: x={x_field}, y={y_field}")
                    continue
                    
                if not all(field in df.columns for field in [x_field, y_field]):
                    print(f"数据中缺少必要的字段: {[x_field, y_field]}")
                    continue
                
                chart = generate_chart_data(
                    df=df,
                    chart_type=viz['type'],
                    x_field=x_field,
                    y_field=y_field,
                    title=viz['title']
                )
                if chart:
                    charts.append({"title": viz['title'], "config": chart})
                    print(f"成功生成{viz['type']}图表: {viz['title']}")
        
        print(f"\n总共生成了 {len(charts)} 个图表")
        return charts
        
    except Exception as e:
        print(f"生成图表时出错: {str(e)}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")
        return [] 