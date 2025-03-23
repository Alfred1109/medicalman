"""
文件处理器包
"""

# 导出所有处理器类
from .pdf_processor import PDFProcessor
from .excel_processor import ExcelProcessor
from .word_processor import WordProcessor

# 处理器注册表
PROCESSORS = [
    PDFProcessor,
    ExcelProcessor,
    WordProcessor
] 