"""
LLM服务工厂模块 - 提供创建和管理各种LLM服务的工厂
"""
import os
from typing import Dict, Any, Optional

from app.services.base_llm_service import BaseLLMService
from app.services.sql_service import SQLService
from app.services.chart_service import ChartService
from app.services.text_analysis_service import TextAnalysisService
from app.services.knowledge_base_service import KnowledgeBaseService

# 导入环境变量中定义的模型配置
VOLCENGINE_MODEL = os.getenv("VOLCENGINE_MODEL", "deepseek-v3-241226")

class LLMServiceFactory:
    """
    LLM服务工厂类
    用于创建和管理不同类型的LLM服务实例
    """
    
    _instances = {}  # 服务实例缓存，用于单例模式
    
    @classmethod
    def get_sql_service(cls, model_name=None):
        """
        获取SQL服务实例
        
        参数:
            model_name: 可选的模型名称，默认使用环境变量中的配置
            
        返回:
            SQLService实例
        """
        key = f"sql_{model_name or VOLCENGINE_MODEL}"
        if key not in cls._instances:
            cls._instances[key] = SQLService(model_name)
        return cls._instances[key]
    
    @classmethod
    def get_chart_service(cls, model_name=None):
        """
        获取图表服务实例
        
        参数:
            model_name: 可选的模型名称，默认使用环境变量中的配置
            
        返回:
            ChartService实例
        """
        key = f"chart_{model_name or VOLCENGINE_MODEL}"
        if key not in cls._instances:
            cls._instances[key] = ChartService(model_name)
        return cls._instances[key]
    
    @classmethod
    def get_knowledge_base_service(cls, model_name=None):
        """
        获取知识库服务实例
        
        参数:
            model_name: 可选的模型名称，默认使用环境变量中的配置
            
        返回:
            KnowledgeBaseService实例
        """
        key = f"kb_{model_name or VOLCENGINE_MODEL}"
        if key not in cls._instances:
            cls._instances[key] = KnowledgeBaseService(model_name)
        return cls._instances[key]
    
    @classmethod
    def get_text_analysis_service(cls, model_name=None):
        """
        获取文本分析服务实例
        
        参数:
            model_name: 可选的模型名称，默认使用环境变量中的配置
            
        返回:
            TextAnalysisService实例
        """
        key = f"text_{model_name or VOLCENGINE_MODEL}"
        if key not in cls._instances:
            cls._instances[key] = TextAnalysisService(model_name)
        return cls._instances[key]
    
    @classmethod
    def get_base_service(cls, model_name=None):
        """
        获取基础LLM服务实例
        
        参数:
            model_name: 可选的模型名称，默认使用环境变量中的配置
            
        返回:
            BaseLLMService实例
        """
        key = f"base_{model_name or VOLCENGINE_MODEL}"
        if key not in cls._instances:
            cls._instances[key] = BaseLLMService(model_name)
        return cls._instances[key]


# 为了向后兼容，保留一个LLMService类，但将功能分发到专门的服务类
class LLMService:
    """
    LLM服务包装类，提供向后兼容性
    该类将请求分发到专门的服务类中处理
    
    注意: 推荐直接使用LLMServiceFactory获取专门的服务类
    """
    
    def __init__(self, sql_model=None, chart_model=None):
        """
        初始化LLM服务
        
        参数:
            sql_model: SQL模型名称
            chart_model: 图表模型名称
        """
        self.sql_service = LLMServiceFactory.get_sql_service(sql_model)
        self.chart_service = LLMServiceFactory.get_chart_service(chart_model)
        self.text_service = LLMServiceFactory.get_text_analysis_service()
        
        print("注意: LLMService类现已重构，推荐直接使用LLMServiceFactory")
    
    # 兼容旧版本的API调用方法，但内部实现已转发到专门的服务类
    def call_llm_api(self, system_prompt, user_message, temperature=0.7, top_p=0.8, top_k=50, max_tokens=None):
        """
        调用LLM API
        
        参数:
            system_prompt: 系统提示词
            user_message: 用户消息
            temperature: 温度参数
            top_p: 核采样概率
            top_k: 考虑的最高概率词汇数量
            max_tokens: 最大生成令牌数
            
        返回:
            LLM响应
        """
        base_service = LLMServiceFactory.get_base_service()
        return base_service.call_api(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_tokens=max_tokens
        )
    
    def analyze_user_query_and_generate_sql(self, user_query):
        """
        分析用户查询并生成SQL查询
        
        参数:
            user_query: 用户查询
            
        返回:
            生成的SQL查询结果
        """
        return self.sql_service.generate_sql(user_query)
    
    def generate_text_analysis(self, user_query, context_data):
        """
        生成文本分析
        
        参数:
            user_query: 用户查询
            context_data: 上下文数据
            
        返回:
            文本分析结果
        """
        return self.text_service.generate_text_analysis(user_query, context_data)
    
    def generate_modular_response(self, user_query, sql_query=None, sql_results=None, chart_configs=None):
        """
        生成模块化响应
        
        参数:
            user_query: 用户查询
            sql_query: SQL查询
            sql_results: SQL查询结果
            chart_configs: 图表配置
            
        返回:
            模块化响应结果
        """
        return self.text_service.generate_modular_response(
            user_query=user_query,
            sql_query=sql_query,
            sql_results=sql_results,
            chart_configs=chart_configs
        )
    
    def generate_query(self, user_query):
        """
        生成查询
        
        参数:
            user_query: 用户查询
            
        返回:
            生成的查询结果
        """
        return self.sql_service.generate_sql(user_query)
    
    def extract_chart_configs(self, content):
        """
        从内容中提取图表配置
        
        参数:
            content: 内容文本
            
        返回:
            提取的图表配置
        """
        return self.chart_service.extract_chart_configs(content)
    
    def generate_chart_config(self, user_query, structured_data):
        """
        生成图表配置
        
        参数:
            user_query: 用户查询
            structured_data: 结构化数据
            
        返回:
            生成的图表配置
        """
        return self.chart_service.generate_chart_config(user_query, structured_data) 