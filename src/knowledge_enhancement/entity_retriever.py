"""
实体检索器 - 从文本中识别实体并检索相关背景信息
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Optional
from loguru import logger


class EntityRetriever:
    """实体检索器类"""
    
    def __init__(self, data_dir: str = "data/processed"):
        """
        初始化实体检索器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        self.entities = {}
        self.entity_aliases = {}
        self.location_hierarchy = {}
        
        self._load_entities()
        self._load_aliases()
        
    def _load_entities(self):
        """加载实体数据"""
        try:
            # 加载提取的实体信息
            entities_file = self.data_dir / "extracted_entities.json"
            if entities_file.exists():
                with open(entities_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.entities = data.get('entities', {})
                    logger.info(f"已加载 {sum(len(v) for v in self.entities.values())} 个实体")
            
            # 构建地点层级关系
            self._build_location_hierarchy()
            
        except Exception as e:
            logger.error(f"加载实体数据失败: {e}")
            
    def _load_aliases(self):
        """加载人物别名映射"""
        try:
            # 从自定义词典中提取别名关系
            dict_file = self.data_dir / "hongloumeng_dict.txt"
            if dict_file.exists():
                with open(dict_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split()
                            if len(parts) >= 2:
                                word = parts[0]
                                # 简单的别名映射逻辑
                                if '宝玉' in word and word != '宝玉':
                                    self.entity_aliases[word] = '贾宝玉'
                                elif '黛玉' in word and word != '黛玉':
                                    self.entity_aliases[word] = '林黛玉'
                                elif '宝钗' in word and word != '宝钗':
                                    self.entity_aliases[word] = '薛宝钗'
                                    
            logger.info(f"已加载 {len(self.entity_aliases)} 个别名映射")
                                    
        except Exception as e:
            logger.error(f"加载别名数据失败: {e}")
    
    def _build_location_hierarchy(self):
        """构建地点层级关系"""
        locations = self.entities.get('locations', [])
        
        # 定义一些已知的层级关系
        hierarchy_rules = {
            '大观园': ['潇湘馆', '蘅芜苑', '怡红院', '稻香村', '栊翠庵', 
                      '缀锦楼', '含芳阁', '暖香坞', '秋爽斋', '紫菱洲', '芦雪庵'],
            '荣国府': ['大观园', '荣庆堂'],
            '贾府': ['荣国府', '宁国府']
        }
        
        for parent, children in hierarchy_rules.items():
            if parent in locations:
                self.location_hierarchy[parent] = [
                    child for child in children if child in locations
                ]
                
        logger.info(f"构建了 {len(self.location_hierarchy)} 个地点层级关系")
    
    def extract_entities_from_text(self, text: str) -> Dict[str, List[str]]:
        """
        从文本中提取实体
        
        Args:
            text: 输入文本
            
        Returns:
            Dict: 提取到的实体字典
        """
        found_entities = {
            'persons': [],
            'locations': [],
            'objects': [],
            'titles': []
        }
        
        # 搜索各类实体
        for entity_type, entity_list in self.entities.items():
            if entity_type in found_entities:
                for entity in entity_list:
                    if entity in text:
                        found_entities[entity_type].append(entity)
        
        # 处理别名
        for alias, main_name in self.entity_aliases.items():
            if alias in text and main_name not in found_entities['persons']:
                found_entities['persons'].append(main_name)
        
        # 去重并排序
        for entity_type in found_entities:
            found_entities[entity_type] = list(set(found_entities[entity_type]))
            
        return found_entities
    
    def get_entity_info(self, entity: str, entity_type: str) -> Dict:
        """
        获取实体的详细信息
        
        Args:
            entity: 实体名称
            entity_type: 实体类型
            
        Returns:
            Dict: 实体信息
        """
        info = {
            'name': entity,
            'type': entity_type,
            'aliases': [],
            'related_entities': [],
            'description': ''
        }
        
        # 获取别名
        for alias, main_name in self.entity_aliases.items():
            if main_name == entity:
                info['aliases'].append(alias)
        
        # 获取地点相关信息
        if entity_type == 'locations':
            # 查找父级地点
            for parent, children in self.location_hierarchy.items():
                if entity in children:
                    info['parent_location'] = parent
                    break
            
            # 查找子级地点
            if entity in self.location_hierarchy:
                info['sub_locations'] = self.location_hierarchy[entity]
        
        # 添加描述信息
        info['description'] = self._get_entity_description(entity, entity_type)
        
        return info
    
    def _get_entity_description(self, entity: str, entity_type: str) -> str:
        """获取实体描述"""
        descriptions = {
            # 主要人物描述
            '贾宝玉': '荣国府贾政之子，生而叼玉，性格多情叛逆，喜欢与姐妹们在一起',
            '林黛玉': '林如海之女，寄居贾府，性格敏感多愁，才华横溢，与宝玉青梅竹马',
            '薛宝钗': '薛姨妈之女，性格稳重大方，处事圆滑，有金锁与宝玉之玉相配',
            '王熙凤': '贾琏之妻，荣国府实际管家，精明能干，泼辣风趣',
            '贾母': '荣国府老祖宗，贾宝玉祖母，慈祥和蔼，极疼爱宝玉和黛玉',
            
            # 地点描述
            '大观园': '贾府为元春省亲而建的大型园林，有山有水，景色优美',
            '潇湘馆': '林黛玉在大观园的居所，以竹子闻名，环境清幽',
            '蘅芜苑': '薛宝钗在大观园的居所，朴素雅致',
            '怡红院': '贾宝玉在大观园的住所，富丽堂皇',
            '荣国府': '贾家老二房，贾政一家居住，是红楼梦主要活动场所',
            '宁国府': '贾家老大房，贾珍一家居住',
        }
        
        return descriptions.get(entity, f"{entity_type}实体")
    
    def get_context_entities(self, text: str) -> Dict:
        """
        获取文本的完整实体上下文信息
        
        Args:
            text: 输入文本
            
        Returns:
            Dict: 完整的实体上下文信息
        """
        # 提取实体
        entities = self.extract_entities_from_text(text)
        
        # 获取详细信息
        context = {
            'extracted_entities': entities,
            'entity_details': {},
            'location_context': {},
            'character_context': {}
        }
        
        # 获取每个实体的详细信息
        for entity_type, entity_list in entities.items():
            context['entity_details'][entity_type] = {}
            for entity in entity_list:
                context['entity_details'][entity_type][entity] = self.get_entity_info(entity, entity_type)
        
        # 构建地点上下文
        if entities['locations']:
            main_location = entities['locations'][0]  # 主要地点
            location_info = self.get_entity_info(main_location, 'locations')
            context['location_context'] = {
                'main_location': main_location,
                'description': location_info['description'],
                'hierarchy': {
                    'parent': location_info.get('parent_location'),
                    'children': location_info.get('sub_locations', [])
                }
            }
        
        # 构建人物上下文
        if entities['persons']:
            context['character_context'] = {
                'main_characters': entities['persons'][:3],  # 主要人物
                'character_info': {
                    char: self.get_entity_info(char, 'persons')['description']
                    for char in entities['persons'][:3]
                }
            }
        
        logger.info(f"提取到 {sum(len(v) for v in entities.values())} 个实体")
        return context


if __name__ == "__main__":
    # 测试代码
    retriever = EntityRetriever()
    
    test_text = "话说宝玉那日在潇湘馆，忽见黛玉倚竹而立"
    context = retriever.get_context_entities(test_text)
    
    print("提取的实体:")
    for entity_type, entities in context['extracted_entities'].items():
        if entities:
            print(f"{entity_type}: {entities}")
    
    print("\n地点上下文:")
    if context['location_context']:
        print(f"主要地点: {context['location_context']['main_location']}")
        print(f"描述: {context['location_context']['description']}") 