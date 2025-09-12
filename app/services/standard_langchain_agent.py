"""
标准LangChain Agent实现
使用官方推荐的最佳实践
"""

import sqlite3
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun

from app.services.base_llm_service import BaseLLMService
from app.services.database_meta_analyzer import DatabaseMetaAnalyzer
from app.config import config

class MedicalLLM(LLM):
    """标准LangChain LLM适配器"""
    
    base_service: Any = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_service = BaseLLMService()
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """调用LLM"""
        try:
            # 简单的提示词处理
            return self.base_service.call_api(
                system_prompt="你是专业的医疗数据分析助手，请简洁准确地回答问题。",
                user_message=prompt
            )
        except Exception as e:
            return f"LLM调用失败: {str(e)}"
    
    @property
    def _llm_type(self) -> str:
        return "medical_llm"

def create_medical_sql_tool():
    """创建医疗数据库查询工具"""
    def run_sql_query(query: str) -> str:
        """执行医疗数据库查询"""
        try:
            meta_analyzer = DatabaseMetaAnalyzer(config.DATABASE_PATH)
            
            # 生成SQL
            sql = meta_analyzer.generate_smart_sql(query)
            if not sql:
                return f"无法为'{query}'生成SQL查询"
            
            # 执行查询
            with sqlite3.connect(config.DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(sql)
                results = [dict(row) for row in cursor.fetchall()]
            
            # 返回格式化结果
            if not results:
                return "查询无结果"
            
            return json.dumps({
                "sql": sql,
                "count": len(results),
                "sample_data": results[:3],  # 只显示前3条
                "message": f"查询成功，共{len(results)}条记录"
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return f"数据库查询失败: {str(e)}"
    
    return Tool(
        name="medical_database_query",
        description="查询医疗数据库，获取门诊、住院、手术、收入等数据。支持中文查询如'门诊量'、'科室收入'等。",
        func=run_sql_query
    )

def create_medical_knowledge_tool():
    """创建医疗知识查询工具"""
    def get_medical_knowledge(query: str) -> str:
        """获取医疗知识"""
        knowledge_base = {
            "高血压": "高血压是指血压持续升高的疾病，正常血压应低于120/80mmHg。治疗包括生活方式改变和药物治疗。",
            "糖尿病": "糖尿病是血糖调节异常的代谢性疾病，分为1型和2型。需要血糖监测、饮食控制和药物治疗。",
            "门诊管理": "门诊管理包括预约调度、就诊流程优化、医疗质量控制等，目标是提高效率和患者满意度。",
            "科室绩效": "科室绩效评估涉及医疗质量、运营效率、患者满意度、财务指标等多维度评价体系。"
        }
        
        for keyword, info in knowledge_base.items():
            if keyword in query:
                return f"关于{keyword}的医疗知识：{info}"
        
        return f"关于'{query}'的医疗知识暂不可用，建议咨询专业医疗机构。"
    
    return Tool(
        name="medical_knowledge_search",
        description="搜索医疗专业知识，包括疾病信息、治疗方案、医学概念等。适合回答'什么是'类型的问题。",
        func=get_medical_knowledge
    )

def create_analysis_tool():
    """创建数据分析工具"""
    def analyze_data(analysis_request: str) -> str:
        """数据分析"""
        if "绩效" in analysis_request or "表现" in analysis_request:
            return "绩效分析建议：1) 关注关键指标趋势 2) 对比同期历史数据 3) 识别改进机会 4) 制定行动计划"
        elif "趋势" in analysis_request:
            return "趋势分析建议：1) 观察数据变化模式 2) 识别季节性因素 3) 预测未来走向 4) 及时调整策略"
        elif "收入" in analysis_request or "财务" in analysis_request:
            return "财务分析建议：1) 监控收入结构变化 2) 控制成本支出 3) 提高盈利能力 4) 优化资源配置"
        else:
            return f"针对'{analysis_request}'的分析建议：建议从数据质量、趋势识别、对比分析、改进建议四个维度进行综合评估。"
    
    return Tool(
        name="data_analysis",
        description="对医疗数据进行分析，提供专业建议和见解。适合回答分析、评估、建议类问题。",
        func=analyze_data
    )

class StandardLangChainAgent:
    """标准LangChain Agent服务"""
    
    def __init__(self):
        # 初始化LLM
        self.llm = MedicalLLM()
        
        # 初始化工具
        self.tools = [
            create_medical_sql_tool(),
            create_medical_knowledge_tool(),
            create_analysis_tool()
        ]
        
        # 创建Agent
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            max_iterations=3,
            handle_parsing_errors=True
        )
        
        print("标准LangChain Agent初始化完成 ✅")
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """处理用户查询"""
        start_time = datetime.now()
        
        try:
            # 使用标准Agent执行查询
            result = self.agent.run(user_query)
            
            end_time = datetime.now()
            process_time = (end_time - start_time).total_seconds()
            
            return {
                "success": True,
                "query": user_query,
                "answer": result,
                "process_time": f"{process_time:.2f}秒",
                "agent_type": "StandardLangChain",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            end_time = datetime.now()
            process_time = (end_time - start_time).total_seconds()
            
            return {
                "success": False,
                "query": user_query,
                "error": str(e),
                "process_time": f"{process_time:.2f}秒",
                "agent_type": "StandardLangChain"
            }

# 创建全局实例
standard_agent = StandardLangChainAgent()
