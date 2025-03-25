"""
知识库服务模块 - 处理知识库内容检索和分析
"""
import traceback
import sqlite3
from typing import Dict, Any, List, Optional, Tuple
import json
from flask import current_app
import os

from app.services.base_llm_service import BaseLLMService
from app.prompts import KB_ANALYSIS_SYSTEM_PROMPT, KB_RESPONSE_SYSTEM_PROMPT, KB_RESPONSE_USER_PROMPT

# 导入LangChain相关库
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.chains.retrieval_qa.base import BaseRetrievalQA

class KnowledgeBaseService(BaseLLMService):
    """
    知识库服务类，处理知识库内容检索和分析
    """
    
    def __init__(self, model_name=None, api_key=None, api_url=None):
        """
        初始化知识库服务
        
        参数:
            model_name: 模型名称，默认使用环境变量中的设置
            api_key: API密钥，默认使用环境变量中的设置
            api_url: API端点URL，默认使用环境变量中的设置
        """
        super().__init__(model_name, api_key, api_url)
        print(f"初始化KnowledgeBaseService，使用模型: {self.model_name}")
        
        # 初始化向量存储
        self.vectorstore = None
        self.retrieval_chain = None
        self._init_vectorstore()
    
    def _init_vectorstore(self):
        """初始化向量存储"""
        try:
            # 检查向量存储目录
            vector_dir = os.path.join(current_app.instance_path, 'vector_db')
            os.makedirs(vector_dir, exist_ok=True)
            
            # 初始化embedding模型
            # 注意：首次运行时会下载模型，确保网络连接正常
            self.embeddings = HuggingFaceEmbeddings(
                model_name="distiluse-base-multilingual-cased-v1"
            )
            
            # 尝试加载已有的向量存储
            vector_db_path = os.path.join(vector_dir, 'faiss_index')
            if os.path.exists(vector_db_path):
                try:
                    print(f"尝试加载已有向量存储: {vector_db_path}")
                    self.vectorstore = FAISS.load_local(vector_db_path, self.embeddings)
                    print("成功加载FAISS向量存储")
                    
                    # 创建检索链
                    self._create_retrieval_chain()
                    return
                except Exception as e:
                    print(f"加载向量存储失败: {str(e)}")
            
            # 如果无法加载，从数据库中初始化
            print("从数据库初始化向量存储")
            self._initialize_from_database()
        except Exception as e:
            print(f"初始化向量存储失败: {str(e)}")
            traceback.print_exc()
    
    def _initialize_from_database(self):
        """从数据库中初始化向量存储"""
        try:
            # 获取数据库路径
            db_path = current_app.config.get('DATABASE_PATH', 'medical_workload.db')
            
            # 检查knowledge_base表是否存在
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 检查表是否存在
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='knowledge_base_chunks'
            """)
            
            if not cursor.fetchone():
                print("知识库表不存在，跳过向量存储初始化")
                conn.close()
                return
            
            # 获取所有知识块
            cursor.execute("""
                SELECT k.id, k.title, c.chunk_index, c.content 
                FROM knowledge_base k
                JOIN knowledge_base_chunks c ON k.id = c.knowledge_id
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                print("知识库为空，跳过向量存储初始化")
                return
            
            # 转换为Document对象
            documents = []
            for id, title, chunk_index, content in rows:
                if not content:
                    continue
                
                # 创建Document对象，包含元数据
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": f"知识库ID:{id}",
                        "title": title,
                        "chunk_index": chunk_index
                    }
                )
                documents.append(doc)
            
            # 创建向量存储
            if documents:
                self.vectorstore = FAISS.from_documents(documents, self.embeddings)
                
                # 保存向量存储
                vector_dir = os.path.join(current_app.instance_path, 'vector_db')
                self.vectorstore.save_local(os.path.join(vector_dir, 'faiss_index'))
                print(f"向量存储已保存，包含 {len(documents)} 个文档")
                
                # 创建检索链
                self._create_retrieval_chain()
            else:
                print("未找到有效知识块，向量存储未创建")
        except Exception as e:
            print(f"从数据库初始化向量存储失败: {str(e)}")
            traceback.print_exc()
    
    def _create_retrieval_chain(self):
        """创建检索链"""
        if not self.vectorstore:
            return
        
        try:
            # 创建检索QA链
            self.retrieval_chain = RetrievalQA.from_chain_type(
                llm=self._langchain_llm,
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever(
                    search_kwargs={"k": 5}  # 返回前5个相关文档
                ),
                return_source_documents=True
            )
            print("检索链创建成功")
        except Exception as e:
            print(f"创建检索链失败: {str(e)}")
            self.retrieval_chain = None
    
    @property
    def _langchain_llm(self):
        """为LangChain提供兼容的LLM包装器"""
        from langchain.llms.base import LLM
        from typing import Optional, List, Mapping, Any
        
        class CustomLLM(LLM):
            """自定义LLM包装器，使用BaseLLMService调用API"""
            
            def __init__(self, base_service):
                """初始化LLM包装器"""
                self.base_service = base_service
                super().__init__()
            
            def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
                """调用LLM API"""
                return self.base_service.call_api(
                    system_prompt=KB_RESPONSE_SYSTEM_PROMPT,
                    user_message=prompt,
                    temperature=0.4,
                    top_p=0.9
                )
            
            @property
            def _llm_type(self) -> str:
                """返回LLM类型"""
                return "custom_llm"
        
        return CustomLLM(self)
    
    def search_knowledge_base_with_langchain(self, user_query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        使用LangChain在知识库中搜索与用户查询相关的内容
        
        参数:
            user_query: 用户查询
            limit: 返回结果数量限制
            
        返回:
            相关知识块列表
        """
        try:
            if not self.vectorstore:
                print("向量存储未初始化，退回到传统搜索")
                return self.search_knowledge_base(user_query, limit=limit)
            
            # 使用向量搜索
            results = self.vectorstore.similarity_search_with_score(user_query, k=limit)
            
            # 转换结果格式
            knowledge_chunks = []
            for doc, score in results:
                knowledge_chunks.append({
                    "id": doc.metadata.get("source", "").replace("知识库ID:", ""),
                    "title": doc.metadata.get("title", "未知标题"),
                    "chunk_index": doc.metadata.get("chunk_index", 0),
                    "content": doc.page_content,
                    "relevance_score": score
                })
            
            return knowledge_chunks
        
        except Exception as e:
            print(f"LangChain向量搜索出错: {str(e)}")
            traceback.print_exc()
            # 回退到传统搜索
            return self.search_knowledge_base(user_query, limit=limit)
    
    def generate_knowledge_response_with_chain(self, user_query: str) -> str:
        """
        使用LangChain检索QA链生成回复
        
        参数:
            user_query: 用户查询
            
        返回:
            生成的回复
        """
        try:
            if not self.retrieval_chain:
                print("检索链未初始化，退回到传统方法")
                knowledge_chunks = self.search_knowledge_base_with_langchain(user_query)
                return self.generate_knowledge_response(user_query, knowledge_chunks)
            
            # 使用检索链生成回复
            result = self.retrieval_chain({"query": user_query})
            
            # 如果有结果，返回
            if result and "result" in result:
                return result["result"]
            else:
                return "未能找到相关信息，请尝试重新表述您的问题。"
        
        except Exception as e:
            print(f"LangChain检索链生成回复出错: {str(e)}")
            traceback.print_exc()
            # 回退到传统方法
            knowledge_chunks = self.search_knowledge_base_with_langchain(user_query)
            return self.generate_knowledge_response(user_query, knowledge_chunks)
    
    def search_knowledge_base(self, user_query: str, db_path: str = 'medical_workload.db', limit: int = 5) -> List[Dict[str, Any]]:
        """
        在知识库中搜索与用户查询相关的内容
        
        参数:
            user_query: 用户查询
            db_path: 数据库路径
            limit: 返回结果数量限制
            
        返回:
            相关知识块列表
        """
        try:
            # 先使用AI分析查询意图和关键词
            search_prompt = f"""
            请分析以下用户查询，提取出3-5个用于在知识库中搜索的关键词或短语：
            
            用户查询: {user_query}
            
            要求:
            1. 仅提取关键词或简短的短语，不要包含介词、连词等虚词
            2. 关键词应该能够代表查询的核心主题和意图
            3. 关注医疗专业术语或重要概念
            4. 以JSON数组格式返回关键词，例如: ["关键词1", "关键词2", "关键词3"]
            """
            
            keywords_json = self.call_api(
                system_prompt="你是一位精确的医疗搜索关键词提取专家。你的任务是从用户查询中提取出最适合在医疗知识库中搜索的关键词。",
                user_message=search_prompt,
                temperature=0.3
            )
            
            # 解析关键词
            try:
                keywords = json.loads(keywords_json.strip())
                if not isinstance(keywords, list):
                    keywords = [user_query]  # 如果返回的不是列表，则使用原始查询
            except Exception as e:
                print(f"解析关键词JSON出错: {str(e)}")
                keywords = [user_query]  # 回退到使用原始查询
                
            print(f"从查询中提取的关键词: {keywords}")
            
            # 获取数据库路径
            if db_path == 'medical_workload.db':
                db_path = current_app.config.get('DATABASE_PATH', db_path)
            
            # 连接数据库
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 构建查询条件
            search_conditions = []
            params = []
            
            for keyword in keywords:
                search_conditions.append("content LIKE ?")
                params.append(f"%{keyword}%")
            
            # 构建SQL查询
            query = f"""
            SELECT kb.id, kb.title, kbc.chunk_index, kbc.content
            FROM knowledge_base kb
            JOIN knowledge_base_chunks kbc ON kb.id = kbc.knowledge_id
            WHERE {" OR ".join(search_conditions)}
            ORDER BY kb.id, kbc.chunk_index
            LIMIT ?
            """
            params.append(limit)
            
            # 执行查询
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # 转换为字典列表
            knowledge_chunks = []
            for row in results:
                knowledge_chunks.append({
                    "id": row["id"],
                    "title": row["title"],
                    "chunk_index": row["chunk_index"],
                    "content": row["content"]
                })
            
            conn.close()
            return knowledge_chunks
        
        except Exception as e:
            print(f"搜索知识库时出错: {str(e)}")
            traceback.print_exc()
            return []
    
    def generate_knowledge_response(self, user_query: str, knowledge_chunks: List[Dict[str, Any]]) -> str:
        """
        根据检索到的知识库内容生成回复
        
        参数:
            user_query: 用户查询
            knowledge_chunks: 知识库块列表
            
        返回:
            生成的回复
        """
        try:
            if not knowledge_chunks:
                return "未找到相关知识库内容，无法提供基于知识库的回答。"
            
            # 格式化知识块为文本
            knowledge_text = "\n\n".join([
                f"标题: {chunk['title']}\n内容片段 {chunk['chunk_index'] + 1}:\n{chunk['content']}"
                for chunk in knowledge_chunks
            ])
            
            # 构建用户提示词
            user_prompt = KB_RESPONSE_USER_PROMPT.format(
                analysis_results=knowledge_text,
                user_query=user_query
            )
            
            # 调用LLM生成回复
            response = self.call_api(
                system_prompt=KB_RESPONSE_SYSTEM_PROMPT,
                user_message=user_prompt,
                temperature=0.4,
                top_p=0.9
            )
            
            if not response:
                return "无法根据知识库内容生成回复，请稍后重试。"
            
            return response
        
        except Exception as e:
            print(f"生成知识库回复时出错: {str(e)}")
            traceback.print_exc()
            return f"处理知识库内容时发生错误: {str(e)}"

def get_knowledge_base():
    """获取知识库"""
    try:
        db_path = config.DATABASE_PATH
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM knowledge_base")
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"获取知识库失败: {str(e)}")
        traceback.print_exc()
        return []

def update_knowledge_base():
    """更新知识库"""
    try:
        db_path = config.DATABASE_PATH
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 更新知识库内容
        cursor.execute("""
            UPDATE knowledge_base 
            SET last_updated = CURRENT_TIMESTAMP 
            WHERE id IN (
                SELECT id FROM knowledge_base 
                WHERE needs_update = 1
            )
        """)
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"更新知识库失败: {str(e)}")
        traceback.print_exc()
        return False 