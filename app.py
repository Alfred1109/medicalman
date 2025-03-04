from flask import Flask, render_template, request, jsonify, send_file, make_response
from modules import (
    process_user_query,
    connect_db,
    generate_chart_data,
    call_llm_api
)
from modules.db_connection import execute_database_queries
from modules.config import *
import sqlite3
import pandas as pd
import json
import os
import requests
import random  # 添加random模块用于生成随机颜色
import re
import io
import traceback  # 添加traceback模块
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageFont
import string
from flask import session
import math
from datetime import datetime, timedelta
from modules.file_processor import get_latest_file

app = Flask(__name__)
app.secret_key = os.urandom(24)  # 用于session加密

# 火山方舟API配置
VOLCENGINE_API_KEY = "3470059d-f774-4302-81e0-50fa017fea38"  # 请替换为您的实际API Key
VOLCENGINE_API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
VOLCENGINE_MODEL = "deepseek-v3-241226"  # 使用深度求索大模型

# 添加文件上传配置
UPLOAD_FOLDER = 'static/uploads/documents'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'xlsx', 'xls', 'csv', 'xlsm', 'ods'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 验证码配置
CAPTCHA_CHARS = string.ascii_uppercase + string.digits
CAPTCHA_LENGTH = 4
CAPTCHA_WIDTH = 120
CAPTCHA_HEIGHT = 40

def allowed_file(filename):
    # 如果文件名中没有点号，表示没有扩展名，我们也允许上传
    if '.' not in filename:
        return True
    return filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def connect_db():
    """连接到数据库"""
    conn = sqlite3.connect("medical_workload.db")
    conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
    return conn

# 生成随机颜色
def generate_random_colors(count):
    """生成随机颜色列表"""
    colors = []
    for _ in range(count):
        r = random.randint(100, 200)
        g = random.randint(100, 200)
        b = random.randint(100, 200)
        colors.append(f'rgba({r}, {g}, {b}, 0.7)')
    return colors

# 生成图表数据
def generate_chart_data(df, chart_type, x_field, y_field, title):
    """根据数据生成Chart.js图表配置"""
    if df.empty:
        return None
    
    labels = df[x_field].tolist()
    data = df[y_field].tolist()
    
    # 生成随机颜色
    colors = generate_random_colors(len(labels))
    
    chart_config = {
        'type': chart_type,
        'data': {
            'labels': labels,
            'datasets': [{
                'label': y_field,
                'data': data,
                'backgroundColor': colors if chart_type in ['bar', 'pie', 'doughnut'] else 'rgba(75, 192, 192, 0.2)',
                'borderColor': 'rgba(75, 192, 192, 1)' if chart_type == 'line' else colors,
                'borderWidth': 1
            }]
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'title': {
                    'display': True,
                    'text': title
                },
                'legend': {
                    'display': True,
                    'position': 'top'
                }
            }
        }
    }
    
    return chart_config

def generate_captcha():
    # 创建图像
    image = Image.new('RGB', (CAPTCHA_WIDTH, CAPTCHA_HEIGHT), color='white')
    draw = ImageDraw.Draw(image)
    
    # 生成随机字符
    captcha_text = ''.join(random.choice(CAPTCHA_CHARS) for _ in range(CAPTCHA_LENGTH))
    
    # 添加字符到图像
    font_size = 30
    try:
        font = ImageFont.truetype('static/fonts/Arial.ttf', font_size)
    except:
        font = ImageFont.load_default()
    
    # 计算文字位置使其居中
    text_width = font.getlength(captcha_text)
    text_height = font_size
    x = (CAPTCHA_WIDTH - text_width) / 2
    y = (CAPTCHA_HEIGHT - text_height) / 2
    
    # 绘制文字
    draw.text((x, y), captcha_text, font=font, fill='black')
    
    # 添加干扰线
    for _ in range(5):
        x1 = random.randint(0, CAPTCHA_WIDTH)
        y1 = random.randint(0, CAPTCHA_HEIGHT)
        x2 = random.randint(0, CAPTCHA_WIDTH)
        y2 = random.randint(0, CAPTCHA_HEIGHT)
        draw.line([(x1, y1), (x2, y2)], fill='gray')
    
    # 添加噪点
    for _ in range(50):
        x = random.randint(0, CAPTCHA_WIDTH)
        y = random.randint(0, CAPTCHA_HEIGHT)
        draw.point((x, y), fill='gray')
    
    # 将图像转换为字节流
    image_io = io.BytesIO()
    image.save(image_io, 'PNG')
    image_io.seek(0)
    
    return captcha_text, image_io

@app.route('/')
def index():
    """主页 - 重定向到仪表盘页面"""
    return render_template('dashboard.html')

@app.route('/dashboard')
def dashboard():
    """仪表盘页面"""
    return render_template('dashboard.html')

@app.route('/ai-chat')
def ai_chat():
    """AI聊天页面"""
    return render_template('ai-chat.html')

@app.route('/alerts')
def alerts():
    """预警通知页面"""
    return render_template('alerts.html')

@app.route('/analysis')
def analysis():
    """多维度分析页面"""
    return render_template('analysis.html')

@app.route('/user-management')
def user_management():
    """用户管理页面"""
    return render_template('user-management.html')

@app.route('/settings')
def settings():
    """系统设置页面"""
    return render_template('settings.html')

@app.route('/help')
def help():
    """帮助与反馈页面"""
    return render_template('help.html')

@app.route('/login')
def login_page():
    """登录页面"""
    return render_template('login.html')

@app.route('/department-analysis')
def department_analysis():
    """科室分析页面"""
    return render_template('department-analysis.html')

@app.route('/financial-analysis')
def financial_analysis():
    """财务分析页面"""
    return render_template('financial-analysis.html')

@app.route('/patient-analysis')
def patient_analysis():
    """患者分析页面"""
    return render_template('patient-analysis.html')

@app.route('/doctor-performance')
def doctor_performance():
    """医生绩效页面"""
    return render_template('doctor-performance.html')

@app.route('/drg-analysis')
def drg_analysis():
    return render_template('drg-analysis.html')

@app.route('/api/departments')
def get_departments():
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # 获取所有科室
        cursor.execute("SELECT DISTINCT department FROM drg_records ORDER BY department")
        departments = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': departments
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取科室列表失败：{str(e)}'
        })

@app.route('/api/specialties')
def get_specialties():
    """获取所有专科"""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT 专科 FROM 门诊量 WHERE 专科 IS NOT NULL ORDER BY 专科")
    specialties = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(specialties)

@app.route('/api/dates')
def get_dates():
    """获取所有日期"""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT date(日期) as 日期 FROM 门诊量 WHERE 日期 IS NOT NULL ORDER BY 日期")
    dates = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(dates)

@app.route('/api/stats/department')
def get_department_stats():
    """获取按科室统计的数据"""
    conn = connect_db()
    df = pd.read_sql_query("""
        SELECT 科室, COUNT(*) as 记录数, SUM(数量) as 总数量, AVG(数量) as 平均数量 
        FROM 门诊量 
        WHERE 科室 IS NOT NULL
        GROUP BY 科室 
        ORDER BY SUM(数量) DESC
    """, conn)
    conn.close()
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/stats/specialty')
def get_specialty_stats():
    """获取按专科统计的数据"""
    conn = connect_db()
    df = pd.read_sql_query("""
        SELECT 专科, COUNT(*) as 记录数, SUM(数量) as 总数量, AVG(数量) as 平均数量 
        FROM 门诊量 
        WHERE 专科 IS NOT NULL
        GROUP BY 专科 
        ORDER BY SUM(数量) DESC
    """, conn)
    conn.close()
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/stats/date')
def get_date_stats():
    """获取按日期统计的数据"""
    conn = connect_db()
    df = pd.read_sql_query("""
        SELECT date(日期) as 日期, COUNT(*) as 记录数, SUM(数量) as 总数量 
        FROM 门诊量 
        WHERE 日期 IS NOT NULL
        GROUP BY date(日期) 
        ORDER BY date(日期)
    """, conn)
    conn.close()
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/query', methods=['POST'])
def query():
    """处理用户查询的API端点"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        data_source_preference = data.get('data_source', None)
        
        if not user_message:
            return jsonify({
                'success': False,
                'message': '请提供查询内容'
            })
        
        # 处理用户查询
        result = process_user_query(user_message, data_source_preference)
        
        # 根据结果类型返回不同的响应
        if result.get('type') == 'error':
            return jsonify({
                'success': False,
                'message': result.get('content', '处理查询时出错')
            })
        elif result.get('type') == 'excel_analysis':
            return jsonify({
                'success': True,
                'message': result.get('content', ''),
                'file_name': result.get('file_name', ''),
                'type': 'excel_analysis',
                'charts': result.get('charts', [])
            })
        elif result.get('type') == 'text_analysis':
            return jsonify({
                'success': True,
                'message': result.get('content', ''),
                'file_name': result.get('file_name', ''),
                'type': 'text_analysis'
            })
        elif result.get('type') == 'knowledge_base':
            return jsonify({
                'success': True,
                'message': result.get('content', ''),
                'type': 'knowledge_base',
                'sources': result.get('sources', [])
            })
        else:
            return jsonify({
                'success': True,
                'message': result.get('content', '无法生成回复'),
                'type': 'general'
            })
    
    except Exception as e:
        print(f"处理查询时出错: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'处理查询时出错: {str(e)}'
        })

@app.route('/upload_document', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件被上传'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'})
    
    if file and allowed_file(file.filename):
        try:
            # 使用安全的文件名
            filename = secure_filename(file.filename)
            # 获取原始文件扩展名
            _, ext = os.path.splitext(filename)
            ext = ext.lower()
            
            # 如果没有扩展名，根据内容类型推断扩展名
            if not ext:
                content_type = file.content_type
                if 'excel' in content_type or 'spreadsheet' in content_type:
                    ext = '.xlsx'
                elif 'csv' in content_type:
                    ext = '.csv'
                elif 'pdf' in content_type:
                    ext = '.pdf'
                elif 'word' in content_type or 'document' in content_type:
                    ext = '.docx'
                elif 'text' in content_type:
                    ext = '.txt'
                else:
                    # 默认为xlsx
                    ext = '.xlsx'
            
            # 生成文件名（保留扩展名）
            name_without_ext = os.path.splitext(filename)[0]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_filename = f"{name_without_ext}_{timestamp}{ext}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
            
            # 保存文件
            file.save(file_path)
            print(f"文件已保存到: {file_path}")
            
            # 尝试读取Excel文件
            try:
                # 根据文件扩展名选择合适的引擎
                _, ext = os.path.splitext(file_path)
                ext = ext.lower()
                
                if ext == '.xlsx' or ext == '.xlsm':
                    df = pd.read_excel(file_path, engine='openpyxl')
                elif ext == '.xls':
                    df = pd.read_excel(file_path, engine='xlrd')
                elif ext == '.ods':
                    df = pd.read_excel(file_path, engine='odf')
                elif ext == '.csv':
                    df = pd.read_csv(file_path)
                else:
                    # 尝试自动检测
                    try:
                        df = pd.read_excel(file_path, engine='openpyxl')
                    except Exception as e1:
                        try:
                            df = pd.read_excel(file_path, engine='xlrd')
                        except Exception as e2:
                            try:
                                df = pd.read_excel(file_path, engine='odf')
                            except Exception as e3:
                                df = pd.read_csv(file_path)
                
                print(f"成功读取Excel文件，数据预览:\n{df.head()}")
            except Exception as e:
                print(f"读取Excel文件时出错: {str(e)}")
            
            # 将文件信息保存到数据库
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO documents (filename, file_path, upload_date)
                VALUES (?, ?, datetime('now'))
            ''', (filename, file_path))
            file_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'file_id': file_id,
                'message': '文件上传成功'
            })
        except Exception as e:
            print(f"文件上传处理时出错: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'文件处理错误：{str(e)}'
            })
    
    return jsonify({
        'success': False,
        'message': '不支持的文件类型'
    })

@app.route('/delete_document', methods=['POST'])
def delete_document():
    data = request.get_json()
    file_id = data.get('file_id')
    
    if not file_id:
        return jsonify({'success': False, 'message': '未提供文件ID'})
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # 获取文件信息
        cursor.execute('SELECT file_path FROM documents WHERE id = ?', (file_id,))
        result = cursor.fetchone()
        
        if result:
            file_path = result[0]
            # 删除物理文件
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # 从数据库中删除记录
            cursor.execute('DELETE FROM documents WHERE id = ?', (file_id,))
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': '文件删除成功'})
        else:
            return jsonify({'success': False, 'message': '文件不存在'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除失败：{str(e)}'})

@app.route('/get_captcha')
def get_captcha():
    # 生成验证码
    captcha_text, image_io = generate_captcha()
    
    # 将验证码存储在session中
    session['captcha'] = captcha_text
    
    # 返回验证码图像
    return send_file(image_io, mimetype='image/png')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    captcha = data.get('captcha')
    
    # 验证验证码
    stored_captcha = session.get('captcha')
    if not stored_captcha or captcha.upper() != stored_captcha:
        return jsonify({
            'success': False,
            'message': '验证码错误'
        })
    
    # 清除已使用的验证码
    session.pop('captcha', None)
    
    # 验证用户名和密码
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                      (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return jsonify({
                'success': True,
                'message': '登录成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '用户名或密码错误'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'登录失败：{str(e)}'
        })

@app.route('/view_document', methods=['GET'])
def view_document():
    """查看上传文件的内容"""
    try:
        # 获取最新上传的文件
        latest_file = get_latest_file('static/uploads/documents')
        
        if not latest_file:
            return jsonify({
                'success': False,
                'message': '没有找到上传的文件'
            })
        
        file_path, file_type, file_content = latest_file
        filename = os.path.basename(file_path)
        
        # 根据文件类型返回不同的内容
        if file_type in ['xlsx', 'xls', 'xlsm', 'ods', 'csv']:
            # Excel或CSV文件
            if isinstance(file_content, pd.DataFrame):
                # 将DataFrame转换为HTML表格
                html_table = file_content.head(50).to_html(classes='table table-striped', index=False)
                return jsonify({
                    'success': True,
                    'file_name': filename,
                    'file_type': file_type,
                    'content_type': 'table',
                    'content': html_table,
                    'total_rows': len(file_content),
                    'total_columns': len(file_content.columns),
                    'columns': file_content.columns.tolist()
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '无法读取Excel文件内容'
                })
        elif file_type in ['pdf', 'docx', 'txt']:
            # 文本文件
            if isinstance(file_content, str):
                # 限制返回的文本长度
                max_length = 10000
                truncated = len(file_content) > max_length
                content = file_content[:max_length] + ('...(内容已截断)' if truncated else '')
                
                return jsonify({
                    'success': True,
                    'file_name': filename,
                    'file_type': file_type,
                    'content_type': 'text',
                    'content': content,
                    'truncated': truncated,
                    'total_length': len(file_content)
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '无法读取文本文件内容'
                })
        elif file_type in ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif']:
            # 图像文件 - 返回图像URL
            image_url = f'/static/uploads/documents/{filename}'
            return jsonify({
                'success': True,
                'file_name': filename,
                'file_type': file_type,
                'content_type': 'image',
                'content': image_url
            })
        else:
            return jsonify({
                'success': False,
                'message': f'不支持查看的文件类型: {file_type}'
            })
    
    except Exception as e:
        print(f"查看文件内容时出错: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'查看文件内容时出错: {str(e)}'
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9101, debug=True) 