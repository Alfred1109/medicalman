"""
响应生成表示器模块
"""
from typing import Dict, List, Any, Optional, Union
import json
from flask import jsonify

class ResponsePresenter:
    """响应生成表示器类"""
    
    @staticmethod
    def format_success_response(data: Any = None, message: str = None) -> Dict[str, Any]:
        """
        格式化成功响应
        
        参数:
            data: 响应数据
            message: 响应消息
            
        返回:
            格式化的响应字典
        """
        response = {'success': True}
        
        if data is not None:
            response['data'] = data
            
        if message is not None:
            response['message'] = message
            
        return response
    
    @staticmethod
    def format_error_response(error: str, code: int = 400) -> Dict[str, Any]:
        """
        格式化错误响应
        
        参数:
            error: 错误消息
            code: 错误代码
            
        返回:
            格式化的响应字典
        """
        return {
            'success': False,
            'error': error,
            'code': code
        }
    
    @staticmethod
    def format_pagination_response(data: List[Any], page: int, per_page: int, 
                                  total: int) -> Dict[str, Any]:
        """
        格式化分页响应
        
        参数:
            data: 分页数据
            page: 当前页码
            per_page: 每页数量
            total: 总数量
            
        返回:
            格式化的分页响应字典
        """
        total_pages = (total + per_page - 1) // per_page  # 向上取整
        
        return {
            'success': True,
            'data': data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        }
    
    @staticmethod
    def format_chart_response(chart_config: Dict[str, Any], 
                             data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        格式化图表响应
        
        参数:
            chart_config: 图表配置
            data: 原始数据
            
        返回:
            格式化的图表响应字典
        """
        response = {
            'success': True,
            'chart_config': chart_config
        }
        
        if data is not None:
            response['data'] = data
            
        return response
    
    @staticmethod
    def format_analysis_response(analysis: str, 
                               data: Optional[List[Dict[str, Any]]] = None,
                               chart_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        格式化分析响应
        
        参数:
            analysis: 分析文本
            data: 原始数据
            chart_config: 图表配置
            
        返回:
            格式化的分析响应字典
        """
        response = {
            'success': True,
            'analysis': analysis
        }
        
        if data is not None:
            response['data'] = data
            
        if chart_config is not None:
            response['chart_config'] = chart_config
            
        return response 