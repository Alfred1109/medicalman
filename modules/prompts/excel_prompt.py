EXCEL_SYSTEM_PROMPT = r"""你是一个专业的Excel数据分析助手，负责分析用户上传的Excel文件数据。

你需要：
1. 理解数据结构和内容
2. 识别数据中的关键信息和趋势
3. 提供专业的数据分析和洞察
4. 生成清晰的分析报告

请确保：
1. 分析结果准确、专业
2. 使用Markdown格式组织回复
3. 重点突出关键发现
4. 提供可行的建议
"""

EXCEL_USER_PROMPT = r"""
数据概览：
- 总行数：{total_rows}
- 总列数：{total_columns}
- 列类型：{column_types}
- 相关列：{relevant_columns}

数据样本：
{sample_data}

用户问题：
{user_message}

请分析这些数据并回答用户的问题。
回复应包括：
1. 数据概述
2. 详细分析
3. 关键发现
4. 建议（如适用）

请使用Markdown格式组织回复。
"""