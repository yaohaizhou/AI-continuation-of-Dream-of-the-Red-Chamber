"""
红楼梦数据处理管道
整合文本预处理、章节分割、分词、实体识别等功能
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union
from loguru import logger

from .text_preprocessor import TextPreprocessor
from .chapter_splitter import ChapterSplitter
from .tokenizer import HongLouMengTokenizer
from .entity_recognizer import EntityRecognizer


class HongLouMengDataPipeline:
    """红楼梦数据处理管道"""
    
    def __init__(self, 
                 custom_dict_path: Optional[str] = None,
                 output_base_dir: str = "data/processed"):
        """
        初始化数据处理管道
        
        Args:
            custom_dict_path: 自定义词典路径
            output_base_dir: 输出基础目录
        """
        self.output_base_dir = Path(output_base_dir)
        self.custom_dict_path = custom_dict_path
        
        # 初始化各个组件
        self.preprocessor = TextPreprocessor()
        self.chapter_splitter = ChapterSplitter(str(self.output_base_dir / "chapters"))
        self.tokenizer = HongLouMengTokenizer(custom_dict_path)
        self.entity_recognizer = EntityRecognizer(custom_dict_path)
        
        # 确保输出目录存在
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
    
    def process_complete_text(self, 
                            input_file: Union[str, Path],
                            include_tokenization: bool = True,
                            include_entity_recognition: bool = True,
                            force_reprocess: bool = False) -> Dict[str, any]:
        """
        完整处理红楼梦文本
        
        Args:
            input_file: 输入文件路径
            include_tokenization: 是否包含分词处理
            include_entity_recognition: 是否包含实体识别
            force_reprocess: 是否强制重新处理
            
        Returns:
            Dict: 处理结果
        """
        input_path = Path(input_file)
        logger.info(f"开始完整处理文件: {input_path}")
        
        results = {
            'input_file': str(input_path),
            'processing_steps': [],
            'output_files': {},
            'statistics': {}
        }
        
        try:
            # 步骤1: 文本预处理
            logger.info("步骤1: 文本预处理")
            preprocess_result = self.preprocessor.process_file(input_path)
            results['processing_steps'].append('text_preprocessing')
            results['statistics']['preprocessing'] = preprocess_result['stats']
            
            # 保存预处理结果
            preprocessed_file = self.output_base_dir / "preprocessed_text.txt"
            self.preprocessor.save_processed_text(preprocess_result, preprocessed_file)
            results['output_files']['preprocessed_text'] = str(preprocessed_file)
            
            # 步骤2: 章节分割
            logger.info("步骤2: 章节分割")
            chapter_result = self.chapter_splitter.split_file(input_path, force_reprocess)
            results['processing_steps'].append('chapter_splitting')
            results['statistics']['chapters'] = {
                'total_chapters': chapter_result['total_chapters'],
                'chapters_info': chapter_result['chapters']
            }
            results['output_files']['chapters_dir'] = str(self.chapter_splitter.output_dir)
            results['output_files']['chapters_metadata'] = str(self.chapter_splitter.output_dir / "metadata.json")
            
            # 步骤3: 分词处理（可选）
            if include_tokenization:
                logger.info("步骤3: 分词处理")
                tokenization_result = self._process_tokenization(preprocess_result['processed_text'])
                results['processing_steps'].append('tokenization')
                results['statistics']['tokenization'] = tokenization_result['stats']
                results['output_files'].update(tokenization_result['output_files'])
            
            # 步骤4: 实体识别（可选）
            if include_entity_recognition:
                logger.info("步骤4: 实体识别")
                entity_result = self._process_entity_recognition(preprocess_result['processed_text'])
                results['processing_steps'].append('entity_recognition')
                results['statistics']['entity_recognition'] = entity_result['stats']
                results['output_files'].update(entity_result['output_files'])
            
            # 生成综合报告
            logger.info("生成综合报告")
            report_result = self._generate_comprehensive_report(results)
            results['output_files']['comprehensive_report'] = report_result['report_file']
            
            logger.info("数据处理管道完成")
            return results
            
        except Exception as e:
            logger.error(f"数据处理管道失败: {e}")
            results['error'] = str(e)
            return results
    
    def _process_tokenization(self, text: str) -> Dict[str, any]:
        """
        处理分词
        
        Args:
            text: 预处理后的文本
            
        Returns:
            Dict: 分词结果
        """
        # 全文分词分析
        analysis_result = self.tokenizer.analyze_text(text)
        
        # 保存分词结果
        tokenization_file = self.output_base_dir / "tokenization_result.json"
        self.tokenizer._save_tokenization_result(analysis_result, tokenization_file)
        
        # 生成词频统计文件
        word_freq_file = self.output_base_dir / "word_frequency.json"
        self._save_word_frequency(analysis_result['word_freq'], word_freq_file)
        
        # 生成实体词汇文件
        entities_file = self.output_base_dir / "extracted_entities.json"
        self._save_extracted_entities(analysis_result['entities'], entities_file)
        
        return {
            'stats': {
                'total_words': analysis_result['word_count'],
                'unique_words': analysis_result['unique_words'],
                'custom_words_found': len(analysis_result['custom_words_found']),
                'classical_words_found': len(analysis_result['classical_words'])
            },
            'output_files': {
                'tokenization_result': str(tokenization_file),
                'word_frequency': str(word_freq_file),
                'extracted_entities': str(entities_file)
            }
        }
    
    def _process_entity_recognition(self, text: str) -> Dict[str, any]:
        """
        处理实体识别
        
        Args:
            text: 预处理后的文本
            
        Returns:
            Dict: 实体识别结果
        """
        # 实体识别
        entities_result = self.entity_recognizer.recognize_entities(text)
        entity_stats = self.entity_recognizer.get_entity_statistics(text)
        
        # 人物共现分析
        co_occurrence = self.entity_recognizer.analyze_character_co_occurrence(text)
        
        # 保存实体识别结果
        entity_recognition_file = self.output_base_dir / "entity_recognition_result.json"
        self.entity_recognizer.export_entities(text, str(entity_recognition_file))
        
        # 保存人物共现分析
        co_occurrence_file = self.output_base_dir / "character_co_occurrence.json"
        self._save_co_occurrence_analysis(co_occurrence, co_occurrence_file)
        
        return {
            'stats': entity_stats,
            'output_files': {
                'entity_recognition_result': str(entity_recognition_file),
                'character_co_occurrence': str(co_occurrence_file)
            }
        }
    
    def _save_word_frequency(self, word_freq: Dict[str, int], output_file: Path):
        """保存词频统计"""
        # 按频率排序
        sorted_freq = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        freq_data = {
            'total_unique_words': len(word_freq),
            'top_100_words': sorted_freq[:100],
            'frequency_distribution': {
                'high_freq': len([w for w, f in word_freq.items() if f >= 10]),
                'medium_freq': len([w for w, f in word_freq.items() if 3 <= f < 10]),
                'low_freq': len([w for w, f in word_freq.items() if f < 3])
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(freq_data, f, ensure_ascii=False, indent=2)
    
    def _save_extracted_entities(self, entities: Dict[str, List[str]], output_file: Path):
        """保存提取的实体"""
        entities_data = {
            'entity_summary': {
                entity_type: len(entity_list) 
                for entity_type, entity_list in entities.items()
            },
            'entities': entities
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(entities_data, f, ensure_ascii=False, indent=2)
    
    def _save_co_occurrence_analysis(self, co_occurrence: Dict[str, Dict[str, int]], 
                                   output_file: Path):
        """保存人物共现分析"""
        # 计算共现统计
        total_pairs = 0
        max_co_occurrence = 0
        top_pairs = []
        
        for person1, relations in co_occurrence.items():
            for person2, count in relations.items():
                total_pairs += 1
                max_co_occurrence = max(max_co_occurrence, count)
                top_pairs.append((person1, person2, count))
        
        # 排序获取最频繁的共现关系
        top_pairs.sort(key=lambda x: x[2], reverse=True)
        
        co_occurrence_data = {
            'statistics': {
                'total_character_pairs': total_pairs,
                'max_co_occurrence_count': max_co_occurrence,
                'top_10_pairs': top_pairs[:10]
            },
            'co_occurrence_matrix': co_occurrence
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(co_occurrence_data, f, ensure_ascii=False, indent=2)
    
    def _generate_comprehensive_report(self, processing_results: Dict[str, any]) -> Dict[str, any]:
        """
        生成综合报告
        
        Args:
            processing_results: 处理结果
            
        Returns:
            Dict: 报告结果
        """
        report_file = self.output_base_dir / "comprehensive_report.md"
        
        # 生成Markdown报告
        report_content = self._create_markdown_report(processing_results)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"综合报告已生成: {report_file}")
        
        return {'report_file': str(report_file)}
    
    def _create_markdown_report(self, results: Dict[str, any]) -> str:
        """创建Markdown格式的报告"""
        from datetime import datetime
        
        report = f"""# 红楼梦文本处理综合报告

生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
输入文件: {results['input_file']}
处理步骤: {', '.join(results['processing_steps'])}

---

## 处理统计概览

"""
        
        # 预处理统计
        if 'preprocessing' in results['statistics']:
            stats = results['statistics']['preprocessing']
            report += f"""### 文本预处理
- 总字符数: {stats['total_chars']:,}
- 总行数: {stats['total_lines']:,}
- 段落数: {stats['total_paragraphs']:,}
- 对话数: {stats['total_dialogues']:,}
- 对话比例: {stats['dialogue_ratio']:.2%}

"""
        
        # 章节统计
        if 'chapters' in results['statistics']:
            stats = results['statistics']['chapters']
            report += f"""### 章节分割
- 总章节数: {stats['total_chapters']}
- 平均章节长度: {sum(c['content_length'] for c in stats['chapters_info']) // len(stats['chapters_info']):,}字

"""
        
        # 分词统计
        if 'tokenization' in results['statistics']:
            stats = results['statistics']['tokenization']
            report += f"""### 分词分析
- 总词数: {stats['total_words']:,}
- 独特词汇数: {stats['unique_words']:,}
- 发现的自定义词汇: {stats['custom_words_found']}个
- 发现的古典词汇: {stats['classical_words_found']}个

"""
        
        # 实体识别统计
        if 'entity_recognition' in results['statistics']:
            stats = results['statistics']['entity_recognition']
            report += f"""### 实体识别
- 总文本长度: {stats['total_text_length']:,}字

#### 实体统计
"""
            for entity_type, count in stats['entity_counts'].items():
                if count > 0:
                    report += f"- {entity_type}: {count}个\n"
            
            report += "\n#### 实体密度（每千字）\n"
            for entity_type, density in stats['entity_density'].items():
                if density > 0:
                    report += f"- {entity_type}: {density}\n"
            
            report += "\n#### 最频繁实体\n"
            for entity_type, freq_info in stats['most_frequent'].items():
                if freq_info:
                    report += f"- {entity_type}: {freq_info['entity']} (出现{freq_info['count']}次)\n"
        
        # 输出文件列表
        report += f"""

---

## 输出文件

"""
        for file_type, file_path in results['output_files'].items():
            report += f"- **{file_type}**: `{file_path}`\n"
        
        # 处理建议
        report += f"""

---

## 处理建议

1. **章节分析**: 可以进一步分析各章节的主题和人物出现频率
2. **人物关系**: 建议深入分析人物共现关系，构建人物关系网络
3. **文风分析**: 可以基于分词结果进行文风特征提取
4. **知识图谱**: 基于实体识别结果构建红楼梦知识图谱

---

*报告由红楼梦AI续写系统自动生成*
"""
        
        return report
    
    def process_single_chapter(self, chapter_file: Union[str, Path]) -> Dict[str, any]:
        """
        处理单个章节文件
        
        Args:
            chapter_file: 章节文件路径
            
        Returns:
            Dict: 处理结果
        """
        chapter_path = Path(chapter_file)
        
        if not chapter_path.exists():
            raise FileNotFoundError(f"章节文件不存在: {chapter_path}")
        
        logger.info(f"处理单个章节: {chapter_path}")
        
        # 读取章节内容
        with open(chapter_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # 分词分析
        tokenization_result = self.tokenizer.analyze_text(text)
        
        # 实体识别
        entities_result = self.entity_recognizer.recognize_entities(text)
        entity_stats = self.entity_recognizer.get_entity_statistics(text)
        
        # 保存结果
        output_dir = chapter_path.parent / "analysis"
        output_dir.mkdir(exist_ok=True)
        
        chapter_analysis_file = output_dir / f"{chapter_path.stem}_analysis.json"
        
        analysis_data = {
            'chapter_file': str(chapter_path),
            'tokenization': tokenization_result,
            'entity_recognition': entities_result,
            'entity_statistics': entity_stats,
            'processing_time': self._get_timestamp()
        }
        
        with open(chapter_analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"章节分析完成: {chapter_analysis_file}")
        
        return analysis_data
    
    def batch_process_chapters(self) -> List[Dict[str, any]]:
        """
        批量处理所有章节
        
        Returns:
            List[Dict]: 处理结果列表
        """
        chapters_dir = self.chapter_splitter.output_dir
        
        if not chapters_dir.exists():
            logger.error("章节目录不存在，请先运行完整文本处理")
            return []
        
        # 查找所有章节文件
        chapter_files = list(chapters_dir.glob("*.md"))
        
        if not chapter_files:
            logger.warning("未找到章节文件")
            return []
        
        logger.info(f"开始批量处理{len(chapter_files)}个章节")
        
        results = []
        
        for chapter_file in sorted(chapter_files):
            try:
                result = self.process_single_chapter(chapter_file)
                results.append(result)
            except Exception as e:
                logger.error(f"处理章节{chapter_file}失败: {e}")
                results.append({
                    'chapter_file': str(chapter_file),
                    'error': str(e)
                })
        
        logger.info(f"批量处理完成，成功处理{len([r for r in results if 'error' not in r])}个章节")
        
        return results
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_pipeline_info(self) -> Dict[str, any]:
        """
        获取管道信息
        
        Returns:
            Dict: 管道信息
        """
        return {
            'output_base_dir': str(self.output_base_dir),
            'custom_dict_path': self.custom_dict_path,
            'components': {
                'preprocessor': 'TextPreprocessor',
                'chapter_splitter': 'ChapterSplitter',
                'tokenizer': 'HongLouMengTokenizer',
                'entity_recognizer': 'EntityRecognizer'
            },
            'tokenizer_stats': self.tokenizer.get_statistics(),
            'entity_recognizer_info': self.entity_recognizer.get_entity_info()
        } 