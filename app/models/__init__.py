"""
模型包初始化文件
"""
# 不在这里导入User类，避免循环导入问题
# from .user import User

# 导出模型类
__all__ = []

# 医疗工作量管理系统模型包

# 说明：包含系统的核心数据模型
# 主要模型：
# - base_model.py: 基础模型父类
# - patient.py: 患者模型
# - doctor.py: 医生模型
# - medical_record.py: 医疗记录模型
# - workload.py: 工作量记录模型
# - user.py: 用户模型

# 版本历史：
# v1.0 - 初始版本
# v1.1 - 2024-03-25 移除冗余模型，优化代码结构 