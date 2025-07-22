"""
ChromaDB向量数据库封装
~~~~~~~~~~~~~~~~~~~

高性能向量数据库，支持语义检索和混合查询，
专为红楼梦古典文学文本优化。
"""

import os
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import chromadb
from chromadb.config import Settings
from chromadb.api.models.Collection import Collection
from loguru import logger

from .text_chunker import TextChunk


@dataclass
class VectorDBConfig:
    """向量数据库配置"""
    db_path: str = "data/vectordb"
    collection_name: str = "hongloumeng_chunks"
    distance_metric: str = "cosine"  # cosine, l2, ip
    batch_size: int = 100
    max_results: int = 20
    similarity_threshold: float = 0.7
    enable_metadata_filter: bool = True


class VectorDatabase:
    """
    ChromaDB向量数据库封装类
    
    特性:
    - 高效的向量存储和检索
    - 元数据过滤和混合查询
    - 批量操作和性能优化
    - 持久化存储和备份恢复
    """
    
    def __init__(self, config: Optional[VectorDBConfig] = None):
        self.config = config or VectorDBConfig()
        self._setup_database()
        
        logger.info(f"向量数据库初始化: {self.config.collection_name}")
        logger.info(f"存储路径: {self.config.db_path}")
    
    def _setup_database(self) -> None:
        """初始化数据库连接"""
        # 创建存储目录
        os.makedirs(self.config.db_path, exist_ok=True)
        
        # 初始化ChromaDB客户端
        self.client = chromadb.PersistentClient(
            path=self.config.db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 获取或创建集合
        try:
            self.collection = self.client.get_collection(
                name=self.config.collection_name
            )
            logger.info(f"加载现有集合: {self.config.collection_name}")
        except Exception as e:
            try:
                self.collection = self.client.create_collection(
                    name=self.config.collection_name,
                    metadata={"hnsw:space": self.config.distance_metric}
                )
                logger.info(f"创建新集合: {self.config.collection_name}")
            except Exception as create_error:
                # 如果创建也失败，尝试直接获取（可能已经存在）
                logger.warning(f"创建集合失败: {create_error}, 尝试获取现有集合")
                self.collection = self.client.get_collection(name=self.config.collection_name)
                logger.info(f"成功获取现有集合: {self.config.collection_name}")
    
    def add_chunks(self, chunks: List[TextChunk], embeddings: List[np.ndarray]) -> None:
        """
        添加文本块和对应的向量
        
        Args:
            chunks: 文本块列表
            embeddings: 对应的向量列表
        """
        if len(chunks) != len(embeddings):
            raise ValueError("文本块数量与向量数量不匹配")
        
        logger.info(f"开始添加 {len(chunks)} 个文本块到向量数据库")
        
        # 准备数据
        ids = []
        documents = []
        metadatas = []
        embedding_vectors = []
        
        for chunk, embedding in zip(chunks, embeddings):
            # 生成唯一ID
            chunk_id = chunk.chunk_id or str(uuid.uuid4())
            ids.append(chunk_id)
            
            # 文档文本
            documents.append(chunk.text)
            
            # 元数据
            metadata = chunk.metadata.copy()
            metadata.update({
                'start_pos': chunk.start_pos,
                'end_pos': chunk.end_pos,
                'text_length': len(chunk.text)
            })
            metadatas.append(metadata)
            
            # 向量（转换为列表）
            embedding_vectors.append(embedding.tolist())
        
        # 批量插入
        for i in range(0, len(ids), self.config.batch_size):
            batch_end = min(i + self.config.batch_size, len(ids))
            
            self.collection.add(
                ids=ids[i:batch_end],
                documents=documents[i:batch_end],
                metadatas=metadatas[i:batch_end],
                embeddings=embedding_vectors[i:batch_end]
            )
            
            logger.debug(f"已插入批次 {i//self.config.batch_size + 1}")
        
        logger.info("文本块添加完成")
    
    def search_similar(self, query_embedding: np.ndarray, 
                      n_results: Optional[int] = None,
                      metadata_filter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        基于向量相似度搜索
        
        Args:
            query_embedding: 查询向量
            n_results: 返回结果数量
            metadata_filter: 元数据过滤条件
            
        Returns:
            搜索结果字典
        """
        n_results = n_results or self.config.max_results
        
        # 执行搜索
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=metadata_filter
        )
        
        # 格式化结果
        formatted_results = {
            'ids': results['ids'][0] if results['ids'] else [],
            'documents': results['documents'][0] if results['documents'] else [],
            'distances': results['distances'][0] if results['distances'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else []
        }
        
        # 转换距离为相似度分数
        similarities = []
        for distance in formatted_results['distances']:
            if self.config.distance_metric == "cosine":
                similarity = 1 - distance
            elif self.config.distance_metric == "l2":
                similarity = 1 / (1 + distance)
            else:  # inner product
                similarity = distance
            similarities.append(max(0, similarity))
        
        formatted_results['similarities'] = similarities
        
        # 过滤低相似度结果
        filtered_results = self._filter_by_similarity(formatted_results)
        
        logger.debug(f"相似度搜索完成，返回 {len(filtered_results['ids'])} 个结果")
        return filtered_results
    
    def search_by_text(self, query_text: str, 
                      n_results: Optional[int] = None,
                      metadata_filter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        基于文本内容搜索（关键词匹配）
        
        Args:
            query_text: 查询文本
            n_results: 返回结果数量  
            metadata_filter: 元数据过滤条件
            
        Returns:
            搜索结果字典
        """
        n_results = n_results or self.config.max_results
        
        # 执行文本搜索
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=metadata_filter
        )
        
        # 格式化结果（与相似度搜索保持一致）
        formatted_results = {
            'ids': results['ids'][0] if results['ids'] else [],
            'documents': results['documents'][0] if results['documents'] else [],
            'distances': results['distances'][0] if results['distances'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else [],
            'similarities': [1.0] * len(results['ids'][0]) if results['ids'] else []  # 文本匹配默认高相似度
        }
        
        logger.debug(f"文本搜索完成，返回 {len(formatted_results['ids'])} 个结果")
        return formatted_results
    
    def hybrid_search(self, query_embedding: np.ndarray, query_text: str,
                     n_results: Optional[int] = None,
                     semantic_weight: float = 0.7,
                     text_weight: float = 0.3,
                     metadata_filter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        混合检索：语义相似度 + 文本匹配
        
        Args:
            query_embedding: 查询向量
            query_text: 查询文本
            n_results: 返回结果数量
            semantic_weight: 语义权重
            text_weight: 文本权重
            metadata_filter: 元数据过滤条件
            
        Returns:
            混合搜索结果
        """
        n_results = n_results or self.config.max_results
        
        # 语义搜索
        semantic_results = self.search_similar(
            query_embedding, 
            n_results=n_results * 2,  # 获取更多候选
            metadata_filter=metadata_filter
        )
        
        # 文本搜索
        text_results = self.search_by_text(
            query_text,
            n_results=n_results * 2,
            metadata_filter=metadata_filter
        )
        
        # 结果融合
        merged_results = self._merge_search_results(
            semantic_results, text_results,
            semantic_weight, text_weight
        )
        
        # 排序并截取
        final_results = self._rank_and_limit_results(merged_results, n_results)
        
        logger.debug(f"混合搜索完成，返回 {len(final_results['ids'])} 个结果")
        return final_results
    
    def _filter_by_similarity(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """根据相似度阈值过滤结果"""
        filtered_indices = [
            i for i, sim in enumerate(results['similarities'])
            if sim >= self.config.similarity_threshold
        ]
        
        return {
            'ids': [results['ids'][i] for i in filtered_indices],
            'documents': [results['documents'][i] for i in filtered_indices],
            'distances': [results['distances'][i] for i in filtered_indices],
            'metadatas': [results['metadatas'][i] for i in filtered_indices],
            'similarities': [results['similarities'][i] for i in filtered_indices]
        }
    
    def _merge_search_results(self, semantic_results: Dict[str, Any], 
                            text_results: Dict[str, Any],
                            semantic_weight: float, text_weight: float) -> Dict[str, Any]:
        """合并语义搜索和文本搜索结果"""
        # 创建结果字典（用ID作为键）
        merged = {}
        
        # 添加语义搜索结果
        for i, doc_id in enumerate(semantic_results['ids']):
            score = semantic_results['similarities'][i] * semantic_weight
            merged[doc_id] = {
                'id': doc_id,
                'document': semantic_results['documents'][i],
                'metadata': semantic_results['metadatas'][i],
                'semantic_score': semantic_results['similarities'][i],
                'text_score': 0.0,
                'combined_score': score
            }
        
        # 添加文本搜索结果
        for i, doc_id in enumerate(text_results['ids']):
            text_score = text_results['similarities'][i] * text_weight
            
            if doc_id in merged:
                # 更新已存在的结果
                merged[doc_id]['text_score'] = text_results['similarities'][i]
                merged[doc_id]['combined_score'] += text_score
            else:
                # 添加新结果
                merged[doc_id] = {
                    'id': doc_id,
                    'document': text_results['documents'][i],
                    'metadata': text_results['metadatas'][i],
                    'semantic_score': 0.0,
                    'text_score': text_results['similarities'][i],
                    'combined_score': text_score
                }
        
        return merged
    
    def _rank_and_limit_results(self, merged_results: Dict[str, Any], 
                              n_results: int) -> Dict[str, Any]:
        """排序和限制结果数量"""
        # 按综合分数排序
        sorted_results = sorted(
            merged_results.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )[:n_results]
        
        # 格式化为标准格式
        return {
            'ids': [r['id'] for r in sorted_results],
            'documents': [r['document'] for r in sorted_results],
            'metadatas': [r['metadata'] for r in sorted_results],
            'similarities': [r['combined_score'] for r in sorted_results],
            'semantic_scores': [r['semantic_score'] for r in sorted_results],
            'text_scores': [r['text_score'] for r in sorted_results]
        }
    
    def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取文档"""
        try:
            results = self.collection.get(ids=[doc_id])
            if results['ids']:
                return {
                    'id': results['ids'][0],
                    'document': results['documents'][0],
                    'metadata': results['metadatas'][0]
                }
        except Exception as e:
            logger.error(f"获取文档失败: {e}")
        
        return None
    
    def delete_by_id(self, doc_id: str) -> bool:
        """根据ID删除文档"""
        try:
            self.collection.delete(ids=[doc_id])
            logger.info(f"删除文档: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    def count(self) -> int:
        """获取文档总数"""
        return self.collection.count()
    
    def list_collections(self) -> List[str]:
        """列出所有集合"""
        collections = self.client.list_collections()
        return [col.name for col in collections]
    
    def reset_collection(self) -> None:
        """重置集合（删除所有数据）"""
        logger.warning("重置集合，删除所有数据")
        self.client.delete_collection(self.config.collection_name)
        self.collection = self.client.create_collection(
            name=self.config.collection_name,
            metadata={"hnsw:space": self.config.distance_metric}
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        total_docs = self.count()
        
        stats = {
            'collection_name': self.config.collection_name,
            'total_documents': total_docs,
            'distance_metric': self.config.distance_metric,
            'db_path': self.config.db_path
        }
        
        if total_docs > 0:
            # 获取一些样本数据的元数据
            sample_results = self.collection.peek(limit=min(100, total_docs))
            
            if sample_results['metadatas']:
                # 分析元数据
                character_counts = {}
                dialogue_count = 0
                chapter_count = 0
                
                for metadata in sample_results['metadatas']:
                    # 统计人物
                    if 'characters' in metadata and metadata['characters']:
                        # 现在characters是逗号分隔的字符串
                        chars = metadata['characters'].split(',')
                        for char in chars:
                            char = char.strip()
                            if char:
                                character_counts[char] = character_counts.get(char, 0) + 1
                    
                    # 统计对话和章节
                    if metadata.get('has_dialogue'):
                        dialogue_count += 1
                    if metadata.get('is_chapter_header'):
                        chapter_count += 1
                
                stats.update({
                    'top_characters': sorted(character_counts.items(), 
                                           key=lambda x: x[1], reverse=True)[:10],
                    'dialogue_chunks': dialogue_count,
                    'chapter_chunks': chapter_count
                })
        
        return stats
    
    def export_data(self, output_path: str) -> None:
        """导出数据到JSON文件"""
        logger.info(f"导出数据到: {output_path}")
        
        all_data = self.collection.get()
        
        export_data = {
            'collection_name': self.config.collection_name,
            'config': {
                'distance_metric': self.config.distance_metric,
                'similarity_threshold': self.config.similarity_threshold
            },
            'data': {
                'ids': all_data['ids'],
                'documents': all_data['documents'],
                'metadatas': all_data['metadatas']
                # 注意：embeddings 很大，这里不导出
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info("数据导出完成")


# 便捷函数
def create_vector_db(db_path: str = "data/vectordb", 
                    collection_name: str = "hongloumeng_chunks",
                    **config_kwargs) -> VectorDatabase:
    """
    创建向量数据库的便捷函数
    
    Args:
        db_path: 数据库路径
        collection_name: 集合名称
        **config_kwargs: 其他配置参数
        
    Returns:
        VectorDatabase实例
    """
    config = VectorDBConfig(
        db_path=db_path,
        collection_name=collection_name,
        **config_kwargs
    )
    return VectorDatabase(config) 