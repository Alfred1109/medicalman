"""
AI聊天服务 - 处理AI聊天相关的业务逻辑
"""
import json
from datetime import datetime
from app.utils.database import execute_query
from app.utils.utils import safe_json_loads
from app.config import config

class AIChatService:
    """AI聊天服务类"""
    
    def get_chat_history(self, chat_id):
        """
        获取指定聊天ID的聊天历史记录
        
        参数:
            chat_id: 聊天ID
            
        返回:
            聊天历史记录列表
        """
        try:
            # 从数据库中获取聊天历史
            results = execute_query(config.CHAT_QUERIES['get_history'], (chat_id,))
            
            if not results:
                return []
                
            # 处理聊天记录
            chat_history = []
            for message in results:
                message_data = {
                    'role': message['role'],
                    'content': message['content'],
                    'content_type': message['content_type'],
                    'time': message['time']
                }
                
                # 处理结构化数据（如果有）
                if message.get('structured_data'):
                    structured_data = safe_json_loads(message['structured_data'])
                    
                    # 添加结构化数据字段
                    for field in config.CHAT_STRUCTURED_DATA_FIELDS:
                        if field in structured_data:
                            message_data[field] = structured_data[field]
                
                chat_history.append(message_data)
                
            return chat_history
        except Exception as e:
            print(config.CHAT_ERROR_MESSAGES['history_error'].format(str(e)))
            return []
            
    def get_chat_title(self, chat_id):
        """
        获取聊天标题
        
        参数:
            chat_id: 聊天ID
            
        返回:
            聊天标题
        """
        try:
            result = execute_query(config.CHAT_QUERIES['get_title'], (chat_id,))
            
            if result and len(result) > 0:
                return result[0]['title']
                
            return None
        except Exception as e:
            print(config.CHAT_ERROR_MESSAGES['title_error'].format(str(e)))
            return None 