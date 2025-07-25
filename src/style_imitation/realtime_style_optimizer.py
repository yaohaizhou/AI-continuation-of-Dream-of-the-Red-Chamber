"""
实时文风优化器

基于风格相似度评估结果，动态调整转换策略，实现文风质量的
迭代优化和实时监控。

核心功能：
- 评估结果分析：解析评估反馈，识别优化方向
- 动态策略调整：根据评估结果调整转换器参数
- 迭代优化循环：多轮优化直到达到目标质量
- 实时质量监控：持续监控和反馈优化效果
"""

import time
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from collections import defaultdict
from enum import Enum

from .intelligent_style_converter import IntelligentStyleConverter, ConversionConfig, ConversionResult
from .style_similarity_evaluator import StyleSimilarityEvaluator, EvaluationResult, SimilarityScores

class OptimizationStrategy(Enum):
    """优化策略类型"""
    VOCABULARY_ENHANCEMENT = "vocabulary_enhancement"      # 词汇增强
    SENTENCE_RESTRUCTURING = "sentence_restructuring"      # 句式重构
    RHETORICAL_IMPROVEMENT = "rhetorical_improvement"      # 修辞改进
    ADDRESSING_CORRECTION = "addressing_correction"        # 称谓纠正
    COMPREHENSIVE_OPTIMIZATION = "comprehensive_optimization"  # 综合优化

class OptimizationResult(Enum):
    """优化结果状态"""
    SUCCESS = "success"           # 优化成功
    IMPROVED = "improved"         # 有改进但未达标
    NO_IMPROVEMENT = "no_improvement"  # 无改进
    DEGRADED = "degraded"         # 质量下降
    MAX_ITERATIONS = "max_iterations"  # 达到最大迭代次数

@dataclass
class OptimizationConfig:
    """优化配置"""
    target_score: float = 70.0              # 目标评分
    max_iterations: int = 5                 # 最大迭代次数
    improvement_threshold: float = 2.0      # 改进阈值
    convergence_threshold: float = 1.0      # 收敛阈值
    aggressive_mode: bool = False           # 激进模式
    preserve_meaning: bool = True           # 保持语义
    enable_rhetorical_enhancement: bool = True  # 启用修辞增强

@dataclass
class OptimizationStep:
    """优化步骤记录"""
    iteration: int                          # 迭代轮次
    strategy: OptimizationStrategy          # 使用的策略
    config_changes: Dict[str, Any]          # 配置变更
    before_score: float                     # 优化前评分
    after_score: float                      # 优化后评分
    improvement: float                      # 改进幅度
    text_before: str                        # 优化前文本
    text_after: str                         # 优化后文本
    processing_time: float                  # 处理时间

@dataclass
class OptimizationSession:
    """优化会话记录"""
    original_text: str                      # 原始文本
    final_text: str                         # 最终文本
    initial_score: float                    # 初始评分
    final_score: float                      # 最终评分
    total_improvement: float                # 总改进幅度
    iterations_used: int                    # 实际迭代次数
    optimization_steps: List[OptimizationStep]  # 优化步骤
    result_status: OptimizationResult       # 结果状态
    total_time: float                       # 总耗时
    strategies_used: List[OptimizationStrategy]  # 使用的策略

@dataclass
class BatchOptimizationResult:
    """批量优化结果"""
    total_texts: int                        # 总文本数
    successful_optimizations: int          # 成功优化数
    average_improvement: float              # 平均改进幅度
    optimization_sessions: List[OptimizationSession]  # 优化会话列表
    strategy_effectiveness: Dict[str, float]  # 策略有效性
    processing_statistics: Dict[str, Any]  # 处理统计

class RealtimeStyleOptimizer:
    """实时文风优化器"""
    
    def __init__(self, 
                 converter: Optional[IntelligentStyleConverter] = None,
                 evaluator: Optional[StyleSimilarityEvaluator] = None,
                 config: Optional[OptimizationConfig] = None):
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.converter = converter or IntelligentStyleConverter()
        self.evaluator = evaluator or StyleSimilarityEvaluator()
        self.config = config or OptimizationConfig()
        
        # 优化历史
        self.optimization_history: List[OptimizationSession] = []
        
        # 策略配置映射
        self._init_strategy_mappings()
        
        # 性能统计
        self.performance_stats = {
            'total_optimizations': 0,
            'successful_optimizations': 0,
            'average_improvement': 0.0,
            'strategy_success_rates': defaultdict(list)
        }
        
    def _init_strategy_mappings(self):
        """初始化策略配置映射"""
        
        # 词汇增强策略
        self.vocabulary_strategies = {
            'low_classical_ratio': {
                'vocabulary_level': 'high',
                'preserve_meaning': True,
                'character_context': None
            },
            'modern_words_detected': {
                'vocabulary_level': 'high',
                'aggressive_replacement': True
            }
        }
        
        # 句式重构策略
        self.sentence_strategies = {
            'short_sentences': {
                'sentence_restructure': True,
                'add_classical_openings': True,
                'expand_sentences': True
            },
            'low_complexity': {
                'sentence_restructure': True,
                'classical_sentence_patterns': True
            }
        }
        
        # 修辞改进策略
        self.rhetorical_strategies = {
            'no_metaphors': {
                'add_rhetorical_devices': True,
                'metaphor_enhancement': True,
                'simile_enhancement': True
            },
            'no_parallelism': {
                'add_rhetorical_devices': True,
                'parallelism_enhancement': True
            }
        }
        
        # 称谓纠正策略
        self.addressing_strategies = {
            'inconsistent_addressing': {
                'character_context': 'formal',
                'scene_context': 'formal_occasion',
                'addressing_consistency': True
            }
        }
        
    def optimize_text(self, 
                     text: str, 
                     config: Optional[OptimizationConfig] = None) -> OptimizationSession:
        """优化单个文本的风格"""
        
        start_time = time.time()
        opt_config = config or self.config
        
        self.logger.info(f"开始优化文本，目标评分: {opt_config.target_score}")
        
        # 初始评估
        current_text = text
        initial_evaluation = self.evaluator.evaluate_similarity(text, detailed=True)
        initial_score = initial_evaluation.similarity_scores.total_score
        
        self.logger.info(f"初始评分: {initial_score:.1f}")
        
        # 优化步骤记录
        optimization_steps = []
        strategies_used = []
        
        # 迭代优化
        for iteration in range(opt_config.max_iterations):
            self.logger.info(f"开始第{iteration + 1}轮优化")
            
            # 分析当前评估结果
            strategy, config_changes = self._analyze_evaluation_and_plan_strategy(
                initial_evaluation if iteration == 0 else current_evaluation,
                opt_config
            )
            
            if strategy is None:
                self.logger.info("未找到合适的优化策略，停止优化")
                break
            
            strategies_used.append(strategy)
            
            # 应用优化策略
            step_start_time = time.time()
            before_score = current_evaluation.similarity_scores.total_score if iteration > 0 else initial_score
            
            optimized_text = self._apply_optimization_strategy(
                current_text, strategy, config_changes
            )
            
            # 评估优化效果
            current_evaluation = self.evaluator.evaluate_similarity(optimized_text, detailed=True)
            after_score = current_evaluation.similarity_scores.total_score
            improvement = after_score - before_score
            
            step_time = time.time() - step_start_time
            
            # 记录优化步骤
            step = OptimizationStep(
                iteration=iteration + 1,
                strategy=strategy,
                config_changes=config_changes,
                before_score=before_score,
                after_score=after_score,
                improvement=improvement,
                text_before=current_text,
                text_after=optimized_text,
                processing_time=step_time
            )
            optimization_steps.append(step)
            
            self.logger.info(
                f"第{iteration + 1}轮完成 - 策略: {strategy.value}, "
                f"评分: {before_score:.1f} → {after_score:.1f} "
                f"(改进: {improvement:+.1f})"
            )
            
            # 检查优化效果
            if after_score >= opt_config.target_score:
                result_status = OptimizationResult.SUCCESS
                current_text = optimized_text
                break
            elif improvement >= opt_config.improvement_threshold:
                result_status = OptimizationResult.IMPROVED
                current_text = optimized_text
            elif improvement < 0:
                self.logger.warning(f"第{iteration + 1}轮优化导致质量下降，回退到上一版本")
                result_status = OptimizationResult.DEGRADED
                break
            elif abs(improvement) < opt_config.convergence_threshold:
                self.logger.info("优化收敛，停止迭代")
                result_status = OptimizationResult.NO_IMPROVEMENT
                current_text = optimized_text
                break
            else:
                current_text = optimized_text
                result_status = OptimizationResult.IMPROVED
        else:
            result_status = OptimizationResult.MAX_ITERATIONS
        
        # 创建优化会话记录
        final_evaluation = self.evaluator.evaluate_similarity(current_text, detailed=True)
        final_score = final_evaluation.similarity_scores.total_score
        total_time = time.time() - start_time
        
        session = OptimizationSession(
            original_text=text,
            final_text=current_text,
            initial_score=initial_score,
            final_score=final_score,
            total_improvement=final_score - initial_score,
            iterations_used=len(optimization_steps),
            optimization_steps=optimization_steps,
            result_status=result_status,
            total_time=total_time,
            strategies_used=strategies_used
        )
        
        # 添加到历史记录
        self.optimization_history.append(session)
        
        # 更新性能统计
        self._update_performance_stats(session)
        
        self.logger.info(
            f"优化完成 - 最终评分: {final_score:.1f} "
            f"(总改进: {session.total_improvement:+.1f}), "
            f"状态: {result_status.value}"
        )
        
        return session
    
    def _analyze_evaluation_and_plan_strategy(self, 
                                            evaluation: EvaluationResult,
                                            config: OptimizationConfig) -> Tuple[Optional[OptimizationStrategy], Dict[str, Any]]:
        """分析评估结果并制定优化策略"""
        
        scores = evaluation.similarity_scores
        suggestions = evaluation.improvement_suggestions
        
        # 找出最需要改进的维度
        dimension_scores = {
            'vocabulary': scores.vocabulary_similarity,
            'sentence': scores.sentence_similarity,
            'rhetorical': scores.rhetorical_similarity,
            'addressing': scores.addressing_similarity
        }
        
        # 按分数排序，优先改进分数最低的维度
        sorted_dimensions = sorted(dimension_scores.items(), key=lambda x: x[1])
        lowest_dimension, lowest_score = sorted_dimensions[0]
        
        self.logger.info(f"优先改进维度: {lowest_dimension} (当前分数: {lowest_score:.3f})")
        
        # 根据最低分维度选择策略
        if lowest_dimension == 'vocabulary' and lowest_score < 0.6:
            return self._plan_vocabulary_strategy(evaluation, config)
        elif lowest_dimension == 'sentence' and lowest_score < 0.6:
            return self._plan_sentence_strategy(evaluation, config)
        elif lowest_dimension == 'rhetorical' and lowest_score < 0.5:
            return self._plan_rhetorical_strategy(evaluation, config)
        elif lowest_dimension == 'addressing' and lowest_score < 0.7:
            return self._plan_addressing_strategy(evaluation, config)
        else:
            # 如果各维度都不算太低，进行综合优化
            return self._plan_comprehensive_strategy(evaluation, config)
    
    def _plan_vocabulary_strategy(self, evaluation: EvaluationResult, config: OptimizationConfig) -> Tuple[OptimizationStrategy, Dict[str, Any]]:
        """制定词汇优化策略"""
        
        analysis = evaluation.detailed_analysis.get('vocabulary_analysis', {})
        classical_ratio = analysis.get('classical_word_ratio', 0)
        modern_words = analysis.get('modern_words_detected', 0)
        
        config_changes = {
            'vocabulary_level': 'high',
            'preserve_meaning': config.preserve_meaning
        }
        
        if classical_ratio < 0.3:
            config_changes['aggressive_classical_replacement'] = True
        
        if modern_words > 0:
            config_changes['modern_word_elimination'] = True
        
        return OptimizationStrategy.VOCABULARY_ENHANCEMENT, config_changes
    
    def _plan_sentence_strategy(self, evaluation: EvaluationResult, config: OptimizationConfig) -> Tuple[OptimizationStrategy, Dict[str, Any]]:
        """制定句式优化策略"""
        
        analysis = evaluation.detailed_analysis.get('text_statistics', {})
        avg_length = analysis.get('avg_sentence_length', 0)
        complexity = analysis.get('sentence_complexity', 0)
        
        config_changes = {
            'sentence_restructure': True,
            'preserve_meaning': config.preserve_meaning
        }
        
        if avg_length < 15:
            config_changes['expand_sentences'] = True
            config_changes['add_classical_openings'] = True
        
        if complexity < 0.5:
            config_changes['increase_complexity'] = True
            config_changes['classical_sentence_patterns'] = True
        
        return OptimizationStrategy.SENTENCE_RESTRUCTURING, config_changes
    
    def _plan_rhetorical_strategy(self, evaluation: EvaluationResult, config: OptimizationConfig) -> Tuple[OptimizationStrategy, Dict[str, Any]]:
        """制定修辞优化策略"""
        
        analysis = evaluation.detailed_analysis.get('rhetorical_analysis', {})
        metaphor_count = analysis.get('metaphor_count', 0)
        parallelism_count = analysis.get('parallelism_count', 0)
        
        config_changes = {
            'add_rhetorical_devices': True,
            'preserve_meaning': config.preserve_meaning
        }
        
        if metaphor_count == 0:
            config_changes['metaphor_enhancement'] = True
            config_changes['simile_enhancement'] = True
        
        if parallelism_count == 0:
            config_changes['parallelism_enhancement'] = True
            config_changes['repetition_enhancement'] = True
        
        return OptimizationStrategy.RHETORICAL_IMPROVEMENT, config_changes
    
    def _plan_addressing_strategy(self, evaluation: EvaluationResult, config: OptimizationConfig) -> Tuple[OptimizationStrategy, Dict[str, Any]]:
        """制定称谓优化策略"""
        
        config_changes = {
            'character_context': 'formal',
            'scene_context': 'formal_occasion',
            'addressing_consistency': True,
            'preserve_meaning': config.preserve_meaning
        }
        
        return OptimizationStrategy.ADDRESSING_CORRECTION, config_changes
    
    def _plan_comprehensive_strategy(self, evaluation: EvaluationResult, config: OptimizationConfig) -> Tuple[Optional[OptimizationStrategy], Dict[str, Any]]:
        """制定综合优化策略"""
        
        # 如果分数已经很高，可能不需要进一步优化
        if evaluation.similarity_scores.total_score >= config.target_score * 0.95:
            return None, {}
        
        config_changes = {
            'vocabulary_level': 'high',
            'sentence_restructure': True,
            'add_rhetorical_devices': config.enable_rhetorical_enhancement,
            'preserve_meaning': config.preserve_meaning,
            'comprehensive_optimization': True
        }
        
        return OptimizationStrategy.COMPREHENSIVE_OPTIMIZATION, config_changes
    
    def _apply_optimization_strategy(self, 
                                   text: str, 
                                   strategy: OptimizationStrategy, 
                                   config_changes: Dict[str, Any]) -> str:
        """应用优化策略"""
        
        # 创建转换配置
        conversion_config = ConversionConfig(
            vocabulary_level=config_changes.get('vocabulary_level', 'medium'),
            sentence_restructure=config_changes.get('sentence_restructure', False),
            add_rhetorical_devices=config_changes.get('add_rhetorical_devices', False),
            preserve_meaning=config_changes.get('preserve_meaning', True),
            character_context=config_changes.get('character_context'),
            scene_context=config_changes.get('scene_context')
        )
        
        # 执行转换
        result = self.converter.convert_text(text, conversion_config)
        return result.converted_text
    
    def batch_optimize(self, 
                      texts: List[str], 
                      config: Optional[OptimizationConfig] = None) -> BatchOptimizationResult:
        """批量优化文本"""
        
        self.logger.info(f"开始批量优化 {len(texts)} 个文本")
        
        opt_config = config or self.config
        sessions = []
        successful_count = 0
        total_improvement = 0.0
        strategy_performance = defaultdict(list)
        
        start_time = time.time()
        
        for i, text in enumerate(texts):
            try:
                self.logger.info(f"优化第 {i+1}/{len(texts)} 个文本")
                session = self.optimize_text(text, opt_config)
                sessions.append(session)
                
                if session.result_status in [OptimizationResult.SUCCESS, OptimizationResult.IMPROVED]:
                    successful_count += 1
                    total_improvement += session.total_improvement
                
                # 记录策略性能
                for strategy in session.strategies_used:
                    strategy_performance[strategy.value].append(session.total_improvement)
                
            except Exception as e:
                self.logger.error(f"优化第 {i+1} 个文本失败: {e}")
        
        # 计算策略有效性
        strategy_effectiveness = {}
        for strategy, improvements in strategy_performance.items():
            if improvements:
                strategy_effectiveness[strategy] = np.mean(improvements)
        
        # 处理统计
        total_time = time.time() - start_time
        processing_stats = {
            'total_time': total_time,
            'average_time_per_text': total_time / len(texts) if texts else 0,
            'success_rate': successful_count / len(texts) if texts else 0,
            'average_iterations': np.mean([s.iterations_used for s in sessions]) if sessions else 0
        }
        
        batch_result = BatchOptimizationResult(
            total_texts=len(texts),
            successful_optimizations=successful_count,
            average_improvement=total_improvement / successful_count if successful_count > 0 else 0,
            optimization_sessions=sessions,
            strategy_effectiveness=strategy_effectiveness,
            processing_statistics=processing_stats
        )
        
        self.logger.info(
            f"批量优化完成 - 成功: {successful_count}/{len(texts)}, "
            f"平均改进: {batch_result.average_improvement:.1f}"
        )
        
        return batch_result
    
    def monitor_quality_realtime(self, 
                               text: str, 
                               quality_threshold: float = 70.0,
                               monitor_interval: float = 0.1) -> Dict[str, Any]:
        """实时质量监控"""
        
        self.logger.info("开始实时质量监控")
        
        monitoring_data = {
            'start_time': time.time(),
            'quality_timeline': [],
            'alerts': [],
            'final_status': None
        }
        
        # 初始评估
        evaluation = self.evaluator.evaluate_similarity(text, detailed=False)
        initial_score = evaluation.similarity_scores.total_score
        
        monitoring_data['quality_timeline'].append({
            'timestamp': time.time() - monitoring_data['start_time'],
            'score': initial_score,
            'status': 'initial'
        })
        
        if initial_score < quality_threshold:
            monitoring_data['alerts'].append({
                'timestamp': time.time() - monitoring_data['start_time'],
                'type': 'quality_alert',
                'message': f"文本质量低于阈值 ({initial_score:.1f} < {quality_threshold})",
                'severity': 'warning'
            })
            
            # 自动优化
            self.logger.info("触发自动优化")
            session = self.optimize_text(text, OptimizationConfig(target_score=quality_threshold))
            
            # 记录优化过程
            for step in session.optimization_steps:
                monitoring_data['quality_timeline'].append({
                    'timestamp': time.time() - monitoring_data['start_time'],
                    'score': step.after_score,
                    'status': f'optimization_step_{step.iteration}',
                    'strategy': step.strategy.value
                })
            
            final_score = session.final_score
            if final_score >= quality_threshold:
                monitoring_data['final_status'] = 'quality_achieved'
                monitoring_data['alerts'].append({
                    'timestamp': time.time() - monitoring_data['start_time'],
                    'type': 'success',
                    'message': f"质量目标已达成 ({final_score:.1f})",
                    'severity': 'info'
                })
            else:
                monitoring_data['final_status'] = 'quality_not_achieved'
                monitoring_data['alerts'].append({
                    'timestamp': time.time() - monitoring_data['start_time'],
                    'type': 'optimization_failed',
                    'message': f"优化后仍未达标 ({final_score:.1f} < {quality_threshold})",
                    'severity': 'error'
                })
        else:
            monitoring_data['final_status'] = 'quality_ok'
            monitoring_data['alerts'].append({
                'timestamp': time.time() - monitoring_data['start_time'],
                'type': 'quality_ok',
                'message': f"文本质量达标 ({initial_score:.1f})",
                'severity': 'info'
            })
        
        total_time = time.time() - monitoring_data['start_time']
        monitoring_data['total_monitoring_time'] = total_time
        
        self.logger.info(f"实时监控完成，耗时: {total_time:.3f}秒")
        
        return monitoring_data
    
    def _update_performance_stats(self, session: OptimizationSession):
        """更新性能统计"""
        
        self.performance_stats['total_optimizations'] += 1
        
        if session.result_status in [OptimizationResult.SUCCESS, OptimizationResult.IMPROVED]:
            self.performance_stats['successful_optimizations'] += 1
        
        # 更新平均改进
        total_improvement = (
            self.performance_stats['average_improvement'] * (self.performance_stats['total_optimizations'] - 1) +
            session.total_improvement
        ) / self.performance_stats['total_optimizations']
        self.performance_stats['average_improvement'] = total_improvement
        
        # 记录策略成功率
        for strategy in session.strategies_used:
            improvement = session.total_improvement if session.total_improvement > 0 else 0
            self.performance_stats['strategy_success_rates'][strategy.value].append(improvement)
    
    def get_optimization_statistics(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        
        if not self.optimization_history:
            return {}
        
        # 基础统计
        total_sessions = len(self.optimization_history)
        successful_sessions = sum(
            1 for s in self.optimization_history 
            if s.result_status in [OptimizationResult.SUCCESS, OptimizationResult.IMPROVED]
        )
        
        improvements = [s.total_improvement for s in self.optimization_history]
        iterations = [s.iterations_used for s in self.optimization_history]
        times = [s.total_time for s in self.optimization_history]
        
        # 策略统计
        strategy_usage = defaultdict(int)
        strategy_improvements = defaultdict(list)
        
        for session in self.optimization_history:
            for strategy in session.strategies_used:
                strategy_usage[strategy.value] += 1
                strategy_improvements[strategy.value].append(session.total_improvement)
        
        strategy_stats = {}
        for strategy, usage_count in strategy_usage.items():
            improvements_list = strategy_improvements[strategy]
            strategy_stats[strategy] = {
                'usage_count': usage_count,
                'average_improvement': np.mean(improvements_list) if improvements_list else 0,
                'success_rate': sum(1 for imp in improvements_list if imp > 0) / len(improvements_list) if improvements_list else 0
            }
        
        return {
            'total_optimizations': total_sessions,
            'successful_optimizations': successful_sessions,
            'success_rate': successful_sessions / total_sessions if total_sessions > 0 else 0,
            'average_improvement': np.mean(improvements) if improvements else 0,
            'improvement_std': np.std(improvements) if improvements else 0,
            'improvement_range': (min(improvements), max(improvements)) if improvements else (0, 0),
            'average_iterations': np.mean(iterations) if iterations else 0,
            'average_time': np.mean(times) if times else 0,
            'strategy_statistics': strategy_stats
        }
    
    def save_optimization_history(self, file_path: str):
        """保存优化历史"""
        
        try:
            # 转换为可序列化的格式
            history_data = []
            for session in self.optimization_history:
                session_dict = asdict(session)
                # 转换枚举值
                session_dict['result_status'] = session.result_status.value
                session_dict['strategies_used'] = [s.value for s in session.strategies_used]
                
                for step in session_dict['optimization_steps']:
                    step['strategy'] = step['strategy'].value if hasattr(step['strategy'], 'value') else step['strategy']
                
                history_data.append(session_dict)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"优化历史已保存到: {file_path}")
            
        except Exception as e:
            self.logger.error(f"保存优化历史失败: {e}")
    
    def generate_optimization_report(self, file_path: str, batch_result: Optional[BatchOptimizationResult] = None):
        """生成优化报告"""
        
        stats = self.get_optimization_statistics()
        
        report_content = f"""# 实时文风优化器 - 优化报告

## 📊 优化统计

- **总优化次数**: {stats.get('total_optimizations', 0)}
- **成功优化次数**: {stats.get('successful_optimizations', 0)}
- **成功率**: {stats.get('success_rate', 0.0):.1%}
- **平均改进幅度**: {stats.get('average_improvement', 0.0):.1f}分
- **改进标准差**: {stats.get('improvement_std', 0.0):.2f}
- **改进范围**: {stats.get('improvement_range', (0, 0))}
- **平均迭代次数**: {stats.get('average_iterations', 0.0):.1f}
- **平均优化时间**: {stats.get('average_time', 0.0):.3f}秒

## 📈 策略效果分析

"""
        
        # 策略统计
        strategy_stats = stats.get('strategy_statistics', {})
        for strategy, stat in sorted(strategy_stats.items(), key=lambda x: x[1]['average_improvement'], reverse=True):
            report_content += f"""
### {strategy.replace('_', ' ').title()}

- **使用次数**: {stat['usage_count']}
- **平均改进**: {stat['average_improvement']:.1f}分
- **成功率**: {stat['success_rate']:.1%}
"""
        
        # 批量优化结果
        if batch_result:
            report_content += f"""

## 🎯 批量优化结果

- **处理文本数**: {batch_result.total_texts}
- **成功优化数**: {batch_result.successful_optimizations}
- **平均改进**: {batch_result.average_improvement:.1f}分
- **总处理时间**: {batch_result.processing_statistics['total_time']:.1f}秒
- **平均每文本时间**: {batch_result.processing_statistics['average_time_per_text']:.3f}秒

### 📊 策略效果排名

"""
            for strategy, effectiveness in sorted(batch_result.strategy_effectiveness.items(), key=lambda x: x[1], reverse=True):
                report_content += f"- **{strategy.replace('_', ' ').title()}**: {effectiveness:.1f}分平均改进\n"
        
        # 最近优化示例
        if self.optimization_history:
            report_content += f"""

## 📝 最近优化示例

"""
            for i, session in enumerate(self.optimization_history[-3:], 1):
                report_content += f"""
### 示例 {i}

**原始文本**: {session.original_text[:100]}{'...' if len(session.original_text) > 100 else ''}

**最终文本**: {session.final_text[:100]}{'...' if len(session.final_text) > 100 else ''}

**优化效果**: {session.initial_score:.1f} → {session.final_score:.1f} (改进: {session.total_improvement:+.1f})

**迭代次数**: {session.iterations_used}

**结果状态**: {session.result_status.value}

**使用策略**: {', '.join([s.value for s in session.strategies_used])}

"""
        
        report_content += f"""

## 🔧 优化配置

### 默认参数
- 目标评分: {self.config.target_score}
- 最大迭代次数: {self.config.max_iterations}
- 改进阈值: {self.config.improvement_threshold}
- 收敛阈值: {self.config.convergence_threshold}
- 保持语义: {self.config.preserve_meaning}

### 优化策略
- 词汇增强: 古典词汇替换，现代词汇消除
- 句式重构: 增加句子长度和复杂度，古典句式模式
- 修辞改进: 添加比喻、对偶等修辞手法
- 称谓纠正: 确保称谓的一致性和准确性
- 综合优化: 多维度同时优化

---
*报告生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.logger.info(f"优化报告已生成: {file_path}")
            
        except Exception as e:
            self.logger.error(f"生成优化报告失败: {e}")


def create_realtime_style_optimizer(converter: Optional[IntelligentStyleConverter] = None,
                                   evaluator: Optional[StyleSimilarityEvaluator] = None,
                                   config: Optional[OptimizationConfig] = None) -> RealtimeStyleOptimizer:
    """创建实时文风优化器实例"""
    return RealtimeStyleOptimizer(converter, evaluator, config) 