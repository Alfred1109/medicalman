from flask import Blueprint, render_template, jsonify, request, send_file
from flask_login import login_required
from app.services.log_service import LogService
from app.utils.decorators import admin_required
import csv
from io import StringIO
from datetime import datetime

logs_bp = Blueprint('logs', __name__)

@logs_bp.route('/logs')
@login_required
@admin_required
def index():
    """系统日志页面"""
    return render_template('logs.html')

@logs_bp.route('/api/logs', methods=['GET'])
@login_required
@admin_required
def get_logs():
    """获取日志列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        level = request.args.get('level')
        module = request.args.get('module')
        user = request.args.get('user')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        keyword = request.args.get('keyword')
        
        # 调用服务层获取日志数据
        logs, total = LogService.get_logs(
            page=page,
            per_page=per_page,
            level=level,
            module=module,
            user=user,
            start_date=start_date,
            end_date=end_date,
            keyword=keyword
        )
        
        return jsonify({
            'success': True,
            'data': {
                'logs': logs,
                'total': total,
                'page': page,
                'per_page': per_page
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@logs_bp.route('/api/logs/<int:log_id>', methods=['GET'])
@login_required
@admin_required
def get_log_detail(log_id):
    """获取日志详情"""
    try:
        log = LogService.get_log_by_id(log_id)
        if not log:
            return jsonify({
                'success': False,
                'message': '日志不存在'
            }), 404
            
        return jsonify({
            'success': True,
            'data': log
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@logs_bp.route('/api/logs/export', methods=['GET'])
@login_required
@admin_required
def export_logs():
    """导出日志"""
    try:
        # 获取筛选参数
        level = request.args.get('level')
        module = request.args.get('module')
        user = request.args.get('user')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        keyword = request.args.get('keyword')
        
        # 获取所有符合条件的日志
        logs, _ = LogService.get_logs(
            page=1,
            per_page=1000,  # 导出最多1000条记录
            level=level,
            module=module,
            user=user,
            start_date=start_date,
            end_date=end_date,
            keyword=keyword
        )
        
        # 创建CSV文件
        output = StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow(['时间', '级别', '模块', '用户', '消息', 'IP地址', '详细信息'])
        
        # 写入数据
        for log in logs:
            writer.writerow([
                log['timestamp'],
                log['level'],
                log['module'],
                log['user'],
                log['message'],
                log['ip_address'],
                log['details']
            ])
        
        # 准备下载
        output.seek(0)
        return send_file(
            StringIO(output.getvalue()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'系统日志_{datetime.now().strftime("%Y%m%d")}.csv'
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@logs_bp.route('/api/logs/clear', methods=['POST'])
@login_required
@admin_required
def clear_logs():
    """清空日志"""
    try:
        LogService.clear_logs()
        return jsonify({
            'success': True,
            'message': '日志已清空'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500 