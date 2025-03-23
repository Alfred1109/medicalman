"""
PDF文件处理器模块
"""
import os
from typing import Dict, Any, Union, List
import pandas as pd
import logging
import io

# 配置日志
logger = logging.getLogger(__name__)

# 导入基类
from app.services.file_service import BaseFileProcessor

class PDFProcessor(BaseFileProcessor):
    """PDF文件处理器"""
    name = "pdf_processor"
    description = "处理PDF文件"
    supported_extensions = ['pdf']
    supported_mime_types = ['application/pdf']
    priority = 20
    
    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """从PDF文件中提取文本内容"""
        try:
            # 尝试使用PyPDF2
            import PyPDF2
            
            with open(file_path, 'rb') as file:
                text = ""
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    page_text = page.extract_text() or ""
                    text += page_text + "\n\n"
            
            # 如果PyPDF2提取的文本很少，尝试使用pdfplumber
            if len(text.strip()) < 100:
                try:
                    import pdfplumber
                    with pdfplumber.open(file_path) as pdf:
                        text = ""
                        for page in pdf.pages:
                            page_text = page.extract_text() or ""
                            text += page_text + "\n\n"
                except ImportError:
                    logger.warning("pdfplumber未安装，无法尝试备选文本提取方法")
                except Exception as e:
                    logger.error(f"使用pdfplumber提取文本失败: {str(e)}")
            
            return text
                
        except ImportError:
            logger.error("PyPDF2未安装，无法提取PDF文本")
            return "无法提取PDF内容：需要安装PyPDF2库"
        except Exception as e:
            logger.error(f"PDF文本提取错误: {str(e)}", exc_info=True)
            return f"PDF解析错误: {str(e)}"
    
    @classmethod
    def extract_metadata(cls, file_path: str) -> Dict[str, Any]:
        """提取PDF文件的元数据"""
        metadata = super().extract_metadata(file_path)
        
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                # 添加PDF特有元数据
                metadata.update({
                    "page_count": len(reader.pages),
                    "pdf_version": reader.pdf_header
                })
                
                # 提取PDF文档信息
                if reader.metadata:
                    info = reader.metadata
                    doc_info = {}
                    
                    for key in info:
                        value = info[key]
                        if isinstance(value, str):
                            doc_info[key] = value
                        elif value is not None:
                            doc_info[key] = str(value)
                    
                    metadata["document_info"] = doc_info
                
        except Exception as e:
            logger.error(f"提取PDF元数据时出错: {str(e)}")
            
        return metadata
    
    @classmethod
    def extract_structured_data(cls, file_path: str) -> Union[pd.DataFrame, Dict, List, None]:
        """尝试从PDF提取表格数据"""
        try:
            # 尝试使用tabula-py提取表格
            try:
                import tabula
                
                # 提取所有表格
                tables = tabula.read_pdf(file_path, pages='all', multiple_tables=True)
                
                if tables and len(tables) > 0:
                    # 如果只有一个表格，直接返回DataFrame
                    if len(tables) == 1:
                        return tables[0]
                    
                    # 如果有多个表格，返回一个字典
                    result = {}
                    for i, table in enumerate(tables):
                        result[f"table_{i+1}"] = table
                    
                    return result
            except ImportError:
                logger.warning("tabula-py未安装，无法提取PDF表格")
            except Exception as e:
                logger.error(f"使用tabula-py提取表格失败: {str(e)}")
            
            # 如果tabula-py失败，尝试使用pdfplumber
            try:
                import pdfplumber
                import pandas as pd
                
                with pdfplumber.open(file_path) as pdf:
                    all_tables = []
                    
                    for i, page in enumerate(pdf.pages):
                        tables = page.extract_tables()
                        
                        for j, table in enumerate(tables):
                            if table and len(table) > 0:
                                # 确保表头作为列名
                                headers = table[0]
                                data = table[1:]
                                
                                # 创建DataFrame
                                df = pd.DataFrame(data, columns=headers)
                                all_tables.append(df)
                    
                    if len(all_tables) == 1:
                        return all_tables[0]
                    elif len(all_tables) > 1:
                        result = {}
                        for i, table in enumerate(all_tables):
                            result[f"table_{i+1}"] = table
                        return result
            except ImportError:
                logger.warning("pdfplumber未安装，无法提取PDF表格")
            except Exception as e:
                logger.error(f"使用pdfplumber提取表格失败: {str(e)}")
                
        except Exception as e:
            logger.error(f"提取PDF结构化数据失败: {str(e)}", exc_info=True)
        
        return None 