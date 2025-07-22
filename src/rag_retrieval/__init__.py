"""
RAG智能检索系统
~~~~~~~~~~~~~~

基于LangChain Chroma的红楼梦智能检索系统，提供：
- QwenEmbeddings: Qwen3文本向量化
- LangChainQwenEmbeddings: LangChain兼容的Qwen embedding
- TextChunker: 智能文本分块器
- LangChainVectorDatabase: LangChain Chroma向量数据库
- RAGPipeline: 完整的RAG检索管道
"""

from .qwen_embeddings import QwenEmbeddings
from .langchain_qwen_embedding import LangChainQwenEmbeddings
from .text_chunker import TextChunker, ChunkStrategy
from .langchain_vector_database import LangChainVectorDatabase, LangChainVectorDBConfig
from .rag_pipeline import RAGPipeline, create_rag_pipeline

__version__ = "1.0.0"
__author__ = "AI-HongLouMeng Team"

__all__ = [
    'QwenEmbeddings',
    'LangChainQwenEmbeddings',
    'TextChunker',
    'ChunkStrategy', 
    'LangChainVectorDatabase',
    'LangChainVectorDBConfig',
    'RAGPipeline',
    'create_rag_pipeline'
] 