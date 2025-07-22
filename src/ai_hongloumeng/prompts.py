"""
提示词模板模块
包含用于AI续写红楼梦的各种提示词模板
"""

from langchain.prompts import PromptTemplate
from typing import Dict, Any


class PromptTemplates:
    """提示词模板类"""
    
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