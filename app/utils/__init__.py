"""
工具类包
包含各种通用工具函数和类
"""
from .validators import Validators
from .security import Security

# 导出工具类
__all__ = ['Validators', 'Security']

# 医疗工作量管理系统工具模块包

# 说明：本模块整合了系统所需的各种工具函数和实用工具类
# 主要模块说明：
# - utils.py: 通用工具函数集合，包含了原helpers.py, json_helper.py和data_helpers.py的功能
# - database.py: 数据库工具，整合了原db.py的功能
# - logger.py: 日志记录工具，整合了原models/log.py的功能
# - error_handler.py: 错误处理工具
# - report_generator.py: 报告生成工具
# - data_analysis.py: 数据分析工具
# - chart.py: 图表生成工具
# - nlp_utils.py: NLP工具
# - vector_store.py: 向量存储工具
# - files.py: 文件处理工具
# - security.py: 安全相关工具

# 版本历史：
# v1.0 - 初始版本
# v1.1 - 2024-03-25 整合冗余模块，优化代码结构
# v1.2 - 2024-03-25 整合data_helpers.py到utils.py 