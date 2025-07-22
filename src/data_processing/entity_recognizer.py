"""
红楼梦实体识别模块
专门识别红楼梦中的人物、地点、物品等实体
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
from loguru import logger


class EntityRecognizer:
    """红楼梦实体识别器"""
    
    def __init__(self, dict_path: Optional[str] = None):
        """
        初始化实体识别器
        
        Args:
            dict_path: 自定义词典路径
        """
        self.dict_path = dict_path or "data/processed/hongloumeng_dict.txt"
        
        # 实体词典
        self.entities = {
            'persons': set(),
            'locations': set(),
            'objects': set(),
            'titles': set(),
            'classical': set()
        }
        
        # 人物关系映射
        self.person_aliases = {}  # 别名映射到主名
        self.person_relations = defaultdict(list)  # 人物关系
        
        # 地点层级关系
        self.location_hierarchy = {}
        
        # 特殊模式
        self.dialogue_patterns = [
            r'"([^"]*)"',           # 双引号对话
            r'"([^"]*)"',           # 中文双引号对话
            r'「([^」]*)」',         # 日式双引号
        ]
        
        self._load_entities()
        self._build_relations()
    
    def _load_entities(self):
        """从词典加载实体"""
        dict_file = Path(self.dict_path)
        
        if not dict_file.exists():
            logger.warning(f"词典文件不存在: {self.dict_path}")
            return
        
        with open(dict_file, 'r', encoding='utf-8') as f:
            current_category = 'classical'  # 默认分类
            
            for line in f:
                line = line.strip()
                
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    # 从注释中提取分类信息
                    if '人物' in line:
                        current_category = 'persons'
                    elif '地点' in line:
                        current_category = 'locations'
                    elif '物品' in line or '特殊物品' in line:
                        current_category = 'objects'
                    elif '称谓' in line:
                        current_category = 'titles'
                    else:
                        current_category = 'classical'
                    continue
                
                try:
                    parts = line.split()
                    if len(parts) >= 2:
                        word = parts[0]
                        pos = parts[2] if len(parts) > 2 else 'n'
                        
                        # 根据词性自动分类
                        if pos == 'nr':
                            self.entities['persons'].add(word)
                        elif pos == 'ns':
                            self.entities['locations'].add(word)
                        elif word in ['老爷', '太太', '奶奶', '姑娘', '公子', '少爷', '二爷']:
                            self.entities['titles'].add(word)
                        elif any(keyword in word for keyword in ['宝玉', '金锁', '通灵', '诗', '词']):
                            self.entities['objects'].add(word)
                        else:
                            self.entities[current_category].add(word)
                            
                except (ValueError, IndexError):
                    continue
        
        logger.info(f"加载实体完成: 人物{len(self.entities['persons'])}个, "
                   f"地点{len(self.entities['locations'])}个")
    
    def _build_relations(self):
        """构建人物关系和别名映射"""
        # 人物别名映射
        alias_mappings = {
            '宝玉': '贾宝玉',
            '黛玉': '林黛玉',
            '宝钗': '薛宝钗',
            '湘云': '史湘云',
            '熙凤': '王熙凤',
            '可卿': '秦可卿',
            '士隐': '甄士隐',
            '雨村': '贾雨村',
        }
        
        for alias, main_name in alias_mappings.items():
            if main_name in self.entities['persons']:
                self.person_aliases[alias] = main_name
        
        # 地点层级关系
        self.location_hierarchy = {
            '大观园': ['潇湘馆', '蘅芜苑', '怡红院', '稻香村', '栊翠庵'],
            '荣国府': ['荣庆堂', '梨香院'],
            '宁国府': ['会芳园', '天香楼']
        }
    
    def recognize_entities(self, text: str) -> Dict[str, List[Dict]]:
        """
        识别文本中的实体
        
        Args:
            text: 输入文本
            
        Returns:
            Dict: 识别结果
        """
        results = {
            'persons': [],
            'locations': [],
            'objects': [],
            'titles': [],
            'dialogues': [],
            'classical': []
        }
        
        # 识别各类实体
        for entity_type, entities in self.entities.items():
            for entity in entities:
                positions = self._find_entity_positions(text, entity)
                for pos in positions:
                    results[entity_type].append({
                        'entity': entity,
                        'start': pos[0],
                        'end': pos[1],
                        'context': self._get_context(text, pos[0], pos[1])
                    })
        
        # 识别对话
        results['dialogues'] = self._extract_dialogues(text)
        
        # 解析人物别名
        results['persons'] = self._resolve_person_aliases(results['persons'])
        
        # 排序结果
        for entity_type in results:
            if results[entity_type]:
                results[entity_type].sort(key=lambda x: x['start'])
        
        return results
    
    def _find_entity_positions(self, text: str, entity: str) -> List[Tuple[int, int]]:
        """
        查找实体在文本中的位置
        
        Args:
            text: 文本
            entity: 实体名称
            
        Returns:
            List[Tuple[int, int]]: 位置列表 [(开始位置, 结束位置)]
        """
        positions = []
        start = 0
        
        while True:
            pos = text.find(entity, start)
            if pos == -1:
                break
            positions.append((pos, pos + len(entity)))
            start = pos + 1
        
        return positions
    
    def _get_context(self, text: str, start: int, end: int, 
                    context_length: int = 20) -> str:
        """
        获取实体的上下文
        
        Args:
            text: 文本
            start: 实体开始位置
            end: 实体结束位置
            context_length: 上下文长度
            
        Returns:
            str: 上下文文本
        """
        context_start = max(0, start - context_length)
        context_end = min(len(text), end + context_length)
        
        context = text[context_start:context_end]
        
        # 标记实体
        entity_in_context = text[start:end]
        relative_start = start - context_start
        relative_end = end - context_start
        
        marked_context = (context[:relative_start] + 
                         f"【{entity_in_context}】" + 
                         context[relative_end:])
        
        return marked_context
    
    def _extract_dialogues(self, text: str) -> List[Dict]:
        """
        提取对话内容
        
        Args:
            text: 文本
            
        Returns:
            List[Dict]: 对话列表
        """
        dialogues = []
        
        for pattern in self.dialogue_patterns:
            for match in re.finditer(pattern, text):
                dialogue_text = match.group(1) if match.groups() else match.group()
                start_pos = match.start()
                end_pos = match.end()
                
                # 尝试识别说话者
                speaker = self._identify_speaker(text, start_pos)
                
                dialogues.append({
                    'entity': dialogue_text,
                    'start': start_pos,
                    'end': end_pos,
                    'speaker': speaker,
                    'context': self._get_context(text, start_pos, end_pos)
                })
        
        return dialogues
    
    def _identify_speaker(self, text: str, dialogue_start: int) -> Optional[str]:
        """
        识别对话的说话者
        
        Args:
            text: 文本
            dialogue_start: 对话开始位置
            
        Returns:
            Optional[str]: 说话者名称
        """
        # 在对话前的一定范围内查找人物名
        search_start = max(0, dialogue_start - 50)
        search_text = text[search_start:dialogue_start]
        
        # 查找最近的人物名
        latest_person = None
        latest_pos = -1
        
        for person in self.entities['persons']:
            pos = search_text.rfind(person)
            if pos > latest_pos:
                latest_pos = pos
                latest_person = person
        
        # 也检查别名
        for alias, main_name in self.person_aliases.items():
            pos = search_text.rfind(alias)
            if pos > latest_pos:
                latest_pos = pos
                latest_person = main_name
        
        return latest_person
    
    def _resolve_person_aliases(self, person_entities: List[Dict]) -> List[Dict]:
        """
        解析人物别名
        
        Args:
            person_entities: 人物实体列表
            
        Returns:
            List[Dict]: 解析后的人物实体列表
        """
        resolved = []
        
        for entity_info in person_entities:
            entity = entity_info['entity']
            
            # 检查是否是别名
            if entity in self.person_aliases:
                entity_info['main_name'] = self.person_aliases[entity]
                entity_info['is_alias'] = True
            else:
                entity_info['main_name'] = entity
                entity_info['is_alias'] = False
            
            resolved.append(entity_info)
        
        return resolved
    
    def analyze_character_co_occurrence(self, text: str, 
                                      window_size: int = 100) -> Dict[str, Dict[str, int]]:
        """
        分析人物共现关系
        
        Args:
            text: 文本
            window_size: 窗口大小
            
        Returns:
            Dict: 共现矩阵
        """
        person_positions = {}
        
        # 找到所有人物的位置
        for person in self.entities['persons']:
            positions = self._find_entity_positions(text, person)
            if positions:
                person_positions[person] = [pos[0] for pos in positions]
        
        # 计算共现
        co_occurrence = defaultdict(lambda: defaultdict(int))
        
        for person1, positions1 in person_positions.items():
            for person2, positions2 in person_positions.items():
                if person1 != person2:
                    for pos1 in positions1:
                        for pos2 in positions2:
                            if abs(pos1 - pos2) <= window_size:
                                co_occurrence[person1][person2] += 1
        
        return dict(co_occurrence)
    
    def get_entity_statistics(self, text: str) -> Dict[str, any]:
        """
        获取实体统计信息
        
        Args:
            text: 文本
            
        Returns:
            Dict: 统计信息
        """
        entities_result = self.recognize_entities(text)
        
        stats = {
            'entity_counts': {},
            'unique_entities': {},
            'entity_density': {},
            'most_frequent': {},
            'total_text_length': len(text)
        }
        
        for entity_type, entities in entities_result.items():
            # 计数统计
            stats['entity_counts'][entity_type] = len(entities)
            
            # 唯一实体统计
            unique = set(e['entity'] for e in entities)
            stats['unique_entities'][entity_type] = len(unique)
            
            # 密度统计（每千字的实体数量）
            density = (len(entities) / len(text)) * 1000 if text else 0
            stats['entity_density'][entity_type] = round(density, 2)
            
            # 最频繁实体
            if entities:
                entity_freq = defaultdict(int)
                for e in entities:
                    entity_freq[e['entity']] += 1
                most_freq = max(entity_freq.items(), key=lambda x: x[1])
                stats['most_frequent'][entity_type] = {
                    'entity': most_freq[0],
                    'count': most_freq[1]
                }
        
        return stats
    
    def export_entities(self, text: str, output_path: str):
        """
        导出实体识别结果
        
        Args:
            text: 文本
            output_path: 输出文件路径
        """
        import json
        
        entities = self.recognize_entities(text)
        stats = self.get_entity_statistics(text)
        
        export_data = {
            'entities': entities,
            'statistics': stats,
            'metadata': {
                'text_length': len(text),
                'recognition_time': self._get_timestamp(),
                'recognizer_version': '1.0'
            }
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"实体识别结果已导出到: {output_path}")
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def add_custom_entity(self, entity: str, entity_type: str):
        """
        动态添加自定义实体
        
        Args:
            entity: 实体名称
            entity_type: 实体类型
        """
        if entity_type in self.entities:
            self.entities[entity_type].add(entity)
            logger.info(f"添加自定义实体: {entity} ({entity_type})")
        else:
            logger.warning(f"未知的实体类型: {entity_type}")
    
    def get_entity_info(self) -> Dict[str, any]:
        """
        获取实体识别器信息
        
        Returns:
            Dict: 实体识别器信息
        """
        return {
            'entity_counts': {
                entity_type: len(entities) 
                for entity_type, entities in self.entities.items()
            },
            'person_aliases_count': len(self.person_aliases),
            'location_hierarchy_count': len(self.location_hierarchy),
            'dict_path': self.dict_path
        } 