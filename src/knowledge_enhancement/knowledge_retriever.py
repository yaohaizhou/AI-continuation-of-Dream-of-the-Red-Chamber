"""
主要知识检索器 - 整合所有知识检索功能的核心模块
"""

from typing import Dict, List, Optional, Any
from loguru import logger

from .entity_retriever import EntityRetriever
from .relationship_retriever import RelationshipRetriever
from .vocabulary_suggester import VocabularySuggester


class KnowledgeRetriever:
    """知识检索器主类，整合所有知识检索功能"""
    
    def __init__(self, data_dir: str = "data/processed"):
        """
        初始化知识检索器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        
        # 初始化各个子模块
        self.entity_retriever = EntityRetriever(data_dir)
        self.relationship_retriever = RelationshipRetriever(data_dir)
        self.vocabulary_suggester = VocabularySuggester(data_dir)
        
        logger.info("知识检索器初始化完成")
    
    def retrieve_comprehensive_context(self, text: str) -> Dict[str, Any]:
        """
        获取文本的全面知识上下文
        
        Args:
            text: 输入文本
            
        Returns:
            Dict: 综合的知识上下文信息
        """
        logger.info(f"开始检索文本知识上下文: {text[:50]}...")
        
        # 1. 实体检索
        entity_context = self.entity_retriever.get_context_entities(text)
        
        # 2. 关系检索
        characters = entity_context['extracted_entities'].get('persons', [])
        location = entity_context['location_context'].get('main_location')
        
        relationship_context = {}
        scene_characters = []
        
        if characters:
            # 获取人物关系
            relationship_context = self.relationship_retriever.get_relationship_context(characters)
            
            # 推荐场景角色
            scene_characters = self.relationship_retriever.get_scene_characters(
                characters, location
            )
        
        # 3. 词汇建议
        vocabulary_suggestions = self.vocabulary_suggester.suggest_words_by_context(text)
        
        # 构建综合上下文
        comprehensive_context = {
            'input_text': text,
            'entity_analysis': entity_context,
            'relationship_analysis': relationship_context,
            'scene_recommendations': {
                'recommended_characters': scene_characters,
                'main_location': location,
                'group_dynamics': relationship_context.get('group_dynamics', '')
            },
            'vocabulary_enhancement': vocabulary_suggestions,
            'knowledge_summary': self._generate_knowledge_summary(
                entity_context, relationship_context, vocabulary_suggestions
            )
        }
        
        logger.info("知识上下文检索完成")
        return comprehensive_context
    
    def _generate_knowledge_summary(self, entity_context: Dict, 
                                  relationship_context: Dict, 
                                  vocabulary_suggestions: Dict) -> Dict[str, str]:
        """生成知识摘要"""
        summary = {
            'main_characters': [],
            'main_location': '',
            'character_relationships': '',
            'scene_atmosphere': '',
            'suggested_writing_style': ''
        }
        
        # 主要人物
        persons = entity_context['extracted_entities'].get('persons', [])
        summary['main_characters'] = persons[:3]  # 前3个主要人物
        
        # 主要地点
        location_context = entity_context.get('location_context', {})
        if location_context:
            summary['main_location'] = location_context.get('main_location', '')
        
        # 人物关系描述
        if relationship_context:
            summary['character_relationships'] = relationship_context.get('group_dynamics', '')
        
        # 场景氛围
        if summary['main_location']:
            scene_vocab = self.vocabulary_suggester.suggest_scene_vocabulary(summary['main_location'])
            atmosphere_words = scene_vocab.get('atmosphere_words', [])
            if atmosphere_words:
                summary['scene_atmosphere'] = '、'.join(atmosphere_words[:3])
        
        # 建议的写作风格
        high_freq_words = vocabulary_suggestions.get('high_frequency', [])
        if any(word in str(vocabulary_suggestions) for word in ['情', '爱', '思']):
            summary['suggested_writing_style'] = 'emotional'
        elif summary['main_location'] in ['潇湘馆', '蘅芜苑']:
            summary['suggested_writing_style'] = 'elegant'
        elif summary['main_location'] in ['怡红院']:
            summary['suggested_writing_style'] = 'luxurious'
        else:
            summary['suggested_writing_style'] = 'classical'
        
        return summary
    
    def get_character_enhancement_context(self, character: str) -> Dict[str, Any]:
        """
        获取特定角色的增强上下文
        
        Args:
            character: 角色名称
            
        Returns:
            Dict: 角色增强上下文
        """
        logger.info(f"获取角色增强上下文: {character}")
        
        # 获取角色详细信息
        entity_info = self.entity_retriever.get_entity_info(character, 'persons')
        
        # 获取角色关系
        relationships = self.relationship_retriever.get_character_relationships(character)
        
        # 获取角色专用词汇
        character_vocab = self.vocabulary_suggester.suggest_character_vocabulary(character)
        
        enhancement_context = {
            'character': character,
            'entity_info': entity_info,
            'relationships': relationships,
            'character_vocabulary': character_vocab,
            'writing_suggestions': {
                'personality_traits': entity_info.get('description', ''),
                'common_companions': [
                    char for char, _ in relationships.get('co_occurrence_relations', [])[:3]
                ],
                'typical_actions': character_vocab.get('action_words', []),
                'speech_style': self._get_character_speech_style(character)
            }
        }
        
        return enhancement_context
    
    def _get_character_speech_style(self, character: str) -> str:
        """获取角色说话风格"""
        speech_styles = {
            '贾宝玉': '温柔体贴，常用"妹妹"、"姐姐"等亲昵称呼',
            '林黛玉': '敏感细腻，言语中常带有愁绪和诗意',
            '薛宝钗': '温和稳重，说话得体大方，很少急躁',
            '王熙凤': '机敏风趣，说话直率，善于调侃和管理',
            '贾母': '慈祥和蔼，说话简短有力，充满长辈关爱'
        }
        
        # 标准化角色名称
        main_name = self.vocabulary_suggester._normalize_character_name(character)
        return speech_styles.get(main_name, '根据人物性格特点说话')
    
    def get_scene_enhancement_context(self, location: str, characters: List[str] = None) -> Dict[str, Any]:
        """
        获取场景增强上下文
        
        Args:
            location: 地点名称
            characters: 角色列表（可选）
            
        Returns:
            Dict: 场景增强上下文
        """
        logger.info(f"获取场景增强上下文: {location}")
        
        # 获取地点信息
        location_info = self.entity_retriever.get_entity_info(location, 'locations')
        
        # 获取场景词汇
        scene_vocab = self.vocabulary_suggester.suggest_scene_vocabulary(location)
        
        # 推荐场景角色
        if not characters:
            characters = []
        
        scene_characters = self.relationship_retriever.get_scene_characters(
            characters, location
        )
        
        enhancement_context = {
            'location': location,
            'location_info': location_info,
            'scene_vocabulary': scene_vocab,
            'recommended_characters': scene_characters,
            'scene_description': {
                'physical_description': location_info.get('description', ''),
                'atmosphere': scene_vocab.get('atmosphere_words', []),
                'typical_activities': scene_vocab.get('action_words', []),
                'common_objects': scene_vocab.get('object_words', [])
            }
        }
        
        return enhancement_context
    
    def generate_writing_prompt_enhancement(self, context: str, 
                                          enhancement_type: str = "comprehensive") -> str:
        """
        生成写作提示词增强内容
        
        Args:
            context: 原始上下文
            enhancement_type: 增强类型 (comprehensive/character/scene/vocabulary)
            
        Returns:
            str: 增强后的提示词内容
        """
        logger.info(f"生成{enhancement_type}类型的提示词增强")
        
        if enhancement_type == "comprehensive":
            knowledge_context = self.retrieve_comprehensive_context(context)
            return self._format_comprehensive_enhancement(knowledge_context)
        
        elif enhancement_type == "character":
            # 提取主要角色
            entity_context = self.entity_retriever.get_context_entities(context)
            characters = entity_context['extracted_entities'].get('persons', [])
            if characters:
                char_context = self.get_character_enhancement_context(characters[0])
                return self._format_character_enhancement(char_context)
        
        elif enhancement_type == "scene":
            # 提取主要地点
            entity_context = self.entity_retriever.get_context_entities(context)
            location = entity_context['location_context'].get('main_location')
            if location:
                scene_context = self.get_scene_enhancement_context(location)
                return self._format_scene_enhancement(scene_context)
        
        elif enhancement_type == "vocabulary":
            vocab_suggestions = self.vocabulary_suggester.suggest_words_by_context(context)
            return self._format_vocabulary_enhancement(vocab_suggestions)
        
        return ""
    
    def _format_comprehensive_enhancement(self, knowledge_context: Dict) -> str:
        """格式化综合增强内容"""
        summary = knowledge_context['knowledge_summary']
        entity_analysis = knowledge_context['entity_analysis']
        relationship_analysis = knowledge_context['relationship_analysis']
        
        enhancement = f"""
【知识背景增强】

【主要人物】
{', '.join(summary['main_characters'])} 

【人物关系】
{summary['character_relationships']}

【场景信息】
地点: {summary['main_location']}
氛围: {summary['scene_atmosphere']}

【人物特征】
"""
        
        # 添加人物描述
        for entity_type, entities in entity_analysis['entity_details'].items():
            if entity_type == 'persons':
                for person, info in entities.items():
                    enhancement += f"- {person}: {info['description']}\n"
        
        enhancement += f"""
【建议的写作风格】
{summary['suggested_writing_style']}风格，体现红楼梦的文学特色

【场景推荐角色】
{', '.join(knowledge_context['scene_recommendations']['recommended_characters'])}
        """
        
        return enhancement.strip()
    
    def _format_character_enhancement(self, char_context: Dict) -> str:
        """格式化角色增强内容"""
        character = char_context['character']
        entity_info = char_context['entity_info']
        writing_suggestions = char_context['writing_suggestions']
        
        enhancement = f"""
【角色背景增强】

【角色信息】
- 姓名: {character}
- 性格特点: {writing_suggestions['personality_traits']}
- 说话风格: {writing_suggestions['speech_style']}

【常见同伴】
{', '.join(writing_suggestions['common_companions'])}

【典型行为】
{', '.join(writing_suggestions['typical_actions'])}
        """
        
        return enhancement.strip()
    
    def _format_scene_enhancement(self, scene_context: Dict) -> str:
        """格式化场景增强内容"""
        location = scene_context['location']
        scene_description = scene_context['scene_description']
        
        enhancement = f"""
【场景背景增强】

【地点信息】
{location}: {scene_description['physical_description']}

【环境氛围】
{', '.join(scene_description['atmosphere'])}

【常见活动】
{', '.join(scene_description['typical_activities'])}

【场景物品】
{', '.join(scene_description['common_objects'])}

【推荐角色】
{', '.join(scene_context['recommended_characters'])}
        """
        
        return enhancement.strip()
    
    def _format_vocabulary_enhancement(self, vocab_suggestions: Dict) -> str:
        """格式化词汇增强内容"""
        enhancement = "【词汇建议增强】\n\n"
        
        for category, words in vocab_suggestions.items():
            if words:
                enhancement += f"【{category}】\n{', '.join(words)}\n\n"
        
        return enhancement.strip()


if __name__ == "__main__":
    # 测试代码
    retriever = KnowledgeRetriever()
    
    test_text = "话说宝玉那日在潇湘馆，忽见黛玉倚竹而立"
    
    # 测试综合知识检索
    context = retriever.retrieve_comprehensive_context(test_text)
    print("知识摘要:")
    for key, value in context['knowledge_summary'].items():
        print(f"{key}: {value}")
    
    # 测试提示词增强
    enhancement = retriever.generate_writing_prompt_enhancement(test_text, "comprehensive")
    print(f"\n提示词增强内容:\n{enhancement}") 