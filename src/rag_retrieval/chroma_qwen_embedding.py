"""
ChromaDB兼容的Qwen Embedding包装器
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

将Qwen3 embedding模型包装成ChromaDB兼容的EmbeddingFunction，
解决维度不匹配问题，提升搜索性能。
"""

from typing import List
import numpy as np
from chromadb.utils.embedding_functions import EmbeddingFunction
from loguru import logger

from .qwen_embeddings import QwenEmbeddings, EmbeddingConfig


class ChromaQwenEmbedding(EmbeddingFunction):
    """
    ChromaDB兼容的Qwen embedding函数
    
    将我们的QwenEmbeddings包装成ChromaDB可以直接使用的embedding函数，
    这样query_texts就会使用我们的1024维Qwen模型而不是默认的384维模型。
    """
    
    def __init__(self, config: EmbeddingConfig = None):
        """初始化ChromaDB兼容的Qwen embedding"""
        self.qwen_embeddings = QwenEmbeddings(config or EmbeddingConfig())
        logger.info("ChromaDB兼容的Qwen Embedding初始化完成")
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        """
        ChromaDB调用接口
        
        Args:
            input: 文本列表
            
        Returns:
            向量列表（每个向量是float列表）
        """
        if not input:
            return []
        
        try:
            # 批量处理文本
            embeddings = self.qwen_embeddings.embed_batch(input)
            
            # 转换为ChromaDB期望的格式（List[List[float]]）
            result = [embedding.tolist() for embedding in embeddings]
            
            logger.debug(f"ChromaDB Qwen embedding处理完成: {len(input)} 个文本")
            return result
            
        except Exception as e:
            logger.error(f"ChromaDB Qwen embedding处理失败: {e}")
            # 返回零向量作为fallback
            zero_vector = [0.0] * self.qwen_embeddings.config.dimension
            return [zero_vector] * len(input) 