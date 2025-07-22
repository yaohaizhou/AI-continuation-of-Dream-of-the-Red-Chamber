"""
知识增强提示词生成器 - 将知识检索结果整合到续写提示词中
"""

from typing import Dict, List, Optional, Any
from langchain.prompts import PromptTemplate
from loguru import logger

from .knowledge_retriever import KnowledgeRetriever


class EnhancedPrompter:
    """知识增强提示词生成器"""
    
    def __init__(self, data_dir: str = "data/processed"):
        """
        初始化增强提示词生成器
        
        Args:
            data_dir: 数据目录路径
        """
        self.knowledge_retriever = KnowledgeRetriever(data_dir)
        
        # 定义增强提示词模板
        self._init_enhanced_templates()
        
        logger.info("知识增强提示词生成器初始化完成")
    
    def _init_enhanced_templates(self):
        """初始化增强提示词模板"""
        
        # 知识增强基础续写模板
        self.ENHANCED_BASIC_TEMPLATE = """你是一位精通《红楼梦》的文学大师，请根据以下丰富的背景知识进行续写。

{knowledge_enhancement}

【原文上下文】
{context}

【续写要求】
1. 严格保持曹雪芹的写作风格和叙事特点
2. 确保人物性格与原著完全一致
3. 注意情节的逻辑性和连贯性
4. 使用典雅的古典文学语言
5. 体现红楼梦深厚的文化内涵
6. 续写长度约{max_length}字

请基于以上知识背景开始续写："""

        # 知识增强对话续写模板
        self.ENHANCED_DIALOGUE_TEMPLATE = """你是《红楼梦》续写专家，请根据以下角色背景信息续写对话场景。

{character_enhancement}

【当前场景】
{scene_context}

【对话背景】
{dialogue_context}

【续写要求】
1. 每个人物的说话风格要完全符合其性格特点
2. 保持古典文学的对话特色和称谓习惯
3. 适当加入动作描写和心理描写
4. 语言要优雅含蓄，体现红楼梦的文学品质
5. 注意人物之间的关系和身份差异

请续写对话："""

        # 知识增强场景描写模板
        self.ENHANCED_SCENE_TEMPLATE = """你是《红楼梦》场景描写专家，请根据以下场景背景信息进行续写。

{scene_enhancement}

【原文上下文】
{context}

【描写要求】
1. 充分体现地点的特色和氛围
2. 使用丰富的感官描写
3. 融入诗词意境和古典美学
4. 注意季节、时间等环境因素
5. 体现红楼梦细腻优美的文学风格
6. 续写长度约{max_length}字

请开始场景续写："""

        # 知识增强诗词创作模板
        self.ENHANCED_POETRY_TEMPLATE = """你是《红楼梦》诗词创作专家，请根据以下背景信息创作诗词。

{vocabulary_enhancement}

【创作背景】
{context}

【创作要求】
1. 符合红楼梦的诗词风格和格律
2. 体现人物的才情和性格特点
3. 融入情景交融的意境
4. 使用典雅的古典诗词语言
5. 注意平仄和韵律的和谐
6. 可创作律诗、绝句、词等形式

请开始诗词创作："""

    def generate_enhanced_prompt(self, context: str, prompt_type: str = "basic", 
                               max_length: int = 800, **kwargs) -> str:
        """
        生成知识增强的提示词
        
        Args:
            context: 原始上下文
            prompt_type: 提示词类型 (basic/dialogue/scene/poetry)
            max_length: 续写长度
            **kwargs: 其他参数
            
        Returns:
            str: 增强后的提示词
        """
        logger.info(f"生成{prompt_type}类型的知识增强提示词")
        
        if prompt_type == "basic":
            return self._generate_basic_enhanced_prompt(context, max_length)
        
        elif prompt_type == "dialogue":
            scene_context = kwargs.get('scene_context', context)
            dialogue_context = kwargs.get('dialogue_context', '')
            return self._generate_dialogue_enhanced_prompt(
                context, scene_context, dialogue_context
            )
        
        elif prompt_type == "scene":
            return self._generate_scene_enhanced_prompt(context, max_length)
        
        elif prompt_type == "poetry":
            return self._generate_poetry_enhanced_prompt(context)
        
        else:
            logger.warning(f"未知的提示词类型: {prompt_type}")
            return self._generate_basic_enhanced_prompt(context, max_length)
    
    def _generate_basic_enhanced_prompt(self, context: str, max_length: int) -> str:
        """生成基础续写的增强提示词"""
        # 获取综合知识上下文
        knowledge_context = self.knowledge_retriever.retrieve_comprehensive_context(context)
        
        # 格式化知识增强内容
        knowledge_enhancement = self.knowledge_retriever._format_comprehensive_enhancement(
            knowledge_context
        )
        
        # 生成最终提示词
        prompt = self.ENHANCED_BASIC_TEMPLATE.format(
            knowledge_enhancement=knowledge_enhancement,
            context=context,
            max_length=max_length
        )
        
        return prompt
    
    def _generate_dialogue_enhanced_prompt(self, context: str, scene_context: str, 
                                         dialogue_context: str) -> str:
        """生成对话续写的增强提示词"""
        # 提取主要角色
        entity_context = self.knowledge_retriever.entity_retriever.get_context_entities(context)
        characters = entity_context['extracted_entities'].get('persons', [])
        
        character_enhancement = ""
        if characters:
            # 获取主要角色的增强信息
            for char in characters[:2]:  # 最多两个主要角色
                char_context = self.knowledge_retriever.get_character_enhancement_context(char)
                char_enhancement = self.knowledge_retriever._format_character_enhancement(char_context)
                character_enhancement += char_enhancement + "\n\n"
        
        # 生成最终提示词
        prompt = self.ENHANCED_DIALOGUE_TEMPLATE.format(
            character_enhancement=character_enhancement.strip(),
            scene_context=scene_context,
            dialogue_context=dialogue_context
        )
        
        return prompt
    
    def _generate_scene_enhanced_prompt(self, context: str, max_length: int) -> str:
        """生成场景描写的增强提示词"""
        # 提取地点信息
        entity_context = self.knowledge_retriever.entity_retriever.get_context_entities(context)
        location = entity_context['location_context'].get('main_location')
        
        scene_enhancement = ""
        if location:
            scene_context = self.knowledge_retriever.get_scene_enhancement_context(location)
            scene_enhancement = self.knowledge_retriever._format_scene_enhancement(scene_context)
        
        # 生成最终提示词
        prompt = self.ENHANCED_SCENE_TEMPLATE.format(
            scene_enhancement=scene_enhancement,
            context=context,
            max_length=max_length
        )
        
        return prompt
    
    def _generate_poetry_enhanced_prompt(self, context: str) -> str:
        """生成诗词创作的增强提示词"""
        # 获取词汇建议
        vocab_suggestions = self.knowledge_retriever.vocabulary_suggester.suggest_words_by_context(context)
        vocabulary_enhancement = self.knowledge_retriever._format_vocabulary_enhancement(
            vocab_suggestions
        )
        
        # 生成最终提示词
        prompt = self.ENHANCED_POETRY_TEMPLATE.format(
            vocabulary_enhancement=vocabulary_enhancement,
            context=context
        )
        
        return prompt
    
    def create_langchain_prompt_template(self, prompt_type: str = "basic") -> PromptTemplate:
        """
        创建LangChain兼容的提示词模板
        
        Args:
            prompt_type: 提示词类型
            
        Returns:
            PromptTemplate: LangChain提示词模板
        """
        if prompt_type == "basic":
            template = self.ENHANCED_BASIC_TEMPLATE
            input_variables = ["knowledge_enhancement", "context", "max_length"]
        
        elif prompt_type == "dialogue":
            template = self.ENHANCED_DIALOGUE_TEMPLATE
            input_variables = ["character_enhancement", "scene_context", "dialogue_context"]
        
        elif prompt_type == "scene":
            template = self.ENHANCED_SCENE_TEMPLATE
            input_variables = ["scene_enhancement", "context", "max_length"]
        
        elif prompt_type == "poetry":
            template = self.ENHANCED_POETRY_TEMPLATE
            input_variables = ["vocabulary_enhancement", "context"]
        
        else:
            template = self.ENHANCED_BASIC_TEMPLATE
            input_variables = ["knowledge_enhancement", "context", "max_length"]
        
        return PromptTemplate(
            input_variables=input_variables,
            template=template
        )
    
    def get_prompt_with_context_analysis(self, context: str, prompt_type: str = "basic", 
                                       **kwargs) -> Dict[str, Any]:
        """
        获取带有上下文分析的完整提示词信息
        
        Args:
            context: 原始上下文
            prompt_type: 提示词类型
            **kwargs: 其他参数
            
        Returns:
            Dict: 包含提示词和分析信息的字典
        """
        # 生成增强提示词
        enhanced_prompt = self.generate_enhanced_prompt(context, prompt_type, **kwargs)
        
        # 获取知识分析
        knowledge_context = self.knowledge_retriever.retrieve_comprehensive_context(context)
        
        return {
            'enhanced_prompt': enhanced_prompt,
            'original_context': context,
            'knowledge_analysis': knowledge_context,
            'prompt_type': prompt_type,
            'enhancement_summary': {
                'identified_characters': knowledge_context['knowledge_summary']['main_characters'],
                'identified_location': knowledge_context['knowledge_summary']['main_location'],
                'suggested_style': knowledge_context['knowledge_summary']['suggested_writing_style'],
                'character_relationships': knowledge_context['knowledge_summary']['character_relationships']
            }
        }
    
    def batch_generate_prompts(self, contexts: List[str], prompt_type: str = "basic", 
                             **kwargs) -> List[Dict[str, Any]]:
        """
        批量生成增强提示词
        
        Args:
            contexts: 上下文列表
            prompt_type: 提示词类型
            **kwargs: 其他参数
            
        Returns:
            List: 增强提示词列表
        """
        results = []
        
        for i, context in enumerate(contexts):
            logger.info(f"处理第{i+1}/{len(contexts)}个上下文")
            try:
                result = self.get_prompt_with_context_analysis(context, prompt_type, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"处理上下文失败: {e}")
                results.append({
                    'enhanced_prompt': f"处理失败: {str(e)}",
                    'original_context': context,
                    'error': str(e)
                })
        
        return results


if __name__ == "__main__":
    # 测试代码
    prompter = EnhancedPrompter()
    
    test_context = "话说宝玉那日在潇湘馆，忽见黛玉倚竹而立"
    
    # 测试基础续写提示词
    enhanced_prompt = prompter.generate_enhanced_prompt(test_context, "basic", max_length=500)
    print("增强提示词:")
    print(enhanced_prompt)
    
    # 测试完整上下文分析
    full_analysis = prompter.get_prompt_with_context_analysis(test_context, "basic")
    print(f"\n增强摘要:")
    for key, value in full_analysis['enhancement_summary'].items():
        print(f"{key}: {value}") 