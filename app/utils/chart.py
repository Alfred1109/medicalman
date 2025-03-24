import random
import pandas as pd
from typing import List, Dict, Any

def generate_random_colors(count):
    """
    生成随机颜色列表
    
    参数:
        count (int): 需要生成的颜色数量
        
    返回:
        list: 颜色值列表，格式为rgba字符串
    """
    colors = []
    for _ in range(count):
        r = random.randint(100, 200)
        g = random.randint(100, 200)
        b = random.randint(100, 200)
        colors.append(f'rgba({r}, {g}, {b}, 0.7)')
    return colors

def generate_chart_data(df, chart_type, x_field, y_field, title):
    """
    根据数据生成Chart.js图表配置
    
    参数:
        df (pandas.DataFrame): 数据帧
        chart_type (str): 图表类型，如'bar', 'line', 'pie'等
        x_field (str): X轴字段名
        y_field (str): Y轴字段名
        title (str): 图表标题
        
    返回:
        dict: Chart.js配置对象
    """
    if df.empty:
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

def generate_dynamic_charts(chart_config, data):
    """
    根据图表配置和数据生成图表
    
    参数:
        chart_config (Dict): 包含图表配置的字典
        data (List[Dict]): 数据列表
        
    返回:
        List[Dict]: 图表配置列表
    """
    charts = []
    
    try:
        print("\n=== 开始生成图表 ===")
        
        # 处理传入的是图表配置对象的情况
        visualization_plan = []
        if isinstance(chart_config, dict) and "charts" in chart_config:
            visualization_plan = chart_config["charts"]
        else:
            visualization_plan = chart_config if isinstance(chart_config, list) else []
            
        print(f"可视化计划数量: {len(visualization_plan)}")
        
        # 将数据列表转换为DataFrame
        df = pd.DataFrame(data) if data else pd.DataFrame()
        # 创建一个包含数据帧的字典
        query_results = {"main_query": df}
        
        if not df.empty:
            print(f"数据列: {df.columns.tolist()}")
        
        for i, viz in enumerate(visualization_plan):
            print(f"\n处理图表 {i+1}:")
            print(f"类型: {viz.get('type')}")
            print(f"字段映射: {viz.get('field_mapping')}")
            
            # 确定数据源
            data_source_key = "main_query"  # 默认使用main_query作为数据源
            if 'data_source' in viz:
                data_source_key = f"query_{viz['data_source']}"
                if data_source_key not in query_results:
                    # 如果指定的数据源不存在，回退到主查询
                    print(f"找不到数据源: {data_source_key}，使用main_query")
                    data_source_key = "main_query"
            
            df = query_results[data_source_key]
            if df.empty:
                print(f"数据源为空: {data_source_key}")
                continue
                
            print(f"数据源行数: {len(df)}")
            
            # 如果没有指定标题，生成一个默认标题
            if 'title' not in viz:
                viz['title'] = f"图表 {i+1}"
                
            if not viz.get('type'):
                viz['type'] = 'bar'  # 默认图表类型
            
            # 尝试自动生成字段映射（如果没有提供）
            if not viz.get('field_mapping'):
                field_mapping = auto_generate_field_mapping(df, viz['type'])
                viz['field_mapping'] = field_mapping
                print(f"自动生成字段映射: {field_mapping}")
            else:
                # 验证和修复现有字段映射
                field_mapping = fix_field_mapping(df, viz.get('field_mapping', {}), viz['type'])
                viz['field_mapping'] = field_mapping
                print(f"修复后的字段映射: {field_mapping}")
            
            # 如果字段映射仍然为空，跳过此图表
            if not viz.get('field_mapping'):
                print(f"图表 {i+1} 缺少字段映射")
                continue
                
            # 处理不同类型的图表
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
                    print(f"数据中缺少必要的字段: {[x_field, y1_field, y2_field]}")
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

def auto_generate_field_mapping(df, chart_type):
    """
    根据数据框和图表类型自动生成字段映射
    
    参数:
        df (pd.DataFrame): 数据框
        chart_type (str): 图表类型
        
    返回:
        dict: 字段映射
    """
    field_mapping = {}
    columns = df.columns.tolist()
    
    if not columns:
        return field_mapping
    
    # 常见的日期/时间列名
    date_patterns = ['日期', '时间', '年份', '月份', '季度', 'date', 'time', 'year', 'month', 'day', '周']
    
    # 常见的度量列名
    measure_patterns = ['数量', '金额', '值', '总数', '平均', '比例', '率', 
                       'count', 'amount', 'value', 'total', 'average', 'ratio', 'rate', '量']
    
    # 尝试找到日期/类别列作为x轴
    x_column = None
    for pattern in date_patterns:
        matching = [col for col in columns if pattern.lower() in col.lower()]
        if matching:
            x_column = matching[0]
            break
    
    # 如果没有找到日期列，使用第一列作为x轴
    if not x_column and len(columns) > 0:
        x_column = columns[0]
    
    # 从其余列中找到可能的y轴指标
    y_columns = []
    if x_column:
        remaining = [col for col in columns if col != x_column]
        
        # 优先选择包含度量词的列
        for col in remaining:
            if any(pattern.lower() in col.lower() for pattern in measure_patterns):
                y_columns.append(col)
        
        # 如果没有找到符合条件的列，使用所有剩余的列
        if not y_columns:
            y_columns = remaining
    
    # 构建字段映射
    if x_column:
        field_mapping['x'] = x_column
        
        if chart_type in ['bar', 'line'] and y_columns:
            if len(y_columns) == 1:
                field_mapping['y'] = y_columns[0]
            else:
                field_mapping['y1'] = y_columns[0]
                if len(y_columns) > 1:
                    field_mapping['y2'] = y_columns[1]
        
        elif chart_type == 'pie' and y_columns:
            field_mapping = {
                'name': x_column,
                'value': y_columns[0]
            }
        
        elif chart_type == 'scatter' and len(y_columns) > 0:
            field_mapping = {
                'x': x_column,
                'y': y_columns[0]
            }
            if len(y_columns) > 1:
                field_mapping['size'] = y_columns[1]
    
    return field_mapping

def fix_field_mapping(df, field_mapping, chart_type):
    """
    验证和修复字段映射，确保它与实际数据列匹配
    
    参数:
        df (pd.DataFrame): 数据框
        field_mapping (dict): 原始字段映射
        chart_type (str): 图表类型
        
    返回:
        dict: 修复后的字段映射
    """
    fixed_mapping = {}
    columns = df.columns.tolist()
    
    if not columns or not field_mapping:
        return auto_generate_field_mapping(df, chart_type)
    
    # 处理x字段
    if 'x' in field_mapping:
        x_field = field_mapping['x']
        # 检查是否存在
        if x_field in columns:
            fixed_mapping['x'] = x_field
        else:
            # 尝试智能匹配
            similar_fields = find_similar_fields(x_field, columns)
            if similar_fields:
                fixed_mapping['x'] = similar_fields[0]
                print(f"将字段映射 'x' 从 '{x_field}' 修改为 '{similar_fields[0]}'")
            else:
                # 如果找不到类似的字段，使用第一列
                if columns:
                    fixed_mapping['x'] = columns[0]
                    print(f"找不到类似于 '{x_field}' 的字段，使用 '{columns[0]}' 作为x轴")
    
    # 处理y字段 - 可能是单个字段或列表
    if 'y' in field_mapping:
        y_field = field_mapping['y']
        if isinstance(y_field, list):
            # 多系列
            y_fields = []
            for field in y_field:
                if field in columns:
                    y_fields.append(field)
                else:
                    similar_fields = find_similar_fields(field, columns)
                    if similar_fields:
                        y_fields.append(similar_fields[0])
                        print(f"将字段映射 'y' 从 '{field}' 修改为 '{similar_fields[0]}'")
            
            if y_fields:
                fixed_mapping['y'] = y_fields
            else:
                # 如果找不到任何匹配，尝试使用数值列
                numeric_cols = [col for col in columns if pd.api.types.is_numeric_dtype(df[col])]
                if numeric_cols:
                    fixed_mapping['y'] = numeric_cols[0]
                    print(f"找不到匹配的字段，使用数值列 '{numeric_cols[0]}' 作为y轴")
        else:
            # 单系列
            if y_field in columns:
                fixed_mapping['y'] = y_field
            else:
                similar_fields = find_similar_fields(y_field, columns)
                if similar_fields:
                    fixed_mapping['y'] = similar_fields[0]
                    print(f"将字段映射 'y' 从 '{y_field}' 修改为 '{similar_fields[0]}'")
                else:
                    # 如果找不到类似的字段，使用除x以外的第一列
                    remaining = [col for col in columns if col != fixed_mapping.get('x')]
                    if remaining:
                        fixed_mapping['y'] = remaining[0]
                        print(f"找不到类似于 '{y_field}' 的字段，使用 '{remaining[0]}' 作为y轴")
    
    # 处理y1, y2字段 (混合图表)
    for key in ['y1', 'y2']:
        if key in field_mapping:
            field_value = field_mapping[key]
            if field_value in columns:
                fixed_mapping[key] = field_value
            else:
                similar_fields = find_similar_fields(field_value, columns)
                if similar_fields:
                    fixed_mapping[key] = similar_fields[0]
                    print(f"将字段映射 '{key}' 从 '{field_value}' 修改为 '{similar_fields[0]}'")
    
    # 处理饼图特殊字段
    if chart_type == 'pie':
        for key in ['name', 'value']:
            if key in field_mapping:
                field_value = field_mapping[key]
                if field_value in columns:
                    fixed_mapping[key] = field_value
                else:
                    similar_fields = find_similar_fields(field_value, columns)
                    if similar_fields:
                        fixed_mapping[key] = similar_fields[0]
                        print(f"将饼图字段映射 '{key}' 从 '{field_value}' 修改为 '{similar_fields[0]}'")
    
    # 如果无法修复，使用自动生成
    if not fixed_mapping or ('x' not in fixed_mapping and chart_type != 'pie'):
        print(f"无法修复字段映射，将使用自动生成")
        return auto_generate_field_mapping(df, chart_type)
    
    return fixed_mapping

def find_similar_fields(target_field, column_list):
    """
    查找与目标字段相似的列名
    
    参数:
        target_field (str): 目标字段
        column_list (list): 列名列表
        
    返回:
        list: 相似列名列表，按相似度排序
    """
    if not target_field or not column_list:
        return []
    
    # 常见字段映射
    common_mappings = {
        'date': ['日期', '时间', '年份', '月份', '时段', '周'],
        'value': ['数量', '值', '数值', '总量', '金额'],
        'name': ['名称', '类别', '分类', '品类', '品种', '种类']
    }
    
    # 特殊情况处理
    lower_target = target_field.lower()
    if lower_target in common_mappings:
        # 检查是否有常见映射匹配
        for pattern in common_mappings[lower_target]:
            matches = [col for col in column_list if pattern.lower() in col.lower()]
            if matches:
                return matches
    
    # 基于部分匹配查找
    matches = [col for col in column_list if lower_target in col.lower() or col.lower() in lower_target]
    if matches:
        return matches
    
    # 通用情况 - 查找任何数值列
    if lower_target in ['value', 'y', 'data', '数值', '值']:
        import pandas as pd
        numeric_cols = [col for col in column_list if '数' in col or '量' in col or '率' in col or '值' in col]
        if numeric_cols:
            return numeric_cols
    
    return [] 