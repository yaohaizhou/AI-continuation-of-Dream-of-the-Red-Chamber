"""
基于LangChain的ChromaDB向量数据库封装
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

使用LangChain的Chroma集成，提供更简洁和强大的向量数据库功能，
专为红楼梦古典文学文本优化。
"""

import os
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from langchain_chroma import Chroma
from langchain_core.documents import Document
from loguru import logger

from .text_chunker import TextChunk
from .langchain_qwen_embedding import LangChainQwenEmbeddings


@dataclass
class LangChainVectorDBConfig:
    """LangChain向量数据库配置"""
    db_path: str = "data/vectordb"
    collection_name: str = "hongloumeng_chunks"
    batch_size: int = 100
    max_results: int = 20
    similarity_threshold: float = 0.7


class LangChainVectorDatabase:
    """
    基于LangChain的ChromaDB向量数据库
    
    主要功能：
    - 使用LangChain的Chroma集成
    - 自动处理embedding和存储
    - 提供统一的搜索接口
    - 简化代码复杂度
    """
    
    def __init__(self, config: Optional[LangChainVectorDBConfig] = None, 
                 embeddings: Optional[LangChainQwenEmbeddings] = None):
        self.config = config or LangChainVectorDBConfig()
        self.embeddings = embeddings or LangChainQwenEmbeddings()
        self._setup_database()
        
        logger.info(f"LangChain向量数据库初始化: {self.config.collection_name}")
        logger.info(f"存储路径: {self.config.db_path}")
    
    def _setup_database(self) -> None:
        """初始化LangChain Chroma数据库"""
        # 创建存储目录
        os.makedirs(self.config.db_path, exist_ok=True)
        
        # 初始化LangChain Chroma
        self.vectorstore = Chroma(
            collection_name=self.config.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.config.db_path
        )
        
        logger.info("LangChain Chroma向量存储初始化完成")
    
    def add_chunks(self, chunks: List[TextChunk]) -> None:
        """
        添加文本块到向量数据库
        
        Args:
            chunks: 文本块列表
        """
        if not chunks:
            return
            
        logger.info(f"开始添加 {len(chunks)} 个文本块到LangChain向量数据库")
        
        # 转换为LangChain Documents
        documents = []
        for chunk in chunks:
            # 准备元数据
            metadata = chunk.metadata.copy()
            metadata.update({
                'chunk_id': chunk.chunk_id,
                'start_pos': chunk.start_pos,
                'end_pos': chunk.end_pos,
                'text_length': len(chunk.text)
            })
            
            # 创建Document
            doc = Document(
                page_content=chunk.text,
                metadata=metadata
            )
            documents.append(doc)
        
        # 批量添加到向量存储
        for i in range(0, len(documents), self.config.batch_size):
            batch_end = min(i + self.config.batch_size, len(documents))
            batch_docs = documents[i:batch_end]
            
            # 生成IDs
            ids = [f"{doc.metadata.get('chunk_id', str(uuid.uuid4()))}" for doc in batch_docs]
            
            self.vectorstore.add_documents(
                documents=batch_docs,
                ids=ids
            )
            
            logger.debug(f"已添加批次 {i//self.config.batch_size + 1}")
        
        logger.info("文本块添加完成")
    
    def search_similar(self, query: str, 
                      n_results: Optional[int] = None,
                      metadata_filter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        语义相似度搜索
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            metadata_filter: 元数据过滤条件
            
        Returns:
            搜索结果字典
        """
        n_results = n_results or self.config.max_results
        
        # 执行相似度搜索
        results = self.vectorstore.similarity_search_with_score(
            query=query,
            k=n_results,
            filter=metadata_filter
        )
        
        # 格式化结果
        formatted_results = {
            'ids': [],
            'documents': [],
            'distances': [],
            'metadatas': [],
            'similarities': []
        }
        
        for doc, score in results:
            # LangChain返回的是相似度分数，需要转换
            similarity = score
            distance = 1 - score  # 转换为距离
            
            # 过滤低相似度结果
            if similarity >= self.config.similarity_threshold:
                formatted_results['ids'].append(doc.metadata.get('chunk_id', ''))
                formatted_results['documents'].append(doc.page_content)
                formatted_results['distances'].append(distance)
                formatted_results['metadatas'].append(doc.metadata)
                formatted_results['similarities'].append(similarity)
        
        logger.debug(f"相似度搜索完成，返回 {len(formatted_results['ids'])} 个结果")
        return formatted_results
    
    def search_by_text(self, query: str, 
                      n_results: Optional[int] = None,
                      metadata_filter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        文本搜索（使用LangChain的语义搜索）
        
        在LangChain中，文本搜索实际上就是语义搜索，
        因为embedding已经正确配置。
        
        Args:
            query: 查询文本
            n_results: 返回结果数量  
            metadata_filter: 元数据过滤条件
            
        Returns:
            搜索结果字典
        """
        logger.debug("LangChain文本搜索使用语义搜索实现")
        return self.search_similar(query, n_results, metadata_filter)
    
    def hybrid_search(self, query_embedding_or_text, query_text: str = None,
                     n_results: Optional[int] = None,
                     metadata_filter: Optional[Dict[str, Any]] = None,
                     **kwargs) -> Dict[str, Any]:
        """
        混合搜索（在LangChain实现中等同于语义搜索）
        
        为了兼容原始接口，支持两种调用方式：
        1. hybrid_search(query_embedding, query_text, ...)  # 原始方式
        2. hybrid_search(query, ...)  # 简化方式
        
        Args:
            query_embedding_or_text: 查询向量或查询文本
            query_text: 查询文本（当第一个参数是向量时）
            n_results: 返回结果数量
            metadata_filter: 元数据过滤条件
            **kwargs: 其他参数（忽略）
            
        Returns:
            混合搜索结果
        """
        # 处理参数兼容性
        if query_text is not None:
            # 原始调用方式：hybrid_search(query_embedding, query_text, ...)
            query = query_text
        else:
            # 简化调用方式：hybrid_search(query, ...)
            query = query_embedding_or_text
            
        logger.debug("LangChain混合搜索使用语义搜索实现")
        return self.search_similar(query, n_results, metadata_filter)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据库统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 获取集合信息
            collection = self.vectorstore._collection
            total_documents = collection.count()
            
            # 基础统计
            stats = {
                'collection_name': self.config.collection_name,
                'total_documents': total_documents,
                'db_path': self.config.db_path
            }
            
            # 如果有文档，获取示例元数据进行分析
            if total_documents > 0:
                sample_results = collection.get(limit=min(100, total_documents))
                
                # 统计人物分布
                character_counts = {}
                dialogue_chunks = 0
                chapter_chunks = 0
                
                for metadata in sample_results['metadatas']:
                    # 统计人物
                    if 'characters' in metadata and metadata['characters']:
                        # characters是逗号分隔的字符串
                        chars = metadata['characters'].split(',')
                        for char in chars:
                            char = char.strip()
                            if char:
                                character_counts[char] = character_counts.get(char, 0) + 1
                    
                    # 统计对话和章节
                    if metadata.get('has_dialogue'):
                        dialogue_chunks += 1
                    if metadata.get('is_chapter_header'):
                        chapter_chunks += 1
                
                # 添加详细统计
                stats.update({
                    'top_characters': list(character_counts.items())[:5],
                    'dialogue_chunks': dialogue_chunks,
                    'chapter_chunks': chapter_chunks
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                'collection_name': self.config.collection_name,
                'total_documents': 0,
                'db_path': self.config.db_path,
                'error': str(e)
            } 