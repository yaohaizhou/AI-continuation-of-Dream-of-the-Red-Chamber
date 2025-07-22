"""
提示词模板模块
包含用于AI续写红楼梦的各种提示词模板
现已集成知识增强功能
"""

from langchain.prompts import PromptTemplate
from typing import Dict, Any, Optional

try:
    from knowledge_enhancement import EnhancedPrompter
except ImportError:
    # 如果知识增强模块不可用，定义一个占位符
    EnhancedPrompter = None


class PromptTemplates:
    """提示词模板类，现已集成知识增强功能"""
    
    def __init__(self, enable_knowledge_enhancement: bool = True):
        """
        初始化提示词模板类
        
        Args:
            enable_knowledge_enhancement: 是否启用知识增强功能
        """
        self.enable_knowledge_enhancement = enable_knowledge_enhancement
        self.enhanced_prompter = None
        
        if enable_knowledge_enhancement:
            try:
                if EnhancedPrompter is not None:
                    self.enhanced_prompter = EnhancedPrompter()
                else:
                    print("知识增强模块不可用，将使用传统提示词")
                    self.enable_knowledge_enhancement = False
            except Exception as e:
                print(f"知识增强功能初始化失败，将使用传统提示词: {e}")
                self.enable_knowledge_enhancement = False
    
    # 基础续写提示词
    BASIC_CONTINUATION_TEMPLATE = """你是一位精通中国古典文学的作家，特别擅长《红楼梦》的写作风格。
请根据以下上下文，以曹雪芹的写作风格续写《红楼梦》。

写作要求：
1. 保持原著的语言风格和叙事特点
2. 保持人物性格的一致性
3. 注意情节的逻辑性和连贯性
4. 使用古典优雅的文言文和白话文结合的语言
5. 体现红楼梦的诗词文化和情感深度

上下文：
{context}

续写长度：约{max_length}字

请开始续写："""

    # 人物对话续写提示词
    CHARACTER_DIALOGUE_TEMPLATE = """请以《红楼梦》的风格续写以下场景中的人物对话。

人物信息：
{character_info}

当前场景：
{scene_context}

对话背景：
{dialogue_context}

请注意：
1. 每个人物的说话风格要符合其性格特点
2. 保持古典文学的对话特色
3. 适当加入动作描写和心理描写
4. 语言要优雅含蓄，符合红楼梦的文学品质

请续写对话："""

    # 场景描写提示词  
    SCENE_DESCRIPTION_TEMPLATE = """请以《红楼梦》的风格描写以下场景。

场景设定：
{scene_setting}

时间：{time}
地点：{location}
相关人物：{characters}

描写要求：
1. 运用细腻的笔触描绘环境氛围
2. 融入诗词意境和文化内涵
3. 体现红楼梦特有的美学风格
4. 注意季节、时辰对环境的影响
5. 适当运用象征和暗示手法

请开始描写："""

    # 诗词创作提示词
    POETRY_CREATION_TEMPLATE = """请为《红楼梦》续写章节创作一首{poetry_type}。

主题：{theme}
情境：{context}
创作者：{character}（如果指定）

要求：
1. 符合古典诗词的格律要求
2. 体现红楼梦的诗词风格和意境
3. 与故事情节和人物性格相符
4. 语言典雅，意境深远
5. 如有指定创作者，需符合该人物的文学水平和性格特点

请创作诗词："""

    # 章节总结提示词
    CHAPTER_SUMMARY_TEMPLATE = """请为以下《红楼梦》续写内容创作章节标题和简要概述。

章节内容：
{chapter_content}

要求：
1. 标题要体现红楼梦的命名特色（如"xxx xxx"的对偶格式）
2. 概述要简洁明了，突出主要情节
3. 保持与原著章节标题的风格一致
4. 体现章节的主要主题和转折点

请创作："""

    @classmethod
    def get_basic_continuation_prompt(cls) -> PromptTemplate:
        """获取基础续写提示词模板"""
        return PromptTemplate(
            template=cls.BASIC_CONTINUATION_TEMPLATE,
            input_variables=["context", "max_length"]
        )
    
    @classmethod  
    def get_character_dialogue_prompt(cls) -> PromptTemplate:
        """获取人物对话提示词模板"""
        return PromptTemplate(
            template=cls.CHARACTER_DIALOGUE_TEMPLATE,
            input_variables=["character_info", "scene_context", "dialogue_context"]
        )
    
    @classmethod
    def get_scene_description_prompt(cls) -> PromptTemplate:
        """获取场景描写提示词模板"""
        return PromptTemplate(
            template=cls.SCENE_DESCRIPTION_TEMPLATE,
            input_variables=["scene_setting", "time", "location", "characters"]
        )
    
    @classmethod
    def get_poetry_creation_prompt(cls) -> PromptTemplate:
        """获取诗词创作提示词模板"""
        return PromptTemplate(
            template=cls.POETRY_CREATION_TEMPLATE,
            input_variables=["poetry_type", "theme", "context", "character"]
        )
    
    @classmethod
    def get_chapter_summary_prompt(cls) -> PromptTemplate:
        """获取章节总结提示词模板"""
        return PromptTemplate(
            template=cls.CHAPTER_SUMMARY_TEMPLATE,
            input_variables=["chapter_content"]
        )
    
    @classmethod
    def get_custom_prompt(cls, template: str, variables: list) -> PromptTemplate:
        """创建自定义提示词模板"""
        return PromptTemplate(
            template=template,
            input_variables=variables
        )
    
    def get_enhanced_prompt(self, context: str, prompt_type: str = "basic", 
                          max_length: int = 800, **kwargs) -> str:
        """
        获取知识增强的提示词
        
        Args:
            context: 原始上下文
            prompt_type: 提示词类型 (basic/dialogue/scene/poetry)
            max_length: 续写长度
            **kwargs: 其他参数
            
        Returns:
            str: 增强后的提示词
        """
        if self.enable_knowledge_enhancement and self.enhanced_prompter:
            return self.enhanced_prompter.generate_enhanced_prompt(
                context, prompt_type, max_length, **kwargs
            )
        else:
            # 回退到传统提示词
            if prompt_type == "basic":
                template = self.BASIC_CONTINUATION_TEMPLATE
                return template.format(context=context, max_length=max_length)
            elif prompt_type == "dialogue":
                template = self.CHARACTER_DIALOGUE_TEMPLATE
                return template.format(
                    character_info=kwargs.get('character_info', ''),
                    scene_context=kwargs.get('scene_context', context),
                    dialogue_context=kwargs.get('dialogue_context', '')
                )
            else:
                template = self.BASIC_CONTINUATION_TEMPLATE
                return template.format(context=context, max_length=max_length)
    
    def analyze_context(self, context: str) -> Optional[Dict]:
        """
        分析上下文，提取知识信息
        
        Args:
            context: 上下文文本
            
        Returns:
            Dict: 分析结果，如果未启用知识增强则返回None
        """
        if self.enable_knowledge_enhancement and self.enhanced_prompter:
            analysis = self.enhanced_prompter.get_prompt_with_context_analysis(context)
            return analysis['enhancement_summary']
        return None
    
    def get_writing_suggestions(self, context: str) -> Dict[str, Any]:
        """
        获取写作建议
        
        Args:
            context: 上下文文本
            
        Returns:
            Dict: 写作建议
        """
        suggestions = {
            'knowledge_enhanced': self.enable_knowledge_enhancement,
            'characters': [],
            'locations': [],
            'suggested_style': 'classical',
            'enhancement_available': bool(self.enhanced_prompter)
        }
        
        if self.enable_knowledge_enhancement and self.enhanced_prompter:
            analysis = self.analyze_context(context)
            if analysis:
                suggestions.update({
                    'characters': analysis.get('identified_characters', []),
                    'locations': [analysis.get('identified_location')] if analysis.get('identified_location') else [],
                    'suggested_style': analysis.get('suggested_style', 'classical'),
                    'character_relationships': analysis.get('character_relationships', '')
                })
        
        return suggestions