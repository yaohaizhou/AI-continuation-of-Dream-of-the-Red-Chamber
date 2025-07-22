"""
知识增强模块 - 红楼梦知识驱动续写
基于预处理的文本数据和实体识别结果，为AI续写提供知识支持
"""

from .knowledge_retriever import KnowledgeRetriever
from .entity_retriever import EntityRetriever
from .relationship_retriever import RelationshipRetriever
from .vocabulary_suggester import VocabularySuggester
from .enhanced_prompter import EnhancedPrompter

__all__ = [
    'KnowledgeRetriever',
    'EntityRetriever', 
    'RelationshipRetriever',
    'VocabularySuggester',
    'EnhancedPrompter'
] 