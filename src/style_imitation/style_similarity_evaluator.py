"""
风格相似度评估器

量化评估文本与红楼梦原著的风格相似度，为智能文风转换器提供
质量反馈和优化建议。

核心功能：
- 多维度相似度计算：词汇、句式、修辞、称谓、整体韵味
- 转换效果量化评估：与原著的匹配程度评分
- 实时质量监控：转换前后对比分析
- 批量评估统计：多文本相似度批量计算和报告
"""

import re
import json
import jieba
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import Counter, defaultdict
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

from .classical_style_analyzer import ClassicalStyleAnalyzer, StyleFeatures
from .intelligent_style_converter import ConversionResult

@dataclass
class SimilarityScores:
    """相似度评分"""
    vocabulary_similarity: float        # 词汇相似度 (0-1)
    sentence_similarity: float          # 句式相似度 (0-1)  
    rhetorical_similarity: float        # 修辞相似度 (0-1)
    addressing_similarity: float        # 称谓相似度 (0-1)
    overall_style_similarity: float     # 整体风格相似度 (0-1)
    total_score: float                  # 综合评分 (0-100)
    grade: str                          # 评分等级 (A+/A/B+/B/C/D)

@dataclass
class EvaluationResult:
    """评估结果"""
    original_text: str                  # 原始文本
    evaluated_text: str                 # 被评估文本
    similarity_scores: SimilarityScores # 相似度评分
    detailed_analysis: Dict[str, Any]   # 详细分析结果
    improvement_suggestions: List[str]   # 改进建议
    evaluation_time: float              # 评估耗时
    baseline_comparison: Dict[str, float] # 与基准的对比

@dataclass
class BatchEvaluationResult:
    """批量评估结果"""
    total_evaluations: int              # 总评估数
    average_scores: SimilarityScores    # 平均评分
    score_distribution: Dict[str, int]  # 评分分布
    best_results: List[EvaluationResult] # 最佳结果
    worst_results: List[EvaluationResult] # 最差结果
    evaluation_statistics: Dict[str, Any] # 评估统计

class StyleSimilarityEvaluator:
    """风格相似度评估器"""
    
    def __init__(self, 
                 analyzer: Optional[ClassicalStyleAnalyzer] = None,
                 original_text_path: str = "data/raw/hongloumeng_80.md"):
        self.logger = logging.getLogger(__name__)
        
        # 初始化分析器
        self.analyzer = analyzer or ClassicalStyleAnalyzer(original_text_path)
        self.original_text_path = Path(original_text_path)
        
        # 初始化原著基准
        self._init_baseline_model()
        
        # 评估权重配置
        self.similarity_weights = {
            'vocabulary': 0.30,      # 词汇匹配度权重
            'sentence': 0.25,        # 句式相似度权重  
            'rhetorical': 0.25,      # 修辞丰富度权重
            'addressing': 0.10,      # 称谓准确度权重
            'overall_style': 0.10    # 整体韵味权重
        }
        
        # 评分等级标准
        self.grade_thresholds = {
            'A+': 90, 'A': 80, 'B+': 70, 'B': 60, 'C': 50, 'D': 0
        }
        
        # 评估历史
        self.evaluation_history: List[EvaluationResult] = []
        
    def _init_baseline_model(self):
        """初始化原著基准模型"""
        
        self.logger.info("初始化红楼梦原著基准模型...")
        
        try:
            # 加载原著文本
            if self.original_text_path.exists():
                with open(self.original_text_path, 'r', encoding='utf-8') as f:
                    self.original_text = f.read()
                
                # 分析原著文风特征
                self.baseline_features = self.analyzer.analyze_text(self.original_text)
                
                # 构建词汇特征库
                self._build_vocabulary_baseline()
                
                # 构建句式特征库
                self._build_sentence_baseline()
                
                # 构建修辞特征库
                self._build_rhetorical_baseline()
                
                # 构建TF-IDF向量化器
                self._build_tfidf_baseline()
                
                self.logger.info("原著基准模型初始化完成")
                
            else:
                self.logger.warning(f"原著文件未找到: {self.original_text_path}")
                self.original_text = ""
                self.baseline_features = None
                
        except Exception as e:
            self.logger.error(f"初始化基准模型失败: {e}")
            self.original_text = ""
            self.baseline_features = None
    
    def _build_vocabulary_baseline(self):
        """构建词汇基准"""
        
        # 原著词汇分布
        words = list(jieba.cut(self.original_text))
        self.baseline_vocab_freq = Counter(words)
        self.baseline_vocab_set = set(words)
        
        # 古典词汇特征
        self.baseline_classical_words = set()
        for category, word_list in self.analyzer.classical_words.items():
            self.baseline_classical_words.update(word_list)
        
        # 词汇丰富度
        self.baseline_vocab_diversity = len(set(words)) / len(words) if words else 0
        
    def _build_sentence_baseline(self):
        """构建句式基准"""
        
        # 句子分割
        sentences = re.split(r'[。！？；…]+', self.original_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 句长分布
        sentence_lengths = [len(s) for s in sentences]
        self.baseline_avg_sentence_length = np.mean(sentence_lengths) if sentence_lengths else 0
        self.baseline_sentence_length_std = np.std(sentence_lengths) if sentence_lengths else 0
        
        # 古典句式模式
        self.baseline_classical_patterns = {
            '只见': len(re.findall(r'只见', self.original_text)),
            '却说': len(re.findall(r'却说', self.original_text)),
            '但见': len(re.findall(r'但见', self.original_text)),
            '原来': len(re.findall(r'原来', self.original_text)),
        }
        
        # 语气词使用
        self.baseline_modal_particles = {
            '也': len(re.findall(r'也', self.original_text)),
            '者': len(re.findall(r'者', self.original_text)),
            '矣': len(re.findall(r'矣', self.original_text)),
            '哉': len(re.findall(r'哉', self.original_text)),
        }
        
    def _build_rhetorical_baseline(self):
        """构建修辞基准"""
        
        # 比喻模式
        metaphor_patterns = [
            r'如.*般', r'似.*样', r'像.*一样', r'好比.*',
            r'如.*一般', r'仿佛.*', r'宛如.*', r'犹如.*'
        ]
        self.baseline_metaphor_count = sum(
            len(re.findall(pattern, self.original_text)) for pattern in metaphor_patterns
        )
        
        # 对偶模式  
        parallelism_patterns = [
            r'(\w+)对(\w+)', r'(\w+)配(\w+)', r'(\w+)，(\w+)'
        ]
        self.baseline_parallelism_count = sum(
            len(re.findall(pattern, self.original_text)) for pattern in parallelism_patterns
        )
        
        # 排比模式
        enumeration_patterns = [
            r'(\w+)，(\w+)，(\w+)', r'(\w+)也(\w+)也(\w+)也'
        ]
        self.baseline_enumeration_count = sum(
            len(re.findall(pattern, self.original_text)) for pattern in enumeration_patterns
        )
        
        # 修辞密度
        text_length = len(self.original_text)
        self.baseline_rhetorical_density = (
            self.baseline_metaphor_count + 
            self.baseline_parallelism_count + 
            self.baseline_enumeration_count
        ) / text_length if text_length > 0 else 0
        
    def _build_tfidf_baseline(self):
        """构建TF-IDF基准"""
        
        try:
            # 分章节处理原著文本
            chapter_pattern = r'第\w+回'
            chapters = re.split(chapter_pattern, self.original_text)
            chapters = [ch.strip() for ch in chapters if ch.strip() and len(ch) > 100]
            
            if len(chapters) < 5:
                # 如果章节分割失败，使用段落分割
                chapters = self.original_text.split('\n\n')
                chapters = [ch.strip() for ch in chapters if ch.strip() and len(ch) > 100]
            
            # 构建TF-IDF向量化器
            self.tfidf_vectorizer = TfidfVectorizer(
                tokenizer=lambda x: list(jieba.cut(x)),
                lowercase=False,
                max_features=5000,
                min_df=2,
                max_df=0.95
            )
            
            if chapters:
                self.baseline_tfidf_matrix = self.tfidf_vectorizer.fit_transform(chapters)
                self.baseline_tfidf_mean = np.mean(self.baseline_tfidf_matrix.toarray(), axis=0)
            else:
                self.baseline_tfidf_matrix = None
                self.baseline_tfidf_mean = None
                
        except Exception as e:
            self.logger.warning(f"TF-IDF基准构建失败: {e}")
            self.tfidf_vectorizer = None
            self.baseline_tfidf_matrix = None
            self.baseline_tfidf_mean = None
    
    def evaluate_similarity(self, 
                           text: str, 
                           original_text: Optional[str] = None,
                           detailed: bool = True) -> EvaluationResult:
        """评估文本与原著的风格相似度"""
        
        start_time = time.time()
        
        self.logger.info(f"开始评估文本相似度，长度: {len(text)}")
        
        # 分析待评估文本的风格特征
        text_features = self.analyzer.analyze_text(text)
        
        # 计算各维度相似度
        vocabulary_sim = self._calculate_vocabulary_similarity(text, text_features)
        sentence_sim = self._calculate_sentence_similarity(text, text_features)
        rhetorical_sim = self._calculate_rhetorical_similarity(text, text_features)
        addressing_sim = self._calculate_addressing_similarity(text, text_features)
        overall_sim = self._calculate_overall_similarity(text)
        
        # 计算加权总分
        total_score = (
            vocabulary_sim * self.similarity_weights['vocabulary'] +
            sentence_sim * self.similarity_weights['sentence'] +
            rhetorical_sim * self.similarity_weights['rhetorical'] +
            addressing_sim * self.similarity_weights['addressing'] +
            overall_sim * self.similarity_weights['overall_style']
        ) * 100
        
        # 确定评分等级
        grade = self._determine_grade(total_score)
        
        # 创建相似度评分对象
        similarity_scores = SimilarityScores(
            vocabulary_similarity=vocabulary_sim,
            sentence_similarity=sentence_sim,
            rhetorical_similarity=rhetorical_sim,
            addressing_similarity=addressing_sim,
            overall_style_similarity=overall_sim,
            total_score=total_score,
            grade=grade
        )
        
        # 详细分析
        detailed_analysis = {}
        if detailed:
            detailed_analysis = self._generate_detailed_analysis(text, text_features, similarity_scores)
        
        # 改进建议
        improvement_suggestions = self._generate_improvement_suggestions(similarity_scores, text_features)
        
        # 与基准的对比
        baseline_comparison = self._compare_with_baseline(text_features)
        
        # 计算评估耗时
        evaluation_time = time.time() - start_time
        
        # 创建评估结果
        result = EvaluationResult(
            original_text=original_text or "",
            evaluated_text=text,
            similarity_scores=similarity_scores,
            detailed_analysis=detailed_analysis,
            improvement_suggestions=improvement_suggestions,
            evaluation_time=evaluation_time,
            baseline_comparison=baseline_comparison
        )
        
        # 添加到历史记录
        self.evaluation_history.append(result)
        
        self.logger.info(f"相似度评估完成，总分: {total_score:.1f}, 等级: {grade}")
        
        return result
    
    def _calculate_vocabulary_similarity(self, text: str, features: StyleFeatures) -> float:
        """计算词汇相似度"""
        
        if not self.baseline_features:
            return 0.5  # 默认值
        
        # 1. 古典词汇比例相似度 (40%)
        text_classical_ratio = features.vocabulary.classical_word_ratio
        baseline_classical_ratio = self.baseline_features.vocabulary.classical_word_ratio
        classical_sim = 1 - abs(text_classical_ratio - baseline_classical_ratio)
        
        # 2. 词汇重叠度 (30%)
        text_words = set(jieba.cut(text))
        overlap_ratio = len(text_words & self.baseline_vocab_set) / len(text_words | self.baseline_vocab_set)
        
        # 3. 词汇丰富度相似度 (20%)
        text_diversity = len(set(jieba.cut(text))) / len(list(jieba.cut(text)))
        diversity_sim = 1 - abs(text_diversity - self.baseline_vocab_diversity)
        
        # 4. 高频古典词汇使用 (10%)
        text_classical_words = set()
        for word in jieba.cut(text):
            if word in self.baseline_classical_words:
                text_classical_words.add(word)
        
        classical_usage_ratio = len(text_classical_words) / len(self.baseline_classical_words) if self.baseline_classical_words else 0
        classical_usage_sim = min(1.0, classical_usage_ratio)
        
        # 加权平均
        vocabulary_similarity = (
            classical_sim * 0.4 +
            overlap_ratio * 0.3 +
            diversity_sim * 0.2 +
            classical_usage_sim * 0.1
        )
        
        return max(0.0, min(1.0, vocabulary_similarity))
    
    def _calculate_sentence_similarity(self, text: str, features: StyleFeatures) -> float:
        """计算句式相似度"""
        
        if not self.baseline_features:
            return 0.5
        
        # 1. 句长分布相似度 (40%)
        text_avg_length = features.sentence.avg_sentence_length
        length_sim = 1 - abs(text_avg_length - self.baseline_avg_sentence_length) / max(text_avg_length, self.baseline_avg_sentence_length, 1)
        
        # 2. 古典句式使用频率 (35%)
        text_classical_patterns = {
            '只见': len(re.findall(r'只见', text)),
            '却说': len(re.findall(r'却说', text)),
            '但见': len(re.findall(r'但见', text)),
            '原来': len(re.findall(r'原来', text)),
        }
        
        text_length = len(text)
        pattern_similarities = []
        for pattern, baseline_count in self.baseline_classical_patterns.items():
            text_count = text_classical_patterns.get(pattern, 0)
            baseline_freq = baseline_count / len(self.original_text) if self.original_text else 0
            text_freq = text_count / text_length if text_length > 0 else 0
            pattern_sim = 1 - abs(text_freq - baseline_freq) / max(text_freq, baseline_freq, 0.0001)
            pattern_similarities.append(pattern_sim)
        
        pattern_sim = np.mean(pattern_similarities) if pattern_similarities else 0.5
        
        # 3. 语气词使用 (15%)
        modal_similarities = []
        for particle, baseline_count in self.baseline_modal_particles.items():
            text_count = len(re.findall(particle, text))
            baseline_freq = baseline_count / len(self.original_text) if self.original_text else 0
            text_freq = text_count / text_length if text_length > 0 else 0
            modal_sim = 1 - abs(text_freq - baseline_freq) / max(text_freq, baseline_freq, 0.0001)
            modal_similarities.append(modal_sim)
        
        modal_sim = np.mean(modal_similarities) if modal_similarities else 0.5
        
        # 4. 句式复杂度 (10%)
        text_complexity = features.sentence.sentence_complexity
        baseline_complexity = self.baseline_features.sentence.sentence_complexity
        complexity_sim = 1 - abs(text_complexity - baseline_complexity) / max(text_complexity, baseline_complexity, 1)
        
        # 加权平均
        sentence_similarity = (
            length_sim * 0.4 +
            pattern_sim * 0.35 +
            modal_sim * 0.15 +
            complexity_sim * 0.1
        )
        
        return max(0.0, min(1.0, sentence_similarity))
    
    def _calculate_rhetorical_similarity(self, text: str, features: StyleFeatures) -> float:
        """计算修辞相似度"""
        
        text_length = len(text)
        if text_length == 0:
            return 0.0
        
        # 1. 比喻使用频率 (40%)
        metaphor_patterns = [
            r'如.*般', r'似.*样', r'像.*一样', r'好比.*',
            r'如.*一般', r'仿佛.*', r'宛如.*', r'犹如.*'
        ]
        text_metaphor_count = sum(len(re.findall(pattern, text)) for pattern in metaphor_patterns)
        text_metaphor_density = text_metaphor_count / text_length
        baseline_metaphor_density = self.baseline_metaphor_count / len(self.original_text) if self.original_text else 0
        metaphor_sim = 1 - abs(text_metaphor_density - baseline_metaphor_density) / max(text_metaphor_density, baseline_metaphor_density, 0.0001)
        
        # 2. 对偶使用频率 (30%)
        parallelism_patterns = [r'(\w+)对(\w+)', r'(\w+)配(\w+)']
        text_parallelism_count = sum(len(re.findall(pattern, text)) for pattern in parallelism_patterns)
        text_parallelism_density = text_parallelism_count / text_length
        baseline_parallelism_density = self.baseline_parallelism_count / len(self.original_text) if self.original_text else 0
        parallelism_sim = 1 - abs(text_parallelism_density - baseline_parallelism_density) / max(text_parallelism_density, baseline_parallelism_density, 0.0001)
        
        # 3. 排比使用频率 (20%)
        enumeration_patterns = [r'(\w+)，(\w+)，(\w+)', r'(\w+)也(\w+)也(\w+)也']
        text_enumeration_count = sum(len(re.findall(pattern, text)) for pattern in enumeration_patterns)
        text_enumeration_density = text_enumeration_count / text_length
        baseline_enumeration_density = self.baseline_enumeration_count / len(self.original_text) if self.original_text else 0
        enumeration_sim = 1 - abs(text_enumeration_density - baseline_enumeration_density) / max(text_enumeration_density, baseline_enumeration_density, 0.0001)
        
        # 4. 整体修辞密度 (10%)
        text_rhetorical_density = features.rhetorical.rhetorical_density
        rhetorical_density_sim = 1 - abs(text_rhetorical_density - self.baseline_rhetorical_density) / max(text_rhetorical_density, self.baseline_rhetorical_density, 0.0001)
        
        # 加权平均
        rhetorical_similarity = (
            metaphor_sim * 0.4 +
            parallelism_sim * 0.3 +
            enumeration_sim * 0.2 +
            rhetorical_density_sim * 0.1
        )
        
        return max(0.0, min(1.0, rhetorical_similarity))
    
    def _calculate_addressing_similarity(self, text: str, features: StyleFeatures) -> float:
        """计算称谓相似度"""
        
        if not self.baseline_features:
            return 0.5
        
        # 1. 身份一致性 (60%)
        text_identity_consistency = features.addressing.identity_consistency
        baseline_identity_consistency = self.baseline_features.addressing.identity_consistency
        identity_sim = 1 - abs(text_identity_consistency - baseline_identity_consistency)
        
        # 2. 情境适应性 (40%)
        text_contextual_appropriateness = features.addressing.contextual_appropriateness
        baseline_contextual_appropriateness = self.baseline_features.addressing.contextual_appropriateness
        contextual_sim = 1 - abs(text_contextual_appropriateness - baseline_contextual_appropriateness)
        
        # 加权平均
        addressing_similarity = (
            identity_sim * 0.6 +
            contextual_sim * 0.4
        )
        
        return max(0.0, min(1.0, addressing_similarity))
    
    def _calculate_overall_similarity(self, text: str) -> float:
        """计算整体风格相似度"""
        
        if not self.tfidf_vectorizer or self.baseline_tfidf_mean is None:
            return 0.5
        
        try:
            # 使用TF-IDF向量计算整体相似度
            text_tfidf = self.tfidf_vectorizer.transform([text])
            text_vector = text_tfidf.toarray()[0]
            
            # 计算余弦相似度
            similarity = cosine_similarity([text_vector], [self.baseline_tfidf_mean])[0][0]
            
            # 调整到0-1范围
            return max(0.0, min(1.0, (similarity + 1) / 2))
            
        except Exception as e:
            self.logger.warning(f"计算整体相似度失败: {e}")
            return 0.5
    
    def _determine_grade(self, score: float) -> str:
        """确定评分等级"""
        for grade, threshold in self.grade_thresholds.items():
            if score >= threshold:
                return grade
        return 'D'
    
    def _generate_detailed_analysis(self, text: str, features: StyleFeatures, scores: SimilarityScores) -> Dict[str, Any]:
        """生成详细分析"""
        
        analysis = {
            'text_statistics': {
                'total_characters': len(text),
                'total_words': len(list(jieba.cut(text))),
                'unique_words': len(set(jieba.cut(text))),
                'avg_sentence_length': features.sentence.avg_sentence_length,
                'sentence_complexity': features.sentence.sentence_complexity
            },
            'vocabulary_analysis': {
                'classical_word_ratio': features.vocabulary.classical_word_ratio,
                'modern_words_detected': len(features.vocabulary.modern_words_detected),
                'emotional_color_distribution': len(features.vocabulary.emotional_color_words)
            },
            'rhetorical_analysis': {
                'metaphor_count': features.rhetorical.metaphor_simile_count,
                'parallelism_count': features.rhetorical.parallelism_count,
                'allusion_count': features.rhetorical.allusion_count,
                'rhetorical_density': features.rhetorical.rhetorical_density
            },
            'style_comparison': {
                'vs_baseline_classical_ratio': f"{features.vocabulary.classical_word_ratio:.3f} vs {self.baseline_features.vocabulary.classical_word_ratio:.3f}" if self.baseline_features else "N/A",
                'vs_baseline_sentence_length': f"{features.sentence.avg_sentence_length:.1f} vs {self.baseline_avg_sentence_length:.1f}",
                'vs_baseline_rhetorical_density': f"{features.rhetorical.rhetorical_density:.4f} vs {self.baseline_rhetorical_density:.4f}"
            }
        }
        
        return analysis
    
    def _generate_improvement_suggestions(self, scores: SimilarityScores, features: StyleFeatures) -> List[str]:
        """生成改进建议"""
        
        suggestions = []
        
        # 词汇相似度建议
        if scores.vocabulary_similarity < 0.7:
            suggestions.append("建议增加古典词汇的使用，减少现代化表达")
            if features.vocabulary.classical_word_ratio < 0.5:
                suggestions.append("古典词汇比例偏低，建议参考文体模板库增加古典用词")
        
        # 句式相似度建议
        if scores.sentence_similarity < 0.7:
            suggestions.append("建议增加古典句式的使用，如'只见'、'却说'等开头")
            if features.sentence.avg_sentence_length < 15:
                suggestions.append("句子偏短，建议适当增加句子长度和复杂度")
        
        # 修辞相似度建议
        if scores.rhetorical_similarity < 0.7:
            suggestions.append("建议增加比喻、对偶等修辞手法的使用")
            if features.rhetorical.metaphor_simile_count == 0:
                suggestions.append("缺乏比喻修辞，建议添加'如...般'、'似...样'等表达")
        
        # 称谓相似度建议
        if scores.addressing_similarity < 0.7:
            suggestions.append("建议检查人物称谓的正确性和一致性")
        
        # 整体风格建议
        if scores.overall_style_similarity < 0.6:
            suggestions.append("整体风格与原著差异较大，建议综合运用古典文风转换器进行优化")
        
        if not suggestions:
            suggestions.append("文风相似度良好，继续保持古典文学特色")
        
        return suggestions
    
    def _compare_with_baseline(self, features: StyleFeatures) -> Dict[str, float]:
        """与基准进行对比"""
        
        if not self.baseline_features:
            return {}
        
        comparison = {
            'classical_word_ratio_diff': features.vocabulary.classical_word_ratio - self.baseline_features.vocabulary.classical_word_ratio,
            'avg_sentence_length_diff': features.sentence.avg_sentence_length - self.baseline_avg_sentence_length,
            'rhetorical_density_diff': features.rhetorical.rhetorical_density - self.baseline_rhetorical_density,
            'literary_elegance_diff': features.literary_elegance - self.baseline_features.literary_elegance,
            'classical_authenticity_diff': features.classical_authenticity - self.baseline_features.classical_authenticity
        }
        
        return comparison
    
    def evaluate_conversion_result(self, conversion_result: ConversionResult) -> EvaluationResult:
        """评估转换结果的相似度"""
        
        return self.evaluate_similarity(
            text=conversion_result.converted_text,
            original_text=conversion_result.original_text,
            detailed=True
        )
    
    def batch_evaluate(self, texts: List[str], detailed: bool = False) -> BatchEvaluationResult:
        """批量评估多个文本"""
        
        self.logger.info(f"开始批量评估 {len(texts)} 个文本")
        
        results = []
        for i, text in enumerate(texts):
            try:
                result = self.evaluate_similarity(text, detailed=detailed)
                results.append(result)
                
                if (i + 1) % 10 == 0:
                    self.logger.info(f"已完成 {i + 1}/{len(texts)} 个文本的评估")
                    
            except Exception as e:
                self.logger.error(f"评估第 {i + 1} 个文本失败: {e}")
        
        # 计算统计信息
        if not results:
            return BatchEvaluationResult(
                total_evaluations=0,
                average_scores=SimilarityScores(0, 0, 0, 0, 0, 0, 'D'),
                score_distribution={},
                best_results=[],
                worst_results=[],
                evaluation_statistics={}
            )
        
        # 平均评分
        avg_vocabulary = np.mean([r.similarity_scores.vocabulary_similarity for r in results])
        avg_sentence = np.mean([r.similarity_scores.sentence_similarity for r in results])
        avg_rhetorical = np.mean([r.similarity_scores.rhetorical_similarity for r in results])
        avg_addressing = np.mean([r.similarity_scores.addressing_similarity for r in results])
        avg_overall = np.mean([r.similarity_scores.overall_style_similarity for r in results])
        avg_total = np.mean([r.similarity_scores.total_score for r in results])
        avg_grade = self._determine_grade(avg_total)
        
        average_scores = SimilarityScores(
            vocabulary_similarity=avg_vocabulary,
            sentence_similarity=avg_sentence,
            rhetorical_similarity=avg_rhetorical,
            addressing_similarity=avg_addressing,
            overall_style_similarity=avg_overall,
            total_score=avg_total,
            grade=avg_grade
        )
        
        # 评分分布
        grade_counts = Counter(r.similarity_scores.grade for r in results)
        score_distribution = dict(grade_counts)
        
        # 最佳和最差结果
        results_sorted = sorted(results, key=lambda x: x.similarity_scores.total_score, reverse=True)
        best_results = results_sorted[:3]
        worst_results = results_sorted[-3:]
        
        # 评估统计
        evaluation_statistics = {
            'total_evaluation_time': sum(r.evaluation_time for r in results),
            'avg_evaluation_time': np.mean([r.evaluation_time for r in results]),
            'score_std': np.std([r.similarity_scores.total_score for r in results]),
            'score_range': (
                min(r.similarity_scores.total_score for r in results),
                max(r.similarity_scores.total_score for r in results)
            )
        }
        
        batch_result = BatchEvaluationResult(
            total_evaluations=len(results),
            average_scores=average_scores,
            score_distribution=score_distribution,
            best_results=best_results,
            worst_results=worst_results,
            evaluation_statistics=evaluation_statistics
        )
        
        self.logger.info(f"批量评估完成，平均评分: {avg_total:.1f}, 等级: {avg_grade}")
        
        return batch_result
    
    def get_evaluation_statistics(self) -> Dict[str, Any]:
        """获取评估统计信息"""
        
        if not self.evaluation_history:
            return {}
        
        scores = [r.similarity_scores.total_score for r in self.evaluation_history]
        
        return {
            'total_evaluations': len(self.evaluation_history),
            'average_score': np.mean(scores),
            'score_std': np.std(scores),
            'score_range': (min(scores), max(scores)),
            'grade_distribution': dict(Counter(r.similarity_scores.grade for r in self.evaluation_history)),
            'avg_evaluation_time': np.mean([r.evaluation_time for r in self.evaluation_history])
        }
    
    def save_evaluation_history(self, file_path: str):
        """保存评估历史"""
        
        try:
            history_data = [asdict(result) for result in self.evaluation_history]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"评估历史已保存到: {file_path}")
            
        except Exception as e:
            self.logger.error(f"保存评估历史失败: {e}")
    
    def generate_evaluation_report(self, file_path: str, batch_result: Optional[BatchEvaluationResult] = None):
        """生成评估报告"""
        
        stats = self.get_evaluation_statistics()
        
        report_content = f"""# 风格相似度评估器 - 评估报告

## 📊 评估统计

- **总评估次数**: {stats.get('total_evaluations', 0)}
- **平均评分**: {stats.get('average_score', 0.0):.1f}
- **评分标准差**: {stats.get('score_std', 0.0):.2f}
- **评分范围**: {stats.get('score_range', (0, 0))}
- **平均评估时间**: {stats.get('avg_evaluation_time', 0.0):.3f}秒

## 📈 评分分布

"""
        
        # 添加评分分布
        grade_dist = stats.get('grade_distribution', {})
        for grade, count in sorted(grade_dist.items()):
            percentage = count / stats.get('total_evaluations', 1) * 100
            report_content += f"- **{grade}级**: {count}次 ({percentage:.1f}%)\n"
        
        # 批量评估结果
        if batch_result:
            report_content += f"""

## 🎯 批量评估结果

- **批量评估文本数**: {batch_result.total_evaluations}
- **平均综合评分**: {batch_result.average_scores.total_score:.1f}
- **平均等级**: {batch_result.average_scores.grade}

### 📊 详细维度评分

- **词汇相似度**: {batch_result.average_scores.vocabulary_similarity:.3f}
- **句式相似度**: {batch_result.average_scores.sentence_similarity:.3f}  
- **修辞相似度**: {batch_result.average_scores.rhetorical_similarity:.3f}
- **称谓相似度**: {batch_result.average_scores.addressing_similarity:.3f}
- **整体风格相似度**: {batch_result.average_scores.overall_style_similarity:.3f}

"""
        
        # 添加最近评估示例
        if self.evaluation_history:
            report_content += f"""

## 📝 最近评估示例

"""
            for i, result in enumerate(self.evaluation_history[-3:]):
                report_content += f"""
### 示例 {i+1}

**评估文本**: {result.evaluated_text[:100]}{'...' if len(result.evaluated_text) > 100 else ''}

**综合评分**: {result.similarity_scores.total_score:.1f} ({result.similarity_scores.grade}级)

**维度评分**:
- 词汇相似度: {result.similarity_scores.vocabulary_similarity:.3f}
- 句式相似度: {result.similarity_scores.sentence_similarity:.3f}
- 修辞相似度: {result.similarity_scores.rhetorical_similarity:.3f}
- 称谓相似度: {result.similarity_scores.addressing_similarity:.3f}
- 整体风格: {result.similarity_scores.overall_style_similarity:.3f}

**改进建议**: {'; '.join(result.improvement_suggestions[:2])}

"""
        
        report_content += f"""

## 🔧 评估配置

### 权重设置
- 词汇匹配度: {self.similarity_weights['vocabulary']:.0%}
- 句式相似度: {self.similarity_weights['sentence']:.0%}
- 修辞丰富度: {self.similarity_weights['rhetorical']:.0%}
- 称谓准确度: {self.similarity_weights['addressing']:.0%}
- 整体韵味: {self.similarity_weights['overall_style']:.0%}

### 评分等级
- A+: 90分以上 (完全符合原著风格)
- A: 80-89分 (基本符合，轻微差异)
- B+: 70-79分 (部分符合，需要优化)
- B: 60-69分 (风格差异明显)
- C: 50-59分 (风格差异较大)
- D: 50分以下 (完全不符合原著风格)

---
*报告生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.logger.info(f"评估报告已生成: {file_path}")
            
        except Exception as e:
            self.logger.error(f"生成评估报告失败: {e}")


# 导入time模块
import time

def create_style_similarity_evaluator(analyzer: Optional[ClassicalStyleAnalyzer] = None) -> StyleSimilarityEvaluator:
    """创建风格相似度评估器实例"""
    return StyleSimilarityEvaluator(analyzer) 