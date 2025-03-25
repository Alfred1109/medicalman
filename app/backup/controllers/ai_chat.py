"""
AI聊天控制器模块
"""
from flask import Blueprint, render_template, request, jsonify, session, current_app
from flask_login import login_required
from app.models.database import Database
from app.services.llm_service import LLMServiceFactory
from app.services.file_service import FileService
import json
import traceback
import os
from werkzeug.utils import secure_filename
from config import ALLOWED_EXTENSIONS, UPLOAD_FOLDER

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
            
        # 知识库查询流程
        if data_source == 'knowledge_base' or data_source == 'auto':
            try:
                print(f"尝试从知识库检索与问题相关的内容: {user_query}")
                
                # 获取知识库服务
                kb_service = LLMServiceFactory.get_knowledge_base_service()
                
                # 使用LangChain检索QA链
                try:
                    # 首先尝试使用LangChain方法
                    kb_response = kb_service.generate_knowledge_response_with_chain(user_query)
                    
                    if kb_response and not kb_response.startswith("未找到相关") and not kb_response.startswith("未能找到"):
                        # 返回使用LangChain生成的回复
                        return jsonify(
                            success=True,
                            message=kb_response,
                            type="text",
                            source="knowledge_base_langchain"
                        )
                    
                    print("LangChain知识库检索未返回满意结果，尝试传统方法")
                except Exception as e:
                    print(f"LangChain知识库检索出错: {str(e)}")
                    traceback.print_exc()
                
                # 回退到传统方法
                # 检索知识库
                knowledge_chunks = kb_service.search_knowledge_base(user_query)
                
                # 如果找到相关内容，生成回复
                if knowledge_chunks:
                    print(f"在知识库中找到 {len(knowledge_chunks)} 个相关内容块")
                    
                    # 生成基于知识库的回复
                    kb_response = kb_service.generate_knowledge_response(user_query, knowledge_chunks)
                    
                    # 构建块ID列表，用于追踪引用
                    chunk_ids = [chunk["id"] for chunk in knowledge_chunks]
                    chunk_indexes = [chunk["chunk_index"] for chunk in knowledge_chunks]
                    
                    # 返回知识库回复
                    return jsonify(
                        success=True,
                        message=kb_response,
                        source="knowledge_base",
                        reference_ids=chunk_ids,
                        reference_indexes=chunk_indexes,
                        type="knowledge_base"
                    )
                else:
                    print("在知识库中未找到相关内容，尝试其他方法")
            except Exception as kb_error:
                print(f"知识库查询出错: {str(kb_error)}")
                traceback.print_exc()
                print("继续尝试其他查询方法")
            
        # 默认流程：分析用户查询并生成SQL
        try:
            # 使用工厂方法获取SQL服务
            sql_service = LLMServiceFactory.get_sql_service()
            
            # 生成SQL查询
            print(f"尝试为查询生成SQL: {user_query}")
            analysis_result = sql_service.generate_sql(user_query)
            
            if not analysis_result or 'sql' not in analysis_result:
                print(f"未能生成SQL查询，analysis_result: {analysis_result}")
                # 如果无法生成SQL查询，使用通用回答
                system_prompt = """
                你是一个专业的医疗助手，擅长回答医疗相关问题。
                请根据用户的问题，提供专业、准确的回答。
                如果问题超出你的知识范围，请诚实地表明。
                请注意：如果问题涉及医疗数据的趋势，请尝试生成SQL查询。例如，"SELECT 日期, SUM(数量) as 总量 FROM 门诊量 GROUP BY strftime('%Y-%m', 日期) ORDER BY 日期"可以查询每月门诊总量。
                """
                
                # 使用工厂方法获取基础服务
                base_service = LLMServiceFactory.get_base_service()
                
                # 调用LLM API
                response = base_service.call_api(system_prompt, user_query)
                
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
                
                # 使用工厂方法获取文本分析服务
                text_service = LLMServiceFactory.get_text_analysis_service()
                
                # 准备上下文数据 - 添加防御性检查
                try:
                    context_data = {"query_result": result_data}
                    
                    # 只有当数据中包含这些字段时才添加它们
                    if result_data and len(result_data) > 0:
                        sample_record = result_data[0]
                        
                        # 检查并添加文本内容 (如果存在)
                        if 'text_content' in sample_record:
                            context_data["text_content"] = sample_record['text_content']
                        
                        # 检查并添加元数据 (如果存在)
                        if 'metadata' in sample_record:
                            context_data["metadata"] = sample_record['metadata']
                        
                        # 检查并添加文件类型 (如果存在)
                        if 'file_type' in sample_record:
                            context_data["file_type"] = sample_record['file_type']
                        
                        # 检查并添加文件名 (如果存在)
                        if 'file_name' in sample_record:
                            context_data["file_name"] = sample_record['file_name']
                        
                        # 检查并添加结构化数据 (如果存在)
                        if 'structured_data' in sample_record and sample_record['structured_data']:
                            context_data["structured_data"] = sample_record['structured_data']
                    
                    # 记录上下文数据的键，帮助调试
                    print(f"上下文数据包含以下字段: {', '.join(context_data.keys())}")
                    
                    # 生成文本分析
                    analysis_result = text_service.generate_sql_analysis(
                        user_query=user_query,
                        sql_query=sql_query,
                        results=result_data[:100],  # 限制数据量
                        has_chart=False
                    )
                    
                    if analysis_result:
                        # 尝试自动生成图表
                        charts = text_service.generate_auto_charts(user_query, result_data[:100])
                        
                        # 如果成功生成了图表，则添加到响应中
                        if charts and len(charts) > 0:
                            print(f"生成了{len(charts)}个图表配置")
                            return jsonify(
                                success=True,
                                message=analysis_result,
                                data=result_data,
                                charts=charts,
                                type="data_analysis"
                            )
                        else:
                            # 无图表的响应
                            return jsonify(
                                success=True,
                                message=analysis_result,
                                data=result_data,
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
                except Exception as context_error:
                    print(f"处理上下文数据时出错: {str(context_error)}")
                    traceback.print_exc()
                    
                    # 出错时直接返回数据
                    return jsonify(
                        success=True,
                        message="查询成功，但无法提供完整分析。",
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
                
                # 使用工厂方法获取基础服务
                base_service = LLMServiceFactory.get_base_service()
                
                # 调用LLM API
                response = base_service.call_api(system_prompt, user_query)
                
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
            
            # 使用工厂方法获取基础服务
            base_service = LLMServiceFactory.get_base_service()
            
            # 调用LLM API
            response = base_service.call_api(system_prompt, user_query)
            
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
            allowed_extensions = ALLOWED_EXTENSIONS
        
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
        upload_folder = UPLOAD_FOLDER
        
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
        upload_folder = UPLOAD_FOLDER
        
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
        
        # 准备上下文数据
        context_data = {
            "text_content": text_content,
            "metadata": metadata,
            "file_type": file_type,
            "file_name": filename
        }
        if structured_data:
            context_data["structured_data"] = structured_data
        
        # 生成分析结果
        text_service = LLMServiceFactory.get_text_analysis_service()
        analysis_result = text_service.generate_text_analysis(
            user_query=user_query,
            context_data=json.dumps(context_data, ensure_ascii=False)
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
        upload_folder = UPLOAD_FOLDER
        
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

def upload_file():
    """上传文件"""
    try:
        allowed_extensions = ALLOWED_EXTENSIONS
        # ... rest of the code ...

def download_file():
    """下载文件"""
    try:
        upload_folder = UPLOAD_FOLDER
        # ... rest of the code ...

def delete_file():
    """删除文件"""
    try:
        upload_folder = UPLOAD_FOLDER
        # ... rest of the code ... 