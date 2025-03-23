"""
Excel文件处理器模块
"""
import os
from typing import Dict, Any, Union, List
import pandas as pd
import logging
import io
import json

# 配置日志
logger = logging.getLogger(__name__)

# 导入基类
from app.services.file_service import BaseFileProcessor

class ExcelProcessor(BaseFileProcessor):
    """Excel文件处理器"""
    name = "excel_processor"
    description = "处理Excel电子表格文件"
    supported_extensions = ['xlsx', 'xls', 'xlsm', 'xlsb', 'ods', 'csv']
    supported_mime_types = [
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.oasis.opendocument.spreadsheet',
        'text/csv',
        'application/vnd.ms-excel.sheet.binary.macroEnabled.12',
        'application/vnd.ms-excel.sheet.macroEnabled.12'
    ]
    priority = 30
    
    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """从Excel文件中提取文本内容"""
        try:
            # 对于CSV文件单独处理
            if file_path.lower().endswith('.csv'):
                try:
                    df = pd.read_csv(file_path)
                except Exception as e:
                    logger.error(f"读取CSV文件失败: {str(e)}")
                    return f"读取CSV文件失败: {str(e)}"
            else:
                # 读取Excel文件
                try:
                    df = pd.read_excel(file_path, sheet_name=None)
                except Exception as e:
                    logger.error(f"读取Excel文件失败: {str(e)}")
                    return f"读取Excel文件失败: {str(e)}"
            
            # 如果是字典（多个工作表），将所有工作表转换为文本
            if isinstance(df, dict):
                text_parts = []
                
                for sheet_name, sheet_df in df.items():
                    text_parts.append(f"=== 工作表: {sheet_name} ===\n")
                    text_parts.append(sheet_df.to_string(index=False))
                    text_parts.append("\n\n")
                
                return "\n".join(text_parts)
            else:
                # 如果是单个数据帧，直接转换为文本
                return df.to_string(index=False)
                
        except Exception as e:
            logger.error(f"Excel文本提取错误: {str(e)}", exc_info=True)
            return f"Excel解析错误: {str(e)}"
    
    @classmethod
    def extract_metadata(cls, file_path: str) -> Dict[str, Any]:
        """提取Excel文件的元数据"""
        metadata = super().extract_metadata(file_path)
        
        try:
            # 对于CSV文件
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path)
                metadata.update({
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": df.columns.tolist(),
                    "sheet_count": 1,
                    "sheet_names": ["Sheet1"]  # CSV默认一个工作表
                })
            else:
                # Excel文件
                excel_file = pd.ExcelFile(file_path)
                all_dfs = pd.read_excel(file_path, sheet_name=None)
                
                sheet_info = []
                total_rows = 0
                for sheet_name, df in all_dfs.items():
                    total_rows += len(df)
                    sheet_info.append({
                        "name": sheet_name,
                        "rows": len(df),
                        "columns": len(df.columns),
                        "column_names": df.columns.tolist()
                    })
                
                metadata.update({
                    "rows": total_rows,
                    "sheet_count": len(excel_file.sheet_names),
                    "sheet_names": excel_file.sheet_names,
                    "sheet_details": sheet_info
                })
                
        except Exception as e:
            logger.error(f"提取Excel元数据时出错: {str(e)}")
            
        return metadata
    
    @classmethod
    def extract_structured_data(cls, file_path: str) -> Union[pd.DataFrame, Dict, List, None]:
        """提取Excel的结构化数据"""
        try:
            # 对于CSV文件
            if file_path.lower().endswith('.csv'):
                return pd.read_csv(file_path)
            
            # 对于Excel文件，读取所有工作表
            return pd.read_excel(file_path, sheet_name=None)
                
        except Exception as e:
            logger.error(f"提取Excel结构化数据失败: {str(e)}", exc_info=True)
            return None
            
    @classmethod
    def get_sheet_names(cls, file_path: str) -> List[str]:
        """获取Excel文件中的所有工作表名称"""
        try:
            if file_path.lower().endswith('.csv'):
                return ["Sheet1"]  # CSV文件只有一个工作表
                
            excel_file = pd.ExcelFile(file_path)
            return excel_file.sheet_names
        except Exception as e:
            logger.error(f"获取工作表名称失败: {str(e)}")
            return [] 