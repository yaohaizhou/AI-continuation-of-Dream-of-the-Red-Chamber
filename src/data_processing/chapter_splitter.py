"""
红楼梦章节分割模块
负责将完整文本按章节分割，并保存为独立文件
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

from .text_preprocessor import TextPreprocessor


class ChapterSplitter:
    """章节分割器"""
    
    def __init__(self, output_dir: str = "data/processed/chapters"):
        """
        初始化章节分割器
        
        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = Path(output_dir)
        self.preprocessor = TextPreprocessor()
        
    def split_file(self, input_file: Path, force_reprocess: bool = False) -> Dict[str, any]:
        """
        分割文件成章节
        
        Args:
            input_file: 输入文件路径
            force_reprocess: 是否强制重新处理
            
        Returns:
            Dict: 分割结果信息
        """
        logger.info(f"开始分割文件: {input_file}")
        
        # 检查输出目录是否已存在章节文件
        if not force_reprocess and self._check_existing_chapters():
            logger.info("检测到已存在章节文件，跳过分割")
            return self._load_existing_metadata()
        
        # 预处理文本
        preprocessed_result = self.preprocessor.process_file(input_file)
        
        # 提取章节信息
        chapters_info = preprocessed_result['chapters_info']
        processed_text = preprocessed_result['processed_text']
        
        if not chapters_info:
            logger.error("未检测到章节信息，请检查文本格式")
            raise ValueError("未检测到章节信息")
        
        logger.info(f"检测到{len(chapters_info)}个章节")
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 分割章节
        split_results = []
        text_lines = processed_text.split('\n')
        
        for i, chapter in enumerate(chapters_info):
            chapter_result = self._split_single_chapter(
                chapter, text_lines, i + 1, len(chapters_info)
            )
            split_results.append(chapter_result)
        
        # 保存元数据
        metadata = {
            'source_file': str(input_file),
            'total_chapters': len(chapters_info),
            'split_timestamp': self._get_timestamp(),
            'chapters': split_results,
            'stats': preprocessed_result['stats']
        }
        
        self._save_metadata(metadata)
        
        logger.info(f"章节分割完成，共生成{len(split_results)}个章节文件")
        
        return metadata
    
    def _split_single_chapter(self, chapter_info: Dict, text_lines: List[str], 
                            chapter_index: int, total_chapters: int) -> Dict[str, any]:
        """
        分割单个章节
        
        Args:
            chapter_info: 章节信息
            text_lines: 文本行列表
            chapter_index: 章节索引
            total_chapters: 总章节数
            
        Returns:
            Dict: 章节分割结果
        """
        chapter_num = chapter_info['chapter_num']
        chapter_title = chapter_info['title']
        
        # 确定章节内容范围
        start_line = chapter_info['line_start']
        end_line = chapter_info.get('line_end', len(text_lines))
        
        # 提取章节内容（排除标题行）
        chapter_content_lines = text_lines[start_line + 1:end_line]
        chapter_content = '\n'.join(chapter_content_lines).strip()
        
        # 生成文件名
        filename = f"{chapter_num:03d}.md"
        file_path = self.output_dir / filename
        
        # 生成章节文件内容
        file_content = self._format_chapter_content(
            chapter_num, chapter_title, chapter_content
        )
        
        # 保存章节文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        # 计算章节统计信息
        stats = self._calculate_chapter_stats(chapter_content)
        
        result = {
            'chapter_num': chapter_num,
            'title': chapter_title,
            'filename': filename,
            'file_path': str(file_path),
            'content_length': len(chapter_content),
            'line_count': len(chapter_content_lines),
            'stats': stats
        }
        
        logger.debug(f"章节{chapter_num}分割完成: {filename}")
        
        return result
    
    def _format_chapter_content(self, chapter_num: int, title: str, content: str) -> str:
        """
        格式化章节内容
        
        Args:
            chapter_num: 章节号
            title: 章节标题
            content: 章节内容
            
        Returns:
            str: 格式化后的内容
        """
        formatted_content = f"""# {title}

---

**章节信息:**
- 章节号: {chapter_num}
- 标题: {title}
- 字数: {len(content)}

---

## 正文

{content}

---

*文件生成时间: {self._get_timestamp()}*
"""
        return formatted_content
    
    def _calculate_chapter_stats(self, content: str) -> Dict[str, any]:
        """
        计算章节统计信息
        
        Args:
            content: 章节内容
            
        Returns:
            Dict: 统计信息
        """
        # 段落统计
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # 对话统计
        dialogue_count = 0
        for pattern in self.preprocessor.dialogue_patterns:
            import re
            dialogue_count += len(re.findall(pattern, content))
        
        # 句子统计（简单按句号、问号、感叹号计算）
        sentence_endings = ['。', '？', '！']
        sentence_count = sum(content.count(ending) for ending in sentence_endings)
        
        return {
            'char_count': len(content),
            'paragraph_count': len(paragraphs),
            'dialogue_count': dialogue_count,
            'sentence_count': sentence_count,
            'avg_paragraph_length': len(content) / len(paragraphs) if paragraphs else 0
        }
    
    def _check_existing_chapters(self) -> bool:
        """
        检查是否已存在章节文件
        
        Returns:
            bool: 是否存在章节文件
        """
        if not self.output_dir.exists():
            return False
        
        # 检查是否有.md文件
        md_files = list(self.output_dir.glob("*.md"))
        metadata_file = self.output_dir / "metadata.json"
        
        return len(md_files) > 0 and metadata_file.exists()
    
    def _load_existing_metadata(self) -> Dict[str, any]:
        """
        加载已存在的元数据
        
        Returns:
            Dict: 元数据信息
        """
        metadata_file = self.output_dir / "metadata.json"
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"无法加载元数据文件: {e}")
            return {}
    
    def _save_metadata(self, metadata: Dict[str, any]):
        """
        保存元数据到文件
        
        Args:
            metadata: 元数据字典
        """
        metadata_file = self.output_dir / "metadata.json"
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"元数据已保存到: {metadata_file}")
    
    def _get_timestamp(self) -> str:
        """
        获取当前时间戳
        
        Returns:
            str: 时间戳字符串
        """
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_chapter_file(self, chapter_num: int) -> Optional[Path]:
        """
        获取指定章节的文件路径
        
        Args:
            chapter_num: 章节号
            
        Returns:
            Optional[Path]: 章节文件路径，如果不存在返回None
        """
        filename = f"{chapter_num:03d}.md"
        file_path = self.output_dir / filename
        
        return file_path if file_path.exists() else None
    
    def list_chapters(self) -> List[Dict[str, any]]:
        """
        列出所有章节信息
        
        Returns:
            List[Dict]: 章节信息列表
        """
        metadata = self._load_existing_metadata()
        return metadata.get('chapters', [])
    
    def merge_chapters(self, chapter_nums: List[int], output_file: Path):
        """
        合并指定章节为单个文件
        
        Args:
            chapter_nums: 章节号列表
            output_file: 输出文件路径
        """
        merged_content = []
        
        for chapter_num in chapter_nums:
            chapter_file = self.get_chapter_file(chapter_num)
            if chapter_file and chapter_file.exists():
                with open(chapter_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                merged_content.append(content)
                merged_content.append("\n" + "="*50 + "\n")  # 章节分隔线
        
        if merged_content:
            # 移除最后一个分隔线
            merged_content.pop()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(merged_content))
            
            logger.info(f"已合并{len(chapter_nums)}个章节到: {output_file}")
        else:
            logger.warning("未找到任何有效的章节文件进行合并") 