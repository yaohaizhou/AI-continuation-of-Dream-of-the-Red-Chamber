"""
关系检索器 - 基于人物共现数据分析人物关系
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from loguru import logger


class RelationshipRetriever:
    """人物关系检索器类"""
    
    def __init__(self, data_dir: str = "data/processed"):
        """
        初始化关系检索器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        self.co_occurrence_matrix = {}
        self.character_relationships = {}
        
        self._load_co_occurrence_data()
        self._build_relationship_rules()
        
    def _load_co_occurrence_data(self):
        """加载人物共现数据"""
        try:
            co_occurrence_file = self.data_dir / "character_co_occurrence.json"
            if co_occurrence_file.exists():
                with open(co_occurrence_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.co_occurrence_matrix = data.get('co_occurrence_matrix', {})
                    
                    # 记录统计信息
                    total_pairs = sum(
                        len(relations) for relations in self.co_occurrence_matrix.values()
                    )
                    logger.info(f"已加载 {total_pairs} 个人物关系数据")
                    
        except Exception as e:
            logger.error(f"加载共现数据失败: {e}")
    
    def _build_relationship_rules(self):
        """构建人物关系规则"""
        # 定义已知的人物关系
        self.character_relationships = {
            # 家庭关系
            '贾宝玉': {
                'grandmother': ['贾母'],
                'father': ['贾政'],
                'mother': ['王夫人'],
                'cousin': ['林黛玉', '薛宝钗'],
                'servant': ['袭人', '晴雯', '麝月'],
                'relationship_type': '主角'
            },
            '林黛玉': {
                'cousin': ['贾宝玉'],
                'aunt': ['贾母'],
                'servant': ['紫鹃', '雪雁'],
                'friend': ['薛宝钗'],
                'relationship_type': '女主角'
            },
            '薛宝钗': {
                'cousin': ['贾宝玉'],
                'mother': ['薛姨妈'],
                'brother': ['薛蟠'],
                'friend': ['林黛玉'],
                'servant': ['香菱'],
                'relationship_type': '女主角'
            },
            '王熙凤': {
                'husband': ['贾琏'],
                'grandmother_in_law': ['贾母'],
                'servant': ['平儿'],
                'relationship_type': '管家'
            },
            '贾母': {
                'grandson': ['贾宝玉'],
                'daughter_in_law': ['王夫人'],
                'granddaughter_in_law': ['王熙凤'],
                'relationship_type': '长辈'
            }
        }
        
    def get_character_relationships(self, character: str) -> Dict:
        """
        获取角色的关系信息
        
        Args:
            character: 角色名称
            
        Returns:
            Dict: 关系信息
        """
        # 标准化角色名称
        character = self._normalize_character_name(character)
        
        relationships = {
            'character': character,
            'family_relations': {},
            'co_occurrence_relations': [],
            'relationship_strength': {},
            'recommended_characters': []
        }
        
        # 获取预定义的家庭关系
        if character in self.character_relationships:
            relationships['family_relations'] = self.character_relationships[character]
        
        # 获取共现关系
        if character in self.co_occurrence_matrix:
            co_relations = self.co_occurrence_matrix[character]
            # 按共现次数排序
            sorted_relations = sorted(
                co_relations.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            relationships['co_occurrence_relations'] = sorted_relations[:10]  # 前10个最相关的
            
            # 计算关系强度
            for related_char, count in sorted_relations:
                if count > 100:  # 高频共现
                    strength = "strong"
                elif count > 50:  # 中频共现
                    strength = "medium"
                else:  # 低频共现
                    strength = "weak"
                relationships['relationship_strength'][related_char] = strength
        
        # 推荐相关角色
        relationships['recommended_characters'] = self._get_recommended_characters(character)
        
        return relationships
    
    def _normalize_character_name(self, character: str) -> str:
        """标准化角色名称"""
        # 简单的名称映射
        name_mapping = {
            '宝玉': '贾宝玉',
            '黛玉': '林黛玉', 
            '宝钗': '薛宝钗',
            '熙凤': '王熙凤'
        }
        return name_mapping.get(character, character)
    
    def _get_recommended_characters(self, character: str) -> List[str]:
        """获取推荐的相关角色"""
        recommendations = []
        
        # 基于共现频率推荐
        if character in self.co_occurrence_matrix:
            co_relations = self.co_occurrence_matrix[character]
            # 获取共现次数最高的前5个角色
            top_related = sorted(
                co_relations.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            recommendations.extend([char for char, _ in top_related])
        
        # 基于关系类型推荐
        if character in self.character_relationships:
            relations = self.character_relationships[character]
            for relation_type, related_chars in relations.items():
                if relation_type != 'relationship_type' and isinstance(related_chars, list):
                    recommendations.extend(related_chars)
        
        return list(set(recommendations))  # 去重
    
    def get_scene_characters(self, main_characters: List[str], location: str = None) -> List[str]:
        """
        根据主要角色和地点推荐场景中可能出现的其他角色
        
        Args:
            main_characters: 主要角色列表
            location: 地点（可选）
            
        Returns:
            List: 推荐的角色列表
        """
        scene_characters = set(main_characters)
        
        # 基于地点推荐角色
        location_character_mapping = {
            '潇湘馆': ['林黛玉', '紫鹃', '雪雁'],
            '蘅芜苑': ['薛宝钗', '香菱'],
            '怡红院': ['贾宝玉', '袭人', '晴雯', '麝月'],
            '荣庆堂': ['贾母', '王夫人', '王熙凤'],
            '大观园': ['贾宝玉', '林黛玉', '薛宝钗', '探春', '迎春', '惜春']
        }
        
        if location and location in location_character_mapping:
            scene_characters.update(location_character_mapping[location])
        
        # 基于主要角色的关系推荐
        for character in main_characters:
            character = self._normalize_character_name(character)
            relationships = self.get_character_relationships(character)
            
            # 添加高频共现的角色
            for related_char, count in relationships['co_occurrence_relations'][:3]:
                if count > 200:  # 只添加高频共现的角色
                    scene_characters.add(related_char)
            
            # 添加家庭成员
            family_relations = relationships['family_relations']
            for relation_type, related_chars in family_relations.items():
                if relation_type in ['servant', 'cousin'] and isinstance(related_chars, list):
                    scene_characters.update(related_chars[:2])  # 最多添加2个
        
        return list(scene_characters)
    
    def get_relationship_context(self, characters: List[str]) -> Dict:
        """
        获取多个角色之间的关系上下文
        
        Args:
            characters: 角色列表
            
        Returns:
            Dict: 关系上下文信息
        """
        context = {
            'characters': characters,
            'relationships': {},
            'interaction_history': {},
            'group_dynamics': ''
        }
        
        # 分析两两之间的关系
        for i, char1 in enumerate(characters):
            char1 = self._normalize_character_name(char1)
            context['relationships'][char1] = {}
            
            for char2 in characters[i+1:]:
                char2 = self._normalize_character_name(char2)
                
                # 获取共现次数
                co_count = 0
                if char1 in self.co_occurrence_matrix and char2 in self.co_occurrence_matrix[char1]:
                    co_count = self.co_occurrence_matrix[char1][char2]
                
                # 分析关系类型
                relation_type = self._analyze_relationship_type(char1, char2, co_count)
                
                context['relationships'][char1][char2] = {
                    'co_occurrence_count': co_count,
                    'relationship_type': relation_type,
                    'interaction_frequency': 'high' if co_count > 500 else 'medium' if co_count > 100 else 'low'
                }
        
        # 生成群体动态描述
        context['group_dynamics'] = self._generate_group_dynamics(characters)
        
        return context
    
    def _analyze_relationship_type(self, char1: str, char2: str, co_count: int) -> str:
        """分析两个角色之间的关系类型"""
        # 特殊关系对
        special_relationships = {
            ('贾宝玉', '林黛玉'): '青梅竹马',
            ('贾宝玉', '薛宝钗'): '表兄妹',
            ('贾宝玉', '袭人'): '主仆',
            ('林黛玉', '薛宝钗'): '朋友',
            ('王熙凤', '平儿'): '主仆',
            ('贾母', '贾宝玉'): '祖孙'
        }
        
        # 检查特殊关系
        pair = (char1, char2) if (char1, char2) in special_relationships else (char2, char1)
        if pair in special_relationships:
            return special_relationships[pair]
        
        # 基于共现频率判断
        if co_count > 1000:
            return '密切'
        elif co_count > 500:
            return '熟悉'
        elif co_count > 100:
            return '认识'
        else:
            return '少见'
    
    def _generate_group_dynamics(self, characters: List[str]) -> str:
        """生成群体动态描述"""
        if not characters:
            return ""
        
        # 根据角色组合生成描述
        chars = [self._normalize_character_name(c) for c in characters]
        
        if '贾宝玉' in chars and '林黛玉' in chars:
            return "宝黛之间情深意重，常有细腻的情感交流"
        elif '贾宝玉' in chars and '薛宝钗' in chars:
            return "宝钗待宝玉温和体贴，体现出大家闺秀的风范"
        elif '王熙凤' in chars:
            return "凤姐在场，气氛必然热闹风趣，管家事务井井有条"
        elif '贾母' in chars:
            return "老祖宗慈祥和蔼，众人都要尽孝心，场面温馨"
        else:
            return "众人聚在一起，各显性格特色"


if __name__ == "__main__":
    # 测试代码
    retriever = RelationshipRetriever()
    
    # 测试获取宝玉的关系信息
    relationships = retriever.get_character_relationships('宝玉')
    print("宝玉的关系信息:")
    print(f"共现关系前5个: {relationships['co_occurrence_relations'][:5]}")
    print(f"推荐角色: {relationships['recommended_characters']}")
    
    # 测试场景角色推荐
    scene_chars = retriever.get_scene_characters(['宝玉'], '潇湘馆')
    print(f"\n潇湘馆场景推荐角色: {scene_chars}")
    
    # 测试关系上下文
    context = retriever.get_relationship_context(['宝玉', '黛玉'])
    print(f"\n群体动态: {context['group_dynamics']}") 