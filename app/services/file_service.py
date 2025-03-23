"""
文件处理服务模块
提供动态文件格式识别和内容提取能力
"""
import os
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd
import datetime
import logging
import json
import mimetypes
from werkzeug.utils import secure_filename

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 文件处理器缓存
FILE_PROCESSORS_CACHE = None
FILE_PROCESSORS_CACHE_TIME = 0

class BaseFileProcessor:
    """
    文件处理器基类
    所有文件处理器都应继承此类
    """
    name = "base_processor"
    description = "基础文件处理器"
    supported_extensions = []
    supported_mime_types = []
    priority = 0  # 优先级：越高越优先使用
    
    @classmethod
    def can_process(cls, file_path: str, mime_type: str = None) -> bool:
        """
        检查是否可以处理给定的文件
        
        参数:
            file_path: 文件路径
            mime_type: 可选的MIME类型
            
        返回:
            是否可以处理此文件
        """
        if not os.path.exists(file_path):
            return False
            
        file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        
        # 检查扩展名
        if file_ext in cls.supported_extensions:
            return True
            
        # 检查MIME类型
        if mime_type is None:
            mime_type, _ = mimetypes.guess_type(file_path)
            
        if mime_type and mime_type in cls.supported_mime_types:
            return True
            
        return False
    
    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """
        从文件中提取纯文本内容
        
        参数:
            file_path: 文件路径
            
        返回:
            提取的文本内容
        """
        raise NotImplementedError("子类必须实现extract_text方法")
    
    @classmethod
    def extract_metadata(cls, file_path: str) -> Dict[str, Any]:
        """
        提取文件元数据
        
        参数:
            file_path: 文件路径
            
        返回:
            文件元数据字典
        """
        # 默认元数据
        stats = os.stat(file_path)
        return {
            "filename": os.path.basename(file_path),
            "size": stats.st_size,
            "created": datetime.datetime.fromtimestamp(stats.st_ctime).isoformat(),
            "modified": datetime.datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "extension": os.path.splitext(file_path)[1].lower().lstrip('.'),
        }
    
    @classmethod
    def extract_structured_data(cls, file_path: str) -> Union[pd.DataFrame, Dict, List, None]:
        """
        从文件中提取结构化数据
        
        参数:
            file_path: 文件路径
            
        返回:
            提取的结构化数据（DataFrame或字典/列表）
        """
        return None
    
    @classmethod
    def get_capabilities(cls) -> Dict[str, Any]:
        """
        获取处理器能力信息
        
        返回:
            能力信息字典
        """
        return {
            "name": cls.name,
            "description": cls.description,
            "supported_extensions": cls.supported_extensions,
            "supported_mime_types": cls.supported_mime_types,
            "priority": cls.priority,
            "can_extract_text": hasattr(cls, 'extract_text') and callable(cls.extract_text),
            "can_extract_structured_data": hasattr(cls, 'extract_structured_data') and callable(cls.extract_structured_data)
        }

# 文本文件处理器
class TextFileProcessor(BaseFileProcessor):
    """纯文本文件处理器"""
    name = "text_processor"
    description = "处理纯文本文件"
    supported_extensions = ['txt', 'log', 'md', 'csv', 'json', 'xml', 'html', 'htm']
    supported_mime_types = ['text/plain', 'text/markdown', 'text/csv', 'application/json', 
                          'text/xml', 'application/xml', 'text/html']
    priority = 10
    
    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """从文本文件中提取内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            encodings = ['latin-1', 'gbk', 'gb2312', 'big5']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            
            # 如果所有编码都失败，以二进制方式读取并解码
            with open(file_path, 'rb') as f:
                content = f.read()
                return content.decode('utf-8', errors='replace')
    
    @classmethod
    def extract_structured_data(cls, file_path: str) -> Union[pd.DataFrame, Dict, List, None]:
        """尝试提取结构化数据"""
        file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        
        # CSV文件
        if file_ext == 'csv':
            try:
                return pd.read_csv(file_path)
            except Exception as e:
                logger.error(f"CSV解析错误: {str(e)}")
                return None
        
        # JSON文件
        elif file_ext == 'json':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"JSON解析错误: {str(e)}")
                return None
        
        return None

# 注册所有的文件处理器
def discover_file_processors() -> Dict[str, BaseFileProcessor]:
    """
    发现并注册所有文件处理器
    
    返回:
        处理器字典 {名称: 处理器类}
    """
    global FILE_PROCESSORS_CACHE, FILE_PROCESSORS_CACHE_TIME
    
    # 检查缓存
    current_time = datetime.datetime.now().timestamp()
    if FILE_PROCESSORS_CACHE and (current_time - FILE_PROCESSORS_CACHE_TIME < 3600):  # 1小时缓存
        return FILE_PROCESSORS_CACHE
    
    processors = {}
    
    # 注册内置处理器
    processors[TextFileProcessor.name] = TextFileProcessor
    
    # 从file_processors包中导入处理器
    try:
        from app.services.file_processors import PROCESSORS
        for processor_class in PROCESSORS:
            processors[processor_class.name] = processor_class
    except ImportError:
        logger.warning("无法导入文件处理器包，某些文件类型可能无法处理")
    
    # 动态加载处理器（如果有其他处理器目录）
    plugin_dirs = [
        os.path.join(os.path.dirname(__file__), 'file_processors'),
        os.path.join(os.path.dirname(__file__), '..', 'plugins', 'file_processors')
    ]
    
    for plugin_dir in plugin_dirs:
        if not os.path.exists(plugin_dir) or not os.path.isdir(plugin_dir):
            continue
            
        for file_name in os.listdir(plugin_dir):
            if file_name.startswith('_') or not file_name.endswith('.py'):
                continue
                
            module_name = file_name[:-3]  # 去掉.py扩展名
            try:
                # 尝试导入模块
                module_path = f"app.services.file_processors.{module_name}"
                module = importlib.import_module(module_path)
                
                # 查找模块中的处理器类
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if (inspect.isclass(item) and 
                        issubclass(item, BaseFileProcessor) and 
                        item != BaseFileProcessor):
                        processors[item.name] = item
            except Exception as e:
                logger.error(f"加载处理器模块 {module_name} 失败: {str(e)}")
    
    # 更新缓存
    FILE_PROCESSORS_CACHE = processors
    FILE_PROCESSORS_CACHE_TIME = current_time
    
    logger.info(f"已加载 {len(processors)} 个文件处理器: {', '.join(processors.keys())}")
    return processors

class FileService:
    """文件服务类"""
    
    @staticmethod
    def analyze_file(file_path: str, user_query: str = None) -> Dict[str, Any]:
        """
        分析文件内容
        
        参数:
            file_path: 文件路径
            user_query: 用户查询（可选）
            
        返回:
            分析结果
        """
        # 确保文件存在
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"文件不存在: {file_path}"
            }
        
        # 获取文件名和扩展名
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
        
        # 猜测MIME类型
        mime_type, _ = mimetypes.guess_type(file_path)
        
        # 发现处理器
        processors = discover_file_processors()
        
        # 选择合适的处理器
        selected_processor = None
        for processor_name, processor_class in processors.items():
            if processor_class.can_process(file_path, mime_type):
                if (selected_processor is None or 
                    processor_class.priority > processors[selected_processor].priority):
                    selected_processor = processor_name
        
        if not selected_processor:
            return {
                "success": False,
                "error": f"无法找到处理此类文件的处理器: {filename} (类型: {mime_type})"
            }
        
        processor = processors[selected_processor]
        
        try:
            # 提取文件元数据
            metadata = processor.extract_metadata(file_path)
            
            # 提取文本内容
            text_content = processor.extract_text(file_path)
            
            # 尝试提取结构化数据
            structured_data = processor.extract_structured_data(file_path)
            
            # 构建结果
            result = {
                "success": True,
                "processor": processor.name,
                "metadata": metadata,
                "text_content": text_content[:10000] if len(text_content) > 10000 else text_content,  # 限制文本大小
                "has_more_content": len(text_content) > 10000
            }
            
            # 如果有结构化数据
            if isinstance(structured_data, pd.DataFrame):
                result["structured_data"] = {
                    "type": "dataframe",
                    "columns": structured_data.columns.tolist(),
                    "data": structured_data.head(100).to_dict(orient='records'),
                    "has_more_data": len(structured_data) > 100,
                    "total_rows": len(structured_data)
                }
            elif structured_data is not None:
                result["structured_data"] = {
                    "type": "json",
                    "data": structured_data
                }
            
            return result
            
        except Exception as e:
            logger.error(f"处理文件时出错: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"处理文件时出错: {str(e)}",
                "processor": processor.name
            }
    
    @staticmethod
    def get_supported_file_types() -> List[Dict[str, Any]]:
        """
        获取所有支持的文件类型
        
        返回:
            支持的文件类型列表
        """
        processors = discover_file_processors()
        supported_types = []
        
        for name, processor in processors.items():
            supported_types.append({
                "name": processor.name,
                "description": processor.description,
                "extensions": processor.supported_extensions,
                "mime_types": processor.supported_mime_types
            })
            
        return supported_types 