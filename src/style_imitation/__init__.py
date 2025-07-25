"""
古典文风仿照引擎

这个模块专门用于将现代化的AI生成文本转换为符合红楼梦原著风格的古典文学文本。

主要功能:
- 古典文风分析: 分析红楼梦原著的语言特征
- 文体风格库: 提供分情景的写作模板
- 智能转换器: 将现代文本转换为古典风格
- 相似度评估: 量化评估文风匹配度
- 实时优化: 根据评估结果动态调整
"""

from .classical_style_analyzer import ClassicalStyleAnalyzer, StyleFeatures, VocabularyFeatures, SentenceFeatures, RhetoricalFeatures, AddressingFeatures
from .style_template_library import StyleTemplateLibrary, DialogueTemplate, NarrativeTemplate, SceneTemplate, RhetoricalTemplate
from .intelligent_style_converter import IntelligentStyleConverter, ConversionResult, ConversionConfig
from .style_similarity_evaluator import StyleSimilarityEvaluator, SimilarityScores, EvaluationResult, BatchEvaluationResult
from .realtime_style_optimizer import RealtimeStyleOptimizer, OptimizationConfig, OptimizationSession, BatchOptimizationResult, OptimizationResult

__all__ = [
    # 第一阶段：古典文风分析器
    'ClassicalStyleAnalyzer',
    'StyleFeatures',
    'VocabularyFeatures', 
    'SentenceFeatures',
    'RhetoricalFeatures',
    'AddressingFeatures',
    
    # 第二阶段：文体风格库
    'StyleTemplateLibrary',
    'DialogueTemplate',
    'NarrativeTemplate', 
    'SceneTemplate',
    'RhetoricalTemplate',
    
    # 第三阶段：智能文风转换器 ✅ 已实现
    'IntelligentStyleConverter',
    'ConversionResult',
    'ConversionConfig',
    
    # 第四阶段：风格相似度评估器 ✅ 已实现
    'StyleSimilarityEvaluator',
    'SimilarityScores',
    'EvaluationResult',
    'BatchEvaluationResult',
    
    # 第五阶段：实时文风优化器 ✅ 已实现
    'RealtimeStyleOptimizer',
    'OptimizationConfig',
    'OptimizationSession',
    'BatchOptimizationResult',
    'OptimizationResult'
]

def create_classical_analyzer(hongloumeng_path: str = "data/raw/hongloumeng_80.md"):
    """创建古典文风分析器实例"""
    return ClassicalStyleAnalyzer(hongloumeng_path)

def create_style_template_library(style_data_path: str = "data/processed/style_templates.json"):
    """创建文体风格库实例"""
    return StyleTemplateLibrary(style_data_path)

def create_intelligent_converter(analyzer: ClassicalStyleAnalyzer = None, template_library: StyleTemplateLibrary = None):
    """创建智能文风转换器实例"""
    return IntelligentStyleConverter(analyzer, template_library)

def create_style_similarity_evaluator(analyzer: ClassicalStyleAnalyzer = None):
    """创建风格相似度评估器实例"""
    return StyleSimilarityEvaluator(analyzer)

def create_realtime_style_optimizer(converter: IntelligentStyleConverter = None, 
                                   evaluator: StyleSimilarityEvaluator = None,
                                   config: OptimizationConfig = None):
    """创建实时文风优化器实例"""
    return RealtimeStyleOptimizer(converter, evaluator, config) 