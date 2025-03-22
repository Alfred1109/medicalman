"""
AI聊天控制器模块
"""
from flask import Blueprint, render_template, request, jsonify, session
from app.controllers.auth import login_required
from app.models.database import Database
from app.services.llm_service import LLMService
import json
import traceback
import os
from werkzeug.utils import secure_filename

# 创建蓝图
ai_chat_bp = Blueprint('ai_chat', __name__)

@ai_chat_bp.route('/ai-chat')
@login_required
def index():
    """AI聊天页面"""
    return render_template('ai-chat.html')

@ai_chat_bp.route('/api/ai-chat/query', methods=['POST'])
@login_required
def process_query():
    """处理AI聊天查询"""
    try:
        # 获取请求数据
        data = request.get_json()
        user_query = data.get('query', '')
        
        if not user_query:
            return jsonify(success=False, error="查询不能为空")
        
        # 获取数据库结构
        db_schema = Database.get_database_schema()
        
        # 分析用户查询并生成SQL
        sql_query = LLMService.analyze_user_query_and_generate_sql(user_query, db_schema)
        
        if not sql_query:
            # 如果无法生成SQL查询，尝试直接回答
            system_prompt = """
            你是一个专业的医疗助手，擅长回答医疗相关问题。
            请根据用户的问题，提供专业、准确的回答。
            如果问题超出你的知识范围，请诚实地表明。
            """
            
            response = LLMService.call_llm_api(system_prompt, user_query)
            
            return jsonify(
                success=True,
                response_type="text",
                response=response,
                query=user_query
            )
        
        # 验证SQL查询安全性
        if not Database.validate_sql_query(sql_query):
            return jsonify(
                success=False,
                error="生成的SQL查询不安全，请重新表述您的问题"
            )
        
        # 执行SQL查询
        try:
            df = Database.query_to_dataframe(sql_query)
            
            # 如果查询结果为空
            if df.empty:
                return jsonify(
                    success=True,
                    response_type="text",
                    response="没有找到符合条件的数据",
                    query=user_query,
                    sql=sql_query
                )
            
            # 将DataFrame转换为字典列表
            result_data = df.to_dict(orient='records')
            
            # 生成数据分析
            analysis_result = LLMService.generate_data_analysis(result_data, user_query)
            
            if analysis_result:
                return jsonify(
                    success=True,
                    response_type="analysis",
                    response=analysis_result['analysis'],
                    data=result_data,
                    query=user_query,
                    sql=sql_query
                )
            else:
                return jsonify(
                    success=True,
                    response_type="data",
                    data=result_data,
                    query=user_query,
                    sql=sql_query
                )
                
        except Exception as e:
            # SQL执行错误
            error_message = f"执行SQL查询时出错: {str(e)}"
            traceback.print_exc()
            
            return jsonify(
                success=False,
                error=error_message,
                query=user_query,
                sql=sql_query
            )
    
    except Exception as e:
        # 处理查询时的一般错误
        error_message = f"处理查询时出错: {str(e)}"
        traceback.print_exc()
        
        return jsonify(success=False, error=error_message)

@ai_chat_bp.route('/api/ai-chat/upload-document', methods=['POST'])
@login_required
def upload_document():
    """上传文档"""
    try:
        # 检查是否有文件
        if 'document' not in request.files:
            return jsonify(success=False, error="没有上传文件")
        
        file = request.files['document']
        
        # 检查文件名
        if file.filename == '':
            return jsonify(success=False, error="未选择文件")
        
        # 获取允许的文件扩展名
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', 
                                                  {'pdf', 'docx', 'txt', 'xlsx', 'xls', 'csv'})
        
        # 检查文件扩展名
        if not ('.' in file.filename and 
                file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify(success=False, error="不支持的文件类型")
        
        # 安全地获取文件名
        filename = secure_filename(file.filename)
        
        # 获取上传目录
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads/documents')
        
        # 确保目录存在
        os.makedirs(upload_folder, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        return jsonify(
            success=True,
            message="文件上传成功",
            filename=filename,
            file_path=file_path
        )
        
    except Exception as e:
        error_message = f"上传文件时出错: {str(e)}"
        traceback.print_exc()
        
        return jsonify(success=False, error=error_message)

@ai_chat_bp.route('/api/ai-chat/analyze-document', methods=['POST'])
@login_required
def analyze_document():
    """分析文档"""
    try:
        # 获取请求数据
        data = request.get_json()
        filename = data.get('filename', '')
        user_query = data.get('query', '')
        
        if not filename:
            return jsonify(success=False, error="未指定文件")
        
        if not user_query:
            return jsonify(success=False, error="查询不能为空")
        
        # 获取上传目录
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads/documents')
        
        # 构建文件路径
        file_path = os.path.join(upload_folder, secure_filename(filename))
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify(success=False, error="文件不存在")
        
        # 根据文件类型处理文件
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        # 读取文件内容
        file_content = ""
        
        if file_extension in ['txt']:
            # 文本文件
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        elif file_extension in ['pdf']:
            # PDF文件
            import PyPDF2
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    file_content += page.extract_text() + "\n"
        elif file_extension in ['docx']:
            # Word文件
            import docx
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                file_content += para.text + "\n"
        elif file_extension in ['xlsx', 'xls', 'csv']:
            # Excel文件
            import pandas as pd
            df = pd.read_excel(file_path) if file_extension in ['xlsx', 'xls'] else pd.read_csv(file_path)
            file_content = df.to_string()
        else:
            return jsonify(success=False, error="不支持的文件类型")
        
        # 分析文件内容
        analysis_result = LLMService.generate_text_analysis(file_content, user_query)
        
        if analysis_result:
            return jsonify(
                success=True,
                response=analysis_result,
                filename=filename,
                query=user_query
            )
        else:
            return jsonify(
                success=False,
                error="无法分析文档",
                filename=filename,
                query=user_query
            )
            
    except Exception as e:
        error_message = f"分析文档时出错: {str(e)}"
        traceback.print_exc()
        
        return jsonify(success=False, error=error_message) 