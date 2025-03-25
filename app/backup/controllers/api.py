from flask import Blueprint, request, jsonify, send_file, make_response
import sqlite3
import pandas as pd
import json
import os
import requests
import random
import re
import io
import traceback
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageFont
import string
from flask import session
import math
from datetime import datetime, timedelta

from app.utils.db import connect_db
from app.utils.chart import generate_chart_data
from app.utils.files import get_latest_file, allowed_file
from app.utils.captcha import generate_captcha

# 创建蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')

# 火山方舟API配置
VOLCENGINE_API_KEY = "3470059d-f774-4302-81e0-50fa017fea38"  # 请替换为您的实际API Key
VOLCENGINE_API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
VOLCENGINE_MODEL = "deepseek-v3-241226"  # 使用深度求索大模型

# 添加文件上传配置
UPLOAD_FOLDER = 'static/uploads/documents'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'xlsx', 'xls', 'csv', 'xlsm', 'ods'}

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@api_bp.route('/departments')
def get_departments():
    """获取所有科室"""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT department FROM medical_data")
    departments = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(departments)

@api_bp.route('/specialties')
def get_specialties():
    """获取所有专业组"""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT specialty FROM medical_data")
    specialties = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(specialties)

@api_bp.route('/dates')
def get_dates():
    """获取所有日期"""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT date FROM medical_data")
    dates = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(dates)

@api_bp.route('/stats/department')
def get_department_stats():
    """获取各科室的统计数据"""
    try:
        query = """
        SELECT 
            department as department,
            COUNT(*) as count,
            SUM(CASE WHEN 就诊类型 = '门诊' THEN 1 ELSE 0 END) as outpatient_count,
            SUM(CASE WHEN 就诊类型 = '住院' THEN 1 ELSE 0 END) as inpatient_count,
            SUM(CASE WHEN 就诊类型 = '手术' THEN 1 ELSE 0 END) as surgery_count
        FROM medical_data
        GROUP BY department
        ORDER BY count DESC
        """
        
        df = execute_query_to_dataframe(query)
        
        if df.empty:
            return jsonify({
                'success': False,
                'message': '未找到科室统计数据'
            }), 404
            
        # 转换为图表数据格式
        chart_data = {
            'departments': df['department'].tolist(),
            'total_counts': df['count'].tolist(),
            'outpatient_counts': df['outpatient_count'].tolist(),
            'inpatient_counts': df['inpatient_count'].tolist(),
            'surgery_counts': df['surgery_count'].tolist()
        }
        
        return jsonify({
            'success': True,
            'data': chart_data
        })
        
    except Exception as e:
        current_app.logger.error(f"获取科室统计数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取统计数据失败: {str(e)}'
        }), 500

@api_bp.route('/stats/specialty')
def get_specialty_stats():
    """获取各专业组的统计数据"""
    try:
        query = """
        SELECT 
            specialty as specialty,
            COUNT(*) as count,
            SUM(CASE WHEN 就诊类型 = '门诊' THEN 1 ELSE 0 END) as outpatient_count,
            SUM(CASE WHEN 就诊类型 = '住院' THEN 1 ELSE 0 END) as inpatient_count,
            SUM(CASE WHEN 就诊类型 = '手术' THEN 1 ELSE 0 END) as surgery_count
        FROM medical_data
        GROUP BY specialty
        ORDER BY count DESC
        """
        
        df = execute_query_to_dataframe(query)
        
        if df.empty:
            return jsonify({
                'success': False,
                'message': '未找到专业组统计数据'
            }), 404
            
        # 转换为图表数据格式
        chart_data = {
            'specialties': df['specialty'].tolist(),
            'total_counts': df['count'].tolist(),
            'outpatient_counts': df['outpatient_count'].tolist(),
            'inpatient_counts': df['inpatient_count'].tolist(),
            'surgery_counts': df['surgery_count'].tolist()
        }
        
        return jsonify({
            'success': True,
            'data': chart_data
        })
        
    except Exception as e:
        current_app.logger.error(f"获取专业组统计数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取统计数据失败: {str(e)}'
        }), 500

@api_bp.route('/stats/date')
def get_date_stats():
    """获取各日期的统计数据"""
    try:
        # 从数据库获取真实数据
        query = """
        SELECT 
            strftime('%Y-%m-%d', 就诊日期) as date,
            COUNT(*) as count,
            SUM(CASE WHEN 就诊类型 = '门诊' THEN 1 ELSE 0 END) as outpatient_count,
            SUM(CASE WHEN 就诊类型 = '住院' THEN 1 ELSE 0 END) as inpatient_count
        FROM 门诊记录
        WHERE 就诊日期 >= date('now', '-30 days')
        GROUP BY strftime('%Y-%m-%d', 就诊日期)
        ORDER BY date
        """
        
        df = execute_query_to_dataframe(query)
        
        if df.empty:
            return jsonify({
                'success': False,
                'message': '未找到统计数据'
            }), 404
            
        # 转换为图表数据格式
        chart_data = {
            'dates': df['date'].tolist(),
            'outpatient_counts': df['outpatient_count'].tolist(),
            'inpatient_counts': df['inpatient_count'].tolist(),
            'total_counts': df['count'].tolist()
        }
        
        return jsonify({
            'success': True,
            'data': chart_data
        })
        
    except Exception as e:
        current_app.logger.error(f"获取日期统计数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取统计数据失败: {str(e)}'
        }), 500

@api_bp.route('/query', methods=['POST'])
def process_query():
    """处理用户查询"""
    try:
        data = request.json
        user_query = data.get('query', '')
        selected_department = data.get('department', '')
        selected_specialty = data.get('specialty', '')
        selected_date = data.get('date', '')
        
        # 从火山方舟API获取处理后的查询
        processed_query = call_llm_api(user_query)
        
        # 构建SQL查询条件
        conditions = []
        params = []
        
        if selected_department:
            conditions.append("科室 = ?")
            params.append(selected_department)
        
        if selected_specialty:
            conditions.append("专业组 = ?")
            params.append(selected_specialty)
        
        if selected_date:
            conditions.append("就诊日期 = ?")
            params.append(selected_date)
        
        # 添加基于用户查询的条件
        if processed_query.get('conditions'):
            for condition in processed_query.get('conditions'):
                field = condition['field']
                operator = condition['operator']
                value = condition['value']
                
                # 根据字段类型添加不同的查询条件
                if field in ['就诊日期', '手术日期']:
                    conditions.append(f"{field} {operator} ?")
                    params.append(value)
                elif field in ['年龄', '住院天数', '手术时长']:
                    conditions.append(f"{field} {operator} ?")
                    params.append(float(value))
                else:
                    conditions.append(f"{field} {operator} ?")
                    params.append(value)
        
        # 构建完整的SQL查询
        sql = """
        SELECT 
            就诊日期,
            科室,
            专业组,
            就诊类型,
            患者姓名,
            性别,
            年龄,
            诊断,
            手术名称,
            手术日期,
            手术时长,
            住院天数,
            费用
        FROM 门诊记录
        """
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        # 添加排序
        if processed_query.get('sort'):
            sort_field = processed_query.get('sort').get('field')
            sort_order = processed_query.get('sort').get('order', 'DESC')
            sql += f" ORDER BY {sort_field} {sort_order}"
        
        # 执行查询
        conn = connect_db()
        df = pd.read_sql_query(sql, conn, params=params)
        conn.close()
        
        # 准备响应
        result = {
            'query': user_query,
            'processed_query': processed_query,
            'data': df.to_dict(orient='records'),
            'chart': None
        }
        
        # 如果需要生成图表
        if processed_query.get('chart'):
            chart_type = processed_query.get('chart').get('type', 'bar')
            x_field = processed_query.get('chart').get('x_field', '科室')
            y_field = processed_query.get('chart').get('y_field', '就诊量')
            title = processed_query.get('chart').get('title', '查询结果')
            
            # 根据图表类型生成不同的数据
            if chart_type == 'bar':
                chart_df = df.groupby(x_field).size().reset_index(name=y_field)
            elif chart_type == 'line':
                chart_df = df.groupby(x_field).size().reset_index(name=y_field)
            elif chart_type == 'pie':
                chart_df = df.groupby(x_field).size().reset_index(name=y_field)
            else:
                chart_df = df.groupby(x_field).size().reset_index(name=y_field)
            
            result['chart'] = generate_chart_data(chart_df, chart_type, x_field, y_field, title)
        
        return jsonify(result)
    except Exception as e:
        print(f"处理查询时出错: {str(e)}")
        traceback.print_exc()  # 打印完整的错误堆栈
        return jsonify({'error': str(e)}), 500

# 创建upload蓝图
upload_bp = Blueprint('upload', __name__, url_prefix='/upload')

@upload_bp.route('/document', methods=['POST'])
def upload_document():
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有文件上传'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # 添加时间戳，确保文件名唯一
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{filename}"
            
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(save_path)
            
            return jsonify({
                'success': True,
                'message': '文件上传成功',
                'filename': filename,
                'file_path': save_path
            })
        else:
            return jsonify({'error': '不允许的文件类型'}), 400
    except Exception as e:
        print(f"上传文件时出错: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@upload_bp.route('/delete_document', methods=['POST'])
def delete_document():
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': '未提供文件名'}), 400
        
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404
        
        os.remove(file_path)
        
        return jsonify({
            'success': True,
            'message': '文件删除成功'
        })
    except Exception as e:
        print(f"删除文件时出错: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@upload_bp.route('/view_document', methods=['GET'])
def view_document():
    filename = request.args.get('filename')
    
    if not filename:
        # 尝试获取最新的文件
        filename = get_latest_file(UPLOAD_FOLDER)
        if not filename:
            return "没有可用的文档", 404
    
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        return "文件不存在", 404
    
    # 根据文件类型返回不同的响应
    if filename.lower().endswith('.pdf'):
        return send_file(file_path, mimetype='application/pdf')
    else:
        # 对于其他类型的文件，提供下载
        return send_file(file_path, as_attachment=True)

# 创建auth_api蓝图处理认证相关API
auth_api_bp = Blueprint('auth_api', __name__, url_prefix='/auth_api')

@auth_api_bp.route('/get_captcha')
def get_captcha():
    """生成验证码图像"""
    captcha_text, image_io = generate_captcha()
    
    # 将验证码存储在会话中
    session['captcha'] = captcha_text
    
    # 返回图像
    response = make_response(send_file(image_io, mimetype='image/png'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@auth_api_bp.route('/login', methods=['POST'])
def login_api():
    """处理登录请求"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    captcha = data.get('captcha')
    
    # 验证码验证
    stored_captcha = session.get('captcha')
    if not stored_captcha or captcha.upper() != stored_captcha:
        return jsonify({'success': False, 'message': '验证码错误'})
    
    # 清除验证码，防止重用
    session.pop('captcha', None)
    
    # 连接数据库
    conn = connect_db()
    cursor = conn.cursor()
    
    # 查询用户
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if user and user['password'] == password:  # 实际应用中应使用哈希比较
        # 设置会话
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'role': user['role']
            }
        })
    else:
        return jsonify({'success': False, 'message': '用户名或密码错误'})

# 调用火山方舟API
def call_llm_api(query):
    """调用火山方舟API处理查询"""
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {VOLCENGINE_API_KEY}"
        }
        
        payload = {
            "model": VOLCENGINE_MODEL,
            "messages": [
                {"role": "system", "content": "你是一个医疗数据分析助手，请帮我分析下面的医疗查询，提取出具体的分析条件。"},
                {"role": "user", "content": query}
            ],
            "top_p": 0.8,
            "temperature": 0.1
        }
        
        response = requests.post(VOLCENGINE_API_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # 解析内容，这里简化处理，实际应用中可能需要更复杂的解析
            try:
                # 尝试解析JSON格式的回复
                if '{' in content and '}' in content:
                    json_str = re.search(r'\{.*\}', content, re.DOTALL).group()
                    return json.loads(json_str)
            except:
                pass
            
            # 如果无法解析JSON，返回简单的条件
            return {
                'conditions': [],
                'sort': {'field': 'workload', 'order': 'DESC'},
                'chart': {'type': 'bar', 'x_field': 'department', 'y_field': 'workload', 'title': '查询结果'}
            }
        else:
            print(f"调用火山方舟API出错: {response.text}")
            return {
                'conditions': [],
                'sort': {'field': 'workload', 'order': 'DESC'},
                'chart': {'type': 'bar', 'x_field': 'department', 'y_field': 'workload', 'title': '查询结果'}
            }
    except Exception as e:
        print(f"调用API时出错: {str(e)}")
        traceback.print_exc()
        return {
            'conditions': [],
            'sort': {'field': 'workload', 'order': 'DESC'},
            'chart': {'type': 'bar', 'x_field': 'department', 'y_field': 'workload', 'title': '查询结果'}
        } 