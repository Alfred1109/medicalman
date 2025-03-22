from app.models.log import Log
from app.extensions import db
from datetime import datetime
from sqlalchemy import and_, or_

class LogService:
    @staticmethod
    def get_logs(page=1, per_page=20, level=None, module=None, user=None, 
                 start_date=None, end_date=None, keyword=None):
        """获取日志列表"""
        query = Log.query
        
        # 应用筛选条件
        if level and level != 'all':
            query = query.filter(Log.level == level.upper())
            
        if module and module != 'all':
            query = query.filter(Log.module == module)
            
        if user and user != 'all':
            query = query.filter(Log.user == user)
            
        if start_date:
            query = query.filter(Log.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))
            
        if end_date:
            query = query.filter(Log.timestamp <= datetime.strptime(end_date, '%Y-%m-%d'))
            
        if keyword:
            query = query.filter(
                or_(
                    Log.message.ilike(f'%{keyword}%'),
                    Log.details.ilike(f'%{keyword}%')
                )
            )
        
        # 按时间倒序排序
        query = query.order_by(Log.timestamp.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 格式化日志数据
        logs = []
        for log in pagination.items:
            logs.append({
                'id': log.id,
                'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'level': log.level,
                'module': log.module,
                'user': log.user,
                'message': log.message,
                'ip_address': log.ip_address,
                'details': log.details,
                'session_id': log.session_id
            })
            
        return logs, pagination.total
    
    @staticmethod
    def get_log_by_id(log_id):
        """获取单个日志详情"""
        log = Log.query.get(log_id)
        if not log:
            return None
            
        return {
            'id': log.id,
            'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'level': log.level,
            'module': log.module,
            'user': log.user,
            'message': log.message,
            'ip_address': log.ip_address,
            'details': log.details,
            'session_id': log.session_id,
            'user_agent': log.user_agent
        }
    
    @staticmethod
    def clear_logs():
        """清空所有日志"""
        try:
            Log.query.delete()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def add_log(level, module, user, message, ip_address, details=None, 
                session_id=None, user_agent=None):
        """添加新日志"""
        try:
            log = Log(
                level=level.upper(),
                module=module,
                user=user,
                message=message,
                ip_address=ip_address,
                details=details,
                session_id=session_id,
                user_agent=user_agent
            )
            db.session.add(log)
            db.session.commit()
            return log
        except Exception as e:
            db.session.rollback()
            raise e 