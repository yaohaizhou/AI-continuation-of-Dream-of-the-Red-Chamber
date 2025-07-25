"""
上下文压缩器
Context Compressor - 解决LLM长度限制的核心模块

这个模块的目标是将长文本（如前面章节内容）压缩为关键信息摘要，
使得在续写新章节时能够在有限的上下文窗口内包含最相关的背景信息。
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
import logging
from pathlib import Path
import os

# 使用统一的模型管理器
try:
    from ..models import get_llm_manager, get_config
    LLM_MANAGER_AVAILABLE = True
except ImportError:
    LLM_MANAGER_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class ChapterSummary:
    """章节摘要数据结构"""
    chapter_num: int
    title: str
    key_events: List[str]
    character_states: Dict[str, str]  # 人物状态变化
    important_dialogues: List[str]
    plot_developments: List[str]
    emotional_tone: str
    word_count: int

@dataclass
class CompressedContext:
    """压缩后的上下文数据结构"""
    current_chapter: int
    previous_chapters_summary: List[ChapterSummary]
    key_character_states: Dict[str, Any]
    ongoing_plot_threads: List[str]
    important_relationships: Dict[str, List[str]]
    compressed_word_count: int
    original_word_count: int
    compression_ratio: float

class ContextCompressor:
    """
    上下文压缩器
    
    核心功能：
    1. 将多个章节压缩为关键信息摘要
    2. 提取人物状态变化和重要事件
    3. 维护情节连贯性所需的最小信息集
    4. 动态调整压缩比例以适应上下文限制
    """
    
    def __init__(self, max_context_length: int = 8000, use_llm: bool = True):
        """
        初始化上下文压缩器
        
        Args:
            max_context_length: 最大上下文长度（字符数）
            use_llm: 是否使用LLM进行智能摘要
        """
        self.max_context_length = max_context_length
        self.use_llm = use_llm and LLM_MANAGER_AVAILABLE
        
        # 初始化LLM管理器（如果可用）
        self.llm_manager = None
        self.config = None
        if self.use_llm:
            self._init_llm()
        
        self.compression_strategies = [
            self._extract_key_events,
            self._extract_character_states_from_text,
            self._extract_plot_developments,
            self._extract_important_dialogues
        ]
        
        # 状态文件路径
        self.state_file = "data/processed/context_compressor_state.json"
        self._ensure_state_dir()
    
    def _init_llm(self) -> None:
        """初始化LLM管理器"""
        try:
            self.config = get_config()
            self.llm_manager = get_llm_manager()
            
            # 检查配置
            if not self.config.llm.api_key:
                logger.warning("OPENAI_API_KEY未设置，将使用规则方法进行摘要")
                self.use_llm = False
                return
            
            logger.info("LLM管理器初始化成功，将使用智能摘要功能")
            
        except Exception as e:
            logger.warning(f"LLM管理器初始化失败，将使用规则方法: {e}")
            self.use_llm = False
    
    def _ensure_state_dir(self) -> None:
        """确保状态文件目录存在"""
        try:
            state_dir = os.path.dirname(self.state_file)
            if state_dir and not os.path.exists(state_dir):
                os.makedirs(state_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"创建状态目录失败: {e}")
    
    def compress_chapters(self, chapters: List[str], target_chapter: int) -> CompressedContext:
        """
        压缩多个章节为上下文摘要
        
        Args:
            chapters: 章节文本列表
            target_chapter: 目标续写章节号
            
        Returns:
            CompressedContext: 压缩后的上下文
        """
        try:
            logger.info(f"开始压缩 {len(chapters)} 个章节，目标章节: {target_chapter}")
            
            # 1. 为每个章节生成摘要
            chapter_summaries = []
            for i, chapter_text in enumerate(chapters):
                summary = self._create_chapter_summary(chapter_text, i + 1)
                chapter_summaries.append(summary)
            
            # 2. 提取关键信息
            key_character_states = self._extract_character_states(chapter_summaries)
            ongoing_plot_threads = self._extract_plot_threads(chapter_summaries)
            important_relationships = self._extract_relationships(chapter_summaries)
            
            # 3. 计算压缩比例
            original_word_count = sum(len(chapter) for chapter in chapters)
            compressed_word_count = self._estimate_compressed_size(chapter_summaries)
            compression_ratio = compressed_word_count / original_word_count if original_word_count > 0 else 0
            
            # 4. 创建压缩上下文
            compressed_context = CompressedContext(
                current_chapter=target_chapter,
                previous_chapters_summary=chapter_summaries,
                key_character_states=key_character_states,
                ongoing_plot_threads=ongoing_plot_threads,
                important_relationships=important_relationships,
                compressed_word_count=compressed_word_count,
                original_word_count=original_word_count,
                compression_ratio=compression_ratio
            )
            
            logger.info(f"压缩完成: {original_word_count} -> {compressed_word_count} 字符 "
                       f"(压缩比: {compression_ratio:.2%})")
            
            return compressed_context
            
        except Exception as e:
            logger.error(f"章节压缩失败: {e}")
            raise
    
    def _create_chapter_summary(self, chapter_text: str, chapter_num: int) -> ChapterSummary:
        """
        为单个章节创建摘要
        
        现在集成LLM来生成智能摘要，优先使用AI，回退到规则方法
        """
        # 提取章节标题（假设格式：第X回 标题）
        lines = chapter_text.split('\n')
        title = lines[0] if lines else f"第{chapter_num}回"
        
        if self.use_llm and self.llm_manager:
            try:
                # 使用LLM生成智能摘要
                summary_data = self._create_llm_summary(chapter_text, chapter_num, title)
                
                return ChapterSummary(
                    chapter_num=chapter_num,
                    title=title,
                    key_events=summary_data.get('key_events', []),
                    character_states=summary_data.get('character_states', {}),
                    important_dialogues=summary_data.get('important_dialogues', []),
                    plot_developments=summary_data.get('plot_developments', []),
                    emotional_tone=summary_data.get('emotional_tone', '平和'),
                    word_count=len(chapter_text)
                )
                
            except Exception as e:
                logger.warning(f"LLM摘要生成失败，回退到规则方法: {e}")
                # 回退到规则方法
                pass
        
        # 规则方法（作为备用）
        key_events = self._extract_key_events(chapter_text)
        character_states = self._extract_character_states_from_text(chapter_text)
        important_dialogues = self._extract_important_dialogues(chapter_text)
        plot_developments = self._extract_plot_developments(chapter_text)
        emotional_tone = self._analyze_emotional_tone(chapter_text)
        
        return ChapterSummary(
            chapter_num=chapter_num,
            title=title,
            key_events=key_events,
            character_states=character_states,
            important_dialogues=important_dialogues,
            plot_developments=plot_developments,
            emotional_tone=emotional_tone,
            word_count=len(chapter_text)
        )
    
    def _create_llm_summary(self, chapter_text: str, chapter_num: int, title: str) -> Dict[str, Any]:
        """使用LLM创建智能章节摘要"""
        
        # 如果章节文本太长，先进行截取
        max_text_length = 3000
        if len(chapter_text) > max_text_length:
            # 取开头和结尾部分
            half_length = max_text_length // 2
            truncated_text = chapter_text[:half_length] + "\n...(中间部分省略)...\n" + chapter_text[-half_length:]
        else:
            truncated_text = chapter_text
        
        # 构建LLM提示词
        system_prompt = """你是红楼梦文学分析专家，请对给定的章节文本进行智能摘要分析。

请按照以下JSON格式返回分析结果：
{
    "key_events": ["事件1", "事件2", "事件3"],
    "character_states": {"人物名": "状态描述"},
    "important_dialogues": ["重要对话1", "重要对话2"],
    "plot_developments": ["情节发展1", "情节发展2"],
    "emotional_tone": "情感基调"
}

要求：
1. key_events: 提取3-5个最重要的事件，简洁描述
2. character_states: 识别主要人物及其当前状态/情感
3. important_dialogues: 提取2-3个关键对话，保持原文风格
4. plot_developments: 识别2-3个重要的情节推进
5. emotional_tone: 用一个词概括章节的主要情感基调（如：欢乐、悲伤、紧张、平和等）"""
        
        prompt = f"""请分析以下红楼梦章节内容：

章节信息：{title}

章节内容：
{truncated_text}

请严格按照JSON格式返回分析结果。"""
        
        try:
            # 使用统一的LLM管理器
            response = self.llm_manager.simple_call(
                prompt=prompt,
                system_prompt=system_prompt,
                task="context_compression"
            )
            
            response_text = response.content.strip()
            
            # 尝试解析JSON响应
            if response_text.startswith('```json'):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith('```'):
                response_text = response_text[3:-3].strip()
            
            summary_data = json.loads(response_text)
            
            # 验证和清理数据
            cleaned_data = {
                'key_events': summary_data.get('key_events', [])[:5],  # 最多5个事件
                'character_states': summary_data.get('character_states', {}),
                'important_dialogues': summary_data.get('important_dialogues', [])[:3],  # 最多3个对话
                'plot_developments': summary_data.get('plot_developments', [])[:3],  # 最多3个发展
                'emotional_tone': summary_data.get('emotional_tone', '平和')
            }
            
            logger.info(f"LLM成功生成第{chapter_num}回摘要")
            return cleaned_data
            
        except json.JSONDecodeError as e:
            logger.error(f"LLM响应JSON解析失败: {e}, 响应内容: {response_text[:200]}")
            raise
        except Exception as e:
            logger.error(f"LLM摘要生成异常: {e}")
            raise

    def _extract_key_events(self, text: str) -> List[str]:
        """提取关键事件 - TODO: 需要智能化"""
        # 简单实现：查找包含动作词的句子
        import re
        sentences = re.split(r'[。！？]', text)
        key_events = []
        
        action_keywords = ['去了', '来了', '说道', '笑道', '见了', '听了', '想起']
        for sentence in sentences[:20]:  # 限制数量
            if any(keyword in sentence for keyword in action_keywords):
                if len(sentence) > 10 and len(sentence) < 100:
                    key_events.append(sentence.strip())
        
        return key_events[:5]  # 最多5个关键事件
    
    def _extract_character_states_from_text(self, text: str) -> Dict[str, str]:
        """从文本中提取人物状态 - TODO: 需要智能化"""
        # 简单实现：检测人物和情感词汇的组合
        character_states = {}
        
        # 主要人物列表（从知识图谱获取）
        main_characters = ['宝玉', '黛玉', '宝钗', '王熙凤', '贾母', '宝玉']
        emotion_words = ['高兴', '生气', '伤心', '担心', '欢喜', '恼怒', '思念']
        
        for char in main_characters:
            if char in text:
                # 查找该人物附近的情感词汇
                for emotion in emotion_words:
                    if f"{char}" in text and emotion in text:
                        character_states[char] = emotion
                        break
        
        return character_states
    
    def _extract_important_dialogues(self, text: str) -> List[str]:
        """提取重要对话 - TODO: 需要智能化"""
        import re
        # 查找对话模式："XXX道："
        dialogue_pattern = r'([^"]*?)道："([^"]*)"'
        dialogues = re.findall(dialogue_pattern, text)
        
        important_dialogues = []
        for speaker, content in dialogues[:3]:  # 最多3个对话
            if len(content) > 5 and len(content) < 50:
                important_dialogues.append(f'{speaker.strip()}道："{content}"')
        
        return important_dialogues
    
    def _extract_plot_developments(self, text: str) -> List[str]:
        """提取情节发展 - TODO: 需要智能化"""
        # 简单实现：查找情节推进相关的句子
        plot_keywords = ['决定', '打算', '计划', '发生', '突然', '原来', '后来']
        sentences = text.split('。')
        
        plot_developments = []
        for sentence in sentences:
            if any(keyword in sentence for keyword in plot_keywords):
                if len(sentence) > 15 and len(sentence) < 80:
                    plot_developments.append(sentence.strip())
        
        return plot_developments[:3]  # 最多3个情节发展
    
    def _analyze_emotional_tone(self, text: str) -> str:
        """分析章节情感基调 - TODO: 需要智能化"""
        # 简单实现：统计情感词汇
        positive_words = ['高兴', '欢喜', '笑', '乐', '喜']
        negative_words = ['伤心', '哭', '愁', '恼', '怒', '悲']
        
        positive_count = sum(text.count(word) for word in positive_words)
        negative_count = sum(text.count(word) for word in negative_words)
        
        if positive_count > negative_count:
            return "欢乐"
        elif negative_count > positive_count:
            return "悲伤"
        else:
            return "平和"
    
    def _extract_character_states(self, summaries: List[ChapterSummary]) -> Dict[str, Any]:
        """从多个章节摘要中提取人物状态"""
        character_states = {}
        
        for summary in summaries:
            for char, state in summary.character_states.items():
                if char not in character_states:
                    character_states[char] = {
                        'current_state': state,
                        'chapter': summary.chapter_num,
                        'developments': []
                    }
                character_states[char]['developments'].append({
                    'chapter': summary.chapter_num,
                    'state': state
                })
        
        return character_states
    
    def _extract_plot_threads(self, summaries: List[ChapterSummary]) -> List[str]:
        """提取持续的情节线索"""
        all_plot_developments = []
        for summary in summaries:
            all_plot_developments.extend(summary.plot_developments)
        
        # TODO: 使用更智能的方法识别持续的情节线索
        # 目前简单返回最近的情节发展
        return all_plot_developments[-5:] if all_plot_developments else []
    
    def _extract_relationships(self, summaries: List[ChapterSummary]) -> Dict[str, List[str]]:
        """提取重要人物关系"""
        relationships = {}
        
        # TODO: 基于对话和共同出现来分析人物关系
        # 目前返回基础关系
        main_characters = ['宝玉', '黛玉', '宝钗', '王熙凤']
        for char in main_characters:
            relationships[char] = [c for c in main_characters if c != char]
        
        return relationships
    
    def _estimate_compressed_size(self, summaries: List[ChapterSummary]) -> int:
        """估算压缩后的大小"""
        total_size = 0
        for summary in summaries:
            # 估算每个摘要的字符数
            size = (
                len(summary.title) +
                sum(len(event) for event in summary.key_events) +
                sum(len(f"{k}:{v}") for k, v in summary.character_states.items()) +
                sum(len(dialogue) for dialogue in summary.important_dialogues) +
                sum(len(dev) for dev in summary.plot_developments)
            )
            total_size += size
        
        return total_size
    
    def generate_context_prompt(self, compressed_context: CompressedContext, 
                              current_context: str) -> str:
        """
        生成用于续写的上下文提示词
        
        Args:
            compressed_context: 压缩的历史上下文
            current_context: 当前章节的上下文
            
        Returns:
            str: 格式化的上下文提示词
        """
        prompt_parts = []
        
        # 1. 历史章节摘要
        prompt_parts.append("## 前文要点摘要")
        for summary in compressed_context.previous_chapters_summary[-5:]:  # 最近5章
            prompt_parts.append(f"### {summary.title}")
            prompt_parts.append(f"关键事件：{'; '.join(summary.key_events[:3])}")
            if summary.character_states:
                states = ', '.join(f"{k}:{v}" for k, v in summary.character_states.items())
                prompt_parts.append(f"人物状态：{states}")
        
        # 2. 当前人物状态
        prompt_parts.append("\n## 当前人物状态")
        for char, state in compressed_context.key_character_states.items():
            prompt_parts.append(f"- {char}: {state.get('current_state', '未知')}")
        
        # 3. 进行中的情节线索
        if compressed_context.ongoing_plot_threads:
            prompt_parts.append("\n## 进行中的情节线索")
            for thread in compressed_context.ongoing_plot_threads:
                prompt_parts.append(f"- {thread}")
        
        # 4. 当前上下文
        prompt_parts.append(f"\n## 当前章节上下文\n{current_context}")
        
        return '\n'.join(prompt_parts)
    
    def save_compressed_context(self, context: CompressedContext, 
                              file_path: str) -> None:
        """保存压缩上下文到文件"""
        try:
            # 转换为可序列化的格式
            context_dict = {
                'current_chapter': context.current_chapter,
                'previous_chapters_summary': [
                    {
                        'chapter_num': s.chapter_num,
                        'title': s.title,
                        'key_events': s.key_events,
                        'character_states': s.character_states,
                        'important_dialogues': s.important_dialogues,
                        'plot_developments': s.plot_developments,
                        'emotional_tone': s.emotional_tone,
                        'word_count': s.word_count
                    }
                    for s in context.previous_chapters_summary
                ],
                'key_character_states': context.key_character_states,
                'ongoing_plot_threads': context.ongoing_plot_threads,
                'important_relationships': context.important_relationships,
                'compressed_word_count': context.compressed_word_count,
                'original_word_count': context.original_word_count,
                'compression_ratio': context.compression_ratio
            }
            
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(context_dict, f, ensure_ascii=False, indent=2)
            
            logger.info(f"压缩上下文已保存到: {file_path}")
            
        except Exception as e:
            logger.error(f"保存压缩上下文失败: {e}")
            raise 