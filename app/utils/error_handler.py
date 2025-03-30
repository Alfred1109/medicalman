"""
错误处理模块 - 提供统一的错误处理机制
"""
import traceback
from typing import Dict, Any, Optional, Tuple, Callable
from functools import wraps
import json
from flask import jsonify, Response, current_app, request
from contextlib import contextmanager
import logging
from app.config import config

from app.utils.logger import log_error

logger = logging.getLogger(__name__)

# 错误类型定义
class ErrorType:
    """错误类型枚举"""
    DATABASE = config.ERROR_TYPES['database']
    API = config.ERROR_TYPES['api']
    AUTH = config.ERROR_TYPES['auth']
    VALIDATION = config.ERROR_TYPES['validation']
    FILE = config.ERROR_TYPES['file']
    MODEL = config.ERROR_TYPES['model']
    INTERNAL = config.ERROR_TYPES['internal']
    NOT_FOUND = config.ERROR_TYPES['not_found']

# 错误代码定义
class ErrorCode:
    """错误代码枚举"""
    # 数据库错误 (1xxx)
    DB_CONNECTION = 1001
    DB_QUERY = 1002
    DB_TRANSACTION = 1003
    DB_DATA = 1004
    
    # API错误 (2xxx)
    API_INVALID_REQUEST = 2001
    API_RATE_LIMIT = 2002
    API_RESOURCE_NOT_FOUND = 2003
    API_PERMISSION_DENIED = 2004
    API_INVALID_PARAMS = 2005
    API_FORMAT_ERROR = 2006
    
    # 认证错误 (3xxx)
    AUTH_INVALID_CREDENTIALS = 3001
    AUTH_TOKEN_EXPIRED = 3002
    AUTH_INSUFFICIENT_PERMISSIONS = 3003
    AUTH_REQUIRED = 3004
    
    # 验证错误 (4xxx)
    VALIDATION_MISSING_FIELD = 4001
    VALIDATION_INVALID_FORMAT = 4002
    VALIDATION_INVALID_VALUE = 4003
    
    # 文件错误 (5xxx)
    FILE_NOT_FOUND = 5001
    FILE_INVALID_FORMAT = 5002
    FILE_TOO_LARGE = 5003
    FILE_PERMISSION_DENIED = 5004
    
    # 模型错误 (6xxx)
    MODEL_LOAD = 6001
    MODEL_INFERENCE = 6002
    MODEL_TIMEOUT = 6003
    
    # 系统内部错误 (7xxx)
    INTERNAL_SERVER = 7001
    INTERNAL_DEPENDENCY = 7002
    
    # 未找到错误 (8xxx)
    RESOURCE_NOT_FOUND = 8001
    ENDPOINT_NOT_FOUND = 8002
    
    # 自定义数据库错误
    DB_INIT_ERROR = 1010
    DB_QUERY_ERROR = 1011

# API错误类，用于抛出API错误
class ApiError(Exception):
    """API错误异常类"""
    def __init__(self, message, error_code=ErrorCode.API_INVALID_REQUEST, 
                 http_status=400, details=None):
        self.message = message
        self.error_code = error_code
        self.http_status = http_status
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self):
        """转换为字典表示"""
        error_dict = {
            "success": False,
            "error": self.message,
            "error_code": self.error_code
        }
        if self.details:
            error_dict["details"] = self.details
        return error_dict

# 标准错误响应格式
def error_response(
    error_type: str,
    error_code: int,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = config.ERROR_STATUS_CODES['internal_server']
) -> Tuple[Response, int]:
    """
    创建标准错误响应
    
    参数:
        error_type: 错误类型
        error_code: 错误代码
        message: 错误消息
        details: 错误详情
        status_code: HTTP状态码
        
    返回:
        带错误信息的Flask响应和状态码
    """
    response_data = {
        "success": False,
        "error": {
            "type": error_type,
            "code": error_code,
            "message": message
        }
    }
    
    if details:
        response_data["error"]["details"] = details
    
    # 记录错误
    log_error(message, error_code=error_code, error_type=error_type, details=details)
    
    return jsonify(response_data), status_code

# API错误处理装饰器
def api_error_handler(func):
    """
    API错误处理装饰器，捕获异常并返回标准化的JSON响应
    
    参数:
        func: 要装饰的函数
        
    返回:
        装饰后的函数
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ApiError as e:
            # 处理自定义API错误
            current_app.logger.error(f"API错误: {e.message}")
            return jsonify(e.to_dict()), e.http_status
        except ValueError as e:
            # 处理参数验证错误
            current_app.logger.error(f"参数验证错误: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e),
                "error_code": ErrorCode.VALIDATION_INVALID_VALUE
            }), 400
        except TypeError as e:
            # 处理类型错误
            current_app.logger.error(f"类型错误: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e),
                "error_code": ErrorCode.API_INVALID_PARAMS
            }), 400
        except KeyError as e:
            # 处理字典键错误
            current_app.logger.error(f"缺少关键字段: {str(e)}")
            return jsonify({
                "success": False,
                "error": f"缺少必要字段: {str(e)}",
                "error_code": ErrorCode.VALIDATION_MISSING_FIELD
            }), 400
        except json.JSONDecodeError as e:
            # 处理JSON解析错误
            current_app.logger.error(f"JSON解析错误: {str(e)}")
            return jsonify({
                "success": False,
                "error": f"无效的JSON格式: {str(e)}",
                "error_code": ErrorCode.API_FORMAT_ERROR
            }), 400
        except Exception as e:
            # 记录未预期的异常
            error_info = {
                "endpoint": request.endpoint,
                "method": request.method,
                "url": request.url,
                "user_agent": request.user_agent.string if request.user_agent else "Unknown",
                "traceback": traceback.format_exc()
            }
            
            current_app.logger.error(f"API请求处理出错: {str(e)}")
            current_app.logger.error(f"详细信息: {json.dumps(error_info, ensure_ascii=False)}")
            
            # 返回通用错误信息
            return jsonify({
                "success": False,
                "error": "服务器内部错误，请稍后重试",
                "error_code": ErrorCode.INTERNAL_SERVER,
                "request_id": request.headers.get("X-Request-ID", "unknown")
            }), 500
    
    return wrapper

# 错误处理装饰器
def handle_exceptions(func: Callable) -> Callable:
    """
    为函数添加统一的异常处理
    
    参数:
        func: 要装饰的函数
        
    返回:
        装饰后的函数
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return error_response(
                ErrorType.VALIDATION,
                ErrorCode.VALIDATION_INVALID_VALUE,
                str(e)
            )
        except FileNotFoundError as e:
            return error_response(
                ErrorType.FILE,
                ErrorCode.FILE_NOT_FOUND,
                str(e)
            )
        except PermissionError as e:
            return error_response(
                ErrorType.FILE,
                ErrorCode.FILE_PERMISSION_DENIED,
                str(e)
            )
        except Exception as e:
            # 记录完整的堆栈信息
            error_details = {
                "traceback": traceback.format_exc()
            }
            
            return error_response(
                ErrorType.INTERNAL,
                ErrorCode.INTERNAL_SERVER,
                f"内部服务器错误: {str(e)}",
                details=error_details,
                status_code=500
            )
    
    return wrapper

# 错误处理器上下文管理器
class ErrorHandler:
    """
    使用上下文管理器处理错误
    """
    def __init__(self, default_error_type=ErrorType.INTERNAL, 
                 default_error_code=ErrorCode.INTERNAL_SERVER,
                 default_status_code=500):
        self.default_error_type = default_error_type
        self.default_error_code = default_error_code
        self.default_status_code = default_status_code
        self.error = None
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error = {
                "type": self.default_error_type,
                "code": self.default_error_code,
                "message": str(exc_val),
                "traceback": traceback.format_exc()
            }
            
            # 记录错误
            log_error(str(exc_val), error_code=self.default_error_code, 
                      error_type=self.default_error_type, 
                      details={"traceback": traceback.format_exc()})
            
            return True  # 抑制异常
        return False
    
    def has_error(self) -> bool:
        """检查是否有错误"""
        return self.error is not None
    
    def get_error_response(self, status_code=None) -> Tuple[Response, int]:
        """返回错误响应"""
        if not self.error:
            return jsonify({"success": True}), 200
            
        response_data = {
            "success": False,
            "error": {
                "type": self.error["type"],
                "code": self.error["code"],
                "message": self.error["message"]
            }
        }
        
        return jsonify(response_data), status_code or self.default_status_code

# API响应构建函数
def api_response(data=None, message="", success=True, status_code=200) -> Tuple[Response, int]:
    """
    创建标准API响应
    
    参数:
        data: 响应数据
        message: 响应消息
        success: 是否成功
        status_code: HTTP状态码
        
    返回:
        带响应信息的Flask响应和状态码
    """
    response = {
        "success": success,
        "message": message,
    }
    
    if data is not None:
        response["data"] = data
        
    return jsonify(response), status_code 

def create_error_response(
    error_type: str,
    error_code: int,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = config.ERROR_STATUS_CODES['internal_server']
) -> tuple:
    """创建标准错误响应"""
    response = {
        'error': {
            'type': error_type,
            'code': error_code,
            'message': message,
            'details': details or {}
        }
    }
    return jsonify(response), status_code

def handle_error(error_type: str = ErrorType.INTERNAL):
    """错误处理装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                return create_error_response(
                    error_type=error_type,
                    error_code=ErrorCode.INTERNAL_SERVER,
                    message=config.ERROR_MESSAGES['internal_server'].format(str(e))
                )
        return wrapper
    return decorator

@contextmanager
def error_context(error_type: str = ErrorType.INTERNAL):
    """错误处理上下文管理器"""
    try:
        yield
    except Exception as e:
        logger.error(f"Error in context: {str(e)}", exc_info=True)
        raise create_error_response(
            error_type=error_type,
            error_code=ErrorCode.INTERNAL_SERVER,
            message=config.ERROR_MESSAGES['internal_server'].format(str(e))
        ) 