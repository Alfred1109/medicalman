"""
图表生成表示器模块
"""
from typing import Dict, List, Any, Optional
import random
import json

class ChartPresenter:
    """图表生成表示器类"""
    
    @staticmethod
    def generate_chart_config(chart_type: str, labels: List[str], data: List[float], 
                             title: str, x_label: str = '', y_label: str = '') -> Dict[str, Any]:
        """
        生成Chart.js图表配置
        
        参数:
            chart_type: 图表类型（bar, line, pie, doughnut等）
            labels: 标签列表
            data: 数据列表
            title: 图表标题
            x_label: X轴标签
            y_label: Y轴标签
            
        返回:
            Chart.js配置对象
        """
        # 生成随机颜色
        colors = ChartPresenter._generate_random_colors(len(labels))
        
        # 创建基本配置
        chart_config = {
            'type': chart_type,
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': title,
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
                        'display': chart_type in ['pie', 'doughnut']
                    },
                    'tooltip': {
                        'enabled': True
                    }
                }
            }
        }
        
        # 添加坐标轴配置（对于条形图和折线图）
        if chart_type in ['bar', 'line']:
            chart_config['options']['scales'] = {
                'x': {
                    'title': {
                        'display': bool(x_label),
                        'text': x_label
                    }
                },
                'y': {
                    'title': {
                        'display': bool(y_label),
                        'text': y_label
                    },
                    'beginAtZero': True
                }
            }
        
        return chart_config
    
    @staticmethod
    def generate_multi_series_chart_config(chart_type: str, labels: List[str], 
                                          datasets: List[Dict[str, Any]], 
                                          title: str, x_label: str = '', 
                                          y_label: str = '') -> Dict[str, Any]:
        """
        生成多系列Chart.js图表配置
        
        参数:
            chart_type: 图表类型（bar, line等）
            labels: 标签列表
            datasets: 数据集列表，每个数据集包含label和data
            title: 图表标题
            x_label: X轴标签
            y_label: Y轴标签
            
        返回:
            Chart.js配置对象
        """
        # 生成随机颜色
        colors = ChartPresenter._generate_random_colors(len(datasets))
        
        # 创建数据集配置
        formatted_datasets = []
        for i, dataset in enumerate(datasets):
            formatted_dataset = {
                'label': dataset['label'],
                'data': dataset['data'],
                'backgroundColor': colors[i] if chart_type == 'bar' else f'rgba({colors[i]}, 0.2)',
                'borderColor': colors[i],
                'borderWidth': 1
            }
            
            # 添加数据集特定配置
            if 'fill' in dataset:
                formatted_dataset['fill'] = dataset['fill']
            
            if 'tension' in dataset:
                formatted_dataset['tension'] = dataset['tension']
            
            formatted_datasets.append(formatted_dataset)
        
        # 创建基本配置
        chart_config = {
            'type': chart_type,
            'data': {
                'labels': labels,
                'datasets': formatted_datasets
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': title
                    },
                    'tooltip': {
                        'enabled': True
                    }
                }
            }
        }
        
        # 添加坐标轴配置
        chart_config['options']['scales'] = {
            'x': {
                'title': {
                    'display': bool(x_label),
                    'text': x_label
                }
            },
            'y': {
                'title': {
                    'display': bool(y_label),
                    'text': y_label
                },
                'beginAtZero': True
            }
        }
        
        return chart_config
    
    @staticmethod
    def _generate_random_colors(count: int) -> List[str]:
        """
        生成随机颜色列表
        
        参数:
            count: 颜色数量
            
        返回:
            颜色列表
        """
        colors = []
        for _ in range(count):
            r = random.randint(100, 200)
            g = random.randint(100, 200)
            b = random.randint(100, 200)
            colors.append(f'rgba({r}, {g}, {b}, 0.7)')
        return colors 