"""
智能文风转换器

将现代化的AI生成文本转换为符合红楼梦原著风格的古典文学文本。

核心功能：
- 词汇层面转换：现代词汇→古典词汇映射
- 句式层面重构：语序调整和助词添加
- 修辞层面增强：比喻、对偶等修辞手法
- 语境层面优化：人物身份和情境适配
"""

import re
import json
import jieba
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict

from .classical_style_analyzer import ClassicalStyleAnalyzer, StyleFeatures
from .style_template_library import StyleTemplateLibrary, DialogueType, NarrativeType

@dataclass
class ConversionResult:
    """转换结果"""
    original_text: str                      # 原始文本
    converted_text: str                     # 转换后文本
    conversion_operations: List[str]        # 转换操作记录
    vocabulary_changes: Dict[str, str]      # 词汇替换记录
    sentence_adjustments: List[str]         # 句式调整记录
    rhetorical_enhancements: List[str]      # 修辞增强记录
    quality_score: float                    # 转换质量评分
    confidence_score: float                 # 转换置信度

@dataclass
class ConversionConfig:
    """转换配置"""
    vocabulary_level: str = "high"          # 词汇转换强度 (low/medium/high)
    sentence_restructure: bool = True       # 是否重构句式
    add_rhetorical_devices: bool = True     # 是否添加修辞
    preserve_meaning: bool = True           # 是否保持语义
    character_context: Optional[str] = None # 人物身份上下文
    scene_context: Optional[str] = None     # 场景上下文

class IntelligentStyleConverter:
    """智能文风转换器"""
    
    def __init__(self, 
                 analyzer: Optional[ClassicalStyleAnalyzer] = None,
                 template_library: Optional[StyleTemplateLibrary] = None):
        self.logger = logging.getLogger(__name__)
        
        # 初始化分析器和模板库
        self.analyzer = analyzer or ClassicalStyleAnalyzer()
        self.template_library = template_library or StyleTemplateLibrary()
        
        # 初始化转换规则
        self._init_conversion_rules()
        
        # 转换历史
        self.conversion_history: List[ConversionResult] = []
        
    def _init_conversion_rules(self):
        """初始化转换规则"""
        
        # 词汇映射规则
        self.vocabulary_mapping = {
            # 常见现代词汇到古典词汇的映射
            "很": "甚", "非常": "极", "特别": "分外",
            "说": "道", "说话": "言语", "说道": "说道",
            "看": "瞧", "看见": "只见", "看到": "瞧见",
            "着急": "心焦", "担心": "担忧", "害怕": "惊恐",
            "高兴": "欢喜", "开心": "喜悦", "生气": "恼怒",
            "漂亮": "标致", "美丽": "娇美", "丑陋": "丑恶",
            "聪明": "伶俐", "笨": "愚钝", "可爱": "可人",
            "房间": "屋子", "家": "府第", "吃": "用",
            "走": "去", "来": "来了", "在": "正在",
            "的": "的", "了": "了", "着": "着",
            
            # 情感表达词汇
            "哭": "哭泣", "笑": "含笑", "想": "思量",
            "等": "等候", "找": "寻", "给": "与",
            "拿": "取", "放": "搁", "坐": "坐下",
            
            # 疾病相关
            "生病": "身子不好", "病了": "身子抱恙", 
            "感冒": "伤风", "发烧": "发热",
            
            # 动作词汇
            "走路": "行走", "跑": "奔跑", "跳": "蹦跳",
            "站": "立", "躺": "卧", "睡": "安寝",
        }
        
        # 称谓映射规则
        self.addressing_mapping = {
            "他": "他", "她": "她", "你": "你",
            "我": "我", "我们": "咱们", "你们": "你们",
            "老爷": "老爷", "太太": "太太", "奶奶": "奶奶",
            "小姐": "姑娘", "夫人": "夫人", "公子": "公子",
        }
        
        # 句式模式
        self.sentence_patterns = {
            "只见": ["只见{subject}{action}", "只见{subject}正{action}"],
            "却说": ["却说{subject}{action}", "却说{subject}在{place}{action}"],
            "但见": ["但见{description}", "但见{subject}{description}"],
            "原来": ["原来{explanation}", "原来{subject}{reason}"],
        }
        
        # 修辞模式
        self.rhetorical_patterns = {
            "比喻": ["{subject}如{object}般{attribute}", "{subject}似{object}样{attribute}"],
            "对偶": ["{phrase1}，{phrase2}", "{action1}对{action2}"],
            "排比": ["{phrase1}，{phrase2}，{phrase3}"],
        }
        
        # 助词添加规则
        self.auxiliary_words = ["之", "也", "者", "矣", "乎", "焉", "哉"]
        
    def convert_text(self, 
                    text: str, 
                    config: Optional[ConversionConfig] = None) -> ConversionResult:
        """转换文本风格"""
        
        if config is None:
            config = ConversionConfig()
            
        self.logger.info(f"开始转换文本，长度: {len(text)}")
        
        # 记录转换操作
        operations = []
        vocabulary_changes = {}
        sentence_adjustments = []
        rhetorical_enhancements = []
        
        # 分句处理
        sentences = self._split_sentences(text)
        converted_sentences = []
        
        for sentence in sentences:
            if not sentence.strip():
                converted_sentences.append(sentence)
                continue
                
            # 1. 词汇层面转换
            sentence_after_vocab = self._convert_vocabulary(sentence, config)
            vocab_changes = self._get_vocabulary_changes(sentence, sentence_after_vocab)
            vocabulary_changes.update(vocab_changes)
            
            # 2. 句式层面重构
            sentence_after_structure = sentence_after_vocab
            if config.sentence_restructure:
                sentence_after_structure = self._restructure_sentence(sentence_after_vocab, config)
                if sentence_after_structure != sentence_after_vocab:
                    sentence_adjustments.append(f"句式调整: {sentence_after_vocab} → {sentence_after_structure}")
            
            # 3. 修辞层面增强
            sentence_after_rhetoric = sentence_after_structure
            if config.add_rhetorical_devices:
                sentence_after_rhetoric = self._enhance_rhetoric(sentence_after_structure, config)
                if sentence_after_rhetoric != sentence_after_structure:
                    rhetorical_enhancements.append(f"修辞增强: {sentence_after_structure} → {sentence_after_rhetoric}")
            
            # 4. 语境层面优化
            final_sentence = self._optimize_context(sentence_after_rhetoric, config)
            
            converted_sentences.append(final_sentence)
            operations.append(f"句子转换: {sentence.strip()} → {final_sentence.strip()}")
        
        # 组合结果
        converted_text = "".join(converted_sentences)
        
        # 计算质量评分
        quality_score = self._calculate_quality_score(text, converted_text)
        confidence_score = self._calculate_confidence_score(len(vocabulary_changes), len(operations))
        
        # 创建转换结果
        result = ConversionResult(
            original_text=text,
            converted_text=converted_text,
            conversion_operations=operations,
            vocabulary_changes=vocabulary_changes,
            sentence_adjustments=sentence_adjustments,
            rhetorical_enhancements=rhetorical_enhancements,
            quality_score=quality_score,
            confidence_score=confidence_score
        )
        
        # 添加到历史记录
        self.conversion_history.append(result)
        
        self.logger.info(f"转换完成，质量评分: {quality_score:.2f}, 置信度: {confidence_score:.2f}")
        
        return result
    
    def _split_sentences(self, text: str) -> List[str]:
        """分句"""
        # 按标点符号分句，保留标点
        pattern = r'([。！？；…]+|[\n\r]+)'
        parts = re.split(pattern, text)
        
        sentences = []
        current_sentence = ""
        
        for i, part in enumerate(parts):
            if re.match(r'[。！？；…\n\r]+', part):
                current_sentence += part
                sentences.append(current_sentence)
                current_sentence = ""
            else:
                current_sentence += part
        
        if current_sentence:
            sentences.append(current_sentence)
            
        return sentences
    
    def _convert_vocabulary(self, sentence: str, config: ConversionConfig) -> str:
        """词汇层面转换"""
        
        # 分词
        words = list(jieba.cut(sentence))
        converted_words = []
        
        for word in words:
            # 查找映射
            if word in self.vocabulary_mapping:
                converted_word = self.vocabulary_mapping[word]
                converted_words.append(converted_word)
            else:
                # 检查是否为现代化词汇，需要转换
                converted_word = self._find_classical_equivalent(word, config)
                converted_words.append(converted_word)
        
        return "".join(converted_words)
    
    def _find_classical_equivalent(self, word: str, config: ConversionConfig) -> str:
        """寻找古典对等词汇"""
        
        # 基于语境和字典查找
        if len(word) == 1:
            return word  # 单字一般保持不变
        
        # 情感词汇转换
        emotion_mapping = {
            "激动": "兴奋", "沮丧": "沮丧", "愤怒": "愤慨",
            "快乐": "快活", "悲伤": "悲戚", "惊讶": "惊奇",
        }
        
        if word in emotion_mapping:
            return emotion_mapping[word]
        
        # 动作词汇转换
        action_mapping = {
            "关心": "关怀", "帮助": "帮衬", "保护": "护佑",
            "决定": "决意", "选择": "拣选", "考虑": "思忖",
        }
        
        if word in action_mapping:
            return action_mapping[word]
        
        return word  # 默认保持原词
    
    def _restructure_sentence(self, sentence: str, config: ConversionConfig) -> str:
        """句式层面重构"""
        
        # 基本的句式调整
        restructured = sentence
        
        # 1. 添加古典开头词
        if self._should_add_classical_start(sentence):
            restructured = self._add_classical_start(restructured)
        
        # 2. 调整语序
        restructured = self._adjust_word_order(restructured)
        
        # 3. 添加助词
        restructured = self._add_auxiliary_words(restructured, config)
        
        return restructured
    
    def _should_add_classical_start(self, sentence: str) -> bool:
        """判断是否应该添加古典开头"""
        # 如果句子较长且没有古典开头词，则添加
        classical_starts = ["只见", "却说", "但见", "原来", "忽然", "忽见"]
        
        for start in classical_starts:
            if sentence.startswith(start):
                return False
        
        # 判断句子类型
        if len(sentence) > 10 and not sentence.startswith(("他", "她", "我", "你")):
            return True
            
        return False
    
    def _add_classical_start(self, sentence: str) -> str:
        """添加古典开头词"""
        
        # 根据句子内容选择合适的开头
        if "看" in sentence or "瞧" in sentence:
            return "只见" + sentence
        elif "说" in sentence or "道" in sentence:
            return "却说" + sentence
        elif "是" in sentence or "有" in sentence:
            return "原来" + sentence
        else:
            return "但见" + sentence
    
    def _adjust_word_order(self, sentence: str) -> str:
        """调整语序"""
        
        # 简单的语序调整规则
        adjusted = sentence
        
        # 处理 "很+形容词" 结构
        pattern = r'很(\w+)'
        adjusted = re.sub(pattern, r'甚是\1', adjusted)
        
        # 处理 "非常+形容词" 结构  
        pattern = r'非常(\w+)'
        adjusted = re.sub(pattern, r'极是\1', adjusted)
        
        return adjusted
    
    def _add_auxiliary_words(self, sentence: str, config: ConversionConfig) -> str:
        """添加助词"""
        
        if config.vocabulary_level != "high":
            return sentence
        
        # 在适当位置添加助词
        enhanced = sentence
        
        # 在句末添加语气词（概率性）
        if not re.search(r'[。！？]$', enhanced):
            return enhanced
        
        # 根据句子语气选择助词
        if "？" in enhanced:
            # 疑问句，可能添加"乎"
            enhanced = enhanced.replace("？", "乎？")
        elif "！" in enhanced:
            # 感叹句，可能添加"哉"
            enhanced = enhanced.replace("！", "哉！")
        
        return enhanced
    
    def _enhance_rhetoric(self, sentence: str, config: ConversionConfig) -> str:
        """修辞层面增强"""
        
        enhanced = sentence
        
        # 1. 寻找可以添加比喻的地方
        enhanced = self._add_metaphor(enhanced)
        
        # 2. 寻找可以形成对偶的结构
        enhanced = self._add_parallelism(enhanced)
        
        return enhanced
    
    def _add_metaphor(self, sentence: str) -> str:
        """添加比喻修辞"""
        
        # 简单的比喻增强
        metaphor_patterns = {
            r'(\w+)很美': r'\1如花似玉',
            r'(\w+)很聪明': r'\1伶俐如冰雪', 
            r'(\w+)很着急': r'\1心如火焚',
            r'(\w+)很伤心': r'\1心如刀绞',
        }
        
        enhanced = sentence
        for pattern, replacement in metaphor_patterns.items():
            enhanced = re.sub(pattern, replacement, enhanced)
            
        return enhanced
    
    def _add_parallelism(self, sentence: str) -> str:
        """添加对偶修辞"""
        
        # 寻找可以形成对偶的结构（这里是简化实现）
        enhanced = sentence
        
        # 例如：将"高兴和快乐"转换为"欢喜对快活"
        pattern = r'(\w+)和(\w+)'
        if re.search(pattern, enhanced):
            enhanced = re.sub(pattern, r'\1对\2', enhanced)
        
        return enhanced
    
    def _optimize_context(self, sentence: str, config: ConversionConfig) -> str:
        """语境层面优化"""
        
        optimized = sentence
        
        # 根据人物身份调整语言
        if config.character_context:
            optimized = self._adjust_for_character(optimized, config.character_context)
        
        # 根据场景调整语言
        if config.scene_context:
            optimized = self._adjust_for_scene(optimized, config.scene_context)
        
        return optimized
    
    def _adjust_for_character(self, sentence: str, character: str) -> str:
        """根据人物身份调整语言"""
        
        # 不同人物的语言特点
        character_styles = {
            "贾宝玉": {"特点": "温文尔雅", "常用词": ["颦儿", "妹妹", "姐姐"]},
            "林黛玉": {"特点": "文雅委婉", "常用词": ["宝哥哥", "姐妹们"]},
            "王熙凤": {"特点": "利落直接", "常用词": ["你们", "咱们", "我说"]},
            "贾母": {"特点": "威严慈祥", "常用词": ["好孩子", "我的心肝"]},
        }
        
        if character in character_styles:
            style = character_styles[character]
            # 这里可以根据人物特点进行更细致的调整
            pass
        
        return sentence
    
    def _adjust_for_scene(self, sentence: str, scene: str) -> str:
        """根据场景调整语言"""
        
        scene_styles = {
            "正式场合": {"特点": "庄重严肃", "避免": ["俗语", "玩笑"]},
            "私人对话": {"特点": "亲密自然", "允许": ["昵称", "俗语"]},
            "诗词场合": {"特点": "文雅高深", "偏好": ["典故", "对偶"]},
        }
        
        if scene in scene_styles:
            style = scene_styles[scene]
            # 根据场景特点调整
            pass
        
        return sentence
    
    def _get_vocabulary_changes(self, original: str, converted: str) -> Dict[str, str]:
        """获取词汇变化记录"""
        
        changes = {}
        
        # 简单的词汇对比（实际应该更复杂）
        orig_words = set(jieba.cut(original))
        conv_words = set(jieba.cut(converted))
        
        # 这里简化处理，实际需要更精确的对应关系
        for orig_word in orig_words:
            if orig_word in self.vocabulary_mapping:
                mapped_word = self.vocabulary_mapping[orig_word]
                if mapped_word in conv_words:
                    changes[orig_word] = mapped_word
        
        return changes
    
    def _calculate_quality_score(self, original: str, converted: str) -> float:
        """计算转换质量评分"""
        
        # 基于多个维度计算质量评分
        
        # 1. 长度变化合理性 (权重: 0.2)
        length_ratio = len(converted) / len(original) if len(original) > 0 else 1.0
        length_score = 1.0 - abs(length_ratio - 1.0) * 0.5  # 理想比例1.0-1.3
        length_score = max(0.0, min(1.0, length_score))
        
        # 2. 古典词汇比例 (权重: 0.3)
        classical_score = self._calculate_classical_ratio(converted)
        
        # 3. 句式复杂度 (权重: 0.2)
        complexity_score = self._calculate_complexity_score(converted)
        
        # 4. 语义保持度 (权重: 0.3)
        semantic_score = self._calculate_semantic_preservation(original, converted)
        
        # 加权平均
        total_score = (length_score * 0.2 + 
                      classical_score * 0.3 + 
                      complexity_score * 0.2 + 
                      semantic_score * 0.3)
        
        return round(total_score, 3)
    
    def _calculate_classical_ratio(self, text: str) -> float:
        """计算古典词汇比例"""
        
        words = list(jieba.cut(text))
        if not words:
            return 0.0
        
        classical_count = 0
        for word in words:
            if len(word) > 1 and self._is_classical_word(word):
                classical_count += 1
        
        return classical_count / len(words)
    
    def _is_classical_word(self, word: str) -> bool:
        """判断是否为古典词汇"""
        
        # 检查是否在古典词汇库中
        classical_indicators = [
            "只见", "却说", "但见", "原来", 
            "甚是", "极是", "颦儿", "怡红院",
            "瞧见", "思量", "伶俐", "标致"
        ]
        
        return word in classical_indicators or word in self.vocabulary_mapping.values()
    
    def _calculate_complexity_score(self, text: str) -> float:
        """计算句式复杂度评分"""
        
        # 基于句长分布和结构复杂度
        sentences = self._split_sentences(text)
        if not sentences:
            return 0.0
        
        total_score = 0.0
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 句长评分（10-30字为最佳）
            length = len(sentence)
            if 10 <= length <= 30:
                length_score = 1.0
            elif length < 10:
                length_score = length / 10.0
            else:
                length_score = 30.0 / length
            
            # 结构复杂度（基于标点和连词）
            complexity_indicators = sentence.count('，') + sentence.count('；') + sentence.count('：')
            complexity_score = min(1.0, complexity_indicators / 3.0)
            
            sentence_score = (length_score + complexity_score) / 2.0
            total_score += sentence_score
        
        return total_score / len(sentences)
    
    def _calculate_semantic_preservation(self, original: str, converted: str) -> float:
        """计算语义保持度"""
        
        # 简化实现：基于关键词保持
        orig_words = set(jieba.cut(original))
        conv_words = set(jieba.cut(converted))
        
        # 移除标点和停用词
        stop_words = {'的', '了', '在', '是', '有', '和', '与', '或', '但', '而'}
        orig_words = {w for w in orig_words if w not in stop_words and len(w) > 1}
        conv_words = {w for w in conv_words if w not in stop_words and len(w) > 1}
        
        if not orig_words:
            return 1.0
        
        # 计算保持的关键概念比例
        preserved_concepts = 0
        for orig_word in orig_words:
            # 直接保持
            if orig_word in conv_words:
                preserved_concepts += 1
            # 通过映射保持
            elif orig_word in self.vocabulary_mapping:
                mapped_word = self.vocabulary_mapping[orig_word]
                if mapped_word in conv_words:
                    preserved_concepts += 1
        
        return preserved_concepts / len(orig_words)
    
    def _calculate_confidence_score(self, vocab_changes: int, total_operations: int) -> float:
        """计算转换置信度"""
        
        # 基于转换操作的数量和复杂度
        if total_operations == 0:
            return 1.0
        
        # 词汇替换的可靠性较高
        vocab_confidence = min(1.0, vocab_changes / (total_operations * 0.7))
        
        # 整体操作的合理性
        operation_confidence = min(1.0, total_operations / 10.0)
        
        return (vocab_confidence + operation_confidence) / 2.0
    
    def batch_convert(self, texts: List[str], config: Optional[ConversionConfig] = None) -> List[ConversionResult]:
        """批量转换文本"""
        
        results = []
        for text in texts:
            result = self.convert_text(text, config)
            results.append(result)
        
        return results
    
    def get_conversion_statistics(self) -> Dict[str, Any]:
        """获取转换统计信息"""
        
        if not self.conversion_history:
            return {}
        
        total_conversions = len(self.conversion_history)
        avg_quality = sum(r.quality_score for r in self.conversion_history) / total_conversions
        avg_confidence = sum(r.confidence_score for r in self.conversion_history) / total_conversions
        
        vocab_changes_count = sum(len(r.vocabulary_changes) for r in self.conversion_history)
        
        return {
            "total_conversions": total_conversions,
            "average_quality_score": round(avg_quality, 3),
            "average_confidence_score": round(avg_confidence, 3),
            "total_vocabulary_changes": vocab_changes_count,
            "average_changes_per_conversion": round(vocab_changes_count / total_conversions, 2)
        }
    
    def save_conversion_history(self, file_path: str):
        """保存转换历史"""
        
        try:
            history_data = [asdict(result) for result in self.conversion_history]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"转换历史已保存到: {file_path}")
            
        except Exception as e:
            self.logger.error(f"保存转换历史失败: {e}")
    
    def generate_conversion_report(self, file_path: str):
        """生成转换报告"""
        
        stats = self.get_conversion_statistics()
        
        report_content = f"""# 智能文风转换器 - 转换报告

## 📊 转换统计

- **总转换次数**: {stats.get('total_conversions', 0)}
- **平均质量评分**: {stats.get('average_quality_score', 0.0):.3f}
- **平均置信度**: {stats.get('average_confidence_score', 0.0):.3f}
- **总词汇替换数**: {stats.get('total_vocabulary_changes', 0)}
- **平均每次替换数**: {stats.get('average_changes_per_conversion', 0.0):.2f}

## 📝 转换示例

"""
        
        # 添加最近几个转换示例
        for i, result in enumerate(self.conversion_history[-3:]):
            report_content += f"""
### 示例 {i+1}

**原文**: {result.original_text[:100]}{'...' if len(result.original_text) > 100 else ''}

**转换后**: {result.converted_text[:100]}{'...' if len(result.converted_text) > 100 else ''}

**质量评分**: {result.quality_score:.3f}
**置信度**: {result.confidence_score:.3f}
**词汇替换**: {len(result.vocabulary_changes)}个

"""
        
        report_content += f"""
## 🔧 转换配置建议

根据当前转换效果，建议的最优配置：
- **词汇转换强度**: {'high' if stats.get('average_quality_score', 0) > 0.8 else 'medium'}
- **句式重构**: 建议启用
- **修辞增强**: 建议启用
- **语义保持**: 建议启用

---
*报告生成时间: {str(self.logger.handlers[0].formatter.formatTime(self.logger.handlers[0], None) if self.logger.handlers else 'Unknown')}*
"""
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.logger.info(f"转换报告已生成: {file_path}")
            
        except Exception as e:
            self.logger.error(f"生成转换报告失败: {e}")


def create_intelligent_converter(analyzer: Optional[ClassicalStyleAnalyzer] = None,
                               template_library: Optional[StyleTemplateLibrary] = None) -> IntelligentStyleConverter:
    """创建智能文风转换器实例"""
    return IntelligentStyleConverter(analyzer, template_library) 