"""
古典文风分析器

分析红楼梦原著的语言特征，提取古典文学的风格特征，
为后续的文风转换和评估提供基础数据。

功能包括：
- 词汇统计分析：高频词汇、时代特征词、情感色彩词
- 句式结构分析：长短句分布、古典句式模式
- 修辞手法分析：比喻、对偶、排比等手法统计
- 称谓体系分析：等级称谓、敬语使用
"""

import re
import json
import jieba
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import Counter, defaultdict

# 配置jieba使用红楼梦专用词典
try:
    jieba.set_dictionary("data/processed/hongloumeng_dict_final.txt")
except:
    # 如果词典文件不存在，使用默认词典
    pass

@dataclass
class VocabularyFeatures:
    """词汇层面特征"""
    high_freq_classical_words: Dict[str, int]      # 高频古典词汇
    period_characteristic_words: Dict[str, int]    # 时代特征词汇  
    emotional_color_words: Dict[str, List[str]]    # 情感色彩词汇
    modern_words_detected: List[str]               # 检测到的现代词汇
    total_word_count: int                          # 总词数
    classical_word_ratio: float                    # 古典词汇比例

@dataclass
class SentenceFeatures:
    """句式结构特征"""
    sentence_length_distribution: Dict[str, int]   # 句长分布（短句、中句、长句）
    classical_patterns: Dict[str, int]             # 古典句式模式
    punctuation_usage: Dict[str, int]              # 标点符号使用
    sentence_complexity: float                     # 句式复杂度
    avg_sentence_length: float                     # 平均句长

@dataclass  
class RhetoricalFeatures:
    """修辞手法特征"""
    metaphor_simile_count: int                     # 比喻象征数量
    parallelism_count: int                         # 对偶排比数量
    allusion_count: int                            # 典故引用数量
    repetition_count: int                          # 反复递进数量
    rhetorical_density: float                      # 修辞密度

@dataclass
class AddressingFeatures:
    """称谓体系特征"""
    hierarchical_titles: Dict[str, int]           # 等级称谓统计
    respectful_language: Dict[str, int]           # 敬语使用统计
    identity_consistency: float                    # 身份一致性得分
    contextual_appropriateness: float              # 情境适应性得分

@dataclass
class StyleFeatures:
    """整体文风特征"""
    vocabulary: VocabularyFeatures
    sentence: SentenceFeatures
    rhetorical: RhetoricalFeatures
    addressing: AddressingFeatures
    literary_elegance: float                       # 文学优雅度
    classical_authenticity: float                  # 古典真实性

class ClassicalStyleAnalyzer:
    """古典文风分析器"""
    
    def __init__(self, hongloumeng_path: str = "data/raw/hongloumeng_80.md"):
        self.hongloumeng_path = Path(hongloumeng_path)
        self.logger = logging.getLogger(__name__)
        
        # 初始化词汇库
        self._init_vocabulary_libraries()
        
        # 加载红楼梦原文（如果存在）
        self.original_text = self._load_original_text()
        
        # 分析结果缓存
        self._analysis_cache = {}
        
    def _init_vocabulary_libraries(self):
        """初始化词汇库"""
        # 高频古典词汇（从红楼梦中提取的特征词汇）
        self.classical_words = {
            "人物称谓": ["宝玉", "黛玉", "宝钗", "凤姐", "老太太", "姑娘", "爷", "奶奶"],
            "地点名称": ["怡红院", "潇湘馆", "稻香村", "蘅芜苑", "大观园"],
            "古典形容": ["花容月貌", "如花似玉", "沉鱼落雁", "闭月羞花"],
            "文雅动作": ["颦蹙", "凝眸", "莞尔", "怡然", "悠然"],
            "情感表达": ["香消玉殒", "心如刀绞", "泪如雨下", "黯然神伤"]
        }
        
        # 时代特征词汇
        self.period_words = {
            "称谓敬语": ["奴婢", "婢子", "小的", "见过", "请安", "敢问", "劳烦"],
            "生活用品": ["胭脂", "水粉", "簪钗", "金钏", "玉佩", "汗巾"],
            "建筑器物": ["楼阁", "轩窗", "雕梁", "画栋", "珠帘", "绣幕"],
            "文学典故": ["诗经", "楚辞", "唐诗", "宋词", "古琴", "书画"]
        }
        
        # 现代词汇（需要避免的）
        self.modern_words = {
            "现代技术": ["电话", "电脑", "手机", "网络", "电视", "汽车"],
            "现代词汇": ["OK", "拜拜", "酷", "棒", "超级", "非常"],
            "现代语法": ["的话", "什么的", "之类的", "等等"]
        }
        
        # 修辞模式
        self.rhetorical_patterns = {
            "比喻": [r"如.*般", r"似.*样", r"像.*一样", r".*如.*"],
            "对偶": [r".*对.*", r".*配.*", r".*与.*相.*"],
            "排比": [r".*也.*也.*也", r"一.*一.*一.*"],
            "反复": [r".*了又.*", r".*再.*再.*"]
        }
        
        # 古典句式模式
        self.classical_sentence_patterns = {
            "判断句": [r".*者，.*也", r".*，.*者也"],
            "疑问句": [r".*何.*哉", r".*岂.*乎"],
            "感叹句": [r".*矣", r".*哉", r".*乎"],
            "省略句": [r".*之.*", r".*其.*"]
        }
        
        # 称谓等级体系
        self.hierarchical_titles = {
            "最高级": ["老太太", "太太", "大人"],
            "尊敬级": ["老爷", "奶奶", "姑娘", "少爷"],
            "平等级": ["哥哥", "姐姐", "弟弟", "妹妹"],
            "谦逊级": ["奴婢", "婢子", "小的", "在下"]
        }

    def _load_original_text(self) -> str:
        """加载红楼梦原文"""
        try:
            if self.hongloumeng_path.exists():
                with open(self.hongloumeng_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                self.logger.warning(f"红楼梦原文文件不存在: {self.hongloumeng_path}")
                return ""
        except Exception as e:
            self.logger.error(f"加载红楼梦原文失败: {e}")
            return ""

    def analyze_text(self, text: str) -> StyleFeatures:
        """分析文本的古典文风特征"""
        self.logger.info(f"开始分析文本，长度: {len(text)} 字符")
        
        # 分词预处理
        words = list(jieba.cut(text))
        sentences = self._split_sentences(text)
        
        # 各维度分析
        vocabulary_features = self._analyze_vocabulary(words)
        sentence_features = self._analyze_sentence_structure(sentences)
        rhetorical_features = self._analyze_rhetorical_devices(text)
        addressing_features = self._analyze_addressing_system(text)
        
        # 计算整体指标
        literary_elegance = self._calculate_literary_elegance(
            vocabulary_features, sentence_features, rhetorical_features
        )
        classical_authenticity = self._calculate_classical_authenticity(
            vocabulary_features, addressing_features
        )
        
        return StyleFeatures(
            vocabulary=vocabulary_features,
            sentence=sentence_features, 
            rhetorical=rhetorical_features,
            addressing=addressing_features,
            literary_elegance=literary_elegance,
            classical_authenticity=classical_authenticity
        )

    def _split_sentences(self, text: str) -> List[str]:
        """分句处理"""
        # 使用中文标点符号分句
        sentences = re.split(r'[。！？；]', text)
        return [s.strip() for s in sentences if s.strip()]

    def _analyze_vocabulary(self, words: List[str]) -> VocabularyFeatures:
        """分析词汇特征"""
        word_counter = Counter(words)
        total_words = len(words)
        
        # 高频古典词汇统计
        high_freq_classical = {}
        for category, word_list in self.classical_words.items():
            for word in word_list:
                if word in word_counter:
                    high_freq_classical[word] = word_counter[word]
        
        # 时代特征词汇统计  
        period_characteristic = {}
        for category, word_list in self.period_words.items():
            for word in word_list:
                if word in word_counter:
                    period_characteristic[word] = word_counter[word]
        
        # 情感色彩词汇分类
        emotional_words = {
            "positive": [],
            "negative": [], 
            "neutral": []
        }
        
        positive_patterns = ["花容", "月貌", "如花", "似玉", "怡然", "莞尔"]
        negative_patterns = ["黯然", "神伤", "泪如", "心如刀", "香消玉殒"]
        
        for word in words:
            if any(pattern in word for pattern in positive_patterns):
                emotional_words["positive"].append(word)
            elif any(pattern in word for pattern in negative_patterns):
                emotional_words["negative"].append(word)
        
        # 现代词汇检测
        modern_detected = []
        for category, word_list in self.modern_words.items():
            for word in word_list:
                if word in words:
                    modern_detected.append(word)
        
        # 计算古典词汇比例
        classical_count = len(high_freq_classical) + len(period_characteristic)
        classical_ratio = classical_count / total_words if total_words > 0 else 0
        
        return VocabularyFeatures(
            high_freq_classical_words=high_freq_classical,
            period_characteristic_words=period_characteristic,
            emotional_color_words=emotional_words,
            modern_words_detected=modern_detected,
            total_word_count=total_words,
            classical_word_ratio=classical_ratio
        )

    def _analyze_sentence_structure(self, sentences: List[str]) -> SentenceFeatures:
        """分析句式结构特征"""
        if not sentences:
            return SentenceFeatures({}, {}, {}, 0.0, 0.0)
            
        # 句长分布统计
        lengths = [len(s) for s in sentences]
        avg_length = sum(lengths) / len(lengths)
        
        length_distribution = {
            "短句(≤10字)": sum(1 for l in lengths if l <= 10),
            "中句(11-20字)": sum(1 for l in lengths if 11 <= l <= 20),
            "长句(>20字)": sum(1 for l in lengths if l > 20)
        }
        
        # 古典句式模式识别
        classical_patterns = {}
        for pattern_name, regex_list in self.classical_sentence_patterns.items():
            count = 0
            for regex in regex_list:
                for sentence in sentences:
                    if re.search(regex, sentence):
                        count += 1
            classical_patterns[pattern_name] = count
        
        # 标点符号使用统计
        all_text = "".join(sentences)
        punctuation_usage = {
            "句号": all_text.count("。"),
            "感叹号": all_text.count("！"),
            "问号": all_text.count("？"),
            "分号": all_text.count("；"),
            "逗号": all_text.count("，")
        }
        
        # 计算句式复杂度
        complexity = self._calculate_sentence_complexity(sentences)
        
        return SentenceFeatures(
            sentence_length_distribution=length_distribution,
            classical_patterns=classical_patterns,
            punctuation_usage=punctuation_usage,
            sentence_complexity=complexity,
            avg_sentence_length=avg_length
        )

    def _analyze_rhetorical_devices(self, text: str) -> RhetoricalFeatures:
        """分析修辞手法特征"""
        metaphor_count = 0
        parallelism_count = 0
        allusion_count = 0
        repetition_count = 0
        
        # 比喻象征检测
        for regex in self.rhetorical_patterns["比喻"]:
            metaphor_count += len(re.findall(regex, text))
        
        # 对偶排比检测
        for regex in self.rhetorical_patterns["对偶"]:
            parallelism_count += len(re.findall(regex, text))
            
        for regex in self.rhetorical_patterns["排比"]:
            parallelism_count += len(re.findall(regex, text))
        
        # 典故引用检测（简化版，检测常见典故关键词）
        allusion_keywords = ["诗经", "楚辞", "唐诗", "宋词", "古琴", "书画", "太虚幻境"]
        for keyword in allusion_keywords:
            allusion_count += text.count(keyword)
        
        # 反复递进检测
        for regex in self.rhetorical_patterns["反复"]:
            repetition_count += len(re.findall(regex, text))
        
        # 计算修辞密度
        total_rhetorical = metaphor_count + parallelism_count + allusion_count + repetition_count
        text_length = len(text)
        rhetorical_density = total_rhetorical / text_length if text_length > 0 else 0
        
        return RhetoricalFeatures(
            metaphor_simile_count=metaphor_count,
            parallelism_count=parallelism_count,
            allusion_count=allusion_count,
            repetition_count=repetition_count,
            rhetorical_density=rhetorical_density
        )

    def _analyze_addressing_system(self, text: str) -> AddressingFeatures:
        """分析称谓体系特征"""
        # 等级称谓统计
        hierarchical_counts = {}
        for level, titles in self.hierarchical_titles.items():
            count = 0
            for title in titles:
                count += text.count(title)
            hierarchical_counts[level] = count
        
        # 敬语使用统计
        respectful_language = {}
        respectful_terms = ["请安", "见过", "敢问", "劳烦", "恭敬", "谨遵"]
        for term in respectful_terms:
            respectful_language[term] = text.count(term)
        
        # 身份一致性得分（简化版）
        total_titles = sum(hierarchical_counts.values())
        consistency = 0.8 if total_titles > 0 else 0.0  # 简化计算
        
        # 情境适应性得分（简化版）
        appropriateness = 0.7 if sum(respectful_language.values()) > 0 else 0.5
        
        return AddressingFeatures(
            hierarchical_titles=hierarchical_counts,
            respectful_language=respectful_language,
            identity_consistency=consistency,
            contextual_appropriateness=appropriateness
        )

    def _calculate_sentence_complexity(self, sentences: List[str]) -> float:
        """计算句式复杂度"""
        if not sentences:
            return 0.0
            
        # 基于句长和标点符号复杂度的简化计算
        total_complexity = 0
        for sentence in sentences:
            length_factor = min(len(sentence) / 20, 2.0)  # 句长因子
            punctuation_factor = sentence.count("，") * 0.1 + sentence.count("；") * 0.2
            total_complexity += length_factor + punctuation_factor
        
        return total_complexity / len(sentences)

    def _calculate_literary_elegance(self, vocab: VocabularyFeatures, 
                                   sentence: SentenceFeatures, 
                                   rhetorical: RhetoricalFeatures) -> float:
        """计算文学优雅度"""
        # 权重分配：词汇40%，句式30%，修辞30%
        vocab_score = vocab.classical_word_ratio
        sentence_score = min(sentence.sentence_complexity / 2.0, 1.0)
        rhetorical_score = min(rhetorical.rhetorical_density * 100, 1.0)
        
        return vocab_score * 0.4 + sentence_score * 0.3 + rhetorical_score * 0.3

    def _calculate_classical_authenticity(self, vocab: VocabularyFeatures,
                                        addressing: AddressingFeatures) -> float:
        """计算古典真实性"""
        # 权重分配：词汇60%，称谓40%
        vocab_score = vocab.classical_word_ratio
        addressing_score = (addressing.identity_consistency + addressing.contextual_appropriateness) / 2
        
        return vocab_score * 0.6 + addressing_score * 0.4

    def compare_with_original(self, text: str) -> Dict[str, float]:
        """与红楼梦原著风格对比"""
        if not self.original_text:
            self.logger.warning("无法与原著对比：原著文本未加载")
            return {}
        
        # 分析目标文本
        target_features = self.analyze_text(text)
        
        # 分析原著文本（使用缓存）
        if "original_features" not in self._analysis_cache:
            self._analysis_cache["original_features"] = self.analyze_text(self.original_text[:50000])  # 取前50k字符
        
        original_features = self._analysis_cache["original_features"]
        
        # 计算相似度
        similarity_scores = {
            "词汇匹配度": self._compare_vocabulary(target_features.vocabulary, original_features.vocabulary),
            "句式相似度": self._compare_sentence_structure(target_features.sentence, original_features.sentence),
            "修辞丰富度": self._compare_rhetorical(target_features.rhetorical, original_features.rhetorical),
            "称谓准确度": self._compare_addressing(target_features.addressing, original_features.addressing),
            "整体相似度": (target_features.literary_elegance + target_features.classical_authenticity) / 2
        }
        
        return similarity_scores

    def _compare_vocabulary(self, target: VocabularyFeatures, original: VocabularyFeatures) -> float:
        """比较词汇特征"""
        # 简化的相似度计算
        ratio_diff = abs(target.classical_word_ratio - original.classical_word_ratio)
        return max(0, 1 - ratio_diff)

    def _compare_sentence_structure(self, target: SentenceFeatures, original: SentenceFeatures) -> float:
        """比较句式结构"""
        # 简化的相似度计算
        length_diff = abs(target.avg_sentence_length - original.avg_sentence_length) / original.avg_sentence_length
        complexity_diff = abs(target.sentence_complexity - original.sentence_complexity) / original.sentence_complexity
        return max(0, 1 - (length_diff + complexity_diff) / 2)

    def _compare_rhetorical(self, target: RhetoricalFeatures, original: RhetoricalFeatures) -> float:
        """比较修辞特征"""
        density_diff = abs(target.rhetorical_density - original.rhetorical_density) / max(original.rhetorical_density, 0.01)
        return max(0, 1 - density_diff)

    def _compare_addressing(self, target: AddressingFeatures, original: AddressingFeatures) -> float:
        """比较称谓特征"""
        consistency_diff = abs(target.identity_consistency - original.identity_consistency)
        appropriateness_diff = abs(target.contextual_appropriateness - original.contextual_appropriateness)
        return max(0, 1 - (consistency_diff + appropriateness_diff) / 2)

    def save_analysis_result(self, features: StyleFeatures, output_path: str):
        """保存分析结果"""
        result = asdict(features)
        result["analysis_timestamp"] = "2025-01-24"
        result["analyzer_version"] = "1.0.0"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"分析结果已保存到: {output_path}")

    def generate_analysis_report(self, features: StyleFeatures) -> str:
        """生成分析报告"""
        report = f"""
# 古典文风分析报告

## 📊 词汇特征
- 总词数: {features.vocabulary.total_word_count}
- 古典词汇比例: {features.vocabulary.classical_word_ratio:.2%}
- 检测到的现代词汇: {len(features.vocabulary.modern_words_detected)} 个

## 📝 句式特征  
- 平均句长: {features.sentence.avg_sentence_length:.1f} 字
- 句式复杂度: {features.sentence.sentence_complexity:.2f}
- 古典句式使用: {sum(features.sentence.classical_patterns.values())} 处

## 🎭 修辞特征
- 比喻象征: {features.rhetorical.metaphor_simile_count} 处
- 对偶排比: {features.rhetorical.parallelism_count} 处  
- 典故引用: {features.rhetorical.allusion_count} 处
- 修辞密度: {features.rhetorical.rhetorical_density:.4f}

## 👤 称谓特征
- 身份一致性: {features.addressing.identity_consistency:.2%}
- 情境适应性: {features.addressing.contextual_appropriateness:.2%}

## 🎯 综合评分
- 文学优雅度: {features.literary_elegance:.2%}
- 古典真实性: {features.classical_authenticity:.2%}

## 💡 改进建议
"""
        
        # 根据分析结果给出建议
        if features.vocabulary.classical_word_ratio < 0.3:
            report += "- 建议增加古典词汇的使用，减少现代化表达\n"
        
        if features.rhetorical.rhetorical_density < 0.01:
            report += "- 建议增加修辞手法，如比喻、对偶等，提升文学性\n"
            
        if features.sentence.avg_sentence_length < 10:
            report += "- 建议适当增加句子长度，使用更多的复合句式\n"
            
        if len(features.vocabulary.modern_words_detected) > 0:
            report += f"- 发现现代词汇: {', '.join(features.vocabulary.modern_words_detected[:5])}，建议替换为古典表达\n"
        
        return report 