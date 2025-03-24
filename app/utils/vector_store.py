"""
向量存储工具模块
提供文档向量化、向量存储和检索功能
"""
import os
import json
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from app.utils.nlp_utils import TextProcessor

# Qdrant客户端实例
_qdrant_client = None

def get_qdrant_client(host="localhost", port=6333, path=None):
    """
    获取Qdrant客户端
    
    参数:
        host: Qdrant服务器主机
        port: Qdrant服务器端口
        path: 本地存储路径
        
    返回:
        QdrantClient实例
    """
    global _qdrant_client
    
    if _qdrant_client is not None:
        return _qdrant_client
    
    try:
        if path:
            # 使用本地文件存储
            # 确保目录存在
            os.makedirs(os.path.dirname(path), exist_ok=True)
            _qdrant_client = QdrantClient(path=path)
        else:
            # 使用远程服务器
            _qdrant_client = QdrantClient(host=host, port=port)
            
        return _qdrant_client
    except Exception as e:
        print(f"连接Qdrant服务器失败: {str(e)}")
        # 出错时使用本地存储作为备选
        instance_path = os.path.join(os.getcwd(), "instance")
        os.makedirs(instance_path, exist_ok=True)
        path = os.path.join(instance_path, "qdrant_data")
        _qdrant_client = QdrantClient(path=path)
        return _qdrant_client


class DocumentVectorizer:
    """文档向量化工具类"""
    
    def __init__(self, collection_name="medical_documents", vector_size=384):
        """
        初始化文档向量化工具
        
        参数:
            collection_name: 集合名称
            vector_size: 向量维度
        """
        self.collection_name = collection_name
        self.vector_size = vector_size
        
        # 获取Qdrant客户端
        instance_path = os.path.join(os.getcwd(), "instance")
        path = os.path.join(instance_path, "qdrant_data")
        self.client = get_qdrant_client(path=path)
        
        # 确保集合存在
        self._ensure_collection()
        
        # 加载SentenceTransformer以生成文本向量
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('distiluse-base-multilingual-cased-v1')
        except Exception as e:
            print(f"加载SentenceTransformer模型失败: {str(e)}")
            self.model = None
            
    def _ensure_collection(self):
        """确保集合存在，如不存在则创建"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                print(f"创建集合: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE)
                )
        except Exception as e:
            print(f"确保集合存在时出错: {str(e)}")
    
    def get_text_embedding(self, text: str) -> List[float]:
        """
        获取文本嵌入向量
        
        参数:
            text: 文本内容
            
        返回:
            嵌入向量
        """
        if self.model is None:
            # 如果模型不可用，生成随机向量（仅用于测试）
            print("警告: 使用随机向量替代实际嵌入")
            return list(np.random.rand(self.vector_size).astype(float))
        
        try:
            # 使用SentenceTransformer模型生成嵌入
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            print(f"生成文本嵌入出错: {str(e)}")
            # 出错时返回随机向量
            return list(np.random.rand(self.vector_size).astype(float))
    
    def index_document(self, doc_id: str, text: str, metadata: Dict[str, Any] = None) -> bool:
        """
        索引文档
        
        参数:
            doc_id: 文档ID
            text: 文档文本
            metadata: 文档元数据
            
        返回:
            是否成功
        """
        try:
            # 获取文本嵌入
            embedding = self.get_text_embedding(text)
            
            # 准备元数据
            payload = metadata or {}
            
            # 添加基本元数据
            if 'text' not in payload:
                payload['text'] = text[:1000]  # 存储前1000个字符
            if 'indexed_at' not in payload:
                payload['indexed_at'] = datetime.now().isoformat()
            
            # 将文档添加到集合
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=doc_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            return True
        except Exception as e:
            print(f"索引文档出错: {str(e)}")
            return False
    
    def search_similar(self, query: str, limit: int = 5, filter_condition: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        搜索相似文档
        
        参数:
            query: 查询文本
            limit: 返回结果数量限制
            filter_condition: 过滤条件
            
        返回:
            相似文档列表
        """
        try:
            # 获取查询文本的嵌入
            query_embedding = self.get_text_embedding(query)
            
            # 准备过滤条件
            filter_param = None
            if filter_condition:
                filter_param = models.Filter(**filter_condition)
            
            # 执行搜索
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                filter=filter_param
            )
            
            # 转换结果格式
            results = []
            for result in search_results:
                item = {
                    'id': result.id,
                    'score': result.score
                }
                
                # 添加payload中的所有字段
                if result.payload:
                    for key, value in result.payload.items():
                        item[key] = value
                
                results.append(item)
                
            return results
        except Exception as e:
            print(f"搜索相似文档出错: {str(e)}")
            return []
    
    def delete_document(self, doc_id: str) -> bool:
        """
        删除文档
        
        参数:
            doc_id: 文档ID
            
        返回:
            是否成功
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=[doc_id]
                )
            )
            return True
        except Exception as e:
            print(f"删除文档出错: {str(e)}")
            return False
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档
        
        参数:
            doc_id: 文档ID
            
        返回:
            文档数据
        """
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[doc_id]
            )
            
            if not result:
                return None
                
            doc = result[0]
            document = {
                'id': doc.id
            }
            
            # 添加payload中的所有字段
            if doc.payload:
                for key, value in doc.payload.items():
                    document[key] = value
                    
            return document
        except Exception as e:
            print(f"获取文档出错: {str(e)}")
            return None


# 用于小型应用的简单文件系统向量存储实现
class SimpleVectorStore:
    """简单文件系统向量存储实现，适用于小型应用"""
    
    def __init__(self, storage_path="instance/vector_store.pkl"):
        """
        初始化简单向量存储
        
        参数:
            storage_path: 存储文件路径
        """
        self.storage_path = storage_path
        self.vectors = {}  # {id: {'vector': [], 'metadata': {}}}
        
        # 加载现有数据
        self._load()
        
        # 加载SentenceTransformer以生成文本向量
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('distiluse-base-multilingual-cased-v1')
            self.vector_size = 384  # 默认向量维度
        except Exception as e:
            print(f"加载SentenceTransformer模型失败: {str(e)}")
            self.model = None
            self.vector_size = 384
    
    def _load(self):
        """从文件加载向量数据"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'rb') as f:
                    self.vectors = pickle.load(f)
                print(f"从 {self.storage_path} 加载了 {len(self.vectors)} 个向量")
        except Exception as e:
            print(f"加载向量数据出错: {str(e)}")
            self.vectors = {}
    
    def _save(self):
        """将向量数据保存到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            with open(self.storage_path, 'wb') as f:
                pickle.dump(self.vectors, f)
        except Exception as e:
            print(f"保存向量数据出错: {str(e)}")
    
    def get_text_embedding(self, text: str) -> List[float]:
        """
        获取文本嵌入向量
        
        参数:
            text: 文本内容
            
        返回:
            嵌入向量
        """
        if self.model is None:
            # 如果模型不可用，生成随机向量（仅用于测试）
            print("警告: 使用随机向量替代实际嵌入")
            return list(np.random.rand(self.vector_size).astype(float))
        
        try:
            # 使用SentenceTransformer模型生成嵌入
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            print(f"生成文本嵌入出错: {str(e)}")
            # 出错时返回随机向量
            return list(np.random.rand(self.vector_size).astype(float))
    
    def add_item(self, item_id: str, text: str, metadata: Dict[str, Any] = None) -> bool:
        """
        添加项目
        
        参数:
            item_id: 项目ID
            text: 文本内容
            metadata: 元数据
            
        返回:
            是否成功
        """
        try:
            vector = self.get_text_embedding(text)
            
            # 准备元数据
            meta = metadata or {}
            
            # 添加基本元数据
            if 'text' not in meta:
                meta['text'] = text[:1000]  # 存储前1000个字符
            if 'indexed_at' not in meta:
                meta['indexed_at'] = datetime.now().isoformat()
            
            # 存储向量和元数据
            self.vectors[item_id] = {
                'vector': vector,
                'metadata': meta
            }
            
            # 保存到文件
            self._save()
            return True
        except Exception as e:
            print(f"添加项目出错: {str(e)}")
            return False
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        搜索相似项
        
        参数:
            query: 查询文本
            limit: 返回结果数量限制
            
        返回:
            相似项列表
        """
        try:
            if not self.vectors:
                return []
                
            query_vector = self.get_text_embedding(query)
            
            # 计算相似度
            results = []
            for item_id, item_data in self.vectors.items():
                vector = item_data['vector']
                metadata = item_data['metadata']
                
                # 计算余弦相似度
                similarity = self._cosine_similarity(query_vector, vector)
                
                results.append({
                    'id': item_id,
                    'score': similarity,
                    **metadata
                })
            
            # 按相似度排序
            results.sort(key=lambda x: x['score'], reverse=True)
            
            # 限制返回数量
            return results[:limit]
        except Exception as e:
            print(f"搜索相似项出错: {str(e)}")
            return []
    
    def _cosine_similarity(self, vec1, vec2):
        """计算余弦相似度"""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm_a = np.linalg.norm(vec1)
            norm_b = np.linalg.norm(vec2)
            
            return dot_product / (norm_a * norm_b)
        except Exception as e:
            print(f"计算余弦相似度出错: {str(e)}")
            return 0
    
    def delete_item(self, item_id: str) -> bool:
        """
        删除项目
        
        参数:
            item_id: 项目ID
            
        返回:
            是否成功
        """
        try:
            if item_id in self.vectors:
                del self.vectors[item_id]
                self._save()
                return True
            return False
        except Exception as e:
            print(f"删除项目出错: {str(e)}")
            return False
    
    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        获取项目
        
        参数:
            item_id: 项目ID
            
        返回:
            项目数据
        """
        try:
            if item_id in self.vectors:
                return {
                    'id': item_id,
                    **self.vectors[item_id]['metadata']
                }
            return None
        except Exception as e:
            print(f"获取项目出错: {str(e)}")
            return None 