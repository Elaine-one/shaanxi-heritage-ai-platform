# -*- coding: utf-8 -*-
"""
向量存储模块
使用 ChromaDB 实现向量存储和检索
支持查询缓存优化
"""

import os
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger
import chromadb
from sentence_transformers import SentenceTransformer

try:
    from cachetools import TTLCache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logger.warning("cachetools 未安装，缓存功能将禁用")


class SimpleCache:
    """简单缓存实现（当 cachetools 不可用时）"""
    
    def __init__(self, maxsize: int = 1000, ttl: float = 300):
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
        self._maxsize = maxsize
        self._ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        import time
        if key in self._cache:
            if time.time() - self._timestamps.get(key, 0) < self._ttl:
                return self._cache[key]
            else:
                del self._cache[key]
                del self._timestamps[key]
        return None
    
    def set(self, key: str, value: Any):
        import time
        if len(self._cache) >= self._maxsize:
            oldest = min(self._timestamps, key=self._timestamps.get)
            del self._cache[oldest]
            del self._timestamps[oldest]
        self._cache[key] = value
        self._timestamps[key] = time.time()


class EmbeddingModel:
    """嵌入模型封装（单例模式），支持缓存"""
    
    _instance = None
    
    def __new__(cls, model_name: str = "BAAI/bge-small-zh", local_model_path: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.model_name = model_name
            cls._instance.local_model_path = local_model_path
            cls._instance.model = None
            cls._instance.dimension = None
            cls._instance._embedding_cache = None
        return cls._instance
    
    def __init__(self, model_name: str = "BAAI/bge-small-zh", local_model_path: str = None):
        if self.model is None:
            if local_model_path and os.path.exists(local_model_path):
                logger.info(f"从本地加载嵌入模型: {local_model_path}")
                self.model = SentenceTransformer(local_model_path)
            else:
                logger.info(f"加载嵌入模型: {model_name}")
                os.environ['HF_HUB_OFFLINE'] = '1'
                try:
                    self.model = SentenceTransformer(model_name)
                except Exception as e:
                    logger.warning(f"离线模式加载失败，尝试在线下载: {e}")
                    os.environ.pop('HF_HUB_OFFLINE', None)
                    self.model = SentenceTransformer(model_name)
            
            self.dimension = self.model.get_sentence_embedding_dimension()
            
            if CACHE_AVAILABLE:
                self._embedding_cache = TTLCache(maxsize=2000, ttl=600)
            else:
                self._embedding_cache = SimpleCache(maxsize=2000, ttl=600)
            
            logger.info(f"嵌入模型加载完成，维度: {self.dimension}")
    
    def _get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def encode(self, texts: List[str]) -> List[List[float]]:
        """将文本列表转换为向量"""
        results = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            cached = self._embedding_cache.get(cache_key) if self._embedding_cache else None
            if cached is not None:
                results.append((i, cached))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        if uncached_texts:
            new_embeddings = self.model.encode(uncached_texts, normalize_embeddings=True).tolist()
            for idx, text, embedding in zip(uncached_indices, uncached_texts, new_embeddings):
                results.append((idx, embedding))
                if self._embedding_cache:
                    cache_key = self._get_cache_key(text)
                    self._embedding_cache.set(cache_key, embedding)
        
        results.sort(key=lambda x: x[0])
        return [r[1] for r in results]
    
    def encode_single(self, text: str) -> List[float]:
        """将单个文本转换为向量（带缓存）"""
        cache_key = self._get_cache_key(text)
        
        if self._embedding_cache:
            cached = self._embedding_cache.get(cache_key)
            if cached is not None:
                return cached
        
        embedding = self.model.encode(text, normalize_embeddings=True).tolist()
        
        if self._embedding_cache:
            self._embedding_cache.set(cache_key, embedding)
        
        return embedding


class VectorStore:
    """向量存储管理器，支持查询缓存"""
    
    COLLECTIONS = {
        'conversations': 'user_conversations',
        'heritage_knowledge': 'heritage_knowledge',
        'attractions': 'attraction_info'
    }
    
    def __init__(self, persist_directory: str = None, embedding_model: str = None, 
                 local_model_path: str = None):
        data_dir = Path(__file__).parent.parent / "data"
        
        if persist_directory is None:
            persist_directory = str(data_dir / "chromadb")
        
        if embedding_model is None:
            from Agent.config.settings import config
            embedding_model = config.EMBEDDING_MODEL
        
        if local_model_path is None:
            local_model_path = str(data_dir / "models" / "bge-small-zh")
        
        os.makedirs(persist_directory, exist_ok=True)
        
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        self.embedding_model = EmbeddingModel(embedding_model, local_model_path)
        
        self.collections = {}
        self._init_collections()
        
        if CACHE_AVAILABLE:
            self._query_cache = TTLCache(maxsize=1000, ttl=300)
        else:
            self._query_cache = SimpleCache(maxsize=1000, ttl=300)
        
        logger.info(f"向量存储初始化完成，路径: {persist_directory}")
    
    def _get_query_cache_key(self, query: str, collection: str, n_results: int, 
                              filter_dict: Dict = None) -> str:
        """生成查询缓存键"""
        filter_str = str(sorted(filter_dict.items())) if filter_dict else ""
        key_str = f"{query}:{collection}:{n_results}:{filter_str}"
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()
    
    def _init_collections(self):
        """初始化所有集合"""
        for key, name in self.COLLECTIONS.items():
            try:
                self.collections[key] = self.client.get_or_create_collection(
                    name=name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"集合 '{name}' 初始化完成")
            except Exception as e:
                logger.error(f"集合 '{name}' 初始化失败: {e}")
    
    def add_conversation(self, session_id: str, user_id: str, role: str, 
                         content: str, metadata: Dict[str, Any] = None):
        """添加对话向量"""
        if 'conversations' not in self.collections:
            return False
        
        doc_id = f"{session_id}_{len(content)}"
        
        embedding = self.embedding_model.encode_single(content)
        
        meta = {
            'session_id': session_id,
            'user_id': user_id,
            'role': role,
            'content_preview': content[:100]
        }
        if metadata:
            meta.update(metadata)
        
        try:
            self.collections['conversations'].add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[meta]
            )
            return True
        except Exception as e:
            logger.error(f"添加对话向量失败: {e}")
            return False
    
    def add_heritage_knowledge(self, heritage_id: int, name: str, 
                               content: str, metadata: Dict[str, Any] = None):
        """添加非遗知识向量"""
        if 'heritage_knowledge' not in self.collections:
            return False
        
        doc_id = f"heritage_{heritage_id}"
        
        embedding = self.embedding_model.encode_single(content)
        
        meta = {
            'heritage_id': heritage_id,
            'name': name
        }
        if metadata:
            for k, v in metadata.items():
                if v is not None:
                    meta[k] = v
        
        try:
            self.collections['heritage_knowledge'].add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[meta]
            )
            return True
        except Exception as e:
            logger.error(f"添加非遗知识向量失败: {e}")
            return False
    
    def add_attraction(self, attraction_id: int, name: str, 
                       content: str, metadata: Dict[str, Any] = None):
        """添加景点信息向量"""
        if 'attractions' not in self.collections:
            return False
        
        doc_id = f"attraction_{attraction_id}"
        
        embedding = self.embedding_model.encode_single(content)
        
        meta = {
            'attraction_id': attraction_id,
            'name': name
        }
        if metadata:
            meta.update(metadata)
        
        try:
            self.collections['attractions'].add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[meta]
            )
            return True
        except Exception as e:
            logger.error(f"添加景点向量失败: {e}")
            return False
    
    def search_conversations(self, query: str, user_id: str = None, 
                            n_results: int = 5) -> List[Dict[str, Any]]:
        """检索相关对话"""
        if 'conversations' not in self.collections:
            return []
        
        query_embedding = self.embedding_model.encode_single(query)
        
        where_filter = None
        if user_id:
            where_filter = {"user_id": user_id}
        
        try:
            results = self.collections['conversations'].query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter,
                include=['documents', 'metadatas', 'distances']
            )
            
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else 0
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"检索对话失败: {e}")
            return []
    
    def search_heritage_knowledge(self, query: str, 
                                  n_results: int = 5) -> List[Dict[str, Any]]:
        """检索非遗知识（带缓存）"""
        if 'heritage_knowledge' not in self.collections:
            return []
        
        cache_key = self._get_query_cache_key(query, 'heritage_knowledge', n_results)
        cached_result = self._query_cache.get(cache_key) if self._query_cache else None
        if cached_result is not None:
            logger.debug(f"缓存命中: {query[:30]}...")
            return cached_result
        
        query_embedding = self.embedding_model.encode_single(query)
        
        try:
            results = self.collections['heritage_knowledge'].query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else 0
                    })
            
            if self._query_cache:
                self._query_cache.set(cache_key, formatted_results)
            
            return formatted_results
        except Exception as e:
            logger.error(f"检索非遗知识失败: {e}")
            return []
    
    def search_attractions(self, query: str, 
                          n_results: int = 5) -> List[Dict[str, Any]]:
        """检索景点信息"""
        if 'attractions' not in self.collections:
            return []
        
        query_embedding = self.embedding_model.encode_single(query)
        
        try:
            results = self.collections['attractions'].query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else 0
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"检索景点失败: {e}")
            return []
    
    def hybrid_search(self, query: str, user_id: str = None, 
                     n_results: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """混合检索：同时检索对话、知识、景点"""
        return {
            'conversations': self.search_conversations(query, user_id, n_results),
            'heritage_knowledge': self.search_heritage_knowledge(query, n_results),
            'attractions': self.search_attractions(query, n_results)
        }
    
    def get_collection_stats(self) -> Dict[str, int]:
        """获取各集合的统计信息"""
        stats = {}
        for key, collection in self.collections.items():
            try:
                stats[key] = collection.count()
            except:
                stats[key] = 0
        return stats


_vector_store_instance = None


def get_vector_store() -> VectorStore:
    """获取向量存储单例"""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance
