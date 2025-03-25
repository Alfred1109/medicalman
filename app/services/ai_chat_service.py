"""
AI聊天服务 - 处理AI聊天相关的业务逻辑
"""
import json
from datetime import datetime
from app.utils.database import execute_query
from app.utils.utils import safe_json_loads

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
            query = f"""
            SELECT message_id, role, content, content_type, time, structured_data
            FROM chat_messages
            WHERE chat_id = ?
            ORDER BY time ASC
            """
            results = execute_query(query, (chat_id,))
            
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
                    
                    # 添加图表数据
                    if 'charts' in structured_data:
                        message_data['charts'] = structured_data['charts']
                    
                    # 添加表格数据
                    if 'tables' in structured_data:
                        message_data['tables'] = structured_data['tables']
                        
                    # 添加分析结果
                    if 'analysis' in structured_data:
                        message_data['analysis'] = structured_data['analysis']
                        
                    # 添加摘要
                    if 'summary' in structured_data:
                        message_data['summary'] = structured_data['summary']
                
                chat_history.append(message_data)
                
            return chat_history
        except Exception as e:
            print(f"获取聊天历史出错: {str(e)}")
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
            query = "SELECT title FROM chats WHERE chat_id = ?"
            result = execute_query(query, (chat_id,))
            
            if result and len(result) > 0:
                return result[0]['title']
                
            return None
        except Exception as e:
            print(f"获取聊天标题出错: {str(e)}")
            return None 