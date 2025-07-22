"""
语义检索引擎
~~~~~~~~~~~

基于向量相似度的高级语义检索接口，
提供便捷的检索方法和结果优化。
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from loguru import logger

from .qwen_embeddings import QwenEmbeddings
from .vector_database import VectorDatabase


class SemanticSearcher:
    """
    语义检索引擎
    
    提供高级的语义检索接口，
    封装了向量化和相似度计算的复杂性。
    """
    
    def __init__(self, embeddings: QwenEmbeddings, vectordb: VectorDatabase):
        self.embeddings = embeddings
        self.vectordb = vectordb
        
        logger.info("语义检索引擎初始化完成")
    
    def search(self, query: str,
              n_results: int = 5,
              similarity_threshold: float = 0.7,
              metadata_filter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行语义检索
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            similarity_threshold: 相似度阈值
            metadata_filter: 元数据过滤器
            
        Returns:
            检索结果
        """
        # 生成查询向量
        query_embedding = self.embeddings.embed_single(query)
        
        # 执行向量检索
        results = self.vectordb.search_similar(
            query_embedding,
            n_results=n_results,
            metadata_filter=metadata_filter
        )
        
        # 应用相似度阈值过滤
        filtered_results = self._apply_threshold_filter(results, similarity_threshold)
        
        logger.debug(f"语义检索完成，返回 {len(filtered_results['documents'])} 个结果")
        return filtered_results
    
    def _apply_threshold_filter(self, results: Dict[str, Any], 
                               threshold: float) -> Dict[str, Any]:
        """应用相似度阈值过滤"""
        valid_indices = [
            i for i, sim in enumerate(results['similarities'])
            if sim >= threshold
        ]
        
        return {
            'ids': [results['ids'][i] for i in valid_indices],
            'documents': [results['documents'][i] for i in valid_indices],
            'metadatas': [results['metadatas'][i] for i in valid_indices],
            'similarities': [results['similarities'][i] for i in valid_indices]
        }


# 便捷函数
def create_semantic_searcher(embeddings: QwenEmbeddings, 
                           vectordb: VectorDatabase) -> SemanticSearcher:
    """创建语义检索器"""
    return SemanticSearcher(embeddings, vectordb) 