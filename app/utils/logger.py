"""
日志工具模块 - 提供统一的日志记录功能
"""
import logging
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any
import traceback
import json

# 配置日志格式和级别
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO

# 日志文件路径
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, f"app_{datetime.now().strftime('%Y%m%d')}.log")

# 确保日志目录存在
os.makedirs(LOG_DIR, exist_ok=True)

# 创建日志处理器
def setup_logger(name: str, level: int = LOG_LEVEL) -> logging.Logger:
    """
    设置并返回日志记录器
    
    参数:
        name: 日志记录器名称
        level: 日志级别
        
    返回:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 清除现有的处理器
    if logger.handlers:
        logger.handlers = []
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console_handler)
    
    # 添加文件处理器
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)
    
    return logger

# 创建应用日志记录器
app_logger = setup_logger("app")

# 用户查询日志记录
def log_user_query(username: str, query: str, result: Optional[Dict[str, Any]] = None) -> None:
    """
    记录用户查询
    
    参数:
        username: 用户名
        query: 查询内容
        result: 查询结果
    """
    try:
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "username": username,
            "query": query,
            "success": result.get("success", False) if result else None
        }
        
        # 如果有错误，记录错误信息
        if result and not result.get("success") and "error" in result:
            log_entry["error"] = result["error"]
        
        # 记录到日志文件
        app_logger.info(f"用户查询: {json.dumps(log_entry, ensure_ascii=False)}")
        
        # 保存到查询历史文件
        query_log_file = os.path.join(LOG_DIR, "query_history.log")
        with open(query_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
    except Exception as e:
        app_logger.error(f"记录用户查询日志时出错: {str(e)}")
        traceback.print_exc()

# 错误日志记录
def log_error(message: str, error_code: int = None, error_type: str = None, details: Optional[Dict[str, Any]] = None) -> None:
    """
    记录错误信息
    
    参数:
        message: 错误消息
        error_code: 错误代码
        error_type: 错误类型
        details: 错误详情
    """
    try:
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": message
        }
        
        if error_code:
            log_entry["error_code"] = error_code
            
        if error_type:
            log_entry["error_type"] = error_type
            
        if details:
            log_entry["details"] = details
            
        app_logger.error(f"系统错误: {json.dumps(log_entry, ensure_ascii=False)}")
        
    except Exception as e:
        app_logger.error(f"记录错误日志时出错: {str(e)}")
        traceback.print_exc()

# 性能日志记录
def log_performance(operation: str, execution_time: float, details: Optional[Dict[str, Any]] = None) -> None:
    """
    记录性能信息
    
    参数:
        operation: 操作名称
        execution_time: 执行时间(秒)
        details: 操作详情
    """
    try:
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operation": operation,
            "execution_time": execution_time
        }
        
        if details:
            log_entry["details"] = details
            
        app_logger.info(f"性能日志: {json.dumps(log_entry, ensure_ascii=False)}")
        
    except Exception as e:
        app_logger.error(f"记录性能日志时出错: {str(e)}")
        traceback.print_exc()

# 查询日志记录
def log_query(query: str, execution_time: float) -> None:
    """
    记录SQL查询
    
    参数:
        query: SQL查询语句
        execution_time: 执行时间(秒)
    """
    try:
        # 简化查询语句（移除多余空格）
        simplified_query = ' '.join(query.split())
        
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "query": simplified_query[:200] + ('...' if len(simplified_query) > 200 else ''),
            "execution_time": execution_time
        }
        
        # 如果执行时间过长，使用警告级别记录
        if execution_time > 1.0:
            app_logger.warning(f"慢查询: {json.dumps(log_entry, ensure_ascii=False)}")
        else:
            app_logger.debug(f"数据库查询: {json.dumps(log_entry, ensure_ascii=False)}")
        
    except Exception as e:
        app_logger.error(f"记录查询日志时出错: {str(e)}")
        traceback.print_exc()

# 用户登录日志记录
def log_user_login(username: str, success: bool, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> None:
    """
    记录用户登录信息
    
    参数:
        username: 用户名
        success: 登录是否成功
        ip_address: IP地址
        user_agent: 用户代理字符串
    """
    try:
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "username": username,
            "success": success
        }
        
        if ip_address:
            log_entry["ip_address"] = ip_address
            
        if user_agent:
            log_entry["user_agent"] = user_agent
            
        # 记录到日志文件
        if success:
            app_logger.info(f"用户登录成功: {json.dumps(log_entry, ensure_ascii=False)}")
        else:
            app_logger.warning(f"用户登录失败: {json.dumps(log_entry, ensure_ascii=False)}")
        
        # 保存到登录历史文件
        login_log_file = os.path.join(LOG_DIR, "login_history.log")
        with open(login_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
    except Exception as e:
        app_logger.error(f"记录用户登录日志时出错: {str(e)}")
        traceback.print_exc()

# 获取应用日志记录器
def get_logger(name: str = "app") -> logging.Logger:
    """
    获取日志记录器
    
    参数:
        name: 日志记录器名称
        
    返回:
        日志记录器实例
    """
    return logging.getLogger(name) if name != "app" else app_logger 