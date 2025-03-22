from app.extensions import db
from datetime import datetime

class Log(db.Model):
    """系统日志模型"""
    __tablename__ = 'logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    level = db.Column(db.String(10), nullable=False)  # INFO, WARNING, ERROR, CRITICAL
    module = db.Column(db.String(50), nullable=False)  # 模块名称
    user = db.Column(db.String(50), nullable=False)  # 操作用户
    message = db.Column(db.String(500), nullable=False)  # 日志消息
    details = db.Column(db.Text)  # 详细信息
    ip_address = db.Column(db.String(50))  # IP地址
    session_id = db.Column(db.String(100))  # 会话ID
    user_agent = db.Column(db.String(500))  # 用户代理
    
    def __repr__(self):
        return f'<Log {self.id}: {self.level} - {self.message}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'level': self.level,
            'module': self.module,
            'user': self.user,
            'message': self.message,
            'details': self.details,
            'ip_address': self.ip_address,
            'session_id': self.session_id,
            'user_agent': self.user_agent
        } 