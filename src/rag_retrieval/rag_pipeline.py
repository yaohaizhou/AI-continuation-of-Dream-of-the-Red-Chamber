"""
RAG智能检索管道
~~~~~~~~~~~~~~~

整合文本分块、向量化、存储和检索的完整RAG系统，
专为红楼梦古典文学文本优化。
"""

import os
import json
import time
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path

from loguru import logger
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.console import Console

from .qwen_embeddings import QwenEmbeddings, EmbeddingConfig
from .text_chunker import TextChunker, ChunkConfig, ChunkStrategy, TextChunk
from .vector_database import VectorDatabase, VectorDBConfig


@dataclass
class RAGConfig:
    """RAG管道配置"""
    # 向量化配置
    embedding_config: EmbeddingConfig = None
    
    # 分块配置  
    chunk_config: ChunkConfig = None
    
    # 向量数据库配置
    vectordb_config: VectorDBConfig = None
    
    # 管道配置
    batch_process_size: int = 50       # 批量处理大小
    auto_save_interval: int = 100      # 自动保存间隔
    enable_progress: bool = True       # 启用进度显示
    
    def __post_init__(self):
        """初始化默认配置"""
        if self.embedding_config is None:
            self.embedding_config = EmbeddingConfig()
        
        if self.chunk_config is None:
            self.chunk_config = ChunkConfig()
        
        if self.vectordb_config is None:
            self.vectordb_config = VectorDBConfig()


class RAGPipeline:
    """
    完整的RAG检索管道
    
    功能特性:
    - 一站式文档处理和向量化
    - 智能文本分块和元数据提取
    - 高效的向量存储和检索
    - 多种检索策略支持
    - 进度显示和错误恢复
    """
    
    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or RAGConfig()
        self.console = Console()
        
        # 初始化组件
        self._init_components()
        
        logger.info("RAG检索管道初始化完成")
        
    def _init_components(self) -> None:
        """初始化核心组件"""
        # 向量化模型
        self.embeddings = QwenEmbeddings(self.config.embedding_config)
        
        # 文本分块器
        self.chunker = TextChunker(self.config.chunk_config)
        
        # 向量数据库
        self.vectordb = VectorDatabase(self.config.vectordb_config)
        
        logger.info("RAG核心组件初始化完成")
    
    def process_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        处理文档：分块 → 向量化 → 存储
        
        Args:
            documents: 文档列表，每个文档需包含 'text' 和 'source_id'
            
        Returns:
            处理结果统计
        """
        logger.info(f"开始处理 {len(documents)} 个文档")
        
        total_chunks = 0
        total_embeddings = 0
        processing_stats = {
            'documents_processed': 0,
            'chunks_created': 0,
            'embeddings_generated': 0,
            'chunks_stored': 0,
            'processing_time': 0,
            'errors': []
        }
        
        start_time = time.time()
        
        if self.config.enable_progress:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                "[progress.percentage]{task.percentage:>3.0f}%",
                TimeElapsedColumn(),
                console=self.console
            )
            
            with progress:
                task = progress.add_task("处理文档", total=len(documents))
                
                for doc in documents:
                    try:
                        result = self._process_single_document(doc)
                        total_chunks += result['chunks_created']
                        total_embeddings += result['embeddings_generated']
                        processing_stats['documents_processed'] += 1
                        
                        progress.advance(task)
                        
                    except Exception as e:
                        error_msg = f"处理文档失败 {doc.get('source_id', 'unknown')}: {str(e)}"
                        logger.error(error_msg)
                        processing_stats['errors'].append(error_msg)
        else:
            # 无进度显示的处理
            for doc in documents:
                try:
                    result = self._process_single_document(doc)
                    total_chunks += result['chunks_created']
                    total_embeddings += result['embeddings_generated']
                    processing_stats['documents_processed'] += 1
                    
                except Exception as e:
                    error_msg = f"处理文档失败 {doc.get('source_id', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    processing_stats['errors'].append(error_msg)
        
        processing_stats.update({
            'chunks_created': total_chunks,
            'embeddings_generated': total_embeddings,
            'chunks_stored': total_chunks,  # 假设全部存储成功
            'processing_time': time.time() - start_time
        })
        
        logger.info(f"文档处理完成: {processing_stats}")
        return processing_stats
    
    def _process_single_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个文档"""
        source_id = document.get('source_id', f"doc_{time.time()}")
        text = document['text']
        
        # 1. 文本分块
        chunks = self.chunker.chunk(text, source_id=source_id)
        
        if not chunks:
            logger.warning(f"文档 {source_id} 未产生任何文本块")
            return {'chunks_created': 0, 'embeddings_generated': 0}
        
        # 2. 批量向量化
        texts = [chunk.text for chunk in chunks]
        embeddings = self.embeddings.embed_batch(texts)
        
        # 3. 存储到向量数据库
        self.vectordb.add_chunks(chunks, embeddings)
        
        logger.debug(f"文档 {source_id} 处理完成: {len(chunks)} 个块")
        
        return {
            'chunks_created': len(chunks),
            'embeddings_generated': len(embeddings)
        }
    
    def process_text_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        处理文本文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            处理结果统计
        """
        documents = []
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                documents.append({
                    'text': text,
                    'source_id': Path(file_path).stem
                })
                
            except Exception as e:
                logger.error(f"读取文件失败 {file_path}: {e}")
        
        return self.process_documents(documents)
    
    def process_chapter_files(self, chapters_dir: str = "data/processed/chapters") -> Dict[str, Any]:
        """
        处理章节文件目录
        
        Args:
            chapters_dir: 章节文件目录
            
        Returns:
            处理结果统计
        """
        chapters_path = Path(chapters_dir)
        
        if not chapters_path.exists():
            raise FileNotFoundError(f"章节目录不存在: {chapters_dir}")
        
        # 获取所有markdown文件
        chapter_files = list(chapters_path.glob("*.md"))
        chapter_files.sort()  # 按文件名排序
        
        logger.info(f"发现 {len(chapter_files)} 个章节文件")
        
        return self.process_text_files([str(f) for f in chapter_files])
    
    def search(self, query: str, 
              search_type: str = "hybrid",
              n_results: int = 5,
              character_filter: Optional[List[str]] = None,
              **kwargs) -> Dict[str, Any]:
        """
        智能检索
        
        Args:
            query: 查询文本
            search_type: 检索类型 ("semantic", "text", "hybrid")
            n_results: 返回结果数量
            character_filter: 人物过滤
            **kwargs: 其他参数
            
        Returns:
            检索结果
        """
        # 构建元数据过滤器
        metadata_filter = None
        if character_filter:
            # ChromaDB的元数据过滤语法
            metadata_filter = {
                "characters": {"$in": character_filter}
            }
        
        # 根据检索类型执行搜索
        if search_type == "semantic":
            # 语义检索
            query_embedding = self.embeddings.embed_single(query)
            results = self.vectordb.search_similar(
                query_embedding,
                n_results=n_results,
                metadata_filter=metadata_filter
            )
            
        elif search_type == "text":
            # 文本检索
            results = self.vectordb.search_by_text(
                query,
                n_results=n_results,
                metadata_filter=metadata_filter
            )
            
        else:  # hybrid
            # 混合检索
            query_embedding = self.embeddings.embed_single(query)
            results = self.vectordb.hybrid_search(
                query_embedding,
                query,
                n_results=n_results,
                semantic_weight=kwargs.get('semantic_weight', 0.7),
                text_weight=kwargs.get('text_weight', 0.3),
                metadata_filter=metadata_filter
            )
        
        # 增强结果信息
        enhanced_results = self._enhance_search_results(results, query)
        
        logger.info(f"检索完成: {search_type}, 返回 {len(enhanced_results['documents'])} 个结果")
        return enhanced_results
    
    def _enhance_search_results(self, results: Dict[str, Any], query: str) -> Dict[str, Any]:
        """增强检索结果"""
        enhanced = results.copy()
        
        # 添加查询信息
        enhanced['query'] = query
        enhanced['search_time'] = time.time()
        
        # 为每个结果添加摘要
        summaries = []
        for i, doc in enumerate(results['documents']):
            # 简单的文本摘要（前100个字符）
            summary = doc[:100] + "..." if len(doc) > 100 else doc
            summaries.append(summary)
        
        enhanced['summaries'] = summaries
        
        return enhanced
    
    def build_knowledge_base(self, reset_existing: bool = False) -> Dict[str, Any]:
        """
        构建完整的知识库
        
        Args:
            reset_existing: 是否重置现有数据
            
        Returns:
            构建结果统计
        """
        logger.info("开始构建红楼梦知识库")
        
        if reset_existing:
            logger.warning("重置现有向量数据库")
            self.vectordb.reset_collection()
        
        # 处理所有章节文件
        stats = self.process_chapter_files()
        
        # 获取数据库统计
        db_stats = self.vectordb.get_statistics()
        
        # 合并统计信息
        build_stats = {
            **stats,
            'database_stats': db_stats,
            'build_timestamp': time.time()
        }
        
        logger.info("知识库构建完成")
        return build_stats
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'pipeline_config': {
                'embedding_model': self.config.embedding_config.model_name,
                'chunk_strategy': self.config.chunk_config.strategy.value,
                'chunk_size': self.config.chunk_config.chunk_size,
                'db_path': self.config.vectordb_config.db_path
            },
            'database_stats': self.vectordb.get_statistics(),
            'embedding_stats': self.embeddings.get_config(),
            'chunker_stats': {
                'strategy': self.config.chunk_config.strategy.value,
                'chunk_size': self.config.chunk_config.chunk_size,
                'overlap': self.config.chunk_config.chunk_overlap
            }
        }
    
    def export_knowledge_base(self, output_dir: str) -> None:
        """导出知识库"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 导出向量数据库
        db_export_path = output_path / "vectordb_export.json"
        self.vectordb.export_data(str(db_export_path))
        
        # 导出系统配置
        config_path = output_path / "system_config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.get_system_status(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"知识库已导出到: {output_dir}")
    
    def quick_test(self, query: str = "宝玉和黛玉的关系") -> None:
        """快速测试RAG系统"""
        self.console.print(f"\n[bold green]RAG系统快速测试[/bold green]")
        self.console.print(f"查询: {query}")
        
        # 检查数据库状态
        db_stats = self.vectordb.get_statistics()
        self.console.print(f"数据库状态: {db_stats['total_documents']} 个文档")
        
        if db_stats['total_documents'] == 0:
            self.console.print("[red]警告: 数据库为空，请先构建知识库[/red]")
            return
        
        # 执行三种检索
        search_types = ["semantic", "text", "hybrid"]
        
        for search_type in search_types:
            self.console.print(f"\n[bold blue]{search_type.upper()} 检索结果:[/bold blue]")
            
            try:
                results = self.search(query, search_type=search_type, n_results=3)
                
                for i, (doc, sim) in enumerate(zip(results['documents'], results['similarities'])):
                    self.console.print(f"{i+1}. 相似度: {sim:.3f}")
                    self.console.print(f"   内容: {doc[:100]}...")
                    if results['metadatas'][i].get('characters'):
                        self.console.print(f"   人物: {results['metadatas'][i]['characters']}")
                    self.console.print()
                    
            except Exception as e:
                self.console.print(f"[red]检索失败: {e}[/red]")


# 便捷函数
def create_rag_pipeline(api_key: Optional[str] = None,
                       db_path: str = "data/vectordb",
                       chunk_strategy: str = "semantic",
                       **config_kwargs) -> RAGPipeline:
    """
    创建RAG管道的便捷函数
    
    Args:
        api_key: DashScope API密钥
        db_path: 向量数据库路径
        chunk_strategy: 分块策略
        **config_kwargs: 其他配置参数
        
    Returns:
        RAGPipeline实例
    """
    if api_key:
        os.environ['DASHSCOPE_API_KEY'] = api_key
    
    # 构建配置
    config = RAGConfig(
        embedding_config=EmbeddingConfig(**config_kwargs.get('embedding_config', {})),
        chunk_config=ChunkConfig(
            strategy=ChunkStrategy(chunk_strategy),
            **config_kwargs.get('chunk_config', {})
        ),
        vectordb_config=VectorDBConfig(
            db_path=db_path,
            **config_kwargs.get('vectordb_config', {})
        )
    )
    
    return RAGPipeline(config) 