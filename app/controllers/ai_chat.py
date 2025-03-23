"""
AI聊天控制器模块
"""
from flask import Blueprint, render_template, request, jsonify, session, current_app
from flask_login import login_required
from app.models.database import Database
from app.services.llm_service import LLMService
from app.services.file_service import FileService
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
        user_query = data.get('message', '')
        data_source = data.get('data_source', 'auto')
        
        if not user_query:
            return jsonify(success=False, error="查询不能为空", message="请输入您的问题")
            
        # 根据数据源类型选择处理流程
        if data_source == 'documents' or (data_source == 'auto' and '文件' in user_query or '文档' in user_query):
            # 文档分析流程
            # 获取最近上传的文档
            # TODO: 实现文档获取逻辑
            return jsonify(
                success=True,
                message="我需要分析文档来回答这个问题，请先上传相关文档。",
                type="text"
            )
            
        # 默认流程：分析用户查询并生成SQL
        try:
            # 调用LLM服务分析用户查询
            analysis_result = LLMService.analyze_user_query_and_generate_sql(user_query)
            
            if not analysis_result or 'sql' not in analysis_result:
                # 如果无法生成SQL查询，使用通用回答
                system_prompt = """
                你是一个专业的医疗助手，擅长回答医疗相关问题。
                请根据用户的问题，提供专业、准确的回答。
                如果问题超出你的知识范围，请诚实地表明。
                """
                
                response = LLMService.call_llm_api(system_prompt, user_query)
                
                return jsonify(
                    success=True,
                    message=response or "抱歉，我无法理解您的问题，请尝试用不同方式提问。",
                    type="text"
                )
            
            # 执行SQL查询
            from app.models.database import Database
            result_data = []
            
            try:
                # 验证SQL安全性
                sql_query = analysis_result.get('sql', '')
                if not Database.validate_sql_query(sql_query):
                    return jsonify(
                        success=False,
                        message="生成的SQL查询不安全，请重新表述您的问题",
                        type="text"
                    )
                
                # 执行查询并获取结果
                df = Database.query_to_dataframe(sql_query)
                
                # 检查查询结果
                if df.empty:
                    return jsonify(
                        success=True,
                        message="没有找到符合条件的数据，请尝试修改查询条件。",
                        type="text"
                    )
                
                # 获取数据并分析
                result_data = df.to_dict(orient='records')
                data_analysis = LLMService.generate_data_analysis(result_data, user_query)
                
                if data_analysis:
                    return jsonify(
                        success=True,
                        message=data_analysis.get('analysis', "数据分析完成。"),
                        data=result_data,
                        charts=data_analysis.get('charts', []),
                        type="data_analysis"
                    )
                else:
                    # 简单返回数据
                    return jsonify(
                        success=True,
                        message="查询结果如下，但无法提供详细分析。",
                        data=result_data,
                        type="data_only"
                    )
                    
            except Exception as query_error:
                print(f"SQL查询执行错误: {str(query_error)}")
                
                # 回退到直接回答
                system_prompt = f"""
                你是一个专业的医疗助手，擅长回答医疗相关问题。
                用户问题是: {user_query}
                尝试执行SQL查询时遇到了错误: {str(query_error)}
                请根据用户的问题，直接提供可能的回答，不要提及SQL错误。
                """
                
                response = LLMService.call_llm_api(system_prompt, user_query)
                
                return jsonify(
                    success=True,
                    message=response or "抱歉，我无法回答这个问题，请尝试用不同方式提问。",
                    type="text"
                )
                
        except Exception as analysis_error:
            print(f"分析用户查询时出错: {str(analysis_error)}")
            
            # 回退到直接回答
            system_prompt = """
            你是一个专业的医疗助手，擅长回答医疗相关问题。
            请根据用户的问题，提供专业、准确的回答。
            如果问题超出你的知识范围，请诚实地表明。
            """
            
            response = LLMService.call_llm_api(system_prompt, user_query)
            
            return jsonify(
                success=True,
                message=response or "抱歉，我无法理解您的问题，请尝试用不同方式提问。",
                type="text"
            )
            
    except Exception as e:
        # 处理查询时的一般错误
        error_message = f"处理查询时出错: {str(e)}"
        traceback.print_exc()
        
        return jsonify(
            success=False, 
            error=error_message, 
            message="服务器处理请求时出错，请稍后再试。",
            type="error"
        )

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
        
        # 获取支持的文件类型
        from app.services.file_service import FileService
        supported_file_types = FileService.get_supported_file_types()
        
        # 收集所有支持的扩展名
        allowed_extensions = set()
        for file_type in supported_file_types:
            allowed_extensions.update(file_type['extensions'])
        
        # 如果没有找到支持的类型，使用配置中的值
        if not allowed_extensions:
            allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', 
                                                    {'pdf', 'docx', 'txt', 'xlsx', 'xls', 'csv'})
        
        # 检查文件扩展名
        if not ('.' in file.filename and 
                file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify(
                success=False, 
                error="不支持的文件类型",
                supported_types=list(allowed_extensions)
            )
        
        # 安全地获取文件名
        filename = secure_filename(file.filename)
        
        # 获取上传目录
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads/documents')
        
        # 确保目录存在
        os.makedirs(upload_folder, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # 检查文件是否可以处理
        try:
            # 尝试分析文件以验证是否可以处理
            result = FileService.analyze_file(file_path)
            
            if not result['success']:
                # 如果无法处理，删除文件并返回错误
                os.remove(file_path)
                return jsonify(
                    success=False, 
                    error=f"无法处理此文件: {result.get('error', '未知错误')}"
                )
                
            # 返回文件元数据
            return jsonify(
                success=True,
                message="文件上传成功",
                filename=filename,
                file_path=file_path,
                metadata=result.get('metadata', {}),
                processor=result.get('processor', 'unknown')
            )
            
        except Exception as e:
            # 文件分析失败，但仍然保留文件
            logger.error(f"文件分析失败，但文件已上传: {str(e)}")
            return jsonify(
                success=True,
                message="文件已上传，但初步分析失败，可能无法正确处理",
                filename=filename,
                file_path=file_path,
                warning=str(e)
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
        
        # 使用文件服务分析文件
        from app.services.file_service import FileService
        result = FileService.analyze_file(file_path)
        
        if not result['success']:
            return jsonify(success=False, error=result.get('error', '无法处理文件'))
        
        # 提取文本内容用于LLM分析
        text_content = result.get('text_content', '')
        file_type = os.path.splitext(filename)[1].lstrip('.').upper() + "文件"
        metadata = result.get('metadata', {})
        
        # 提取结构化数据（如果有）
        structured_data = result.get('structured_data')
        
        # 生成分析结果
        analysis_result = LLMService.generate_text_analysis(
            text_content=text_content, 
            user_query=user_query,
            metadata=metadata,
            structured_data=structured_data,
            file_type=file_type,
            file_name=filename
        )
        
        if analysis_result:
            result_data = {
                'success': True,
                'response': analysis_result,
                'filename': filename,
                'query': user_query,
                'metadata': metadata
            }
            
            # 如果有结构化数据，添加到结果中
            if structured_data:
                if 'type' in structured_data and structured_data['type'] == 'dataframe':
                    result_data['structured_data'] = {
                        'type': 'table',
                        'headers': structured_data['columns'],
                        'data': structured_data['data'][:20],  # 限制返回的行数
                        'has_more': structured_data['has_more_data'],
                        'total_rows': structured_data['total_rows']
                    }
                else:
                    result_data['structured_data'] = {
                        'type': 'json',
                        'data': structured_data['data']
                    }
            
            return jsonify(result_data)
        else:
            return jsonify(
                success=False,
                error="无法分析文档内容",
                filename=filename,
                query=user_query
            )
            
    except Exception as e:
        error_message = f"分析文档时出错: {str(e)}"
        traceback.print_exc()
        
        return jsonify(success=False, error=error_message)

@ai_chat_bp.route('/api/ai-chat/delete-document', methods=['POST'])
@login_required
def delete_document():
    """删除上传的文档"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify(success=False, error="未提供文件名")
        
        # 获取上传目录
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads/documents')
        
        # 构建文件路径
        file_path = os.path.join(upload_folder, secure_filename(filename))
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify(success=False, error="文件不存在")
        
        # 删除文件
        os.remove(file_path)
        
        return jsonify(
            success=True,
            message="文件删除成功"
        )
    except Exception as e:
        error_message = f"删除文件时出错: {str(e)}"
        traceback.print_exc()
        
        return jsonify(success=False, error=error_message)

@ai_chat_bp.route('/api/ai-chat/supported-file-types', methods=['GET'])
@login_required
def get_supported_file_types():
    """获取支持的文件类型"""
    try:
        from app.services.file_service import FileService
        file_types = FileService.get_supported_file_types()
        
        # 按处理器名称分组
        result = []
        for file_type in file_types:
            result.append({
                "name": file_type['name'],
                "description": file_type['description'],
                "extensions": file_type['extensions'],
                "mime_types": file_type['mime_types']
            })
        
        return jsonify({
            "success": True,
            "file_types": result
        })
    except Exception as e:
        error_message = f"获取支持的文件类型时出错: {str(e)}"
        traceback.print_exc()
        
        return jsonify(success=False, error=error_message) 