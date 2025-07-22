"""
混合检索器
~~~~~~~~~

结合语义检索和文本匹配的智能检索器，
提供多种检索策略和结果融合算法。
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from loguru import logger

from .qwen_embeddings import QwenEmbeddings
from .vector_database import VectorDatabase
from .semantic_search import SemanticSearcher


class HybridRetriever:
    """
    混合检索器
    
    结合多种检索策略：
    - 语义相似度检索
    - 关键词文本检索
    - 元数据过滤检索
    - 结果融合和重排序
    """
    
    def __init__(self, embeddings: QwenEmbeddings, vectordb: VectorDatabase):
        self.embeddings = embeddings
        self.vectordb = vectordb
        self.semantic_searcher = SemanticSearcher(embeddings, vectordb)
        
        logger.info("混合检索器初始化完成")
    
    def search(self, query: str,
              search_strategy: str = "hybrid",
              n_results: int = 5,
              semantic_weight: float = 0.7,
              text_weight: float = 0.3,
              metadata_filter: Optional[Dict[str, Any]] = None,
              **kwargs) -> Dict[str, Any]:
        """
        执行混合检索
        
        Args:
            query: 查询文本
            search_strategy: 检索策略 ("semantic", "text", "hybrid", "auto")
            n_results: 返回结果数量
            semantic_weight: 语义检索权重
            text_weight: 文本检索权重
            metadata_filter: 元数据过滤器
            **kwargs: 其他参数
            
        Returns:
            检索结果
        """
        if search_strategy == "semantic":
            return self._semantic_search(query, n_results, metadata_filter)
        elif search_strategy == "text":
            return self._text_search(query, n_results, metadata_filter)
        elif search_strategy == "hybrid":
            return self._hybrid_search(
                query, n_results, semantic_weight, text_weight, metadata_filter
            )
        elif search_strategy == "auto":
            return self._auto_search(query, n_results, metadata_filter, **kwargs)
        else:
            raise ValueError(f"不支持的检索策略: {search_strategy}")
    
    def _semantic_search(self, query: str, n_results: int, 
                        metadata_filter: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """纯语义检索"""
        return self.semantic_searcher.search(
            query, n_results=n_results, metadata_filter=metadata_filter
        )
    
    def _text_search(self, query: str, n_results: int,
                    metadata_filter: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """纯文本检索"""
        return self.vectordb.search_by_text(
            query, n_results=n_results, metadata_filter=metadata_filter
        )
    
    def _hybrid_search(self, query: str, n_results: int,
                      semantic_weight: float, text_weight: float,
                      metadata_filter: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """混合检索"""
        # 语义检索
        query_embedding = self.embeddings.embed_single(query)
        
        # 执行混合检索
        return self.vectordb.hybrid_search(
            query_embedding, query,
            n_results=n_results,
            semantic_weight=semantic_weight,
            text_weight=text_weight,
            metadata_filter=metadata_filter
        )
    
    def _auto_search(self, query: str, n_results: int,
                    metadata_filter: Optional[Dict[str, Any]],
                    **kwargs) -> Dict[str, Any]:
        """
        自动选择最优检索策略
        
        根据查询内容的特点自动选择检索策略
        """
        # 分析查询特征
        query_features = self._analyze_query(query)
        
        # 根据特征选择策略
        if query_features['has_names'] and query_features['is_short']:
            # 包含人名且较短，使用文本检索
            strategy = "text"
            logger.debug("自动选择策略: 文本检索（人名查询）")
        elif query_features['is_semantic'] and query_features['is_long']:
            # 语义性强且较长，使用语义检索
            strategy = "semantic" 
            logger.debug("自动选择策略: 语义检索（语义查询）")
        else:
            # 默认使用混合检索
            strategy = "hybrid"
            logger.debug("自动选择策略: 混合检索（通用查询）")
        
        return self.search(
            query, search_strategy=strategy, n_results=n_results,
            metadata_filter=metadata_filter, **kwargs
        )
    
    def _analyze_query(self, query: str) -> Dict[str, bool]:
        """分析查询特征"""
        # 红楼梦人名列表（简化版）
        character_names = ['宝玉', '黛玉', '宝钗', '凤姐', '湘云', '迎春', '探春', '惜春']
        
        features = {
            'has_names': any(name in query for name in character_names),
            'is_short': len(query) <= 20,
            'is_long': len(query) > 50,
            'is_semantic': any(word in query for word in ['关系', '为什么', '如何', '怎样', '情感', '性格']),
            'is_specific': any(word in query for word in ['第', '回', '章节', '具体'])
        }
        
        return features
    
    def search_with_context(self, query: str,
                           context_queries: List[str],
                           n_results: int = 5,
                           context_weight: float = 0.3) -> Dict[str, Any]:
        """
        基于上下文的检索
        
        Args:
            query: 主查询
            context_queries: 上下文查询列表
            n_results: 返回结果数量
            context_weight: 上下文权重
            
        Returns:
            检索结果
        """
        # 主查询检索
        main_results = self.search(query, n_results=n_results * 2)
        
        # 上下文查询检索
        context_results = []
        for ctx_query in context_queries:
            ctx_result = self.search(ctx_query, n_results=n_results)
            context_results.append(ctx_result)
        
        # 结果融合
        final_results = self._merge_with_context(
            main_results, context_results, context_weight, n_results
        )
        
        logger.debug(f"上下文检索完成，返回 {len(final_results['documents'])} 个结果")
        return final_results
    
    def _merge_with_context(self, main_results: Dict[str, Any],
                           context_results: List[Dict[str, Any]],
                           context_weight: float,
                           n_results: int) -> Dict[str, Any]:
        """融合主查询和上下文查询结果"""
        # 简化实现：提升在上下文中出现的结果的权重
        doc_scores = {}
        
        # 主查询结果
        for i, doc_id in enumerate(main_results['ids']):
            doc_scores[doc_id] = {
                'main_score': main_results['similarities'][i],
                'context_score': 0.0,
                'document': main_results['documents'][i],
                'metadata': main_results['metadatas'][i]
            }
        
        # 上下文结果加权
        for ctx_result in context_results:
            for i, doc_id in enumerate(ctx_result['ids']):
                if doc_id in doc_scores:
                    doc_scores[doc_id]['context_score'] += ctx_result['similarities'][i]
                else:
                    doc_scores[doc_id] = {
                        'main_score': 0.0,
                        'context_score': ctx_result['similarities'][i],
                        'document': ctx_result['documents'][i],
                        'metadata': ctx_result['metadatas'][i]
                    }
        
        # 计算综合分数
        for doc_id in doc_scores:
            main_score = doc_scores[doc_id]['main_score']
            context_score = doc_scores[doc_id]['context_score']
            doc_scores[doc_id]['final_score'] = (
                main_score * (1 - context_weight) + context_score * context_weight
            )
        
        # 排序并返回
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1]['final_score'],
            reverse=True
        )[:n_results]
        
        return {
            'ids': [doc_id for doc_id, _ in sorted_docs],
            'documents': [score_data['document'] for _, score_data in sorted_docs],
            'metadatas': [score_data['metadata'] for _, score_data in sorted_docs],
            'similarities': [score_data['final_score'] for _, score_data in sorted_docs]
        }
    
    def search_by_character(self, character_name: str,
                           context: str = "",
                           n_results: int = 5) -> Dict[str, Any]:
        """
        基于人物的检索
        
        Args:
            character_name: 人物名称
            context: 额外上下文
            n_results: 返回结果数量
            
        Returns:
            检索结果
        """
        # 构建人物过滤器
        metadata_filter = {
            "characters": {"$in": [character_name]}
        }
        
        # 构建查询
        if context:
            query = f"{character_name} {context}"
        else:
            query = character_name
        
        return self.search(
            query,
            search_strategy="hybrid",
            n_results=n_results,
            metadata_filter=metadata_filter
        )
    
    def search_by_theme(self, theme: str,
                       related_characters: Optional[List[str]] = None,
                       n_results: int = 5) -> Dict[str, Any]:
        """
        基于主题的检索
        
        Args:
            theme: 主题描述
            related_characters: 相关人物
            n_results: 返回结果数量
            
        Returns:
            检索结果
        """
        # 构建查询
        if related_characters:
            character_context = " ".join(related_characters)
            query = f"{theme} {character_context}"
        else:
            query = theme
        
        # 构建人物过滤器
        metadata_filter = None
        if related_characters:
            metadata_filter = {
                "characters": {"$in": related_characters}
            }
        
        return self.search(
            query,
            search_strategy="semantic",  # 主题检索偏向语义
            n_results=n_results,
            metadata_filter=metadata_filter
        )


# 便捷函数
def create_hybrid_retriever(embeddings: QwenEmbeddings,
                           vectordb: VectorDatabase) -> HybridRetriever:
    """创建混合检索器"""
    return HybridRetriever(embeddings, vectordb) 