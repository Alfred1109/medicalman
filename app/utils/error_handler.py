"""
错误处理模块 - 提供统一的错误处理机制
"""
import traceback
from typing import Dict, Any, Optional, Tuple, Callable
from functools import wraps
import json
from flask import jsonify, Response

from app.utils.logger import log_error

# 错误类型定义
class ErrorType:
    DATABASE_ERROR = "database_error"
    API_ERROR = "api_error"
    AUTH_ERROR = "auth_error"
    VALIDATION_ERROR = "validation_error"
    FILE_ERROR = "file_error"
    MODEL_ERROR = "model_error"
    INTERNAL_ERROR = "internal_error"
    NOT_FOUND = "not_found"

# 错误代码定义
class ErrorCode:
    # 数据库错误 (1xxx)
    DB_CONNECTION_ERROR = 1001
    DB_QUERY_ERROR = 1002
    DB_TRANSACTION_ERROR = 1003
    DB_DATA_ERROR = 1004
    
    # API错误 (2xxx)
    API_INVALID_REQUEST = 2001
    API_RATE_LIMIT = 2002
    API_RESOURCE_NOT_FOUND = 2003
    API_PERMISSION_DENIED = 2004
    
    # 认证错误 (3xxx)
    AUTH_INVALID_CREDENTIALS = 3001
    AUTH_TOKEN_EXPIRED = 3002
    AUTH_INSUFFICIENT_PERMISSIONS = 3003
    
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
    MODEL_LOAD_ERROR = 6001
    MODEL_INFERENCE_ERROR = 6002
    MODEL_TIMEOUT_ERROR = 6003
    
    # 系统内部错误 (7xxx)
    INTERNAL_SERVER_ERROR = 7001
    INTERNAL_DEPENDENCY_ERROR = 7002
    
    # 未找到错误 (8xxx)
    RESOURCE_NOT_FOUND = 8001
    ENDPOINT_NOT_FOUND = 8002

# 标准错误响应格式
def error_response(
    error_type: str,
    error_code: int,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 400
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
                ErrorType.VALIDATION_ERROR,
                ErrorCode.VALIDATION_INVALID_VALUE,
                str(e)
            )
        except FileNotFoundError as e:
            return error_response(
                ErrorType.FILE_ERROR,
                ErrorCode.FILE_NOT_FOUND,
                str(e)
            )
        except PermissionError as e:
            return error_response(
                ErrorType.FILE_ERROR,
                ErrorCode.FILE_PERMISSION_DENIED,
                str(e)
            )
        except Exception as e:
            # 记录完整的堆栈信息
            error_details = {
                "traceback": traceback.format_exc()
            }
            
            return error_response(
                ErrorType.INTERNAL_ERROR,
                ErrorCode.INTERNAL_SERVER_ERROR,
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
    def __init__(self, default_error_type=ErrorType.INTERNAL_ERROR, 
                 default_error_code=ErrorCode.INTERNAL_SERVER_ERROR,
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