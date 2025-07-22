"""
红楼梦分词器模块
集成jieba分词器与红楼梦自定义词典，支持词性标注和命名实体识别
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from collections import defaultdict

import jieba
import jieba.posseg as pseg
from loguru import logger


class HongLouMengTokenizer:
    """红楼梦专用分词器"""
    
    def __init__(self, dict_path: Optional[str] = None):
        """
        初始化分词器
        
        Args:
            dict_path: 自定义词典路径，如果为None则使用默认路径
        """
        self.dict_path = dict_path or "data/processed/hongloumeng_dict.txt"
        self.is_initialized = False
        
        # 词典缓存
        self.custom_words = {}
        self.word_freq = {}
        self.word_pos = {}
        
        # 实体类别
        self.entity_categories = {
            'person': set(),      # 人物
            'location': set(),    # 地点
            'object': set(),      # 物品
            'title': set(),       # 称谓
            'classical': set()    # 古典词汇
        }
        
        # 初始化分词器
        self._initialize()
    
    def _initialize(self):
        """初始化分词器和自定义词典"""
        try:
            # 加载自定义词典
            self._load_custom_dict()
            
            # 配置jieba
            self._configure_jieba()
            
            self.is_initialized = True
            logger.info("红楼梦分词器初始化完成")
            
        except Exception as e:
            logger.error(f"分词器初始化失败: {e}")
            raise
    
    def _load_custom_dict(self):
        """加载红楼梦自定义词典"""
        dict_file = Path(self.dict_path)
        
        if not dict_file.exists():
            logger.warning(f"自定义词典文件不存在: {self.dict_path}")
            return
        
        logger.info(f"加载自定义词典: {self.dict_path}")
        
        with open(dict_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                
                try:
                    parts = line.split()
                    if len(parts) >= 2:
                        word = parts[0]
                        freq = int(parts[1])
                        pos = parts[2] if len(parts) > 2 else 'n'
                        
                        self.custom_words[word] = {'freq': freq, 'pos': pos}
                        self.word_freq[word] = freq
                        self.word_pos[word] = pos
                        
                        # 根据词性分类实体
                        self._categorize_entity(word, pos)
                        
                except (ValueError, IndexError) as e:
                    logger.warning(f"词典第{line_num}行格式错误: {line}")
        
        logger.info(f"成功加载{len(self.custom_words)}个自定义词汇")
    
    def _categorize_entity(self, word: str, pos: str):
        """根据词性和内容对实体进行分类"""
        if pos == 'nr':  # 人名
            self.entity_categories['person'].add(word)
        elif pos == 'ns':  # 地名
            self.entity_categories['location'].add(word)
        elif word in ['老爷', '太太', '奶奶', '姑娘', '公子', '少爷', '二爷']:
            self.entity_categories['title'].add(word)
        elif pos == 'n' and any(keyword in word for keyword in ['宝玉', '金锁', '通灵', '诗', '词']):
            self.entity_categories['object'].add(word)
        else:
            self.entity_categories['classical'].add(word)
    
    def _configure_jieba(self):
        """配置jieba分词器"""
        # 添加自定义词典到jieba
        for word, info in self.custom_words.items():
            jieba.add_word(word, freq=info['freq'], tag=info['pos'])
        
        # 尝试启用paddle模式（可选）
        try:
            jieba.enable_paddle()
            logger.debug("成功启用jieba paddle模式")
        except Exception as e:
            logger.warning(f"无法启用paddle模式，使用默认模式: {e}")
        
        jieba.setLogLevel(20)  # 减少日志输出
        
        logger.debug("jieba分词器配置完成")
    
    def tokenize(self, text: str, mode: str = 'default') -> List[str]:
        """
        分词
        
        Args:
            text: 输入文本
            mode: 分词模式 ('default', 'search', 'all')
            
        Returns:
            List[str]: 分词结果
        """
        if not self.is_initialized:
            self._initialize()
        
        if mode == 'search':
            # 搜索引擎模式
            return list(jieba.cut_for_search(text))
        elif mode == 'all':
            # 全模式
            return list(jieba.cut(text, cut_all=True))
        else:
            # 精确模式（默认）
            return list(jieba.cut(text, cut_all=False))
    
    def tokenize_with_pos(self, text: str) -> List[Tuple[str, str]]:
        """
        分词并标注词性
        
        Args:
            text: 输入文本
            
        Returns:
            List[Tuple[str, str]]: [(词, 词性)] 列表
        """
        if not self.is_initialized:
            self._initialize()
        
        # 使用jieba的词性标注
        result = []
        for word, pos in pseg.cut(text):
            # 检查是否是自定义词汇，如果是则使用自定义词性
            if word in self.word_pos:
                pos = self.word_pos[word]
            result.append((word, pos))
        
        return result
    
    def analyze_text(self, text: str) -> Dict[str, any]:
        """
        全面分析文本
        
        Args:
            text: 输入文本
            
        Returns:
            Dict: 分析结果
        """
        # 基础分词
        words = self.tokenize(text)
        words_with_pos = self.tokenize_with_pos(text)
        
        # 统计信息
        word_count = len(words)
        unique_words = len(set(words))
        
        # 词频统计
        word_freq = defaultdict(int)
        pos_freq = defaultdict(int)
        
        for word, pos in words_with_pos:
            word_freq[word] += 1
            pos_freq[pos] += 1
        
        # 实体识别
        entities = self._extract_entities(words)
        
        # 特殊词汇识别
        classical_words = [w for w in words if w in self.entity_categories['classical']]
        
        return {
            'words': words,
            'words_with_pos': words_with_pos,
            'word_count': word_count,
            'unique_words': unique_words,
            'word_freq': dict(word_freq),
            'pos_freq': dict(pos_freq),
            'entities': entities,
            'classical_words': classical_words,
            'custom_words_found': [w for w in words if w in self.custom_words]
        }
    
    def _extract_entities(self, words: List[str]) -> Dict[str, List[str]]:
        """
        提取命名实体
        
        Args:
            words: 分词结果
            
        Returns:
            Dict: 实体分类结果
        """
        entities = {
            'persons': [],
            'locations': [],
            'objects': [],
            'titles': []
        }
        
        for word in words:
            if word in self.entity_categories['person']:
                entities['persons'].append(word)
            elif word in self.entity_categories['location']:
                entities['locations'].append(word)
            elif word in self.entity_categories['object']:
                entities['objects'].append(word)
            elif word in self.entity_categories['title']:
                entities['titles'].append(word)
        
        # 去重并保持顺序
        for key in entities:
            entities[key] = list(dict.fromkeys(entities[key]))
        
        return entities
    
    def tokenize_file(self, file_path: Union[str, Path], 
                     output_path: Optional[Union[str, Path]] = None) -> Dict[str, any]:
        """
        对文件进行分词处理
        
        Args:
            file_path: 输入文件路径
            output_path: 输出文件路径，如果为None则生成默认路径
            
        Returns:
            Dict: 处理结果
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        logger.info(f"开始处理文件: {file_path}")
        
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # 分词分析
        analysis_result = self.analyze_text(text)
        
        # 准备输出路径
        if output_path is None:
            output_path = file_path.parent / f"{file_path.stem}_tokenized.json"
        else:
            output_path = Path(output_path)
        
        # 保存结果
        self._save_tokenization_result(analysis_result, output_path)
        
        logger.info(f"文件处理完成，结果保存到: {output_path}")
        
        return {
            'input_file': str(file_path),
            'output_file': str(output_path),
            'analysis': analysis_result
        }
    
    def batch_tokenize(self, input_dir: Union[str, Path], 
                      output_dir: Optional[Union[str, Path]] = None) -> List[Dict[str, any]]:
        """
        批量处理目录中的文件
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录，如果为None则在输入目录下创建tokenized子目录
            
        Returns:
            List[Dict]: 处理结果列表
        """
        input_dir = Path(input_dir)
        
        if not input_dir.exists():
            raise FileNotFoundError(f"目录不存在: {input_dir}")
        
        if output_dir is None:
            output_dir = input_dir / "tokenized"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 查找所有文本文件
        text_files = []
        for ext in ['*.txt', '*.md']:
            text_files.extend(input_dir.glob(ext))
        
        if not text_files:
            logger.warning(f"在{input_dir}中未找到文本文件")
            return []
        
        logger.info(f"找到{len(text_files)}个文件，开始批量处理")
        
        results = []
        
        for file_path in text_files:
            try:
                output_file = output_dir / f"{file_path.stem}_tokenized.json"
                result = self.tokenize_file(file_path, output_file)
                results.append(result)
                
            except Exception as e:
                logger.error(f"处理文件{file_path}失败: {e}")
                results.append({
                    'input_file': str(file_path),
                    'error': str(e)
                })
        
        logger.info(f"批量处理完成，成功处理{len([r for r in results if 'error' not in r])}个文件")
        
        return results
    
    def _save_tokenization_result(self, result: Dict[str, any], output_path: Path):
        """
        保存分词结果到文件
        
        Args:
            result: 分词结果
            output_path: 输出文件路径
        """
        # 转换为可序列化的格式
        serializable_result = {
            'words': result['words'],
            'words_with_pos': result['words_with_pos'],
            'word_count': result['word_count'],
            'unique_words': result['unique_words'],
            'word_freq': result['word_freq'],
            'pos_freq': result['pos_freq'],
            'entities': result['entities'],
            'classical_words': result['classical_words'],
            'custom_words_found': result['custom_words_found']
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_result, f, ensure_ascii=False, indent=2)
    
    def get_word_suggestions(self, partial_word: str, limit: int = 10) -> List[str]:
        """
        根据部分词汇获取建议
        
        Args:
            partial_word: 部分词汇
            limit: 返回建议数量限制
            
        Returns:
            List[str]: 建议词汇列表
        """
        suggestions = []
        
        for word in self.custom_words:
            if partial_word in word:
                suggestions.append(word)
        
        # 按词频排序
        suggestions.sort(key=lambda w: self.word_freq.get(w, 0), reverse=True)
        
        return suggestions[:limit]
    
    def add_custom_word(self, word: str, freq: int = 100, pos: str = 'n'):
        """
        动态添加自定义词汇
        
        Args:
            word: 词汇
            freq: 词频
            pos: 词性
        """
        self.custom_words[word] = {'freq': freq, 'pos': pos}
        self.word_freq[word] = freq
        self.word_pos[word] = pos
        
        # 添加到jieba
        jieba.add_word(word, freq=freq, tag=pos)
        
        # 分类实体
        self._categorize_entity(word, pos)
        
        logger.info(f"添加自定义词汇: {word} ({pos})")
    
    def get_statistics(self) -> Dict[str, any]:
        """
        获取分词器统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            'total_custom_words': len(self.custom_words),
            'entity_counts': {
                'persons': len(self.entity_categories['person']),
                'locations': len(self.entity_categories['location']),
                'objects': len(self.entity_categories['object']),
                'titles': len(self.entity_categories['title']),
                'classical': len(self.entity_categories['classical'])
            },
            'dict_path': self.dict_path,
            'is_initialized': self.is_initialized
        } 