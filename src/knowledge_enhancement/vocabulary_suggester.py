"""
词汇建议器 - 基于词频分析和自定义词典推荐词汇
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
from loguru import logger


class VocabularySuggester:
    """词汇建议器类"""
    
    def __init__(self, data_dir: str = "data/processed"):
        """
        初始化词汇建议器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        self.word_frequency = {}
        self.custom_vocabulary = {}
        self.vocabulary_by_category = defaultdict(list)
        self.high_frequency_words = set()
        
        self._load_word_frequency()
        self._load_custom_vocabulary()
        self._categorize_vocabulary()
        
    def _load_word_frequency(self):
        """加载词频数据"""
        try:
            freq_file = self.data_dir / "word_frequency.json"
            if freq_file.exists():
                with open(freq_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # 转换为字典格式
                    top_words = data.get('top_100_words', [])
                    for word_data in top_words:
                        if len(word_data) == 2:
                            word, freq = word_data
                            self.word_frequency[word] = freq
                    
                    # 标记高频词汇
                    self.high_frequency_words = set(
                        word for word, freq in self.word_frequency.items() 
                        if freq > 500
                    )
                    
                    logger.info(f"已加载 {len(self.word_frequency)} 个词频数据")
                    
        except Exception as e:
            logger.error(f"加载词频数据失败: {e}")
            
    def _load_custom_vocabulary(self):
        """加载自定义词典"""
        try:
            dict_file = self.data_dir / "hongloumeng_dict.txt"
            if dict_file.exists():
                with open(dict_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split()
                            if len(parts) >= 3:
                                word, freq, pos = parts[0], int(parts[1]), parts[2]
                                self.custom_vocabulary[word] = {
                                    'frequency': freq,
                                    'pos': pos,
                                    'category': self._categorize_word(word, pos)
                                }
                                
                logger.info(f"已加载 {len(self.custom_vocabulary)} 个自定义词汇")
                
        except Exception as e:
            logger.error(f"加载自定义词典失败: {e}")
    
    def _categorize_word(self, word: str, pos: str) -> str:
        """根据词汇和词性分类"""
        # 人物相关
        if pos == 'nr' or any(char in word for char in ['宝玉', '黛玉', '宝钗', '熙凤', '贾', '薛', '王', '史']):
            return 'person'
        
        # 地点相关
        elif pos == 'ns' or any(place in word for place in ['园', '馆', '院', '府', '楼', '阁']):
            return 'location'
        
        # 称谓相关
        elif any(title in word for title in ['太太', '爷', '姑娘', '老', '二', '三', '公子', '小姐']):
            return 'title'
        
        # 古典词汇
        elif any(classical in word for classical in ['诗', '词', '书', '画', '琴', '棋', '花', '月', '风', '雪']):
            return 'classical'
        
        # 服饰物品
        elif any(item in word for item in ['衣', '裙', '钗', '环', '玉', '金', '银', '珠']):
            return 'clothing_jewelry'
        
        # 器物用品
        elif any(item in word for item in ['茶', '酒', '香', '炉', '瓶', '盘', '杯', '壶']):
            return 'objects'
        
        # 文学词汇
        elif any(literary in word for literary in ['情', '意', '心', '思', '梦', '缘', 'fate']):
            return 'literary'
        
        else:
            return 'general'
    
    def _categorize_vocabulary(self):
        """对词汇进行分类"""
        for word, info in self.custom_vocabulary.items():
            category = info['category']
            self.vocabulary_by_category[category].append(word)
            
        logger.info(f"词汇分类完成: {list(self.vocabulary_by_category.keys())}")
    
    def suggest_words_by_context(self, context: str, word_count: int = 10) -> Dict[str, List[str]]:
        """
        根据上下文建议词汇
        
        Args:
            context: 上下文文本
            word_count: 建议词汇数量
            
        Returns:
            Dict: 分类的建议词汇
        """
        suggestions = {
            'high_frequency': [],
            'contextual': [],
            'classical': [],
            'character_related': [],
            'location_related': []
        }
        
        # 分析上下文中的关键词
        context_keywords = self._extract_context_keywords(context)
        
        # 高频词汇建议（红楼梦常用词）
        high_freq_candidates = [
            word for word in self.high_frequency_words 
            if len(word) > 1 and word not in ['，', '。', '"', '"', ':', '?', '!']
        ]
        suggestions['high_frequency'] = random.sample(
            high_freq_candidates, min(word_count//2, len(high_freq_candidates))
        )
        
        # 根据上下文类型推荐词汇
        if any(char in context for char in ['宝玉', '黛玉', '宝钗']):
            suggestions['character_related'] = self.vocabulary_by_category['person'][:word_count//3]
        
        if any(place in context for place in ['园', '馆', '院', '府']):
            suggestions['location_related'] = self.vocabulary_by_category['location'][:word_count//3]
        
        # 古典词汇建议
        suggestions['classical'] = random.sample(
            self.vocabulary_by_category['classical'], 
            min(word_count//3, len(self.vocabulary_by_category['classical']))
        )
        
        # 上下文相关词汇
        contextual_words = self._get_contextual_words(context_keywords)
        suggestions['contextual'] = contextual_words[:word_count//3]
        
        return suggestions
    
    def _extract_context_keywords(self, context: str) -> List[str]:
        """提取上下文关键词"""
        keywords = []
        
        # 简单的关键词提取
        for word in self.custom_vocabulary:
            if word in context:
                keywords.append(word)
        
        return keywords
    
    def _get_contextual_words(self, keywords: List[str]) -> List[str]:
        """根据关键词获取相关词汇"""
        contextual_words = []
        
        for keyword in keywords:
            if keyword in self.custom_vocabulary:
                category = self.custom_vocabulary[keyword]['category']
                # 添加同类别的其他词汇
                same_category_words = [
                    w for w in self.vocabulary_by_category[category] 
                    if w != keyword
                ]
                contextual_words.extend(same_category_words[:3])
        
        return list(set(contextual_words))
    
    def suggest_character_vocabulary(self, character: str) -> Dict[str, List[str]]:
        """
        为特定角色建议相关词汇
        
        Args:
            character: 角色名称
            
        Returns:
            Dict: 角色相关词汇分类
        """
        character_vocab = {
            'names_titles': [],
            'related_items': [],
            'personality_words': [],
            'action_words': []
        }
        
        # 角色特定词汇映射
        character_mappings = {
            '贾宝玉': {
                'names_titles': ['宝玉', '宝二爷', '宝哥哥', '二爷'],
                'related_items': ['通灵宝玉', '怡红院', '绛芸轩'],
                'personality_words': ['多情', '痴情', '温柔', '叛逆'],
                'action_words': ['笑道', '叹道', '怜惜', '疼爱']
            },
            '林黛玉': {
                'names_titles': ['黛玉', '林妹妹', '颦儿', '潇湘妃子'],
                'related_items': ['潇湘馆', '紫鹃', '雪雁', '葬花锄'],
                'personality_words': ['敏感', '多愁', '才情', '清高'],
                'action_words': ['嗔道', '泣道', '吟诗', '抚琴']
            },
            '薛宝钗': {
                'names_titles': ['宝钗', '宝姐姐', '蘅芜君'],
                'related_items': ['蘅芜苑', '金锁', '香菱'],
                'personality_words': ['稳重', '大方', '贤德', '圆滑'],
                'action_words': ['温言', '劝慰', '体贴', '关怀']
            },
            '王熙凤': {
                'names_titles': ['熙凤', '凤姐', '凤哥儿', '琏二奶奶'],
                'related_items': ['平儿', '荣庆堂'],
                'personality_words': ['机敏', '泼辣', '风趣', '能干'],
                'action_words': ['笑着说', '打趣', '管理', '吩咐']
            }
        }
        
        # 标准化角色名称
        main_name = self._normalize_character_name(character)
        
        if main_name in character_mappings:
            character_vocab = character_mappings[main_name]
        
        return character_vocab
    
    def _normalize_character_name(self, character: str) -> str:
        """标准化角色名称"""
        name_mapping = {
            '宝玉': '贾宝玉',
            '黛玉': '林黛玉',
            '宝钗': '薛宝钗',
            '熙凤': '王熙凤'
        }
        return name_mapping.get(character, character)
    
    def suggest_scene_vocabulary(self, location: str) -> Dict[str, List[str]]:
        """
        为特定场景建议词汇
        
        Args:
            location: 地点名称
            
        Returns:
            Dict: 场景相关词汇
        """
        scene_vocab = {
            'location_words': [],
            'atmosphere_words': [],
            'action_words': [],
            'object_words': []
        }
        
        # 场景特定词汇映射
        scene_mappings = {
            '潇湘馆': {
                'location_words': ['竹林', '书斋', '窗棂', '幽径'],
                'atmosphere_words': ['清幽', '雅致', '静谧', '书香'],
                'action_words': ['读书', '吟诗', '抚琴', '垂泪'],
                'object_words': ['诗卷', '古琴', '竹叶', '梧桐']
            },
            '怡红院': {
                'location_words': ['富丽', '华美', '绣房', '暖阁'],
                'atmosphere_words': ['温馨', '热闹', '富贵', '奢华'],
                'action_words': ['嬉戏', '谈笑', '赏花', '饮茶'],
                'object_words': ['锦被', '珠帘', '香炉', '花瓶']
            },
            '蘅芜苑': {
                'location_words': ['朴素', '雅洁', '简约', '素净'],
                'atmosphere_words': ['恬静', '清雅', '淡然', '宁和'],
                'action_words': ['女红', '抄经', '侍奉', '劝慰'],
                'object_words': ['针线', '经书', '素帕', '白练']
            },
            '大观园': {
                'location_words': ['园林', '假山', '池塘', '小桥'],
                'atmosphere_words': ['诗意', '如画', '繁华', '雅致'],
                'action_words': ['游赏', '题诗', '赛诗', '聚会'],
                'object_words': ['花树', '亭台', '石径', '流水']
            }
        }
        
        if location in scene_mappings:
            scene_vocab = scene_mappings[location]
        
        return scene_vocab
    
    def get_style_words(self, style_type: str = "elegant") -> List[str]:
        """
        获取特定风格的词汇
        
        Args:
            style_type: 风格类型
            
        Returns:
            List: 风格词汇列表
        """
        style_mappings = {
            'elegant': ['雅致', '清幽', '淡雅', '素净', '恬静'],
            'luxurious': ['富丽', '华美', '奢华', '珠光', '宝气'],
            'emotional': ['柔情', '深情', '痴情', '眷恋', '缠绵'],
            'literary': ['诗意', '书香', '文雅', '才情', '韵致'],
            'classical': ['古典', '传统', '典雅', '古朴', '庄重']
        }
        
        return style_mappings.get(style_type, [])
    
    def enhance_text_vocabulary(self, text: str, enhancement_level: str = "medium") -> Dict:
        """
        为文本提供词汇增强建议
        
        Args:
            text: 原文本
            enhancement_level: 增强级别 (light/medium/heavy)
            
        Returns:
            Dict: 增强建议
        """
        enhancement = {
            'original_text': text,
            'suggested_replacements': {},
            'additional_vocabulary': [],
            'style_suggestions': []
        }
        
        # 根据增强级别确定建议数量
        suggestion_counts = {
            'light': 3,
            'medium': 5,
            'heavy': 8
        }
        count = suggestion_counts.get(enhancement_level, 5)
        
        # 分析文本并提供建议
        context_suggestions = self.suggest_words_by_context(text, count)
        enhancement['additional_vocabulary'] = context_suggestions
        
        # 风格建议
        if any(char in text for char in ['情', '爱', '思']):
            enhancement['style_suggestions'].append('emotional')
        if any(place in text for place in ['园', '馆', '院']):
            enhancement['style_suggestions'].append('elegant')
        if any(luxury in text for luxury in ['金', '玉', '珠', '宝']):
            enhancement['style_suggestions'].append('luxurious')
        
        return enhancement


if __name__ == "__main__":
    # 测试代码
    suggester = VocabularySuggester()
    
    test_text = "宝玉在潇湘馆见到黛玉"
    
    # 测试上下文词汇建议
    suggestions = suggester.suggest_words_by_context(test_text)
    print("上下文词汇建议:")
    for category, words in suggestions.items():
        if words:
            print(f"{category}: {words}")
    
    # 测试角色词汇建议
    char_vocab = suggester.suggest_character_vocabulary('宝玉')
    print(f"\n宝玉相关词汇: {char_vocab}")
    
    # 测试场景词汇建议  
    scene_vocab = suggester.suggest_scene_vocabulary('潇湘馆')
    print(f"\n潇湘馆场景词汇: {scene_vocab}") 