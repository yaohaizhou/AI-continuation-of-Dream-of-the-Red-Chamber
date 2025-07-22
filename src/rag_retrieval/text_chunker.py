"""
智能文本分块器
~~~~~~~~~~~~~

为RAG系统提供多种文本分块策略，
专为红楼梦古典文学文本优化。
"""

import re
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from loguru import logger


class ChunkStrategy(Enum):
    """分块策略枚举"""
    FIXED_SIZE = "fixed_size"           # 固定大小分块
    SEMANTIC = "semantic"               # 语义分块
    PARAGRAPH = "paragraph"             # 段落分块  
    SENTENCE = "sentence"               # 句子分块
    CHAPTER = "chapter"                 # 章节分块
    DIALOGUE = "dialogue"               # 对话分块
    HYBRID = "hybrid"                   # 混合策略


@dataclass
class ChunkConfig:
    """分块配置"""
    strategy: ChunkStrategy = ChunkStrategy.SEMANTIC
    chunk_size: int = 512              # 目标块大小（字符数）
    chunk_overlap: int = 50             # 重叠字符数
    min_chunk_size: int = 100           # 最小块大小
    max_chunk_size: int = 1024          # 最大块大小
    preserve_structure: bool = True     # 保持结构完整性
    add_metadata: bool = True           # 添加元数据


@dataclass 
class TextChunk:
    """文本块数据结构"""
    text: str                          # 文本内容
    start_pos: int                     # 起始位置
    end_pos: int                       # 结束位置
    chunk_id: str                      # 块ID
    metadata: Dict[str, Any]           # 元数据


class TextChunker:
    """
    智能文本分块器
    
    支持多种分块策略，专为古典文学文本优化。
    特别针对红楼梦的文本结构进行了优化。
    """
    
    def __init__(self, config: Optional[ChunkConfig] = None):
        self.config = config or ChunkConfig()
        
        # 红楼梦特定的文本模式
        self._init_patterns()
        
        logger.info(f"文本分块器初始化: {self.config.strategy.value}")
        logger.info(f"目标块大小: {self.config.chunk_size}, 重叠: {self.config.chunk_overlap}")
    
    def _init_patterns(self) -> None:
        """初始化文本模式"""
        # 章节标题模式
        self.chapter_pattern = re.compile(r'^第[一二三四五六七八九十百千\d]+回\s+.*')
        
        # 段落分隔模式
        self.paragraph_pattern = re.compile(r'\n\s*\n+')
        
        # 句子结束模式
        self.sentence_pattern = re.compile(r'[。！？；]\s*')
        
        # 对话模式 
        self.dialogue_pattern = re.compile(r'["""][^"""]*["""]')
        
        # 人名模式（红楼梦常见人名）
        self.name_pattern = re.compile(r'(宝玉|黛玉|宝钗|凤姐|湘云|迎春|探春|惜春|李纨|妙玉|晴雯|袭人)')
    
    def chunk(self, text: str, source_id: Optional[str] = None) -> List[TextChunk]:
        """
        主分块方法
        
        Args:
            text: 输入文本
            source_id: 来源标识符
            
        Returns:
            文本块列表
        """
        if not text.strip():
            return []
        
        logger.info(f"开始分块: {len(text)} 字符，策略: {self.config.strategy.value}")
        
        # 根据策略选择分块方法
        if self.config.strategy == ChunkStrategy.FIXED_SIZE:
            chunks = self._chunk_fixed_size(text)
        elif self.config.strategy == ChunkStrategy.SEMANTIC:
            chunks = self._chunk_semantic(text)
        elif self.config.strategy == ChunkStrategy.PARAGRAPH:
            chunks = self._chunk_paragraph(text)
        elif self.config.strategy == ChunkStrategy.SENTENCE:
            chunks = self._chunk_sentence(text)
        elif self.config.strategy == ChunkStrategy.CHAPTER:
            chunks = self._chunk_chapter(text)
        elif self.config.strategy == ChunkStrategy.DIALOGUE:
            chunks = self._chunk_dialogue(text)
        else:  # HYBRID
            chunks = self._chunk_hybrid(text)
        
        # 添加元数据
        if self.config.add_metadata:
            chunks = self._add_metadata(chunks, text, source_id)
        
        logger.info(f"分块完成: {len(chunks)} 个块")
        return chunks
    
    def _chunk_fixed_size(self, text: str) -> List[TextChunk]:
        """固定大小分块"""
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = min(start + self.config.chunk_size, len(text))
            
            # 处理重叠
            if start > 0:
                overlap_start = max(0, start - self.config.chunk_overlap)
                chunk_text = text[overlap_start:end]
                actual_start = overlap_start
            else:
                chunk_text = text[start:end]
                actual_start = start
            
            chunks.append(TextChunk(
                text=chunk_text,
                start_pos=actual_start,
                end_pos=end,
                chunk_id=f"chunk_{chunk_id}",
                metadata={}
            ))
            
            start = end
            chunk_id += 1
        
        return chunks
    
    def _chunk_semantic(self, text: str) -> List[TextChunk]:
        """语义分块 - 保持语义完整性"""
        # 首先按段落分割
        paragraphs = self.paragraph_pattern.split(text)
        chunks = []
        current_chunk = ""
        current_start = 0
        chunk_id = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 检查添加当前段落是否会超过限制
            if len(current_chunk) + len(para) + 2 <= self.config.max_chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                # 保存当前块
                if current_chunk:
                    chunks.append(TextChunk(
                        text=current_chunk,
                        start_pos=current_start,
                        end_pos=current_start + len(current_chunk),
                        chunk_id=f"semantic_{chunk_id}",
                        metadata={}
                    ))
                    chunk_id += 1
                
                # 开始新块
                current_chunk = para
                current_start = text.find(para, current_start)
        
        # 处理最后一个块
        if current_chunk:
            chunks.append(TextChunk(
                text=current_chunk,
                start_pos=current_start,
                end_pos=current_start + len(current_chunk),
                chunk_id=f"semantic_{chunk_id}",
                metadata={}
            ))
        
        return chunks
    
    def _chunk_paragraph(self, text: str) -> List[TextChunk]:
        """段落分块"""
        paragraphs = self.paragraph_pattern.split(text)
        chunks = []
        pos = 0
        
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                continue
            
            # 找到段落在原文中的位置
            start_pos = text.find(para, pos)
            end_pos = start_pos + len(para)
            
            chunks.append(TextChunk(
                text=para,
                start_pos=start_pos,
                end_pos=end_pos,
                chunk_id=f"para_{i}",
                metadata={}
            ))
            
            pos = end_pos
        
        return chunks
    
    def _chunk_sentence(self, text: str) -> List[TextChunk]:
        """句子分块"""
        sentences = self.sentence_pattern.split(text)
        chunks = []
        pos = 0
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 找到句子在原文中的位置
            start_pos = text.find(sentence, pos)
            end_pos = start_pos + len(sentence)
            
            chunks.append(TextChunk(
                text=sentence,
                start_pos=start_pos,
                end_pos=end_pos,
                chunk_id=f"sent_{i}",
                metadata={}
            ))
            
            pos = end_pos
        
        return chunks
    
    def _chunk_chapter(self, text: str) -> List[TextChunk]:
        """章节分块"""
        lines = text.split('\n')
        chunks = []
        current_chapter = []
        chapter_id = 0
        start_pos = 0
        
        for line in lines:
            if self.chapter_pattern.match(line.strip()):
                # 保存上一章
                if current_chapter:
                    chapter_text = '\n'.join(current_chapter)
                    chunks.append(TextChunk(
                        text=chapter_text,
                        start_pos=start_pos,
                        end_pos=start_pos + len(chapter_text),
                        chunk_id=f"chapter_{chapter_id}",
                        metadata={}
                    ))
                    chapter_id += 1
                
                # 开始新章
                current_chapter = [line]
                start_pos = text.find(line)
            else:
                if current_chapter:  # 如果已经开始一章
                    current_chapter.append(line)
        
        # 处理最后一章
        if current_chapter:
            chapter_text = '\n'.join(current_chapter)
            chunks.append(TextChunk(
                text=chapter_text,
                start_pos=start_pos,
                end_pos=start_pos + len(chapter_text),
                chunk_id=f"chapter_{chapter_id}",
                metadata={}
            ))
        
        return chunks
    
    def _chunk_dialogue(self, text: str) -> List[TextChunk]:
        """对话分块 - 提取对话内容"""
        dialogues = self.dialogue_pattern.findall(text)
        chunks = []
        
        for i, dialogue in enumerate(dialogues):
            start_pos = text.find(dialogue)
            end_pos = start_pos + len(dialogue)
            
            chunks.append(TextChunk(
                text=dialogue,
                start_pos=start_pos,
                end_pos=end_pos,
                chunk_id=f"dialogue_{i}",
                metadata={}
            ))
        
        return chunks
    
    def _chunk_hybrid(self, text: str) -> List[TextChunk]:
        """混合策略 - 综合多种方法"""
        # 先按章节分割
        chapter_chunks = self._chunk_chapter(text)
        
        # 如果没有章节标记，使用语义分块
        if not chapter_chunks:
            return self._chunk_semantic(text)
        
        # 对每个章节进行进一步分块
        final_chunks = []
        for chapter_chunk in chapter_chunks:
            if len(chapter_chunk.text) > self.config.max_chunk_size:
                # 章节过长，进行语义分块
                sub_config = ChunkConfig(
                    strategy=ChunkStrategy.SEMANTIC,
                    chunk_size=self.config.chunk_size,
                    chunk_overlap=self.config.chunk_overlap
                )
                sub_chunker = TextChunker(sub_config)
                sub_chunks = sub_chunker._chunk_semantic(chapter_chunk.text)
                
                # 更新子块的位置和ID
                for j, sub_chunk in enumerate(sub_chunks):
                    sub_chunk.start_pos += chapter_chunk.start_pos
                    sub_chunk.end_pos += chapter_chunk.start_pos
                    sub_chunk.chunk_id = f"{chapter_chunk.chunk_id}_sub_{j}"
                
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(chapter_chunk)
        
        return final_chunks
    
    def _add_metadata(self, chunks: List[TextChunk], original_text: str, 
                     source_id: Optional[str] = None) -> List[TextChunk]:
        """为文本块添加元数据"""
        for chunk in chunks:
            # 基础元数据
            chunk.metadata.update({
                'source_id': source_id,
                'chunk_length': len(chunk.text),
                'chunk_strategy': self.config.strategy.value,
                'position_ratio': chunk.start_pos / len(original_text) if original_text else 0
            })
            
            # 文学元数据
            chunk.metadata.update(self._extract_literary_metadata(chunk.text))
        
        return chunks
    
    def _extract_literary_metadata(self, text: str) -> Dict[str, Any]:
        """提取文学元数据"""
        metadata = {}
        
        # 人物检测
        names = self.name_pattern.findall(text)
        if names:
            metadata['characters'] = list(set(names))
            metadata['character_count'] = len(set(names))
        
        # 对话检测
        dialogues = self.dialogue_pattern.findall(text)
        if dialogues:
            metadata['has_dialogue'] = True
            metadata['dialogue_count'] = len(dialogues)
        else:
            metadata['has_dialogue'] = False
            metadata['dialogue_count'] = 0
        
        # 章节检测
        if self.chapter_pattern.search(text):
            metadata['is_chapter_header'] = True
            chapter_match = self.chapter_pattern.search(text)
            if chapter_match:
                metadata['chapter_title'] = chapter_match.group().strip()
        else:
            metadata['is_chapter_header'] = False
        
        # 文本统计
        metadata.update({
            'sentence_count': len(self.sentence_pattern.split(text)),
            'paragraph_count': len(self.paragraph_pattern.split(text)),
            'contains_classical_words': bool(re.search(r'[之乎者也矣哉]', text))
        })
        
        return metadata
    
    def get_chunk_statistics(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """获取分块统计信息"""
        if not chunks:
            return {}
        
        lengths = [len(chunk.text) for chunk in chunks]
        
        stats = {
            'total_chunks': len(chunks),
            'avg_chunk_length': sum(lengths) / len(lengths),
            'min_chunk_length': min(lengths),
            'max_chunk_length': max(lengths),
            'total_characters': sum(lengths),
            'strategy': self.config.strategy.value
        }
        
        # 文学统计
        character_chunks = sum(1 for chunk in chunks if chunk.metadata.get('characters'))
        dialogue_chunks = sum(1 for chunk in chunks if chunk.metadata.get('has_dialogue'))
        chapter_chunks = sum(1 for chunk in chunks if chunk.metadata.get('is_chapter_header'))
        
        stats.update({
            'chunks_with_characters': character_chunks,
            'chunks_with_dialogue': dialogue_chunks,
            'chapter_header_chunks': chapter_chunks
        })
        
        return stats


def create_chunker(strategy: str = "semantic", **config_kwargs) -> TextChunker:
    """
    创建文本分块器的便捷函数
    
    Args:
        strategy: 分块策略
        **config_kwargs: 其他配置参数
        
    Returns:
        TextChunker实例
    """
    config = ChunkConfig(
        strategy=ChunkStrategy(strategy),
        **config_kwargs
    )
    return TextChunker(config) 