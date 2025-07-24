"""
章节间信息传递机制

处理章节之间的状态传递、信息继承和一致性维护，
确保40回续写的连贯性和逻辑一致性。

Author: AI Assistant
Date: 2025-07-23
"""

import json
import logging
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Set, Any
from pathlib import Path
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class CharacterStatus(Enum):
    """人物状态枚举"""
    HEALTHY = "健康"
    ILL = "生病"
    PREGNANT = "怀孕"
    DECEASED = "已故"
    MISSING = "失踪"
    TRAVELING = "外出"
    CONFINED = "禁足"
    UNKNOWN = "未知"

class PlotStatus(Enum):
    """情节状态枚举"""
    ONGOING = "进行中"
    RESOLVED = "已解决"
    SUSPENDED = "暂停"
    INTRODUCED = "新引入"
    ESCALATED = "升级"
    CONCLUDED = "结束"

class RelationshipType(Enum):
    """关系类型枚举"""
    FAMILY = "家族"
    MARRIAGE = "婚姻"
    FRIENDSHIP = "友谊"
    ROMANTIC = "恋情"
    MASTER_SERVANT = "主仆"
    RIVALRY = "对立"
    ALLIANCE = "联盟"

@dataclass
class CharacterState:
    """人物状态信息"""
    name: str
    status: CharacterStatus
    location: str
    emotional_state: str
    physical_condition: str
    social_position: str
    key_concerns: List[str]
    relationships: Dict[str, str]  # 其他人物 -> 关系描述
    last_significant_action: str
    fate_progress: float  # 命运实现进度 0-1
    
class PlotThread:
    """情节线程"""
    def __init__(self, thread_id: str, title: str, description: str, 
                 status: PlotStatus, participants: List[str]):
        self.thread_id = thread_id
        self.title = title
        self.description = description
        self.status = status
        self.participants = participants
        self.key_events: List[str] = []
        self.unresolved_issues: List[str] = []
        self.expected_resolution: Optional[str] = None
        self.priority_level: int = 1  # 1-5, 5最重要

@dataclass
class EnvironmentState:
    """环境状态信息"""
    primary_location: str
    secondary_locations: List[str]
    season: str
    weather: str
    time_of_day: str
    social_atmosphere: str
    political_situation: str
    economic_condition: str

@dataclass
class LiteraryElements:
    """文学元素信息"""
    symbolic_imagery: List[str]  # 象征意象
    metaphors_used: List[str]    # 使用的隐喻
    foreshadowing: List[str]     # 伏笔设置
    recurring_motifs: List[str]  # 重复主题
    poetic_references: List[str] # 诗词引用
    cultural_allusions: List[str] # 文化典故

@dataclass 
class ChapterState:
    """完整的章节状态信息"""
    chapter_number: int
    chapter_title: str
    timestamp: str
    character_states: Dict[str, CharacterState]
    plot_threads: Dict[str, PlotThread]
    environment: EnvironmentState
    literary_elements: LiteraryElements
    key_dialogues: List[str]
    unresolved_questions: List[str]
    continuation_notes: List[str]  # 续写注意事项
    quality_score: float  # 章节质量评分
    consistency_issues: List[str]  # 发现的一致性问题

class ChapterInfoTransfer:
    """章节间信息传递机制"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.states_dir = Path("data/processed/chapter_states")
        self.states_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化人物关系映射
        self.character_relationships = self._load_character_relationships()
        
        # 初始化情节线程追踪
        self.active_plot_threads: Dict[str, PlotThread] = {}
        
        logger.info("章节信息传递机制初始化完成")
    
    def extract_chapter_state(self, chapter_number: int, chapter_content: str, 
                            chapter_title: str = "") -> ChapterState:
        """
        从章节内容中提取状态信息
        
        Args:
            chapter_number: 章节号
            chapter_content: 章节内容文本
            chapter_title: 章节标题
            
        Returns:
            提取的章节状态信息
        """
        logger.info(f"开始提取第{chapter_number}回状态信息")
        
        # 提取人物状态
        character_states = self._extract_character_states(chapter_content)
        
        # 提取情节线程
        plot_threads = self._extract_plot_threads(chapter_content, chapter_number)
        
        # 提取环境状态
        environment = self._extract_environment_state(chapter_content)
        
        # 提取文学元素
        literary_elements = self._extract_literary_elements(chapter_content)
        
        # 提取关键对话
        key_dialogues = self._extract_key_dialogues(chapter_content)
        
        # 识别未解决问题
        unresolved_questions = self._identify_unresolved_questions(chapter_content)
        
        # 生成续写注意事项
        continuation_notes = self._generate_continuation_notes(
            character_states, plot_threads, unresolved_questions
        )
        
        # 创建章节状态
        chapter_state = ChapterState(
            chapter_number=chapter_number,
            chapter_title=chapter_title,
            timestamp=datetime.now().isoformat(),
            character_states=character_states,
            plot_threads=plot_threads,
            environment=environment,
            literary_elements=literary_elements,
            key_dialogues=key_dialogues,
            unresolved_questions=unresolved_questions,
            continuation_notes=continuation_notes,
            quality_score=0.0,  # 待评估
            consistency_issues=[]  # 待检查
        )
        
        logger.info(f"成功提取第{chapter_number}回状态信息，包含{len(character_states)}个人物")
        return chapter_state
    
    def _extract_character_states(self, content: str) -> Dict[str, CharacterState]:
        """提取人物状态信息"""
        character_states = {}
        
        # 预定义的主要人物列表
        major_characters = [
            "贾宝玉", "林黛玉", "薛宝钗", "王熙凤", "贾母", "王夫人", 
            "贾政", "贾琏", "贾珍", "贾蓉", "秦可卿", "贾迎春", 
            "贾探春", "贾惜春", "史湘云", "妙玉", "贾巧姐", "李纨",
            "晴雯", "袭人", "紫鹃", "平儿", "香菱", "鸳鸯"
        ]
        
        for character in major_characters:
            if character in content:
                # 分析该人物在本章节中的状态
                character_context = self._extract_character_context(content, character)
                
                if character_context:
                    state = CharacterState(
                        name=character,
                        status=self._determine_character_status(character_context, character),
                        location=self._extract_character_location(character_context),
                        emotional_state=self._analyze_emotional_state(character_context),
                        physical_condition=self._analyze_physical_condition(character_context),
                        social_position=self._determine_social_position(character),
                        key_concerns=self._extract_key_concerns(character_context),
                        relationships=self._extract_relationships(character_context, character),
                        last_significant_action=self._extract_last_action(character_context),
                        fate_progress=self._calculate_fate_progress(character)
                    )
                    character_states[character] = state
        
        return character_states
    
    def _extract_character_context(self, content: str, character: str) -> str:
        """提取特定人物的相关上下文"""
        sentences = re.split(r'[。！？]', content)
        character_sentences = [s for s in sentences if character in s]
        return '。'.join(character_sentences[:10])  # 取前10句相关内容
    
    def _determine_character_status(self, context: str, character: str) -> CharacterStatus:
        """判断人物状态"""
        # 关键词映射
        status_keywords = {
            CharacterStatus.ILL: ["病", "疾", "不适", "虚弱", "咳嗽", "发热"],
            CharacterStatus.DECEASED: ["死", "亡", "逝", "殒", "归天", "命终"],
            CharacterStatus.TRAVELING: ["出门", "远行", "外出", "游历", "离家"],
            CharacterStatus.CONFINED: ["禁足", "关闭", "不出", "闭门"],
            CharacterStatus.PREGNANT: ["有孕", "怀胎", "身孕", "妊娠"]
        }
        
        for status, keywords in status_keywords.items():
            if any(keyword in context for keyword in keywords):
                return status
        
        return CharacterStatus.HEALTHY
    
    def _extract_character_location(self, context: str) -> str:
        """提取人物位置"""
        # 常见地点模式
        location_patterns = [
            r'在([^，。！？]{2,8}?[院房楼阁园轩堂斋])',
            r'到([^，。！？]{2,8}?[院房楼阁园轩堂斋])',
            r'([^，。！？]{2,8}?[院房楼阁园轩堂斋])里',
            r'([^，。！？]{2,8}?[院房楼阁园轩堂斋])中'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, context)
            if match:
                return match.group(1)
        
        return "未明确"
    
    def _analyze_emotional_state(self, context: str) -> str:
        """分析情感状态"""
        emotion_keywords = {
            "喜悦": ["喜", "乐", "笑", "欢", "悦", "兴"],
            "悲伤": ["悲", "哭", "泣", "泪", "伤", "愁"],
            "愤怒": ["怒", "怒", "恨", "气", "恼", "愤"],
            "焦虑": ["急", "慌", "忧", "虑", "不安", "惊"],
            "平静": ["静", "安", "稳", "和", "淡", "宁"]
        }
        
        for emotion, keywords in emotion_keywords.items():
            if any(keyword in context for keyword in keywords):
                return emotion
        
        return "平常"
    
    def _analyze_physical_condition(self, context: str) -> str:
        """分析身体状况"""
        condition_keywords = {
            "虚弱": ["虚", "弱", "疲", "乏", "困"],
            "健康": ["健", "壮", "好", "佳", "康"],
            "患病": ["病", "疾", "症", "痛", "不适"]
        }
        
        for condition, keywords in condition_keywords.items():
            if any(keyword in context for keyword in keywords):
                return condition
        
        return "正常"
    
    def _determine_social_position(self, character: str) -> str:
        """确定社会地位"""
        position_map = {
            "贾母": "老祖宗", "王夫人": "二太太", "王熙凤": "琏二奶奶",
            "贾宝玉": "二爷", "林黛玉": "姑娘", "薛宝钗": "姑娘",
            "贾政": "老爷", "贾琏": "二爷", "晴雯": "丫鬟",
            "袭人": "丫鬟", "紫鹃": "丫鬟", "平儿": "姨娘"
        }
        return position_map.get(character, "人物")
    
    def _extract_key_concerns(self, context: str) -> List[str]:
        """提取关键关注点"""
        concerns = []
        
        # 关注点关键词
        concern_patterns = [
            r'担心([^，。！？]{2,10})',
            r'忧虑([^，。！？]{2,10})',
            r'关心([^，。！？]{2,10})',
            r'在意([^，。！？]{2,10})',
            r'思念([^，。！？]{2,10})'
        ]
        
        for pattern in concern_patterns:
            matches = re.findall(pattern, context)
            concerns.extend(matches)
        
        return concerns[:5]  # 返回前5个关注点
    
    def _extract_relationships(self, context: str, character: str) -> Dict[str, str]:
        """提取人物关系"""
        relationships = {}
        
        # 关系词汇
        relationship_patterns = [
            r'和([^，。！？]{2,5})([^，。！？]{2,8})',
            r'对([^，。！？]{2,5})([^，。！？]{2,8})',
            r'与([^，。！？]{2,5})([^，。！？]{2,8})'
        ]
        
        for pattern in relationship_patterns:
            matches = re.findall(pattern, context)
            for match in matches:
                if len(match) == 2:
                    other_person, relation = match
                    if other_person != character and len(other_person) <= 4:
                        relationships[other_person] = relation
        
        return dict(list(relationships.items())[:5])  # 返回前5个关系
    
    def _extract_last_action(self, context: str) -> str:
        """提取最后重要行动"""
        # 行动动词
        action_patterns = [
            r'([^，。！？]{2,10}[了着过])',
            r'(说[^，。！？]{2,20})',
            r'(去[^，。！？]{2,10})',
            r'(来[^，。！？]{2,10})'
        ]
        
        for pattern in action_patterns:
            match = re.search(pattern, context[-200:])  # 在最后200字符中查找
            if match:
                return match.group(1)
        
        return "未明确行动"
    
    def _calculate_fate_progress(self, character: str) -> float:
        """计算命运实现进度"""
        # 这里可以与太虚幻境判词系统集成
        # 暂时返回默认值
        return 0.0
    
    def _extract_plot_threads(self, content: str, chapter_number: int) -> Dict[str, PlotThread]:
        """提取情节线程"""
        plot_threads = {}
        
        # 识别情节关键词
        plot_keywords = [
            "事情", "事件", "问题", "矛盾", "冲突", "计划", 
            "阴谋", "秘密", "传言", "流言", "决定", "安排"
        ]
        
        thread_id = 1
        for keyword in plot_keywords:
            if keyword in content:
                # 提取相关上下文
                thread_context = self._extract_plot_context(content, keyword)
                if thread_context:
                    thread = PlotThread(
                        thread_id=f"ch{chapter_number}_thread_{thread_id}",
                        title=f"{keyword}相关情节",
                        description=thread_context[:100],  # 前100字符作为描述
                        status=PlotStatus.ONGOING,
                        participants=self._extract_plot_participants(thread_context)
                    )
                    plot_threads[thread.thread_id] = thread
                    thread_id += 1
        
        return plot_threads
    
    def _extract_plot_context(self, content: str, keyword: str) -> str:
        """提取情节上下文"""
        sentences = re.split(r'[。！？]', content)
        relevant_sentences = [s for s in sentences if keyword in s]
        return '。'.join(relevant_sentences[:3])  # 取前3句
    
    def _extract_plot_participants(self, context: str) -> List[str]:
        """提取情节参与者"""
        major_characters = [
            "贾宝玉", "林黛玉", "薛宝钗", "王熙凤", "贾母", "王夫人", 
            "贾政", "贾琏", "贾珍", "贾蓉", "秦可卿"
        ]
        
        participants = []
        for character in major_characters:
            if character in context:
                participants.append(character)
        
        return participants
    
    def _extract_environment_state(self, content: str) -> EnvironmentState:
        """提取环境状态"""
        return EnvironmentState(
            primary_location=self._extract_primary_location(content),
            secondary_locations=self._extract_secondary_locations(content),
            season=self._extract_season(content),
            weather=self._extract_weather(content),
            time_of_day=self._extract_time(content),
            social_atmosphere=self._analyze_social_atmosphere(content),
            political_situation="平稳",  # 默认值
            economic_condition="正常"   # 默认值
        )
    
    def _extract_primary_location(self, content: str) -> str:
        """提取主要地点"""
        location_patterns = [
            r'([^，。！？]{2,8}?[院房楼阁园轩堂斋])',
            r'(贾府|荣国府|宁国府|大观园)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, content[:200])  # 在前200字符中查找
            if match:
                return match.group(1)
        
        return "贾府"
    
    def _extract_secondary_locations(self, content: str) -> List[str]:
        """提取次要地点"""
        locations = []
        location_pattern = r'([^，。！？]{2,8}?[院房楼阁园轩堂斋])'
        matches = re.findall(location_pattern, content)
        return list(set(matches))[:5]  # 返回不重复的前5个地点
    
    def _extract_season(self, content: str) -> str:
        """提取季节"""
        season_keywords = {
            "春": ["春", "花开", "柳绿", "暖"],
            "夏": ["夏", "炎热", "荷花", "蝉"],
            "秋": ["秋", "凉", "落叶", "菊"],
            "冬": ["冬", "雪", "寒", "梅"]
        }
        
        for season, keywords in season_keywords.items():
            if any(keyword in content for keyword in keywords):
                return season
        
        return "未明确"
    
    def _extract_weather(self, content: str) -> str:
        """提取天气"""
        weather_keywords = [
            "晴", "雨", "雪", "阴", "风", "雾", "霜", "露"
        ]
        
        for keyword in weather_keywords:
            if keyword in content:
                return keyword
        
        return "未明确"
    
    def _extract_time(self, content: str) -> str:
        """提取时间"""
        time_patterns = [
            r'(早|晨|午|晚|夜|子|丑|寅|卯|辰|巳|午|未|申|酉|戌|亥)时?',
            r'(黎明|清晨|上午|中午|下午|傍晚|夜晚|深夜)'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return "未明确"
    
    def _analyze_social_atmosphere(self, content: str) -> str:
        """分析社会氛围"""
        atmosphere_keywords = {
            "紧张": ["紧张", "压抑", "不安", "忧虑"],
            "欢乐": ["欢乐", "快乐", "喜庆", "热闹"],
            "悲伤": ["悲伤", "哀愁", "凄凉", "萧瑟"],
            "平静": ["平静", "安宁", "和谐", "安详"]
        }
        
        for atmosphere, keywords in atmosphere_keywords.items():
            if any(keyword in content for keyword in keywords):
                return atmosphere
        
        return "正常"
    
    def _extract_literary_elements(self, content: str) -> LiteraryElements:
        """提取文学元素"""
        return LiteraryElements(
            symbolic_imagery=self._extract_symbolic_imagery(content),
            metaphors_used=self._extract_metaphors(content),
            foreshadowing=self._extract_foreshadowing(content),
            recurring_motifs=self._extract_motifs(content),
            poetic_references=self._extract_poetry(content),
            cultural_allusions=self._extract_allusions(content)
        )
    
    def _extract_symbolic_imagery(self, content: str) -> List[str]:
        """提取象征意象"""
        symbols = []
        symbolic_items = [
            "花", "月", "雪", "风", "雨", "梦", "镜", "水", "玉", "石",
            "鸟", "燕", "鸿", "蝶", "梅", "兰", "竹", "菊", "桃", "柳"
        ]
        
        for symbol in symbolic_items:
            if symbol in content:
                symbols.append(symbol)
        
        return symbols[:10]  # 返回前10个象征
    
    def _extract_metaphors(self, content: str) -> List[str]:
        """提取隐喻"""
        metaphor_patterns = [
            r'如([^，。！？]{2,10})',
            r'似([^，。！？]{2,10})',
            r'像([^，。！？]{2,10})',
            r'比作([^，。！？]{2,10})'
        ]
        
        metaphors = []
        for pattern in metaphor_patterns:
            matches = re.findall(pattern, content)
            metaphors.extend(matches)
        
        return metaphors[:5]
    
    def _extract_foreshadowing(self, content: str) -> List[str]:
        """提取伏笔"""
        # 伏笔通常包含暗示性词汇
        foreshadowing_keywords = [
            "将来", "日后", "他日", "异日", "不久", "早晚", "总有一天"
        ]
        
        foreshadowing = []
        for keyword in foreshadowing_keywords:
            if keyword in content:
                # 提取包含该关键词的句子
                sentences = re.split(r'[。！？]', content)
                for sentence in sentences:
                    if keyword in sentence:
                        foreshadowing.append(sentence.strip())
                        break
        
        return foreshadowing[:3]
    
    def _extract_motifs(self, content: str) -> List[str]:
        """提取重复主题"""
        motifs = []
        motif_keywords = [
            "命运", "因缘", "缘分", "宿命", "天意", "注定",
            "情", "爱", "恨", "离", "别", "聚", "散"
        ]
        
        for motif in motif_keywords:
            if motif in content:
                motifs.append(motif)
        
        return motifs[:5]
    
    def _extract_poetry(self, content: str) -> List[str]:
        """提取诗词引用"""
        # 查找诗词格式的内容
        poetry_patterns = [
            r'[""]([\s\S]{10,50})[""]\s*$',  # 引号包围的诗句
            r'([^，。！？]{4,8}，[^，。！？]{4,8})',  # 对联格式
        ]
        
        poetry = []
        for pattern in poetry_patterns:
            matches = re.findall(pattern, content)
            poetry.extend(matches)
        
        return poetry[:3]
    
    def _extract_allusions(self, content: str) -> List[str]:
        """提取文化典故"""
        allusion_keywords = [
            "古人", "古语", "俗话", "传说", "典故", "史记", "诗经", "论语"
        ]
        
        allusions = []
        for keyword in allusion_keywords:
            if keyword in content:
                # 提取相关上下文
                index = content.find(keyword)
                if index != -1:
                    context = content[max(0, index-20):index+50]
                    allusions.append(context)
        
        return allusions[:3]
    
    def _extract_key_dialogues(self, content: str) -> List[str]:
        """提取关键对话"""
        # 查找对话格式
        dialogue_patterns = [
            r'["""]([\s\S]{10,100})["""]',  # 引号内的对话
            r'([^，。！？]{2,6})[道说][:：]["""]([\s\S]{10,100})["""]'  # 某人说："..."
        ]
        
        dialogues = []
        for pattern in dialogue_patterns:
            matches = re.findall(pattern, content)
            if matches:  # 确保matches不为空
                if isinstance(matches[0], tuple):
                    dialogues.extend([f"{m[0]}：{m[1]}" for m in matches])
                else:
                    dialogues.extend(matches)
        
        return dialogues[:5]  # 返回前5段重要对话
    
    def _identify_unresolved_questions(self, content: str) -> List[str]:
        """识别未解决问题"""
        questions = []
        
        # 疑问句模式
        question_patterns = [
            r'([^，。！？]{5,30}?[吗呢么]？?)',
            r'([^，。！？]{5,30}?如何)',
            r'([^，。！？]{5,30}?怎么)',
            r'为何([^，。！？]{5,30})',
            r'何时([^，。！？]{5,30})'
        ]
        
        for pattern in question_patterns:
            matches = re.findall(pattern, content)
            questions.extend(matches)
        
        # 未完成事项
        incomplete_patterns = [
            r'尚未([^，。！？]{5,20})',
            r'还要([^，。！？]{5,20})',
            r'仍需([^，。！？]{5,20})',
            r'待([^，。！？]{5,20})'
        ]
        
        for pattern in incomplete_patterns:
            matches = re.findall(pattern, content)
            questions.extend([f"未完成：{m}" for m in matches])
        
        return questions[:10]
    
    def _generate_continuation_notes(self, character_states: Dict[str, CharacterState],
                                   plot_threads: Dict[str, PlotThread],
                                   unresolved_questions: List[str]) -> List[str]:
        """生成续写注意事项"""
        notes = []
        
        # 基于人物状态生成注意事项
        for name, state in character_states.items():
            if state.status in [CharacterStatus.ILL, CharacterStatus.DECEASED]:
                notes.append(f"注意{name}的{state.status.value}状态，影响后续情节发展")
            
            if state.key_concerns:
                notes.append(f"{name}关注：{', '.join(state.key_concerns[:2])}")
        
        # 基于情节线程生成注意事项
        for thread_id, thread in plot_threads.items():
            if thread.status == PlotStatus.ONGOING:
                notes.append(f"继续推进：{thread.title}")
        
        # 基于未解决问题生成注意事项
        for question in unresolved_questions[:3]:
            notes.append(f"需要解答：{question}")
        
        return notes[:10]
    
    def pass_info_to_next(self, current_state, 
                         next_chapter_plan: Dict) -> Dict[str, Any]:
        """
        将当前章节状态信息传递给下一章节
        
        Args:
            current_state: 当前章节状态
            next_chapter_plan: 下一章节规划
            
        Returns:
            下一章节的写作指导信息
        """
        # 处理字典格式的状态数据
        if isinstance(current_state, dict):
            chapter_number = current_state.get("chapter_number", 0)
            character_states = current_state.get("character_states", {})
            plot_threads = current_state.get("plot_threads", {})
            environment = current_state.get("environment", {})
            literary_elements = current_state.get("literary_elements", {})
        else:
            # ChapterState对象
            chapter_number = current_state.chapter_number
            character_states = current_state.character_states
            plot_threads = current_state.plot_threads
            environment = current_state.environment
            literary_elements = current_state.literary_elements
        
        logger.info(f"传递第{chapter_number}回信息到第{chapter_number + 1}回")
        
        guidance = {
            "chapter_number": chapter_number + 1,
            "inherited_character_states": {},
            "continuing_plot_threads": {},
            "environmental_continuity": {},
            "literary_continuity": {},
            "writing_guidelines": [],
            "consistency_requirements": []
        }
        
        # 传递人物状态
        for name, state in character_states.items():
            if isinstance(state, dict):
                # 字典格式
                guidance["inherited_character_states"][name] = {
                    "last_status": state.get("status", "未知"),
                    "last_location": state.get("location", "未明确"),
                    "emotional_state": state.get("emotional_state", "平常"),
                    "key_concerns": state.get("key_concerns", []),
                    "relationships": state.get("relationships", {}),
                    "fate_progress": state.get("fate_progress", 0.0)
                }
            else:
                # CharacterState对象
                guidance["inherited_character_states"][name] = {
                    "last_status": state.status.value,
                    "last_location": state.location,
                    "emotional_state": state.emotional_state,
                    "key_concerns": state.key_concerns,
                    "relationships": state.relationships,
                    "fate_progress": state.fate_progress
                }
        
        # 传递情节线程
        for thread_id, thread in plot_threads.items():
            if isinstance(thread, dict):
                # 字典格式
                status = thread.get("status", "进行中")
                if status in ["进行中", "新引入"]:
                    guidance["continuing_plot_threads"][thread_id] = {
                        "title": thread.get("title", ""),
                        "description": thread.get("description", ""),
                        "participants": thread.get("participants", []),
                        "status": status,
                        "expected_development": "待续"
                    }
            else:
                # PlotThread对象
                if thread.status in [PlotStatus.ONGOING, PlotStatus.INTRODUCED]:
                    guidance["continuing_plot_threads"][thread_id] = {
                        "title": thread.title,
                        "description": thread.description,
                        "participants": thread.participants,
                        "status": thread.status.value,
                        "expected_development": "待续"
                    }
        
        # 传递环境连续性
        if isinstance(environment, dict):
            guidance["environmental_continuity"] = {
                "season": environment.get("season", "未明确"),
                "location": environment.get("primary_location", "贾府"),
                "social_atmosphere": environment.get("social_atmosphere", "正常")
            }
        else:
            guidance["environmental_continuity"] = {
                "season": environment.season,
                "location": environment.primary_location,
                "social_atmosphere": environment.social_atmosphere
            }
        
        # 传递文学连续性
        if isinstance(literary_elements, dict):
            guidance["literary_continuity"] = {
                "recurring_motifs": literary_elements.get("recurring_motifs", []),
                "symbolic_imagery": literary_elements.get("symbolic_imagery", []),
                "foreshadowing_to_fulfill": literary_elements.get("foreshadowing", [])
            }
        else:
            guidance["literary_continuity"] = {
                "recurring_motifs": literary_elements.recurring_motifs,
                "symbolic_imagery": literary_elements.symbolic_imagery,
                "foreshadowing_to_fulfill": literary_elements.foreshadowing
            }
        
        # 生成写作指导
        guidance["writing_guidelines"] = self._generate_writing_guidelines_dict(
            character_states, plot_threads, current_state, next_chapter_plan
        )
        
        # 生成一致性要求
        guidance["consistency_requirements"] = self._generate_consistency_requirements_dict(
            character_states, environment, literary_elements
        )
        
        logger.info(f"成功生成第{guidance['chapter_number']}回写作指导")
        return guidance
    
    def _generate_writing_guidelines(self, current_state: ChapterState, 
                                   next_plan: Dict) -> List[str]:
        """生成写作指导"""
        guidelines = []
        
        # 人物发展指导
        guidelines.append("人物发展指导：")
        for name, state in current_state.character_states.items():
            if state.key_concerns:
                guidelines.append(f"- {name}需关注：{', '.join(state.key_concerns[:2])}")
        
        # 情节发展指导
        ongoing_plots = [t for t in current_state.plot_threads.values() 
                        if t.status == PlotStatus.ONGOING]
        if ongoing_plots:
            guidelines.append("情节发展指导：")
            for plot in ongoing_plots[:3]:
                guidelines.append(f"- 继续推进：{plot.title}")
        
        # 未解决问题指导
        if current_state.unresolved_questions:
            guidelines.append("未解决问题：")
            for question in current_state.unresolved_questions[:3]:
                guidelines.append(f"- 需要处理：{question}")
        
        return guidelines
    
    def _generate_consistency_requirements(self, current_state: ChapterState) -> List[str]:
        """生成一致性要求"""
        requirements = []
        
        # 人物一致性要求
        requirements.append("人物一致性要求：")
        for name, state in current_state.character_states.items():
            requirements.append(
                f"- {name}应保持{state.emotional_state}情绪和{state.physical_condition}状态"
            )
        
        # 环境一致性要求
        requirements.append("环境一致性要求：")
        env = current_state.environment
        requirements.append(f"- 保持{env.season}季{env.weather}天气的环境设定")
        requirements.append(f"- 维持{env.social_atmosphere}的社会氛围")
        
        # 文学一致性要求
        if current_state.literary_elements.recurring_motifs:
            requirements.append("文学一致性要求：")
            motifs = current_state.literary_elements.recurring_motifs[:3]
            requirements.append(f"- 呼应主题：{', '.join(motifs)}")
        
        return requirements
    
    def _generate_writing_guidelines_dict(self, character_states, plot_threads, 
                                        current_state, next_plan) -> List[str]:
        """生成写作指导（处理字典格式）"""
        guidelines = []
        
        # 人物发展指导
        guidelines.append("人物发展指导：")
        for name, state in character_states.items():
            if isinstance(state, dict):
                key_concerns = state.get("key_concerns", [])
            else:
                key_concerns = state.key_concerns
            
            if key_concerns:
                guidelines.append(f"- {name}需关注：{', '.join(key_concerns[:2])}")
        
        # 情节发展指导
        ongoing_plots = []
        for thread_id, thread in plot_threads.items():
            if isinstance(thread, dict):
                status = thread.get("status", "")
                title = thread.get("title", "")
                if status == "进行中":
                    ongoing_plots.append(title)
            else:
                if thread.status == PlotStatus.ONGOING:
                    ongoing_plots.append(thread.title)
        
        if ongoing_plots:
            guidelines.append("情节发展指导：")
            for plot in ongoing_plots[:3]:
                guidelines.append(f"- 继续推进：{plot}")
        
        # 未解决问题指导
        if isinstance(current_state, dict):
            unresolved_questions = current_state.get("unresolved_questions", [])
        else:
            unresolved_questions = current_state.unresolved_questions
            
        if unresolved_questions:
            guidelines.append("未解决问题：")
            for question in unresolved_questions[:3]:
                guidelines.append(f"- 需要处理：{question}")
        
        return guidelines
    
    def _generate_consistency_requirements_dict(self, character_states, 
                                              environment, literary_elements) -> List[str]:
        """生成一致性要求（处理字典格式）"""
        requirements = []
        
        # 人物一致性要求
        requirements.append("人物一致性要求：")
        for name, state in character_states.items():
            if isinstance(state, dict):
                emotional_state = state.get("emotional_state", "平常")
                physical_condition = state.get("physical_condition", "正常")
            else:
                emotional_state = state.emotional_state
                physical_condition = state.physical_condition
                
            requirements.append(
                f"- {name}应保持{emotional_state}情绪和{physical_condition}状态"
            )
        
        # 环境一致性要求
        requirements.append("环境一致性要求：")
        if isinstance(environment, dict):
            season = environment.get("season", "未明确")
            weather = environment.get("weather", "未明确")
            social_atmosphere = environment.get("social_atmosphere", "正常")
        else:
            season = environment.season
            weather = environment.weather
            social_atmosphere = environment.social_atmosphere
            
        requirements.append(f"- 保持{season}季{weather}天气的环境设定")
        requirements.append(f"- 维持{social_atmosphere}的社会氛围")
        
        # 文学一致性要求
        if isinstance(literary_elements, dict):
            recurring_motifs = literary_elements.get("recurring_motifs", [])
        else:
            recurring_motifs = literary_elements.recurring_motifs
            
        if recurring_motifs:
            requirements.append("文学一致性要求：")
            motifs = recurring_motifs[:3]
            requirements.append(f"- 呼应主题：{', '.join(motifs)}")
        
        return requirements
    
    def maintain_consistency(self, chapter_states) -> List[str]:
        """
        维护跨章节一致性
        
        Args:
            chapter_states: 多个章节的状态信息（可以是ChapterState对象或字典）
            
        Returns:
            发现的一致性问题列表
        """
        logger.info(f"检查{len(chapter_states)}个章节的一致性")
        
        issues = []
        
        if len(chapter_states) < 2:
            return issues
        
        # 检查人物状态一致性
        character_issues = self._check_character_consistency_dict(chapter_states)
        issues.extend(character_issues)
        
        # 检查情节一致性
        plot_issues = self._check_plot_consistency_dict(chapter_states)
        issues.extend(plot_issues)
        
        # 检查环境一致性
        env_issues = self._check_environment_consistency_dict(chapter_states)
        issues.extend(env_issues)
        
        # 检查时间线一致性
        timeline_issues = self._check_timeline_consistency_dict(chapter_states)
        issues.extend(timeline_issues)
        
        logger.info(f"发现{len(issues)}个一致性问题")
        return issues
    
    def _check_character_consistency_dict(self, states) -> List[str]:
        """检查人物一致性（处理字典格式）"""
        issues = []
        
        # 跟踪每个人物的状态变化
        character_timelines = {}
        
        for state in states:
            # 获取章节号和人物状态
            if isinstance(state, dict):
                chapter_number = state.get("chapter_number", 0)
                character_states = state.get("character_states", {})
            else:
                chapter_number = state.chapter_number
                character_states = state.character_states
            
            for name, char_state in character_states.items():
                if name not in character_timelines:
                    character_timelines[name] = []
                
                if isinstance(char_state, dict):
                    char_data = {
                        "chapter": chapter_number,
                        "status": char_state.get("status", "健康"),
                        "location": char_state.get("location", "未明确"),
                        "emotional_state": char_state.get("emotional_state", "平常")
                    }
                else:
                    char_data = {
                        "chapter": chapter_number,
                        "status": char_state.status.value if hasattr(char_state.status, 'value') else str(char_state.status),
                        "location": char_state.location,
                        "emotional_state": char_state.emotional_state
                    }
                
                character_timelines[name].append(char_data)
        
        # 检查不合理的状态变化
        for name, timeline in character_timelines.items():
            if len(timeline) < 2:
                continue
                
            for i in range(1, len(timeline)):
                prev_state = timeline[i-1]
                curr_state = timeline[i]
                
                # 检查死亡后复活问题
                if (prev_state["status"] == "已故" and 
                    curr_state["status"] != "已故"):
                    issues.append(
                        f"第{curr_state['chapter']}回：{name}在第{prev_state['chapter']}回已故，"
                        f"但第{curr_state['chapter']}回又出现"
                    )
        
        return issues
    
    def _check_plot_consistency_dict(self, states) -> List[str]:
        """检查情节一致性（处理字典格式）"""
        issues = []
        
        # 跟踪情节线程的发展
        plot_timeline = {}
        
        for state in states:
            if isinstance(state, dict):
                chapter_number = state.get("chapter_number", 0)
                plot_threads = state.get("plot_threads", {})
            else:
                chapter_number = state.chapter_number
                plot_threads = state.plot_threads
            
            for thread_id, thread in plot_threads.items():
                if thread_id not in plot_timeline:
                    plot_timeline[thread_id] = []
                
                if isinstance(thread, dict):
                    thread_data = {
                        "chapter": chapter_number,
                        "status": thread.get("status", "进行中"),
                        "description": thread.get("description", "")
                    }
                else:
                    thread_data = {
                        "chapter": chapter_number,
                        "status": thread.status.value if hasattr(thread.status, 'value') else str(thread.status),
                        "description": thread.description
                    }
                
                plot_timeline[thread_id].append(thread_data)
        
        # 检查情节发展的合理性
        for thread_id, timeline in plot_timeline.items():
            if len(timeline) < 2:
                continue
                
            for i in range(1, len(timeline)):
                prev_plot = timeline[i-1]
                curr_plot = timeline[i]
                
                # 检查已结束的情节是否又重新开始
                if (prev_plot["status"] == "结束" and 
                    curr_plot["status"] in ["进行中", "新引入"]):
                    issues.append(
                        f"第{curr_plot['chapter']}回：{thread_id}在第{prev_plot['chapter']}回"
                        f"已结束，但第{curr_plot['chapter']}回又重新开始"
                    )
        
        return issues
    
    def _check_environment_consistency_dict(self, states) -> List[str]:
        """检查环境一致性（处理字典格式）"""
        issues = []
        
        # 检查季节变化的合理性
        seasons = []
        for state in states:
            if isinstance(state, dict):
                chapter_number = state.get("chapter_number", 0)
                environment = state.get("environment", {})
                season = environment.get("season", "未明确")
            else:
                chapter_number = state.chapter_number
                season = state.environment.season
            
            if season != "未明确":
                seasons.append({
                    "chapter": chapter_number,
                    "season": season
                })
        
        # 检查季节跳跃
        season_order = ["春", "夏", "秋", "冬"]
        for i in range(1, len(seasons)):
            prev_season = seasons[i-1]["season"]
            curr_season = seasons[i]["season"]
            
            if prev_season in season_order and curr_season in season_order:
                prev_idx = season_order.index(prev_season)
                curr_idx = season_order.index(curr_season)
                
                # 检查是否跳过了太多季节
                if abs(curr_idx - prev_idx) > 2:
                    issues.append(
                        f"第{seasons[i]['chapter']}回：季节从{prev_season}直接跳到{curr_season}，"
                        f"变化过于突然"
                    )
        
        return issues
    
    def _check_timeline_consistency_dict(self, states) -> List[str]:
        """检查时间线一致性（处理字典格式）"""
        issues = []
        
        # 检查章节编号的连续性
        chapter_numbers = []
        for state in states:
            if isinstance(state, dict):
                chapter_numbers.append(state.get("chapter_number", 0))
            else:
                chapter_numbers.append(state.chapter_number)
        
        chapter_numbers.sort()
        
        for i in range(1, len(chapter_numbers)):
            if chapter_numbers[i] - chapter_numbers[i-1] > 1:
                issues.append(
                    f"章节编号从第{chapter_numbers[i-1]}回跳到第{chapter_numbers[i]}回，"
                    f"缺少中间章节"
                )
        
        return issues
    
    def _check_character_consistency(self, states: List[ChapterState]) -> List[str]:
        """检查人物一致性"""
        issues = []
        
        # 跟踪每个人物的状态变化
        character_timelines = {}
        
        for state in states:
            for name, char_state in state.character_states.items():
                if name not in character_timelines:
                    character_timelines[name] = []
                character_timelines[name].append({
                    "chapter": state.chapter_number,
                    "status": char_state.status,
                    "location": char_state.location,
                    "emotional_state": char_state.emotional_state
                })
        
        # 检查不合理的状态变化
        for name, timeline in character_timelines.items():
            if len(timeline) < 2:
                continue
                
            for i in range(1, len(timeline)):
                prev_state = timeline[i-1]
                curr_state = timeline[i]
                
                # 检查死亡后复活问题
                if (prev_state["status"] == CharacterStatus.DECEASED and 
                    curr_state["status"] != CharacterStatus.DECEASED):
                    issues.append(
                        f"第{curr_state['chapter']}回：{name}在第{prev_state['chapter']}回已故，"
                        f"但第{curr_state['chapter']}回又出现"
                    )
                
                # 检查不合理的位置跳转
                if (prev_state["location"] != "未明确" and curr_state["location"] != "未明确" and
                    prev_state["location"] != curr_state["location"]):
                    # 简单的距离检查（这里可以扩展为更复杂的地点关系检查）
                    if not self._is_reasonable_location_change(
                        prev_state["location"], curr_state["location"]):
                        issues.append(
                            f"第{curr_state['chapter']}回：{name}从{prev_state['location']}"
                            f"到{curr_state['location']}的位置变化可能不合理"
                        )
        
        return issues
    
    def _is_reasonable_location_change(self, from_loc: str, to_loc: str) -> bool:
        """检查位置变化是否合理"""
        # 这里可以构建一个地点关系图来判断
        # 暂时返回True，实际应该基于红楼梦的地理设定
        return True
    
    def _check_plot_consistency(self, states: List[ChapterState]) -> List[str]:
        """检查情节一致性"""
        issues = []
        
        # 跟踪情节线程的发展
        plot_timeline = {}
        
        for state in states:
            for thread_id, thread in state.plot_threads.items():
                if thread_id not in plot_timeline:
                    plot_timeline[thread_id] = []
                plot_timeline[thread_id].append({
                    "chapter": state.chapter_number,
                    "status": thread.status,
                    "description": thread.description
                })
        
        # 检查情节发展的合理性
        for thread_id, timeline in plot_timeline.items():
            if len(timeline) < 2:
                continue
                
            for i in range(1, len(timeline)):
                prev_plot = timeline[i-1]
                curr_plot = timeline[i]
                
                # 检查已结束的情节是否又重新开始
                if (prev_plot["status"] == PlotStatus.CONCLUDED and 
                    curr_plot["status"] in [PlotStatus.ONGOING, PlotStatus.INTRODUCED]):
                    issues.append(
                        f"第{curr_plot['chapter']}回：{thread_id}在第{prev_plot['chapter']}回"
                        f"已结束，但第{curr_plot['chapter']}回又重新开始"
                    )
        
        return issues
    
    def _check_environment_consistency(self, states: List[ChapterState]) -> List[str]:
        """检查环境一致性"""
        issues = []
        
        # 检查季节变化的合理性
        seasons = []
        for state in states:
            if state.environment.season != "未明确":
                seasons.append({
                    "chapter": state.chapter_number,
                    "season": state.environment.season
                })
        
        # 检查季节跳跃
        season_order = ["春", "夏", "秋", "冬"]
        for i in range(1, len(seasons)):
            prev_season = seasons[i-1]["season"]
            curr_season = seasons[i]["season"]
            
            if prev_season in season_order and curr_season in season_order:
                prev_idx = season_order.index(prev_season)
                curr_idx = season_order.index(curr_season)
                
                # 检查是否跳过了太多季节
                if abs(curr_idx - prev_idx) > 2:
                    issues.append(
                        f"第{seasons[i]['chapter']}回：季节从{prev_season}直接跳到{curr_season}，"
                        f"变化过于突然"
                    )
        
        return issues
    
    def _check_timeline_consistency(self, states: List[ChapterState]) -> List[str]:
        """检查时间线一致性"""
        issues = []
        
        # 检查章节编号的连续性
        chapter_numbers = [state.chapter_number for state in states]
        chapter_numbers.sort()
        
        for i in range(1, len(chapter_numbers)):
            if chapter_numbers[i] - chapter_numbers[i-1] > 1:
                issues.append(
                    f"章节编号从第{chapter_numbers[i-1]}回跳到第{chapter_numbers[i]}回，"
                    f"缺少中间章节"
                )
        
        return issues
    
    def save_chapter_state(self, chapter_state: ChapterState) -> None:
        """保存章节状态到文件"""
        filename = f"chapter_{chapter_state.chapter_number:03d}_state.json"
        filepath = self.states_dir / filename
        
        # 手动转换为可序列化的字典
        state_dict = {
            "chapter_number": chapter_state.chapter_number,
            "chapter_title": chapter_state.chapter_title,
            "timestamp": chapter_state.timestamp,
            "character_states": {},
            "plot_threads": {},
            "environment": asdict(chapter_state.environment),
            "literary_elements": asdict(chapter_state.literary_elements),
            "key_dialogues": chapter_state.key_dialogues,
            "unresolved_questions": chapter_state.unresolved_questions,
            "continuation_notes": chapter_state.continuation_notes,
            "quality_score": chapter_state.quality_score,
            "consistency_issues": chapter_state.consistency_issues
        }
        
        # 处理人物状态 - 转换枚举
        for name, char_state in chapter_state.character_states.items():
            state_dict["character_states"][name] = {
                "name": char_state.name,
                "status": char_state.status.value,  # 转换枚举
                "location": char_state.location,
                "emotional_state": char_state.emotional_state,
                "physical_condition": char_state.physical_condition,
                "social_position": char_state.social_position,
                "key_concerns": char_state.key_concerns,
                "relationships": char_state.relationships,
                "last_significant_action": char_state.last_significant_action,
                "fate_progress": char_state.fate_progress
            }
        
        # 处理情节线程 - 转换枚举和对象
        for thread_id, plot_thread in chapter_state.plot_threads.items():
            state_dict["plot_threads"][thread_id] = {
                "thread_id": plot_thread.thread_id,
                "title": plot_thread.title,
                "description": plot_thread.description,
                "status": plot_thread.status.value,  # 转换枚举
                "participants": plot_thread.participants,
                "key_events": plot_thread.key_events,
                "unresolved_issues": plot_thread.unresolved_issues,
                "expected_resolution": plot_thread.expected_resolution,
                "priority_level": plot_thread.priority_level
            }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state_dict, f, ensure_ascii=False, indent=2)
            logger.info(f"成功保存第{chapter_state.chapter_number}回状态到 {filepath}")
        except Exception as e:
            logger.error(f"保存章节状态失败: {e}")
            raise
    
    def load_chapter_state(self, chapter_number: int) -> Optional[ChapterState]:
        """从文件加载章节状态"""
        filename = f"chapter_{chapter_number:03d}_state.json"
        filepath = self.states_dir / filename
        
        if not filepath.exists():
            logger.warning(f"章节状态文件不存在: {filepath}")
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                state_dict = json.load(f)
            
            # 重建对象结构（这里需要更复杂的反序列化逻辑）
            # 暂时返回字典形式
            logger.info(f"成功加载第{chapter_number}回状态")
            return state_dict  # 这里应该转换为ChapterState对象
        except Exception as e:
            logger.error(f"加载章节状态失败: {e}")
            return None
    
    def get_transfer_summary(self, from_chapter: int, to_chapter: int) -> Dict[str, Any]:
        """获取章节信息传递摘要"""
        from_state = self.load_chapter_state(from_chapter)
        if not from_state:
            return {"error": f"无法加载第{from_chapter}回状态"}
        
        summary = {
            "from_chapter": from_chapter,
            "to_chapter": to_chapter,
            "transfer_timestamp": datetime.now().isoformat(),
            "character_count": len(from_state.get("character_states", {})),
            "plot_thread_count": len(from_state.get("plot_threads", {})),
            "unresolved_count": len(from_state.get("unresolved_questions", [])),
            "key_transfer_points": []
        }
        
        # 添加关键传递点
        if "character_states" in from_state:
            for name, state in from_state["character_states"].items():
                summary["key_transfer_points"].append(
                    f"{name}: {state.get('status', '未知')}状态，位于{state.get('location', '未知')}"
                )
        
        return summary
    
    def _load_character_relationships(self) -> Dict[str, Dict[str, str]]:
        """加载人物关系映射"""
        # 这里可以从知识图谱或配置文件加载
        # 暂时返回空字典
        return {}


def create_chapter_info_transfer(config_path: str = "config/config.yaml") -> ChapterInfoTransfer:
    """创建章节信息传递机制实例"""
    return ChapterInfoTransfer(config_path) 