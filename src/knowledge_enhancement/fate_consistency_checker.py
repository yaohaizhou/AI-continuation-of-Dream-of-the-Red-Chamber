"""
命运一致性检验器 - 太虚幻境判词应用核心模块

基于太虚幻境判词数据，智能检验续写内容是否符合角色既定命运，
自动检测违背原著设定的内容，并提供基于判词的情节发展建议。

Author: AI-HongLouMeng Project
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
from loguru import logger


class FateViolationType(Enum):
    """命运违背类型"""
    DESTINY_CONTRADICTION = "destiny_contradiction"  # 命运轨迹矛盾
    CHARACTER_INCONSISTENCY = "character_inconsistency"  # 性格不符
    TIMELINE_ERROR = "timeline_error"  # 时间线错误
    SYMBOL_MISUSE = "symbol_misuse"  # 象征意象误用
    EMOTIONAL_TONE_MISMATCH = "emotional_tone_mismatch"  # 情感基调不符


@dataclass
class FateViolation:
    """命运违背检测结果"""
    character: str  # 涉及角色
    violation_type: FateViolationType  # 违背类型
    severity: str  # 严重程度：critical/warning/suggestion
    description: str  # 违背描述
    prophecy_reference: str  # 相关判词
    suggested_fix: str  # 修正建议
    confidence: float  # 检测置信度


@dataclass
class ConsistencyScore:
    """一致性评分"""
    overall_score: float  # 总体评分 (0-100)
    character_scores: Dict[str, float]  # 各角色评分
    aspect_scores: Dict[str, float]  # 各方面评分
    violations: List[FateViolation]  # 违背列表
    recommendations: List[str]  # 改进建议


@dataclass
class FateGuidance:
    """命运指导建议"""
    character: str  # 角色名
    current_situation: str  # 当前情况
    prophecy_hint: str  # 判词暗示
    suggested_development: str  # 建议发展
    symbolic_elements: List[str]  # 建议象征元素
    emotional_tone: str  # 建议情感基调


class FateConsistencyChecker:
    """命运一致性检验器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.prophecies_path = self.data_dir / "processed" / "taixu_prophecies.json"
        
        # 核心数据
        self.prophecies = {}
        self.character_fates = {}
        self.symbolic_meanings = {}
        self.timeline_markers = {}
        
        # 检测规则
        self.fate_rules = {}
        self.character_traits = {}
        self.violation_patterns = {}
        
        # 初始化
        self._load_prophecy_data()
        self._build_fate_rules()
        self._build_detection_patterns()
    
    def _load_prophecy_data(self) -> None:
        """加载太虚幻境判词数据"""
        try:
            if not self.prophecies_path.exists():
                raise FileNotFoundError(f"判词数据文件不存在: {self.prophecies_path}")
            
            with open(self.prophecies_path, 'r', encoding='utf-8') as f:
                self.prophecies = json.load(f)
            
            # 构建角色命运映射
            self._build_character_fate_mapping()
            
            # 构建象征意象映射
            self._build_symbolic_mapping()
            
            # 构建时间线标记
            self._build_timeline_mapping()
            
            logger.info(f"成功加载判词数据: {len(self.character_fates)} 个角色命运")
            
        except Exception as e:
            logger.error(f"加载判词数据失败: {e}")
            raise
    
    def _build_character_fate_mapping(self) -> None:
        """构建角色命运映射"""
        sections = ["main_册", "副册", "又副册"]
        
        for section_name in sections:
            section = self.prophecies.get(section_name, [])
            for prophecy in section:
                characters = prophecy.get("characters", [])
                fate_interpretations = prophecy.get("fate_interpretations", [])
                
                for fate in fate_interpretations:
                    character = fate.get("character")
                    if character:
                        self.character_fates[character] = {
                            "fate_summary": fate.get("fate_summary", ""),
                            "key_events": fate.get("key_events", []),
                            "symbolic_meaning": fate.get("symbolic_meaning", ""),
                            "timeline_hints": fate.get("timeline_hints", []),
                            "prophecy": prophecy,
                            "section": section_name
                        }
    
    def _build_symbolic_mapping(self) -> None:
        """构建象征意象映射"""
        sections = ["main_册", "副册", "又副册"]
        
        for section_name in sections:
            section = self.prophecies.get(section_name, [])
            for prophecy in section:
                image = prophecy.get("image", {})
                symbolic_elements = image.get("symbolic_elements", [])
                visual_metaphors = image.get("visual_metaphors", [])
                
                characters = prophecy.get("characters", [])
                for character in characters:
                    if character not in self.symbolic_meanings:
                        self.symbolic_meanings[character] = []
                    
                    self.symbolic_meanings[character].extend([
                        {"element": elem, "type": "symbolic"} for elem in symbolic_elements
                    ])
                    self.symbolic_meanings[character].extend([
                        {"element": elem, "type": "metaphor"} for elem in visual_metaphors
                    ])
    
    def _build_timeline_mapping(self) -> None:
        """构建时间线标记映射"""
        timeline_keywords = {
            "early": ["幼年", "襁褓", "童年", "年少"],
            "youth": ["青春", "年华", "花样年华", "青葱"],
            "marriage": ["出嫁", "婚配", "成亲", "结缡"],
            "middle": ["中年", "三十", "四十", "半生"],
            "late": ["晚年", "暮年", "老来", "夕阳"],
            "death": ["去世", "辞世", "香消玉殒", "命终", "归天"]
        }
        
        self.timeline_markers = timeline_keywords
    
    def _build_fate_rules(self) -> None:
        """构建命运规则引擎"""
        # 基于判词构建核心命运规则
        self.fate_rules = {
            "林黛玉": {
                "destiny": "early_death",  # 早逝
                "manner": "melancholy",    # 忧郁而终
                "forbidden_outcomes": ["结婚", "结为夫妻", "成亲", "婚配", "长寿", "白头偕老", "幸福结局", "儿孙满堂", "安享晚年", "长命百岁"],
                "required_traits": ["多愁善感", "才华横溢", "孤高自许"],
                "symbolic_associations": ["玉带", "林中", "枯木", "悲秋"]
            },
            "薛宝钗": {
                "destiny": "lonely_marriage",  # 独守空房
                "manner": "cold_solitude",     # 冷寂孤独
                "forbidden_outcomes": ["真爱", "夫妻恩爱", "儿女双全"],
                "required_traits": ["理性务实", "大度包容", "外圆内方"],
                "symbolic_associations": ["金簪", "雪里", "停机", "寒冬"]
            },
            "贾元春": {
                "destiny": "short_glory",      # 荣华短暂
                "manner": "imperial_sorrow",   # 宫廷忧伤
                "forbidden_outcomes": ["长期富贵", "家庭团聚", "自由生活"],
                "required_traits": ["仁慈善良", "思亲情深", "身不由己"],
                "symbolic_associations": ["榴花", "宫闱", "弓箭", "香橼"]
            },
            "贾探春": {
                "destiny": "distant_marriage", # 远嫁他乡
                "manner": "talented_but_helpless", # 有才无奈
                "forbidden_outcomes": ["留在家中", "实现抱负", "改变家族"],
                "required_traits": ["精明能干", "志向远大", "生不逢时"],
                "symbolic_associations": ["风筝", "大海", "清明", "千里"]
            }
        }
        
        # 补充所有新提取的角色命运规则
        self.fate_rules.update({
            "史湘云": {
                "destiny": "orphan_wandering",  # 幼年失亲，飘零孤独
                "manner": "noble_but_lonely",   # 高贵但孤独
                "forbidden_outcomes": ["长期婚姻", "稳定家庭", "父母团聚", "永久富贵"],
                "required_traits": ["豪爽大方", "才情出众", "命运坎坷"],
                "symbolic_associations": ["飞云", "逝水", "湘江", "楚云"]
            },
            "妙玉": {
                "destiny": "fallen_purity",     # 追求纯洁却堕落
                "manner": "nun_contaminated",   # 出家人被污染
                "forbidden_outcomes": ["结婚", "成亲", "生儿育女", "世俗生活", "夫妻生活", "享受天伦", "家庭幸福"],
                "required_traits": ["洁癖高傲", "超然物外", "终难自保"],
                "symbolic_associations": ["美玉", "泥污", "洁净", "污染"]
            },
            "贾迎春": {
                "destiny": "marry_evil",        # 嫁给恶人
                "manner": "tortured_death",     # 被折磨致死
                "forbidden_outcomes": ["美满婚姻", "好丈夫", "长寿", "幸福生活"],
                "required_traits": ["懦弱善良", "逆来顺受", "缺乏主见"],
                "symbolic_associations": ["中山狼", "恶狼", "柔弱", "一载"]
            },
            "贾惜春": {
                "destiny": "become_nun",        # 出家为尼
                "manner": "see_through_world",  # 看破红尘
                "forbidden_outcomes": ["结婚", "成家", "世俗生活", "享受富贵"],
                "required_traits": ["冷漠无情", "超脱世俗", "勘破三春"],
                "symbolic_associations": ["古庙", "青灯", "古佛", "缁衣"]
            },
            "王熙凤": {
                "destiny": "clever_defeated",   # 机关算尽反误卿卿性命
                "manner": "power_collapse",     # 权势崩塌
                "forbidden_outcomes": ["长期权势", "善终", "家庭和睦", "子孙满堂"],
                "required_traits": ["精明能干", "权力欲强", "机关算尽"],
                "symbolic_associations": ["雌凤", "冰山", "末世", "三人木"]
            },
            "贾巧姐": {
                "destiny": "noble_to_poor",     # 贵族沦为平民
                "manner": "saved_by_kindness",  # 因善得救
                "forbidden_outcomes": ["永远富贵", "高门嫁娶", "不劳而获"],
                "required_traits": ["天真善良", "适应能力强", "知恩图报"],
                "symbolic_associations": ["荒村", "野店", "纺绩", "恩人"]
            },
            "李纨": {
                "destiny": "widowed_educator",  # 守寡教子
                "manner": "late_glory_empty",   # 晚年荣华终成空
                "forbidden_outcomes": ["再婚", "夫妻恩爱", "长久荣华"],
                "required_traits": ["贤妻良母", "教子有方", "品格高洁"],
                "symbolic_associations": ["茂兰", "凤冠霞帔", "桃李", "一盆兰"]
            },
            "秦可卿": {
                "destiny": "suicide_shame",     # 因丑事羞愧自杀
                "manner": "hanging_death",      # 悬梁自尽
                "forbidden_outcomes": ["清白名声", "长寿", "美满生活", "受人尊敬"],
                "required_traits": ["美貌妖娆", "情深如海", "不能自控"],
                "symbolic_associations": ["高楼", "悬梁", "情海", "淫乱"]
            },
            "香菱": {
                "destiny": "tragic_life",       # 悲惨一生
                "manner": "fragrant_soul_return", # 香魂返故乡
                "forbidden_outcomes": ["圆满人生", "家庭幸福", "避免苦难"],
                "required_traits": ["坚韧善良", "才情横溢", "命运多舛"],
                "symbolic_associations": ["荷花", "一茎香", "两地", "孤木"]
            },
            "晴雯": {
                "destiny": "die_young",         # 夭折早死
                "manner": "slandered_death",    # 因诽谤而死
                "forbidden_outcomes": ["长寿", "得到认可", "避免流言"],
                "required_traits": ["心高气傲", "美貌灵巧", "招人嫉妒"],
                "symbolic_associations": ["霁月", "彩云", "心高", "下贱"]
            },
            "袭人": {
                "destiny": "serve_faithfully",  # 忠心服侍
                "manner": "unrecognized_loyalty", # 忠诚不被认可
                "forbidden_outcomes": ["得到真爱", "被重视", "改变身份"],
                "required_traits": ["温柔体贴", "忠心耿耿", "默默付出"],
                "symbolic_associations": ["温柔", "和顺", "桂兰", "优伶"]
            }
        })
        
        # 扩展到所有有判词的角色
        for character, fate_data in self.character_fates.items():
            if character not in self.fate_rules:
                self.fate_rules[character] = self._extract_rules_from_fate(fate_data)
    
    def _extract_rules_from_fate(self, fate_data: Dict[str, Any]) -> Dict[str, Any]:
        """从命运数据中提取规则"""
        fate_summary = fate_data.get("fate_summary", "")
        key_events = fate_data.get("key_events", [])
        
        # 根据命运概述推断规则
        forbidden_outcomes = []
        required_traits = []
        destiny_type = "uncertain"
        
        if "早逝" in fate_summary or "夭折" in fate_summary:
            forbidden_outcomes.extend(["长寿", "白头偕老", "儿孙满堂"])
            destiny_type = "early_death"
        elif "独守" in fate_summary or "孤独" in fate_summary:
            forbidden_outcomes.extend(["恩爱夫妻", "幸福家庭"])
            destiny_type = "loneliness"
        elif "远嫁" in fate_summary or "离别" in fate_summary:
            forbidden_outcomes.extend(["团聚", "回乡", "陪伴亲人"])
            destiny_type = "separation"
        
        return {
            "destiny": destiny_type,
            "forbidden_outcomes": forbidden_outcomes,
            "required_traits": required_traits,
            "key_events": key_events
        }
    
    def _build_detection_patterns(self) -> None:
        """构建违背检测模式"""
        self.violation_patterns = {
            FateViolationType.DESTINY_CONTRADICTION: {
                "patterns": [
                    r"(.+)(长命百岁|白头偕老|安享晚年)",  # 与早逝命运矛盾
                    r"(.+)(夫妻恩爱|琴瑟和鸣|举案齐眉)",  # 与独守空房矛盾
                    r"(.+)(团聚|回家|重逢)",             # 与远嫁分离矛盾
                ],
                "severity": "critical"
            },
            FateViolationType.CHARACTER_INCONSISTENCY: {
                "patterns": [
                    r"林黛玉.*(开朗|活泼|无忧无虑)",      # 性格不符
                    r"薛宝钗.*(任性|冲动|直率)",          # 性格不符
                    r"贾探春.*(甘于平庸|没有志向)",       # 性格不符
                ],
                "severity": "warning"
            },
            FateViolationType.EMOTIONAL_TONE_MISMATCH: {
                "patterns": [
                    r"(.+)(欢声笑语|其乐融融|幸福美满)",   # 与悲剧基调不符
                ],
                "severity": "suggestion"
            }
        }
    
    def check_consistency(self, text: str, characters: Optional[List[str]] = None) -> ConsistencyScore:
        """检查续写内容的命运一致性"""
        logger.info("开始命运一致性检验...")
        
        # 1. 提取文本中的角色和情节
        detected_characters = self._extract_characters(text)
        if characters:
            detected_characters.update(characters)
        
        # 2. 检测各类违背
        violations = []
        character_scores = {}
        
        for character in detected_characters:
            if character in self.character_fates:
                character_violations = self._check_character_consistency(text, character)
                violations.extend(character_violations)
                
                # 计算角色评分
                character_scores[character] = self._calculate_character_score(character_violations)
        
        # 3. 计算总体评分
        overall_score = self._calculate_overall_score(violations, character_scores)
        
        # 4. 生成方面评分
        aspect_scores = self._calculate_aspect_scores(violations)
        
        # 5. 生成改进建议
        recommendations = self._generate_recommendations(violations, detected_characters)
        
        return ConsistencyScore(
            overall_score=overall_score,
            character_scores=character_scores,
            aspect_scores=aspect_scores,
            violations=violations,
            recommendations=recommendations
        )
    
    def _extract_characters(self, text: str) -> Set[str]:
        """提取文本中的角色"""
        detected = set()
        
        # 检查所有已知角色
        for character in self.character_fates.keys():
            # 完整姓名匹配
            if character in text:
                detected.add(character)
                continue
            
            # 简化姓名匹配（如"黛玉"、"宝钗"）
            short_name = character[-2:] if len(character) > 2 else character
            if short_name in text and len(short_name) >= 2:
                detected.add(character)
        
        return detected
    
    def _check_character_consistency(self, text: str, character: str) -> List[FateViolation]:
        """检查单个角色的一致性"""
        violations = []
        character_fate = self.character_fates[character]
        character_rules = self.fate_rules.get(character, {})
        
        # 1. 检查命运轨迹违背
        destiny_violations = self._check_destiny_violations(text, character, character_rules)
        violations.extend(destiny_violations)
        
        # 2. 检查性格一致性
        trait_violations = self._check_trait_violations(text, character, character_rules)
        violations.extend(trait_violations)
        
        # 3. 检查象征意象使用
        symbol_violations = self._check_symbol_violations(text, character)
        violations.extend(symbol_violations)
        
        # 4. 检查情感基调
        tone_violations = self._check_emotional_tone(text, character, character_fate)
        violations.extend(tone_violations)
        
        return violations
    
    def _check_destiny_violations(self, text: str, character: str, rules: Dict[str, Any]) -> List[FateViolation]:
        """检查命运轨迹违背"""
        violations = []
        forbidden_outcomes = rules.get("forbidden_outcomes", [])
        
        for outcome in forbidden_outcomes:
            # 检查是否出现禁止的结局
            if outcome in text and character in text:
                # 确认是针对该角色的描述
                char_context = self._extract_character_context(text, character)
                if outcome in char_context:
                    violation = FateViolation(
                        character=character,
                        violation_type=FateViolationType.DESTINY_CONTRADICTION,
                        severity="critical",
                        description=f"{character}出现了与判词预言矛盾的结局：{outcome}",
                        prophecy_reference=self.character_fates[character]["fate_summary"],
                        suggested_fix=f"根据判词，{character}的命运应该是{self.character_fates[character]['fate_summary']}，建议修改相关描述",
                        confidence=0.8
                    )
                    violations.append(violation)
        
        return violations
    
    def _check_trait_violations(self, text: str, character: str, rules: Dict[str, Any]) -> List[FateViolation]:
        """检查性格特征违背"""
        violations = []
        
        # 基于规则检查性格一致性
        if character == "林黛玉":
            # 检查是否有与黛玉性格不符的描述
            inconsistent_traits = ["开朗大笑", "无忧无虑", "粗鲁直接", "不学无术"]
            for trait in inconsistent_traits:
                if trait in text:
                    char_context = self._extract_character_context(text, character)
                    if trait in char_context:
                        violation = FateViolation(
                            character=character,
                            violation_type=FateViolationType.CHARACTER_INCONSISTENCY,
                            severity="warning",
                            description=f"{character}的性格描述与原著不符：{trait}",
                            prophecy_reference="堪怜咏絮才 - 黛玉多愁善感，才华横溢",
                            suggested_fix=f"黛玉性格应体现多愁善感、才华横溢的特点",
                            confidence=0.7
                        )
                        violations.append(violation)
        
        return violations
    
    def _check_symbol_violations(self, text: str, character: str) -> List[FateViolation]:
        """检查象征意象违背"""
        violations = []
        character_symbols = self.symbolic_meanings.get(character, [])
        
        # 检查是否误用了其他角色的象征元素
        for other_char, other_symbols in self.symbolic_meanings.items():
            if other_char != character:
                for symbol_info in other_symbols:
                    symbol = symbol_info["element"]
                    if symbol in text and character in text:
                        # 检查是否在描述该角色时误用了其他角色的象征
                        char_context = self._extract_character_context(text, character)
                        if symbol in char_context:
                            violation = FateViolation(
                                character=character,
                                violation_type=FateViolationType.SYMBOL_MISUSE,
                                severity="suggestion",
                                description=f"在描述{character}时使用了{other_char}的象征元素：{symbol}",
                                prophecy_reference=f"{symbol}是{other_char}的专属象征",
                                suggested_fix=f"建议使用{character}自己的象征元素：{[s['element'] for s in character_symbols]}",
                                confidence=0.6
                            )
                            violations.append(violation)
        
        return violations
    
    def _check_emotional_tone(self, text: str, character: str, fate_data: Dict[str, Any]) -> List[FateViolation]:
        """检查情感基调一致性"""
        violations = []
        
        # 根据命运判断应有的情感基调
        fate_summary = fate_data.get("fate_summary", "")
        expected_tone = "tragic"  # 红楼梦总体是悲剧基调
        
        # 检查是否有过于欢快的描述
        cheerful_patterns = ["欢声笑语", "其乐融融", "幸福美满", "笑容满面", "喜气洋洋"]
        for pattern in cheerful_patterns:
            if pattern in text and character in text:
                char_context = self._extract_character_context(text, character)
                if pattern in char_context:
                    violation = FateViolation(
                        character=character,
                        violation_type=FateViolationType.EMOTIONAL_TONE_MISMATCH,
                        severity="suggestion",
                        description=f"{character}的情感基调过于欢快，与悲剧命运不符：{pattern}",
                        prophecy_reference=fate_summary,
                        suggested_fix="建议采用更符合悲剧美学的情感表达",
                        confidence=0.5
                    )
                    violations.append(violation)
        
        return violations
    
    def _extract_character_context(self, text: str, character: str) -> str:
        """提取角色相关的上下文"""
        # 找到角色出现的位置，提取前后各50个字符作为上下文
        char_positions = []
        start = 0
        while True:
            pos = text.find(character, start)
            if pos == -1:
                break
            char_positions.append(pos)
            start = pos + 1
        
        contexts = []
        for pos in char_positions:
            start_pos = max(0, pos - 50)
            end_pos = min(len(text), pos + len(character) + 50)
            context = text[start_pos:end_pos]
            contexts.append(context)
        
        return " ".join(contexts)
    
    def _calculate_character_score(self, violations: List[FateViolation]) -> float:
        """计算角色一致性评分"""
        if not violations:
            return 100.0
        
        total_penalty = 0
        for violation in violations:
            if violation.severity == "critical":
                total_penalty += 30 * violation.confidence
            elif violation.severity == "warning":
                total_penalty += 20 * violation.confidence
            elif violation.severity == "suggestion":
                total_penalty += 10 * violation.confidence
        
        score = max(0, 100 - total_penalty)
        return score
    
    def _calculate_overall_score(self, violations: List[FateViolation], character_scores: Dict[str, float]) -> float:
        """计算总体一致性评分"""
        if not character_scores:
            return 100.0
        
        # 基于角色评分的加权平均
        total_score = sum(character_scores.values())
        average_score = total_score / len(character_scores)
        
        # 考虑严重违背的额外惩罚
        critical_violations = [v for v in violations if v.severity == "critical"]
        if critical_violations:
            penalty = len(critical_violations) * 10
            average_score = max(0, average_score - penalty)
        
        return round(average_score, 1)
    
    def _calculate_aspect_scores(self, violations: List[FateViolation]) -> Dict[str, float]:
        """计算各方面评分"""
        aspects = {
            "命运轨迹": 100.0,
            "性格一致性": 100.0,
            "象征运用": 100.0,
            "情感基调": 100.0
        }
        
        for violation in violations:
            penalty = 20 * violation.confidence
            
            if violation.violation_type == FateViolationType.DESTINY_CONTRADICTION:
                aspects["命运轨迹"] = max(0, aspects["命运轨迹"] - penalty)
            elif violation.violation_type == FateViolationType.CHARACTER_INCONSISTENCY:
                aspects["性格一致性"] = max(0, aspects["性格一致性"] - penalty)
            elif violation.violation_type == FateViolationType.SYMBOL_MISUSE:
                aspects["象征运用"] = max(0, aspects["象征运用"] - penalty)
            elif violation.violation_type == FateViolationType.EMOTIONAL_TONE_MISMATCH:
                aspects["情感基调"] = max(0, aspects["情感基调"] - penalty)
        
        return {k: round(v, 1) for k, v in aspects.items()}
    
    def _generate_recommendations(self, violations: List[FateViolation], characters: Set[str]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于违背类型生成建议
        violation_types = [v.violation_type for v in violations]
        
        if FateViolationType.DESTINY_CONTRADICTION in violation_types:
            recommendations.append("请确保角色的命运发展符合太虚幻境判词的预言")
        
        if FateViolationType.CHARACTER_INCONSISTENCY in violation_types:
            recommendations.append("请保持角色性格与原著的一致性")
        
        if FateViolationType.SYMBOL_MISUSE in violation_types:
            recommendations.append("请使用角色专属的象征元素，避免混用其他角色的象征")
        
        if FateViolationType.EMOTIONAL_TONE_MISMATCH in violation_types:
            recommendations.append("请保持与红楼梦悲剧美学相符的情感基调")
        
        # 为涉及的角色提供具体建议
        for character in characters:
            if character in self.character_fates:
                fate_summary = self.character_fates[character]["fate_summary"]
                recommendations.append(f"对于{character}：建议参考判词预言 - {fate_summary}")
        
        return recommendations
    
    def get_fate_guidance(self, character: str, context: str = "") -> Optional[FateGuidance]:
        """获取角色命运指导"""
        if character not in self.character_fates:
            return None
        
        fate_data = self.character_fates[character]
        prophecy = fate_data["prophecy"]
        
        # 分析当前上下文
        current_situation = self._analyze_current_situation(context, character)
        
        # 获取判词暗示
        prophecy_hint = fate_data["fate_summary"]
        
        # 生成发展建议
        suggested_development = self._generate_development_suggestion(character, context, fate_data)
        
        # 推荐象征元素
        symbolic_elements = [s["element"] for s in self.symbolic_meanings.get(character, [])]
        
        # 推荐情感基调
        emotional_tone = prophecy.get("poem", {}).get("emotional_tone", "悲剧")
        
        return FateGuidance(
            character=character,
            current_situation=current_situation,
            prophecy_hint=prophecy_hint,
            suggested_development=suggested_development,
            symbolic_elements=symbolic_elements[:5],  # 限制数量
            emotional_tone=emotional_tone
        )
    
    def _analyze_current_situation(self, context: str, character: str) -> str:
        """分析当前情况"""
        if not context:
            return "未提供上下文"
        
        # 简单的情况分析
        char_context = self._extract_character_context(context, character)
        if len(char_context) > 100:
            return char_context[:100] + "..."
        return char_context or "未在上下文中发现该角色"
    
    def _generate_development_suggestion(self, character: str, context: str, fate_data: Dict[str, Any]) -> str:
        """生成发展建议"""
        fate_summary = fate_data["fate_summary"]
        key_events = fate_data.get("key_events", [])
        
        # 基于判词生成建议
        suggestions = []
        
        if "早逝" in fate_summary:
            suggestions.append("情节发展应暗示角色的脆弱和生命的短暂")
        elif "独守" in fate_summary:
            suggestions.append("应强调感情的冷寂和婚姻的不幸")
        elif "远嫁" in fate_summary:
            suggestions.append("可以暗示离别的伤感和身不由己的无奈")
        
        if key_events:
            suggestions.append(f"可以围绕这些关键事件展开：{', '.join(key_events[:3])}")
        
        return "；".join(suggestions) if suggestions else "请参考判词预言进行发展"
    
    def generate_consistency_report(self, score: ConsistencyScore, detailed: bool = True) -> str:
        """生成一致性检验报告"""
        report = []
        report.append("# 命运一致性检验报告")
        report.append("")
        
        # 总体评分
        score_emoji = "🎉" if score.overall_score >= 90 else "✅" if score.overall_score >= 70 else "⚠️" if score.overall_score >= 50 else "❌"
        report.append(f"## 总体评分: {score_emoji} {score.overall_score}/100")
        report.append("")
        
        # 各角色评分
        if score.character_scores:
            report.append("## 角色一致性评分")
            for character, char_score in score.character_scores.items():
                char_emoji = "✅" if char_score >= 80 else "⚠️" if char_score >= 60 else "❌"
                report.append(f"- **{character}**: {char_emoji} {char_score}/100")
            report.append("")
        
        # 各方面评分
        if score.aspect_scores:
            report.append("## 方面评分")
            for aspect, aspect_score in score.aspect_scores.items():
                aspect_emoji = "✅" if aspect_score >= 80 else "⚠️" if aspect_score >= 60 else "❌"
                report.append(f"- **{aspect}**: {aspect_emoji} {aspect_score}/100")
            report.append("")
        
        # 违背检测
        if score.violations:
            report.append("## 检测到的问题")
            
            critical_violations = [v for v in score.violations if v.severity == "critical"]
            warning_violations = [v for v in score.violations if v.severity == "warning"]
            suggestion_violations = [v for v in score.violations if v.severity == "suggestion"]
            
            if critical_violations:
                report.append("### ❌ 严重问题")
                for violation in critical_violations:
                    report.append(f"- **{violation.character}**: {violation.description}")
                    if detailed:
                        report.append(f"  - 判词参考: {violation.prophecy_reference}")
                        report.append(f"  - 修正建议: {violation.suggested_fix}")
                report.append("")
            
            if warning_violations:
                report.append("### ⚠️ 警告事项")
                for violation in warning_violations:
                    report.append(f"- **{violation.character}**: {violation.description}")
                    if detailed:
                        report.append(f"  - 修正建议: {violation.suggested_fix}")
                report.append("")
            
            if suggestion_violations:
                report.append("### 💡 优化建议")
                for violation in suggestion_violations:
                    report.append(f"- **{violation.character}**: {violation.description}")
                report.append("")
        
        # 改进建议
        if score.recommendations:
            report.append("## 总体建议")
            for i, recommendation in enumerate(score.recommendations, 1):
                report.append(f"{i}. {recommendation}")
            report.append("")
        
        # 评分说明
        if detailed:
            report.append("## 评分说明")
            report.append("- **90-100分**: 完全符合判词预言，角色命运一致")
            report.append("- **70-89分**: 基本符合，有轻微不一致")
            report.append("- **50-69分**: 部分符合，存在明显问题")
            report.append("- **50分以下**: 严重违背判词预言")
            report.append("")
        
        return "\n".join(report)
    
    def batch_check_characters(self, text: str) -> Dict[str, ConsistencyScore]:
        """批量检查多个角色的一致性"""
        detected_characters = self._extract_characters(text)
        results = {}
        
        for character in detected_characters:
            if character in self.character_fates:
                score = self.check_consistency(text, [character])
                results[character] = score
        
        return results


def main():
    """主函数，用于测试命运一致性检验功能"""
    checker = FateConsistencyChecker()
    
    # 测试文本
    test_texts = [
        "林黛玉与宝玉结为夫妻，从此过上了幸福美满的生活，两人白头偕老，儿孙满堂。",  # 违背命运
        "薛宝钗独守空房，丈夫宝玉出家后，她终日以泪洗面，度过了孤独的余生。",      # 符合命运
        "贾探春在家中发挥才能，管理家务，最终改变了贾府的命运。",                  # 部分违背
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n=== 测试文本 {i} ===")
        print(f"内容: {text}")
        
        score = checker.check_consistency(text)
        report = checker.generate_consistency_report(score, detailed=False)
        print(report)
        
        # 获取指导建议
        for character in score.character_scores.keys():
            guidance = checker.get_fate_guidance(character, text)
            if guidance:
                print(f"\n{character}的命运指导:")
                print(f"- 判词暗示: {guidance.prophecy_hint}")
                print(f"- 建议发展: {guidance.suggested_development}")


if __name__ == "__main__":
    main() 