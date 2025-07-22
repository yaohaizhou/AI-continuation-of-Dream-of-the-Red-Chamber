"""
RAG智能检索系统
~~~~~~~~~~~~~~

基于向量相似度的语义检索系统，支持混合检索策略，
专为红楼梦古典文学文本优化。

核心组件:
- QwenEmbeddings: Qwen3 text-embedding-v4模型封装
- TextChunker: 智能文本分块器
- VectorDatabase: ChromaDB向量数据库
- SemanticSearcher: 语义检索引擎
- HybridRetriever: 混合检索器
- RAGPipeline: 完整RAG管道
"""

from .qwen_embeddings import QwenEmbeddings
from .text_chunker import TextChunker, ChunkStrategy
from .vector_database import VectorDatabase
from .semantic_search import SemanticSearcher
from .hybrid_retriever import HybridRetriever
from .rag_pipeline import RAGPipeline, create_rag_pipeline

__version__ = "1.0.0"
__author__ = "AI-HongLouMeng Team"

__all__ = [
    'QwenEmbeddings',
    'TextChunker',
    'ChunkStrategy', 
    'VectorDatabase',
    'SemanticSearcher',
    'HybridRetriever',
    'RAGPipeline',
    'create_rag_pipeline'
] 