"""
增强配置模块 - 混合Agent架构配置
包含复杂度分析、图表优化、内容增强等配置
"""

# 查询复杂度分析配置
COMPLEXITY_ANALYSIS_CONFIG = {
    # 复杂度判断关键词
    "simple_keywords": [
        "查看", "显示", "列出", "有哪些", "是什么", "简单统计"
    ],
    "moderate_keywords": [
        "分析", "趋势", "对比", "统计", "图表", "变化", "分布"
    ],
    "complex_keywords": [
        "综合分析", "整体", "深度分析", "优化建议", "未来规划", 
        "多维度", "全面", "策略", "预测", "改进方案"
    ],
    
    # 复杂度权重配置
    "complexity_weights": {
        "keyword_match": 0.3,
        "query_length": 0.2,
        "data_sources": 0.2,
        "output_types": 0.15,
        "analysis_depth": 0.15
    },
    
    # 置信度阈值
    "confidence_thresholds": {
        "simple": 0.7,
        "moderate": 0.6,
        "complex": 0.5
    }
}

# Agent工具配置
AGENT_TOOLS_CONFIG = {
    # 工具执行超时时间（秒）
    "execution_timeout": 30,
    
    # 最大重试次数
    "max_retries": 2,
    
    # 工具优先级
    "tool_priority": {
        "sql_query_tool": 1,
        "knowledge_search_tool": 2,
        "chart_generation_tool": 3,
        "data_analysis_tool": 4,
        "multi_query_tool": 5
    },
    
    # Agent执行计划配置
    "execution_plan": {
        "max_steps": 5,
        "step_timeout": 20,
        "fallback_enabled": True
    }
}

# Vega-Lite 图表增强配置
VEGA_CHART_CONFIG = {
    # 医疗主题颜色方案
    "color_schemes": {
        "medical_primary": [
            '#4A90E2',  # 专业蓝
            '#7ED321',  # 健康绿
            '#F5A623',  # 温暖橙
            '#D0021B',  # 警告红
            '#9013FE',  # 科技紫
            '#50E3C2',  # 清新青
            '#B8E986',  # 自然绿
            '#4A4A4A'   # 稳重灰
        ],
        "medical_secondary": [
            '#E3F2FD',  # 浅蓝
            '#E8F5E8',  # 浅绿
            '#FFF3E0',  # 浅橙
            '#FFEBEE',  # 浅红
            '#F3E5F5',  # 浅紫
            '#E0F2F1'   # 浅青
        ]
    },
    
    # Vega-Lite图表类型智能选择规则
    "chart_type_rules": {
        "time_series": {
            "condition": "有时间字段 AND 有数值字段",
            "mark": "line",
            "encoding_features": ["point", "tooltip", "smooth_interpolation"]
        },
        "category_distribution": {
            "condition": "分类字段 <= 6 AND 有数值字段",
            "mark": "arc",
            "encoding_features": ["theta_quantitative", "color_nominal", "tooltip"]
        },
        "category_comparison": {
            "condition": "分类字段 > 6 AND 有数值字段",
            "mark": "bar", 
            "encoding_features": ["x_nominal", "y_quantitative", "tooltip"]
        },
        "correlation": {
            "condition": "数值字段 >= 2",
            "mark": "point",
            "encoding_features": ["x_quantitative", "y_quantitative", "size", "tooltip"]
        }
    },
    
    # Vega-Lite 配置优化
    "optimization": {
        "max_data_points": 50,  # 单个图表最大数据点
        "auto_sampling": True,  # 自动数据采样
        "default_width": 400,   # 默认宽度
        "default_height": 300,  # 默认高度
        "responsive": True,     # 响应式设计
        "theme": "quartz",      # 默认主题
        "tooltip_theme": "dark" # 工具提示主题
    },
    
    # Vega-Lite 医疗主题配置
    "medical_theme_config": {
        "axis": {
            "labelFontSize": 11,
            "titleFontSize": 12,
            "titleFontWeight": "bold",
            "labelColor": "#666",
            "titleColor": "#333"
        },
        "title": {
            "fontSize": 16,
            "fontWeight": "bold",
            "color": "#333",
            "anchor": "start"
        },
        "legend": {
            "labelFontSize": 11,
            "titleFontSize": 12,
            "titleColor": "#333"
        }
    }
}

# 内容增强配置
CONTENT_ENHANCEMENT_CONFIG = {
    # 内容分析关键词
    "analysis_keywords": {
        "positive_indicators": ["增长", "提高", "改善", "优秀", "良好"],
        "negative_indicators": ["下降", "减少", "恶化", "不良", "问题"],
        "neutral_indicators": ["稳定", "保持", "一般", "正常", "平均"]
    },
    
    # 内容结构模板
    "content_templates": {
        "comprehensive_analysis": [
            "数据概览",
            "关键发现",
            "趋势分析", 
            "深度解读",
            "专业建议",
            "后续建议"
        ],
        "simple_report": [
            "查询结果",
            "数据说明",
            "简要分析"
        ]
    },
    
    # 医学术语解释配置
    "medical_terms": {
        "auto_explain": True,
        "explanation_style": "简明",
        "include_examples": True
    },
    
    # 内容质量指标
    "quality_metrics": {
        "min_content_length": 200,
        "max_content_length": 2000,
        "paragraph_count_range": [3, 8],
        "professional_terms_ratio": 0.1
    }
}

# 前端展示优化配置
FRONTEND_DISPLAY_CONFIG = {
    # 图表容器配置
    "chart_container": {
        "default_height": "400px",
        "responsive_height": True,
        "aspect_ratio": "16:9",
        "loading_animation": True
    },
    
    # 表格展示配置
    "table_display": {
        "max_rows_per_page": 20,
        "enable_pagination": True,
        "enable_search": True,
        "enable_export": True,
        "zebra_striping": True
    },
    
    # 内容展示配置
    "content_display": {
        "enable_markdown": True,
        "syntax_highlighting": True,
        "auto_scroll": True,
        "reading_mode": True
    },
    
    # 响应式配置
    "responsive": {
        "mobile_chart_height": "300px",
        "tablet_chart_height": "350px",
        "desktop_chart_height": "400px",
        "mobile_table_columns": 3,
        "tablet_table_columns": 5,
        "desktop_table_columns": -1  # 显示所有列
    }
}

# 性能优化配置
PERFORMANCE_CONFIG = {
    # 缓存配置
    "cache": {
        "enable_query_cache": True,
        "cache_ttl": 300,  # 5分钟
        "max_cache_size": 100
    },
    
    # 异步处理配置
    "async_processing": {
        "enable_background_tasks": True,
        "task_timeout": 60,
        "max_concurrent_tasks": 5
    },
    
    # 数据采样配置
    "data_sampling": {
        "large_dataset_threshold": 1000,
        "sampling_ratio": 0.1,
        "preserve_trends": True
    }
}

# API响应格式配置
API_RESPONSE_FORMAT = {
    "success_response": {
        "success": True,
        "message": "str",
        "answer": "str",  # 前端显示用
        "data": "dict",
        "charts": "list",
        "tables": "list", 
        "processing_info": "dict",
        "quality_metrics": "dict",
        "process_time": "str"
    },
    
    "error_response": {
        "success": False,
        "message": "str",
        "error": "str",
        "error_code": "str",
        "data": "dict",
        "fallback_content": "str"
    }
}

# 日志配置
LOGGING_CONFIG = {
    "log_queries": True,
    "log_complexity_analysis": True,
    "log_agent_execution": True,
    "log_chart_generation": True,
    "log_performance_metrics": True,
    "detail_level": "info"  # debug, info, warning, error
}
