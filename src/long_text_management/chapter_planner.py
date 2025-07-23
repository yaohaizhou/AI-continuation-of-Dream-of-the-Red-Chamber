"""
章节规划器 - 红楼梦后40回智能规划系统

基于太虚幻境判词数据，为红楼梦后40回（第81-120回）制定详细的章节规划，
包括人物命运安排、情节发展时间线、关键转折点设计等核心功能。

Author: AI-HongLouMeng Project
"""

import json
import re
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
from datetime import datetime
from loguru import logger


class ChapterTheme(Enum):
    """章节主题类型"""
    FATE_FULFILLMENT = "fate_fulfillment"      # 命运实现
    CHARACTER_DECLINE = "character_decline"     # 人物衰落
    FAMILY_COLLAPSE = "family_collapse"        # 家族崩塌
    LOVE_TRAGEDY = "love_tragedy"              # 爱情悲剧
    REDEMPTION = "redemption"                  # 救赎主题
    FINAL_RESOLUTION = "final_resolution"      # 最终了结


class ChapterPriority(Enum):
    """章节重要程度"""
    CRITICAL = "critical"      # 关键章节（命运转折）
    IMPORTANT = "important"    # 重要章节（情节推进）
    SUPPORTING = "supporting"  # 支撑章节（细节描写）


@dataclass
class FateEvent:
    """命运事件"""
    character: str              # 涉及人物
    event_type: str            # 事件类型
    description: str           # 事件描述
    prophecy_reference: str    # 对应判词
    timeline_hint: str         # 时间线暗示
    symbolic_elements: List[str]  # 象征元素


@dataclass
class ChapterPlan:
    """单章规划"""
    chapter_num: int              # 章节号 (81-120)
    title: str                   # 章节标题
    theme: ChapterTheme          # 主题类型
    priority: ChapterPriority    # 重要程度
    
    # 人物安排
    main_characters: List[str]   # 主要人物
    supporting_characters: List[str]  # 次要人物
    
    # 情节设计
    key_events: List[FateEvent]  # 关键事件
    plot_summary: str           # 情节梗概
    emotional_tone: str         # 情感基调
    
    # 文学元素
    symbolic_imagery: List[str]  # 象征意象
    literary_devices: List[str]  # 文学手法
    cross_references: List[str]  # 与前文关联
    
    # 规划元数据
    estimated_length: int       # 预估字数
    difficulty_level: str       # 续写难度
    fate_compliance: float      # 命运符合度
    
    # 承接关系
    prerequisite_chapters: List[int]  # 前置章节
    leads_to_chapters: List[int]     # 后续章节


@dataclass
class OverallPlan:
    """总体规划"""
    chapters: List[ChapterPlan]     # 所有章节规划
    character_arcs: Dict[str, List[int]]  # 人物弧线（角色在哪些章节出现）
    fate_timeline: Dict[str, int]   # 命运时间线（角色命运实现的章节）
    thematic_structure: Dict[ChapterTheme, List[int]]  # 主题结构
    critical_turning_points: List[int]  # 关键转折点章节
    
    # 总体统计
    total_estimated_words: int      # 总预估字数
    completion_percentage: float    # 规划完成度
    fate_coverage: Dict[str, bool]  # 命运覆盖情况
    
    # 元数据
    creation_date: str             # 创建日期
    last_updated: str              # 最后更新
    version: str                   # 版本号


class ChapterPlanner:
    """章节规划器"""
    
    def __init__(self, data_dir: str = "data"):
        """初始化章节规划器"""
        self.data_dir = Path(data_dir)
        self.prophecies_path = self.data_dir / "processed" / "taixu_prophecies.json"
        self.plans_output_path = self.data_dir / "processed" / "chapter_plans.json"
        
        # 核心数据
        self.prophecies = {}
        self.character_fates = {}
        self.chapter_templates = {}
        
        # 规划参数
        self.target_chapters = 40  # 目标章节数 (81-120)
        self.avg_chapter_length = 12000  # 平均章节字数
        self.total_target_words = 480000  # 总目标字数 (约48万字)
        
        # 初始化
        self._load_prophecy_data()
        self._build_character_fates()
        self._initialize_templates()
        
        logger.info(f"章节规划器初始化完成，目标规划 {self.target_chapters} 章节")
    
    def _load_prophecy_data(self) -> None:
        """加载太虚幻境判词数据"""
        try:
            if not self.prophecies_path.exists():
                raise FileNotFoundError(f"判词数据文件不存在: {self.prophecies_path}")
            
            with open(self.prophecies_path, 'r', encoding='utf-8') as f:
                self.prophecies = json.load(f)
            
            logger.info("成功加载太虚幻境判词数据")
            
        except Exception as e:
            logger.error(f"加载判词数据失败: {e}")
            raise
    
    def _build_character_fates(self) -> None:
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
                            "prophecy_poem": prophecy.get("poem", {}),
                            "symbolic_elements": prophecy.get("image", {}).get("symbolic_elements", []),
                            "emotional_tone": prophecy.get("poem", {}).get("emotional_tone", "悲剧"),
                            "section": section_name
                        }
        
        logger.info(f"构建了 {len(self.character_fates)} 个角色的命运数据")
    
    def _initialize_templates(self) -> None:
        """初始化章节模板"""
        # 基于角色命运定义章节模板
        self.chapter_templates = {
            # 早期章节 (81-90): 危机显现
            "crisis_emergence": {
                "themes": [ChapterTheme.FAMILY_COLLAPSE],
                "character_focus": ["王熙凤", "贾巧姐", "贾迎春"],
                "tone": "不安",
                "symbolic_elements": ["秋风", "落叶", "暮色"]
            },
            
            # 中期章节 (91-105): 命运展开
            "fate_unfolding": {
                "themes": [ChapterTheme.LOVE_TRAGEDY, ChapterTheme.CHARACTER_DECLINE],
                "character_focus": ["林黛玉", "薛宝钗", "贾宝玉"],
                "tone": "悲怆",
                "symbolic_elements": ["残花", "冷月", "空房"]
            },
            
            # 后期章节 (106-120): 最终了结
            "final_resolution": {
                "themes": [ChapterTheme.FATE_FULFILLMENT, ChapterTheme.FINAL_RESOLUTION],
                "character_focus": ["贾惜春", "史湘云", "妙玉"],
                "tone": "悲凉",
                "symbolic_elements": ["青灯", "古寺", "飞云"]
            }
        }
    
    def generate_overall_plan(self) -> OverallPlan:
        """生成40回的总体规划"""
        logger.info("开始生成红楼梦后40回总体规划...")
        
        # 1. 分析角色命运，确定关键时间点
        fate_timeline = self._analyze_fate_timeline()
        
        # 2. 设计关键转折点
        turning_points = self._design_turning_points(fate_timeline)
        
        # 3. 生成章节规划
        chapters = self._generate_chapter_plans(fate_timeline, turning_points)
        
        # 4. 构建人物弧线
        character_arcs = self._build_character_arcs(chapters)
        
        # 5. 确定主题结构
        thematic_structure = self._build_thematic_structure(chapters)
        
        # 6. 计算统计信息
        stats = self._calculate_statistics(chapters)
        
        overall_plan = OverallPlan(
            chapters=chapters,
            character_arcs=character_arcs,
            fate_timeline=fate_timeline,
            thematic_structure=thematic_structure,
            critical_turning_points=turning_points,
            total_estimated_words=stats["total_words"],
            completion_percentage=100.0,  # 规划阶段完成度
            fate_coverage=stats["fate_coverage"],
            creation_date=datetime.now().strftime("%Y-%m-%d"),
            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            version="1.0"
        )
        
        logger.info(f"总体规划生成完成: {len(chapters)} 章节，预估 {stats['total_words']} 字")
        return overall_plan
    
    def _analyze_fate_timeline(self) -> Dict[str, int]:
        """分析角色命运时间线"""
        fate_timeline = {}
        
        # 基于判词暗示和情节逻辑分配命运实现的章节
        fate_assignments = {
            # 早期命运实现 (81-90回)
            "贾迎春": 85,  # 嫁给孙绍祖后很快死亡
            "贾元春": 88,  # 在虎兔年间去世
            
            # 中期命运实现 (91-105回)
            "林黛玉": 97,  # 香消玉殒的核心章节
            "薛宝钗": 98,  # 独守空房的开始
            "王熙凤": 102, # 机关算尽的败落
            "贾探春": 105, # 远嫁他乡
            
            # 后期命运实现 (106-120回)
            "妙玉": 110,   # 终陷淖泥中
            "贾巧姐": 112, # 巧得遇恩人
            "史湘云": 115, # 湘江水逝楚云飞
            "贾惜春": 118, # 独卧青灯古佛旁
            "李纨": 119,   # 晚年荣华终成空
            "秦可卿": 81,  # 在前80回已死，但影响后续
            
            # 副册、又副册角色
            "香菱": 108,   # 香魂返故乡
            "晴雯": 93,    # 早期死亡
            "袭人": 100    # 忠心服侍后的结局
        }
        
        fate_timeline.update(fate_assignments)
        
        logger.info(f"分析了 {len(fate_timeline)} 个角色的命运时间线")
        return fate_timeline
    
    def _design_turning_points(self, fate_timeline: Dict[str, int]) -> List[int]:
        """设计关键转折点章节"""
        turning_points = []
        
        # 基于命运时间线确定关键转折点
        major_fates = ["林黛玉", "薛宝钗", "王熙凤", "贾探春"]
        
        for character in major_fates:
            if character in fate_timeline:
                chapter = fate_timeline[character]
                if chapter not in turning_points:
                    turning_points.append(chapter)
        
        # 添加结构性转折点
        turning_points.extend([81, 90, 100, 110, 120])  # 每10回一个大转折
        
        # 排序并去重
        turning_points = sorted(list(set(turning_points)))
        
        logger.info(f"确定了 {len(turning_points)} 个关键转折点")
        return turning_points
    
    def _generate_chapter_plans(self, fate_timeline: Dict[str, int], 
                               turning_points: List[int]) -> List[ChapterPlan]:
        """生成具体的章节规划"""
        chapters = []
        
        for chapter_num in range(81, 121):  # 第81回到第120回
            plan = self._create_single_chapter_plan(
                chapter_num, fate_timeline, turning_points
            )
            chapters.append(plan)
        
        logger.info(f"生成了 {len(chapters)} 个章节的详细规划")
        return chapters
    
    def _create_single_chapter_plan(self, chapter_num: int, 
                                   fate_timeline: Dict[str, int],
                                   turning_points: List[int]) -> ChapterPlan:
        """创建单个章节的规划"""
        
        # 确定该章节的主要角色命运事件
        chapter_fates = {char: fate for char, fate in fate_timeline.items() 
                        if fate == chapter_num}
        
        # 确定主题和优先级
        if chapter_num in turning_points:
            priority = ChapterPriority.CRITICAL
        elif chapter_fates:
            priority = ChapterPriority.IMPORTANT
        else:
            priority = ChapterPriority.SUPPORTING
        
        # 根据章节位置确定主题
        theme = self._determine_chapter_theme(chapter_num, chapter_fates)
        
        # 生成章节标题
        title = self._generate_chapter_title(chapter_num, chapter_fates, theme)
        
        # 确定人物安排
        main_chars, supporting_chars = self._assign_chapter_characters(
            chapter_num, chapter_fates
        )
        
        # 创建关键事件
        key_events = self._create_chapter_events(chapter_num, chapter_fates)
        
        # 生成情节梗概
        plot_summary = self._generate_plot_summary(chapter_num, key_events, theme)
        
        # 确定文学元素
        symbolic_imagery = self._select_symbolic_imagery(main_chars, theme)
        literary_devices = self._select_literary_devices(theme, chapter_fates)
        
        # 计算预估字数
        estimated_length = self._estimate_chapter_length(priority, len(key_events))
        
        # 计算命运符合度
        fate_compliance = self._calculate_fate_compliance(chapter_fates, key_events)
        
        # 确定承接关系
        prerequisites, leads_to = self._determine_chapter_relationships(
            chapter_num, main_chars
        )
        
        return ChapterPlan(
            chapter_num=chapter_num,
            title=title,
            theme=theme,
            priority=priority,
            main_characters=main_chars,
            supporting_characters=supporting_chars,
            key_events=key_events,
            plot_summary=plot_summary,
            emotional_tone=self._determine_emotional_tone(chapter_fates, theme),
            symbolic_imagery=symbolic_imagery,
            literary_devices=literary_devices,
            cross_references=self._generate_cross_references(chapter_num, main_chars),
            estimated_length=estimated_length,
            difficulty_level=self._assess_difficulty_level(chapter_fates, theme),
            fate_compliance=fate_compliance,
            prerequisite_chapters=prerequisites,
            leads_to_chapters=leads_to
        )
    
    def _determine_chapter_theme(self, chapter_num: int, 
                                chapter_fates: Dict[str, int]) -> ChapterTheme:
        """确定章节主题"""
        
        # 基于章节位置和角色命运确定主题
        if chapter_num <= 90:
            # 早期：家族衰落和危机显现
            if chapter_fates:
                return ChapterTheme.FATE_FULFILLMENT
            else:
                return ChapterTheme.FAMILY_COLLAPSE
                
        elif chapter_num <= 105:
            # 中期：爱情悲剧和人物衰落
            major_love_characters = ["林黛玉", "薛宝钗", "贾宝玉"]
            if any(char in chapter_fates for char in major_love_characters):
                return ChapterTheme.LOVE_TRAGEDY
            else:
                return ChapterTheme.CHARACTER_DECLINE
                
        else:
            # 后期：最终了结和救赎
            if chapter_num == 120:
                return ChapterTheme.FINAL_RESOLUTION
            elif "贾巧姐" in chapter_fates:
                return ChapterTheme.REDEMPTION
            else:
                return ChapterTheme.FATE_FULFILLMENT
    
    def _generate_chapter_title(self, chapter_num: int, 
                               chapter_fates: Dict[str, int],
                               theme: ChapterTheme) -> str:
        """生成章节标题"""
        
        # 基于主要角色和事件生成标题
        if chapter_fates:
            main_char = list(chapter_fates.keys())[0]
            fate_data = self.character_fates.get(main_char, {})
            
            # 使用判词元素构建标题
            symbolic_elements = fate_data.get("symbolic_elements", [])
            if symbolic_elements and len(symbolic_elements) > 0:
                symbol = symbolic_elements[0]
                if main_char == "林黛玉":
                    return f"第{chapter_num}回 玉带飘零香消散 黛玉魂归离恨天"
                elif main_char == "薛宝钗":
                    return f"第{chapter_num}回 金簪雪里终埋没 宝钗独守空房寒"
                elif main_char == "王熙凤":
                    return f"第{chapter_num}回 凤凰涅槃冰山倒 机关算尽反丧身"
                elif main_char == "贾探春":
                    return f"第{chapter_num}回 风筝飞向远山外 探春远嫁他乡泪"
                else:
                    return f"第{chapter_num}回 {symbol}寓命运 {main_char}应谶归"
            else:
                return f"第{chapter_num}回 {main_char}应谶记 天命难违尘缘了"
        else:
            # 无特定角色命运的章节
            if theme == ChapterTheme.FAMILY_COLLAPSE:
                return f"第{chapter_num}回 贾府衰败势如流 往昔繁华化虚无"
            elif theme == ChapterTheme.CHARACTER_DECLINE:
                return f"第{chapter_num}回 昔日风光今何在 人生如梦总成空"
            else:
                return f"第{chapter_num}回 红楼一梦话沧桑 世事无常叹浮生"
    
    def _assign_chapter_characters(self, chapter_num: int, 
                                  chapter_fates: Dict[str, int]) -> Tuple[List[str], List[str]]:
        """分配章节人物"""
        
        main_characters = list(chapter_fates.keys()) if chapter_fates else []
        supporting_characters = []
        
        # 根据情节需要添加相关角色
        for main_char in main_characters:
            if main_char == "林黛玉":
                supporting_characters.extend(["贾宝玉", "紫鹃", "贾母"])
            elif main_char == "薛宝钗":
                supporting_characters.extend(["贾宝玉", "莺儿", "薛姨妈"])
            elif main_char == "王熙凤":
                supporting_characters.extend(["贾琏", "平儿", "贾巧姐"])
            elif main_char == "贾探春":
                supporting_characters.extend(["赵姨娘", "贾政", "侍书"])
        
        # 去重并限制数量
        supporting_characters = list(set(supporting_characters))
        if len(supporting_characters) > 5:
            supporting_characters = supporting_characters[:5]
        
        # 如果没有主要角色，根据章节位置添加
        if not main_characters:
            if chapter_num <= 90:
                main_characters = ["贾宝玉", "王熙凤"]
            elif chapter_num <= 105:
                main_characters = ["贾宝玉", "薛宝钗"]
            else:
                main_characters = ["贾惜春", "贾宝玉"]
        
        return main_characters, supporting_characters
    
    def _create_chapter_events(self, chapter_num: int, 
                              chapter_fates: Dict[str, int]) -> List[FateEvent]:
        """创建章节关键事件"""
        events = []
        
        for character, _ in chapter_fates.items():
            fate_data = self.character_fates.get(character, {})
            fate_summary = fate_data.get("fate_summary", "")
            key_events = fate_data.get("key_events", [])
            symbolic_elements = fate_data.get("symbolic_elements", [])
            
            # 根据角色创建命运事件
            if character == "林黛玉":
                event = FateEvent(
                    character=character,
                    event_type="death",
                    description="林黛玉在病中咏诗，香消玉殒，魂归离恨天",
                    prophecy_reference="玉带林中挂",
                    timeline_hint="青春年华终结",
                    symbolic_elements=["玉带", "林中", "香消"]
                )
                events.append(event)
                
            elif character == "薛宝钗":
                event = FateEvent(
                    character=character,
                    event_type="marriage_loneliness",
                    description="薛宝钗婚后独守空房，感受到深深的孤寂",
                    prophecy_reference="金簪雪里埋",
                    timeline_hint="婚后生活开始",
                    symbolic_elements=["金簪", "雪里", "寒冷"]
                )
                events.append(event)
                
            elif character == "王熙凤":
                event = FateEvent(
                    character=character,
                    event_type="power_collapse",
                    description="王熙凤的权势彻底崩塌，机关算尽反误了性命",
                    prophecy_reference="一从二令三人木",
                    timeline_hint="末世来临",
                    symbolic_elements=["雌凤", "冰山", "三人木"]
                )
                events.append(event)
                
            elif character == "贾探春":
                event = FateEvent(
                    character=character,
                    event_type="distant_marriage",
                    description="贾探春为了家族远嫁他乡，临别时涕泣不已",
                    prophecy_reference="千里东风一梦遥",
                    timeline_hint="清明时节",
                    symbolic_elements=["风筝", "大海", "千里"]
                )
                events.append(event)
                
            # 继续为其他角色创建事件...
            else:
                # 通用事件创建逻辑
                event = FateEvent(
                    character=character,
                    event_type="fate_fulfillment",
                    description=f"{character}的命运按照判词预言得到应验：{fate_summary}",
                    prophecy_reference=fate_summary,
                    timeline_hint="命运转折点",
                    symbolic_elements=symbolic_elements[:3]  # 最多3个象征元素
                )
                events.append(event)
        
        return events
    
    def _generate_plot_summary(self, chapter_num: int, 
                              key_events: List[FateEvent], 
                              theme: ChapterTheme) -> str:
        """生成情节梗概"""
        
        if not key_events:
            # 无特定命运事件的章节
            if theme == ChapterTheme.FAMILY_COLLAPSE:
                return f"贾府继续衰败，家族成员各有心事，昔日繁华已成过往云烟。"
            elif theme == ChapterTheme.CHARACTER_DECLINE:
                return f"众人感受到命运的无常，各自在生活的变故中挣扎求存。"
            else:
                return f"故事继续推进，人物命运渐趋明朗，悲剧色彩愈加浓重。"
        
        # 有具体命运事件的章节
        main_event = key_events[0]
        character = main_event.character
        
        plot_parts = []
        
        # 开头：背景设置
        plot_parts.append(f"话说{character}近日来")
        
        # 中间：事件发展
        if main_event.event_type == "death":
            plot_parts.append(f"病情日重，{main_event.description}")
        elif main_event.event_type == "marriage_loneliness":
            plot_parts.append(f"独处深闺，{main_event.description}")
        elif main_event.event_type == "power_collapse":
            plot_parts.append(f"权势不稳，{main_event.description}")
        elif main_event.event_type == "distant_marriage":
            plot_parts.append(f"接到远嫁消息，{main_event.description}")
        else:
            plot_parts.append(main_event.description)
        
        # 结尾：影响和反响
        plot_parts.append(f"此事在府中引起波澜，众人各有感慨，正应了当年太虚幻境的判词预言。")
        
        return "，".join(plot_parts)
    
    def _select_symbolic_imagery(self, main_characters: List[str], 
                                theme: ChapterTheme) -> List[str]:
        """选择象征意象"""
        imagery = []
        
        # 基于角色添加专属象征
        for character in main_characters:
            fate_data = self.character_fates.get(character, {})
            char_symbols = fate_data.get("symbolic_elements", [])
            imagery.extend(char_symbols[:2])  # 每个角色最多2个象征
        
        # 基于主题添加通用象征
        theme_symbols = {
            ChapterTheme.LOVE_TRAGEDY: ["残花", "冷月", "空房", "泪痕"],
            ChapterTheme.FAMILY_COLLAPSE: ["秋风", "落叶", "颓墙", "斜阳"],
            ChapterTheme.CHARACTER_DECLINE: ["暮云", "寒雨", "枯枝", "空巢"],
            ChapterTheme.FATE_FULFILLMENT: ["应谶", "天数", "宿命", "归途"],
            ChapterTheme.FINAL_RESOLUTION: ["终结", "归宿", "安息", "解脱"],
            ChapterTheme.REDEMPTION: ["重生", "希望", "温暖", "善缘"]
        }
        
        if theme in theme_symbols:
            imagery.extend(theme_symbols[theme][:3])
        
        # 去重并限制数量
        return list(set(imagery))[:6]
    
    def _select_literary_devices(self, theme: ChapterTheme, 
                                chapter_fates: Dict[str, int]) -> List[str]:
        """选择文学手法"""
        devices = ["对比", "象征", "暗示"]  # 基础手法
        
        # 基于主题添加特定手法
        if theme == ChapterTheme.LOVE_TRAGEDY:
            devices.extend(["情景交融", "直抒胸臆"])
        elif theme == ChapterTheme.FAMILY_COLLAPSE:
            devices.extend(["烘托", "渲染"])
        elif theme == ChapterTheme.FATE_FULFILLMENT:
            devices.extend(["照应", "伏笔"])
        
        # 如果有多个角色命运，使用平行手法
        if len(chapter_fates) > 1:
            devices.append("平行结构")
        
        return list(set(devices))
    
    def _estimate_chapter_length(self, priority: ChapterPriority, 
                                event_count: int) -> int:
        """估算章节字数"""
        base_length = {
            ChapterPriority.CRITICAL: 15000,    # 关键章节较长
            ChapterPriority.IMPORTANT: 12000,   # 重要章节标准长度
            ChapterPriority.SUPPORTING: 10000   # 支撑章节较短
        }
        
        length = base_length[priority]
        
        # 根据事件数量调整
        length += event_count * 2000
        
        # 限制范围
        return max(8000, min(18000, length))
    
    def _calculate_fate_compliance(self, chapter_fates: Dict[str, int], 
                                  key_events: List[FateEvent]) -> float:
        """计算命运符合度"""
        if not chapter_fates:
            return 1.0  # 无特定命运要求的章节视为完全符合
        
        # 检查每个角色的命运是否在事件中得到体现
        total_chars = len(chapter_fates)
        covered_chars = len([event.character for event in key_events])
        
        return min(1.0, covered_chars / total_chars)
    
    def _determine_chapter_relationships(self, chapter_num: int, 
                                       main_characters: List[str]) -> Tuple[List[int], List[int]]:
        """确定章节承接关系"""
        prerequisites = []
        leads_to = []
        
        # 简单的承接关系逻辑
        if chapter_num > 81:
            prerequisites.append(chapter_num - 1)  # 前一章
        
        if chapter_num < 120:
            leads_to.append(chapter_num + 1)  # 后一章
        
        # 基于人物弧线的特殊承接关系
        if "林黛玉" in main_characters and chapter_num < 100:
            # 黛玉相关章节的承接
            if chapter_num + 5 <= 120:
                leads_to.append(chapter_num + 5)
        
        return prerequisites, leads_to
    
    def _determine_emotional_tone(self, chapter_fates: Dict[str, int], 
                                 theme: ChapterTheme) -> str:
        """确定情感基调"""
        if chapter_fates:
            # 有角色命运的章节，使用角色的情感基调
            for character in chapter_fates.keys():
                fate_data = self.character_fates.get(character, {})
                return fate_data.get("emotional_tone", "悲剧")
        
        # 基于主题确定基调
        theme_tones = {
            ChapterTheme.LOVE_TRAGEDY: "悲怆",
            ChapterTheme.FAMILY_COLLAPSE: "悲凉",
            ChapterTheme.CHARACTER_DECLINE: "沉重",
            ChapterTheme.FATE_FULFILLMENT: "悲壮",
            ChapterTheme.FINAL_RESOLUTION: "悲壮",
            ChapterTheme.REDEMPTION: "温暖"
        }
        
        return theme_tones.get(theme, "悲剧")
    
    def _assess_difficulty_level(self, chapter_fates: Dict[str, int], 
                                theme: ChapterTheme) -> str:
        """评估续写难度"""
        if not chapter_fates:
            return "中等"  # 无特定命运的章节难度中等
        
        # 主要角色的命运章节难度较高
        major_characters = ["林黛玉", "薛宝钗", "王熙凤", "贾宝玉"]
        if any(char in chapter_fates for char in major_characters):
            return "困难"
        
        # 关键主题的章节
        if theme in [ChapterTheme.FINAL_RESOLUTION, ChapterTheme.LOVE_TRAGEDY]:
            return "困难"
        
        return "中等"
    
    def _generate_cross_references(self, chapter_num: int, 
                                  main_characters: List[str]) -> List[str]:
        """生成与前文的关联"""
        references = []
        
        # 基于角色添加关联
        for character in main_characters:
            if character == "林黛玉":
                references.append("第五回太虚幻境判词")
                references.append("第二十三回黛玉葬花")
            elif character == "薛宝钗":
                references.append("第五回金陵十二钗")
                references.append("第二十八回宝钗捉蝶")
            # 可以继续添加更多角色的关联
        
        # 添加通用关联
        references.append(f"第{chapter_num-1}回前文")
        if chapter_num <= 90:
            references.append("第八十回前文总结")
        
        return list(set(references))[:5]  # 最多5个关联
    
    def _build_character_arcs(self, chapters: List[ChapterPlan]) -> Dict[str, List[int]]:
        """构建人物弧线"""
        character_arcs = {}
        
        for chapter in chapters:
            # 主要角色
            for character in chapter.main_characters:
                if character not in character_arcs:
                    character_arcs[character] = []
                character_arcs[character].append(chapter.chapter_num)
            
            # 次要角色（权重较低）
            for character in chapter.supporting_characters:
                if character not in character_arcs:
                    character_arcs[character] = []
                if chapter.chapter_num not in character_arcs[character]:
                    character_arcs[character].append(chapter.chapter_num)
        
        # 排序
        for character in character_arcs:
            character_arcs[character].sort()
        
        return character_arcs
    
    def _build_thematic_structure(self, chapters: List[ChapterPlan]) -> Dict[ChapterTheme, List[int]]:
        """构建主题结构"""
        thematic_structure = {}
        
        for chapter in chapters:
            theme = chapter.theme
            if theme not in thematic_structure:
                thematic_structure[theme] = []
            thematic_structure[theme].append(chapter.chapter_num)
        
        return thematic_structure
    
    def _calculate_statistics(self, chapters: List[ChapterPlan]) -> Dict[str, Any]:
        """计算统计信息"""
        total_words = sum(chapter.estimated_length for chapter in chapters)
        
        # 检查命运覆盖情况
        fate_coverage = {}
        planned_characters = set()
        
        for chapter in chapters:
            for event in chapter.key_events:
                planned_characters.add(event.character)
        
        for character in self.character_fates.keys():
            fate_coverage[character] = character in planned_characters
        
        return {
            "total_words": total_words,
            "fate_coverage": fate_coverage
        }
    
    def save_plan(self, plan: OverallPlan, file_path: Optional[str] = None) -> None:
        """保存规划到文件"""
        if file_path is None:
            file_path = self.plans_output_path
        
        try:
            # 转换为可序列化的格式
            def make_serializable(obj):
                """将对象转换为可序列化格式"""
                if hasattr(obj, 'value'):  # 枚举类型
                    return obj.value
                elif isinstance(obj, dict):
                    return {k: make_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [make_serializable(item) for item in obj]
                else:
                    return obj
            
            # 处理章节数据
            chapters_data = []
            for chapter in plan.chapters:
                chapter_dict = asdict(chapter)
                # 转换枚举类型
                chapter_dict["theme"] = chapter_dict["theme"].value
                chapter_dict["priority"] = chapter_dict["priority"].value
                chapters_data.append(chapter_dict)
            
            plan_dict = {
                "chapters": chapters_data,
                "character_arcs": plan.character_arcs,
                "fate_timeline": plan.fate_timeline,
                "thematic_structure": {theme.value: chapters for theme, chapters in plan.thematic_structure.items()},
                "critical_turning_points": plan.critical_turning_points,
                "total_estimated_words": plan.total_estimated_words,
                "completion_percentage": plan.completion_percentage,
                "fate_coverage": plan.fate_coverage,
                "creation_date": plan.creation_date,
                "last_updated": plan.last_updated,
                "version": plan.version
            }
            
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 保存文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(plan_dict, f, ensure_ascii=False, indent=2)
            
            logger.info(f"章节规划已保存到: {file_path}")
            
        except Exception as e:
            logger.error(f"保存章节规划失败: {e}")
            raise
    
    def load_plan(self, file_path: Optional[str] = None) -> Optional[OverallPlan]:
        """从文件加载规划"""
        if file_path is None:
            file_path = self.plans_output_path
        
        try:
            if not Path(file_path).exists():
                logger.warning(f"规划文件不存在: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                plan_dict = json.load(f)
            
            # 转换回对象格式
            chapters = []
            for chapter_data in plan_dict["chapters"]:
                # 转换枚举类型
                chapter_data["theme"] = ChapterTheme(chapter_data["theme"])
                chapter_data["priority"] = ChapterPriority(chapter_data["priority"])
                
                # 转换事件对象
                events = []
                for event_data in chapter_data["key_events"]:
                    event = FateEvent(**event_data)
                    events.append(event)
                chapter_data["key_events"] = events
                
                chapter = ChapterPlan(**chapter_data)
                chapters.append(chapter)
            
            # 转换主题结构
            thematic_structure = {}
            for theme_str, chapter_nums in plan_dict["thematic_structure"].items():
                theme = ChapterTheme(theme_str)
                thematic_structure[theme] = chapter_nums
            
            plan = OverallPlan(
                chapters=chapters,
                character_arcs=plan_dict["character_arcs"],
                fate_timeline=plan_dict["fate_timeline"],
                thematic_structure=thematic_structure,
                critical_turning_points=plan_dict["critical_turning_points"],
                total_estimated_words=plan_dict["total_estimated_words"],
                completion_percentage=plan_dict["completion_percentage"],
                fate_coverage=plan_dict["fate_coverage"],
                creation_date=plan_dict["creation_date"],
                last_updated=plan_dict["last_updated"],
                version=plan_dict["version"]
            )
            
            logger.info(f"成功加载章节规划: {file_path}")
            return plan
            
        except Exception as e:
            logger.error(f"加载章节规划失败: {e}")
            return None
    
    def get_chapter_plan(self, chapter_num: int, plan: OverallPlan) -> Optional[ChapterPlan]:
        """获取特定章节的规划"""
        for chapter in plan.chapters:
            if chapter.chapter_num == chapter_num:
                return chapter
        return None
    
    def generate_planning_report(self, plan: OverallPlan) -> str:
        """生成规划报告"""
        report_lines = []
        
        # 标题
        report_lines.append("# 红楼梦后40回章节规划报告")
        report_lines.append(f"**生成时间**: {plan.creation_date}")
        report_lines.append(f"**版本**: {plan.version}")
        report_lines.append("")
        
        # 总体统计
        report_lines.append("## 📊 总体统计")
        report_lines.append(f"- **规划章节数**: {len(plan.chapters)} 回")
        report_lines.append(f"- **预估总字数**: {plan.total_estimated_words:,} 字")
        report_lines.append(f"- **平均章节长度**: {plan.total_estimated_words // len(plan.chapters):,} 字")
        report_lines.append(f"- **关键转折点**: {len(plan.critical_turning_points)} 个")
        report_lines.append("")
        
        # 角色命运覆盖
        covered_count = sum(1 for covered in plan.fate_coverage.values() if covered)
        total_count = len(plan.fate_coverage)
        report_lines.append("## 👥 角色命运覆盖")
        report_lines.append(f"- **已规划角色**: {covered_count}/{total_count} 个")
        
        for character, covered in plan.fate_coverage.items():
            status = "✅" if covered else "❌"
            fate_chapter = plan.fate_timeline.get(character, "未安排")
            report_lines.append(f"  - {status} {character}: 第{fate_chapter}回")
        report_lines.append("")
        
        # 主题分布
        report_lines.append("## 🎭 主题分布")
        for theme, chapters in plan.thematic_structure.items():
            report_lines.append(f"- **{theme.value}**: {len(chapters)} 回 - {chapters}")
        report_lines.append("")
        
        # 关键转折点
        report_lines.append("## 🎯 关键转折点")
        for point in plan.critical_turning_points:
            chapter_plan = self.get_chapter_plan(point, plan)
            if chapter_plan:
                report_lines.append(f"- **第{point}回**: {chapter_plan.title}")
        report_lines.append("")
        
        # 章节列表（前10回作为示例）
        report_lines.append("## 📖 章节规划预览 (前10回)")
        for chapter in plan.chapters[:10]:
            report_lines.append(f"### {chapter.title}")
            report_lines.append(f"- **主题**: {chapter.theme.value}")
            report_lines.append(f"- **优先级**: {chapter.priority.value}")
            report_lines.append(f"- **主要人物**: {', '.join(chapter.main_characters)}")
            report_lines.append(f"- **预估字数**: {chapter.estimated_length:,} 字")
            report_lines.append(f"- **情节梗概**: {chapter.plot_summary}")
            if chapter.key_events:
                report_lines.append(f"- **关键事件**: {chapter.key_events[0].description}")
            report_lines.append("")
        
        return "\n".join(report_lines)


def main():
    """主函数，用于测试章节规划功能"""
    planner = ChapterPlanner()
    
    try:
        # 生成总体规划
        logger.info("开始生成章节规划...")
        overall_plan = planner.generate_overall_plan()
        
        # 保存规划
        planner.save_plan(overall_plan)
        
        # 生成报告
        report = planner.generate_planning_report(overall_plan)
        
        # 保存报告
        report_path = "reports/chapter_planning_report.md"
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("章节规划完成！")
        print(f"规划文件: {planner.plans_output_path}")
        print(f"报告文件: {report_path}")
        
        # 显示关键信息
        print(f"\n📊 规划概要:")
        print(f"- 总计 {len(overall_plan.chapters)} 回")
        print(f"- 预估 {overall_plan.total_estimated_words:,} 字")
        print(f"- 覆盖 {sum(overall_plan.fate_coverage.values())} 个角色命运")
        
    except Exception as e:
        logger.error(f"章节规划失败: {e}")
        raise


if __name__ == "__main__":
    main() 