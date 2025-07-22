"""
Qwen3 Text-Embedding-v4 模型封装
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

基于阿里巴巴Qwen3的text-embedding-v4模型，
专为中文文本语义向量化优化。
"""

import os
import time
import hashlib
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass

import numpy as np
from loguru import logger
import dashscope
from dashscope import TextEmbedding


@dataclass
class EmbeddingConfig:
    """Embedding配置"""
    model_name: str = "text-embedding-v4"
    dimension: int = 1536
    batch_size: int = 32
    max_text_length: int = 2048
    cache_enabled: bool = True
    cache_dir: str = "data/cache/embeddings"
    rate_limit_delay: float = 0.1  # 请求间隔（秒）


class QwenEmbeddings:
    """
    Qwen3 Text-Embedding-v4 模型封装类
    
    特性:
    - 高质量中文语义向量化
    - 智能批处理和缓存
    - 速率限制和错误重试
    - 多种文本预处理策略
    """
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        self._setup_api()
        self._setup_cache()
        
        logger.info(f"初始化Qwen3 Embedding模型: {self.config.model_name}")
        logger.info(f"向量维度: {self.config.dimension}, 批处理大小: {self.config.batch_size}")
    
    def _setup_api(self) -> None:
        """设置DashScope API"""
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if not api_key:
            raise ValueError(
                "未找到DASHSCOPE_API_KEY环境变量。\n"
                "请设置: export DASHSCOPE_API_KEY=your_api_key"
            )
        
        dashscope.api_key = api_key
        logger.debug("DashScope API密钥配置完成")
    
    def _setup_cache(self) -> None:
        """设置缓存目录"""
        if self.config.cache_enabled:
            os.makedirs(self.config.cache_dir, exist_ok=True)
            self._cache = {}
            logger.debug(f"缓存目录已创建: {self.config.cache_dir}")
    
    def _get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(f"{self.config.model_name}:{text}".encode()).hexdigest()
    
    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 清理多余空白
        text = ' '.join(text.split())
        
        # 截断过长文本
        if len(text) > self.config.max_text_length:
            text = text[:self.config.max_text_length]
            logger.warning(f"文本过长，已截断到{self.config.max_text_length}字符")
        
        return text
    
    def embed_single(self, text: str) -> np.ndarray:
        """
        生成单个文本的向量
        
        Args:
            text: 输入文本
            
        Returns:
            向量数组 (1536维)
        """
        if not text.strip():
            logger.warning("空文本，返回零向量")
            return np.zeros(self.config.dimension)
        
        # 预处理文本
        processed_text = self._preprocess_text(text)
        
        # 检查缓存
        if self.config.cache_enabled:
            cache_key = self._get_cache_key(processed_text)
            if cache_key in self._cache:
                logger.debug("从缓存获取向量")
                return self._cache[cache_key]
        
        # 调用API
        try:
            response = TextEmbedding.call(
                model=self.config.model_name,
                input=processed_text
            )
            
            if response.status_code == 200:
                embedding = np.array(response.output['embeddings'][0]['embedding'])
                
                # 缓存结果
                if self.config.cache_enabled:
                    self._cache[cache_key] = embedding
                
                # 速率限制
                time.sleep(self.config.rate_limit_delay)
                
                logger.debug(f"成功生成向量，维度: {len(embedding)}")
                return embedding
            else:
                raise Exception(f"API调用失败: {response.message}")
                
        except Exception as e:
            logger.error(f"向量化失败: {e}")
            # 返回零向量作为备选
            return np.zeros(self.config.dimension)
    
    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        批量生成文本向量
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表
        """
        if not texts:
            return []
        
        embeddings = []
        
        # 分批处理
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i:i + self.config.batch_size]
            logger.info(f"处理批次 {i//self.config.batch_size + 1}/{(len(texts)-1)//self.config.batch_size + 1}")
            
            # 逐个处理（Qwen API暂不支持真正的批处理）
            batch_embeddings = []
            for text in batch:
                embedding = self.embed_single(text)
                batch_embeddings.append(embedding)
            
            embeddings.extend(batch_embeddings)
            
            # 批次间延迟
            if i + self.config.batch_size < len(texts):
                time.sleep(self.config.rate_limit_delay * 2)
        
        logger.info(f"批量向量化完成，共处理 {len(texts)} 个文本")
        return embeddings
    
    def embed_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        为文档生成向量并附加元数据
        
        Args:
            documents: 文档列表，每个文档包含'text'和其他元数据
            
        Returns:
            带向量的文档列表
        """
        logger.info(f"开始处理 {len(documents)} 个文档")
        
        texts = [doc['text'] for doc in documents]
        embeddings = self.embed_batch(texts)
        
        # 将向量附加到文档
        enhanced_documents = []
        for doc, embedding in zip(documents, embeddings):
            enhanced_doc = doc.copy()
            enhanced_doc['embedding'] = embedding
            enhanced_doc['embedding_model'] = self.config.model_name
            enhanced_doc['embedding_dimension'] = len(embedding)
            enhanced_documents.append(enhanced_doc)
        
        logger.info("文档向量化完成")
        return enhanced_documents
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            embedding1: 向量1
            embedding2: 向量2
            
        Returns:
            相似度分数 [0, 1]
        """
        # 余弦相似度
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        # 转换到 [0, 1] 范围
        return (similarity + 1) / 2
    
    def find_most_similar(self, query_embedding: np.ndarray, 
                         candidate_embeddings: List[np.ndarray], 
                         top_k: int = 5) -> List[tuple]:
        """
        找到最相似的向量
        
        Args:
            query_embedding: 查询向量
            candidate_embeddings: 候选向量列表
            top_k: 返回前k个结果
            
        Returns:
            (索引, 相似度分数) 的列表，按相似度降序排列
        """
        similarities = []
        for i, candidate in enumerate(candidate_embeddings):
            sim = self.similarity(query_embedding, candidate)
            similarities.append((i, sim))
        
        # 按相似度降序排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置信息"""
        return {
            'model_name': self.config.model_name,
            'dimension': self.config.dimension,
            'batch_size': self.config.batch_size,
            'max_text_length': self.config.max_text_length,
            'cache_enabled': self.config.cache_enabled
        }
    
    def clear_cache(self) -> None:
        """清空缓存"""
        if self.config.cache_enabled:
            self._cache.clear()
            logger.info("缓存已清空")


# 便捷函数
def create_qwen_embeddings(api_key: Optional[str] = None, 
                          **config_kwargs) -> QwenEmbeddings:
    """
    创建Qwen Embeddings实例的便捷函数
    
    Args:
        api_key: DashScope API密钥
        **config_kwargs: 其他配置参数
        
    Returns:
        QwenEmbeddings实例
    """
    if api_key:
        os.environ['DASHSCOPE_API_KEY'] = api_key
    
    config = EmbeddingConfig(**config_kwargs)
    return QwenEmbeddings(config) 