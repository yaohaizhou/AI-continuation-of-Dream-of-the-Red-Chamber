"""
LangChain兼容的Qwen Embedding包装器
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

将Qwen3 embedding模型包装成LangChain兼容的Embeddings类，
用于与LangChain的Chroma集成。
"""

from typing import List
import numpy as np
from langchain_core.embeddings import Embeddings
from loguru import logger

from .qwen_embeddings import QwenEmbeddings, EmbeddingConfig


class LangChainQwenEmbeddings(Embeddings):
    """
    LangChain兼容的Qwen embedding类
    
    继承自LangChain的Embeddings基类，可以直接用于LangChain的向量存储。
    """
    
    def __init__(self, config: EmbeddingConfig = None):
        """初始化LangChain兼容的Qwen embedding"""
        self.qwen_embeddings = QwenEmbeddings(config or EmbeddingConfig())
        logger.info("LangChain兼容的Qwen Embedding初始化完成")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        嵌入文档列表
        
        Args:
            texts: 文档文本列表
            
        Returns:
            嵌入向量列表
        """
        try:
            # 确保所有输入都是字符串类型
            texts = [str(text) if not isinstance(text, str) else text for text in texts]
            
            # 批量处理文本
            embeddings = self.qwen_embeddings.embed_batch(texts)
            
            # 转换为LangChain期望的格式（List[List[float]]）
            result = [embedding.tolist() for embedding in embeddings]
            
            logger.debug(f"LangChain文档嵌入完成: {len(texts)} 个文档")
            return result
            
        except Exception as e:
            logger.error(f"LangChain文档嵌入失败: {e}")
            # 返回零向量作为fallback
            zero_vector = [0.0] * self.qwen_embeddings.config.dimension
            return [zero_vector] * len(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """
        嵌入查询文本
        
        Args:
            text: 查询文本
            
        Returns:
            嵌入向量
        """
        try:
            # 确保输入是字符串类型
            if not isinstance(text, str):
                text = str(text)
            
            # 处理单个查询
            embedding = self.qwen_embeddings.embed_single(text)
            result = embedding.tolist()
            
            logger.debug(f"LangChain查询嵌入完成")
            return result
            
        except Exception as e:
            logger.error(f"LangChain查询嵌入失败: {e}")
            # 返回零向量作为fallback
            return [0.0] * self.qwen_embeddings.config.dimension 