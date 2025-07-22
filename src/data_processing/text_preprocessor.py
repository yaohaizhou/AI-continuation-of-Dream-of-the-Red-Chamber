"""
红楼梦文本预处理模块
负责文本的编码统一、格式清理、基础规范化
"""

import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from loguru import logger


class TextPreprocessor:
    """文本预处理器"""
    
    def __init__(self):
        """初始化预处理器"""
        # 常见的无用标记和符号
        self.useless_marks = [
            "----",  # 章节分隔线
            "===",   # 其他分隔线
            "***",   # 星号分隔线
            "...",   # 省略号
        ]
        
        # 对话标记模式
        self.dialogue_patterns = [
            r'"[^"]*"',           # 双引号对话
            r'"[^"]*"',           # 中文双引号对话  
            r'「[^」]*」',         # 日式双引号
            r'『[^』]*』',         # 日式双书名号
        ]
        
        # 章节标题模式
        self.chapter_pattern = r'###\s*(第[一二三四五六七八九十百千万零〇]+回\s+.*?)$'
        
    def process_file(self, file_path: Path) -> Dict[str, any]:
        """
        处理文件，进行完整的预处理
        
        Args:
            file_path: 输入文件路径
            
        Returns:
            Dict: 包含处理结果的字典
        """
        logger.info(f"开始处理文件: {file_path}")
        
        # 读取文件并确保编码
        text = self._ensure_utf8_encoding(file_path)
        
        # 基础清理
        cleaned_text = self._basic_cleaning(text)
        
        # 格式规范化
        normalized_text = self._normalize_format(cleaned_text)
        
        # 提取章节信息
        chapters_info = self._extract_chapter_info(normalized_text)
        
        # 段落分割
        paragraphs = self._split_paragraphs(normalized_text)
        
        # 对话标记
        dialogues = self._mark_dialogues(normalized_text)
        
        # 统计信息
        stats = self._calculate_stats(normalized_text, paragraphs, dialogues)
        
        result = {
            'original_text': text,
            'processed_text': normalized_text,
            'chapters_info': chapters_info,
            'paragraphs': paragraphs,
            'dialogues': dialogues,
            'stats': stats
        }
        
        logger.info(f"文件处理完成，共{stats['total_chars']}字，{stats['total_paragraphs']}段落，{stats['total_dialogues']}对话")
        
        return result
    
    def _ensure_utf8_encoding(self, file_path: Path) -> str:
        """
        确保文件以UTF-8编码读取
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: UTF-8编码的文本内容
        """
        encodings = ['utf-8', 'gb2312', 'gbk', 'big5']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    text = f.read()
                logger.debug(f"成功使用{encoding}编码读取文件")
                return text
            except UnicodeDecodeError:
                continue
        
        # 如果所有编码都失败，强制使用utf-8并忽略错误
        logger.warning("无法确定文件编码，强制使用UTF-8")
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    def _basic_cleaning(self, text: str) -> str:
        """
        基础文本清理
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        # 移除无用标记
        for mark in self.useless_marks:
            text = text.replace(mark, '')
        
        # 规范化空白字符
        text = re.sub(r'\r\n', '\n', text)  # 统一换行符
        text = re.sub(r'\r', '\n', text)    # 统一换行符
        text = re.sub(r'　', ' ', text)      # 全角空格转半角
        text = re.sub(r'\t', ' ', text)     # Tab转空格
        
        # 移除多余空行（但保留段落分隔）
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # 移除行首行尾空格
        lines = []
        for line in text.split('\n'):
            lines.append(line.strip())
        text = '\n'.join(lines)
        
        return text
    
    def _normalize_format(self, text: str) -> str:
        """
        格式规范化
        
        Args:
            text: 清理后的文本
            
        Returns:
            str: 规范化后的文本
        """
        # 规范化标点符号
        replacements = {
            ',': '，',    # 半角逗号转全角
            '.': '。',    # 半角句号转全角
            ';': '；',    # 半角分号转全角
            ':': '：',    # 半角冒号转全角
            '?': '？',    # 半角问号转全角
            '!': '！',    # 半角感叹号转全角
            '"': '"',     # 英文双引号转中文左引号
            '"': '"',     # 英文双引号转中文右引号（如有必要）
            "'": ''',     # 英文单引号转中文左引号
            "'": ''',     # 英文单引号转中文右引号（如有必要）
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Unicode规范化
        text = unicodedata.normalize('NFKC', text)
        
        return text
    
    def _extract_chapter_info(self, text: str) -> List[Dict[str, any]]:
        """
        提取章节信息
        
        Args:
            text: 规范化文本
            
        Returns:
            List[Dict]: 章节信息列表
        """
        chapters = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # 匹配章节标题
            match = re.match(self.chapter_pattern, line.strip())
            if match:
                chapter_title = match.group(1).strip()
                
                # 提取回数
                chapter_num_match = re.search(r'第([一二三四五六七八九十百千万零〇]+)回', chapter_title)
                chapter_num = self._chinese_to_number(chapter_num_match.group(1)) if chapter_num_match else len(chapters) + 1
                
                chapters.append({
                    'chapter_num': chapter_num,
                    'title': chapter_title,
                    'line_start': i,
                    'char_start': len('\n'.join(lines[:i]))
                })
        
        # 计算章节结束位置
        for i, chapter in enumerate(chapters[:-1]):
            next_chapter = chapters[i + 1]
            chapter['line_end'] = next_chapter['line_start']
            chapter['char_end'] = next_chapter['char_start']
        
        # 最后一章的结束位置
        if chapters:
            chapters[-1]['line_end'] = len(lines)
            chapters[-1]['char_end'] = len(text)
        
        return chapters
    
    def _split_paragraphs(self, text: str) -> List[Dict[str, any]]:
        """
        段落分割
        
        Args:
            text: 规范化文本
            
        Returns:
            List[Dict]: 段落信息列表
        """
        paragraphs = []
        text_lines = text.split('\n')
        
        current_paragraph = []
        start_line = 0
        
        for i, line in enumerate(text_lines):
            line = line.strip()
            
            if not line:  # 空行，结束当前段落
                if current_paragraph:
                    paragraph_text = '\n'.join(current_paragraph)
                    paragraphs.append({
                        'text': paragraph_text,
                        'line_start': start_line,
                        'line_end': i,
                        'char_count': len(paragraph_text)
                    })
                    current_paragraph = []
                start_line = i + 1
            else:
                current_paragraph.append(line)
        
        # 处理最后一个段落
        if current_paragraph:
            paragraph_text = '\n'.join(current_paragraph)
            paragraphs.append({
                'text': paragraph_text,
                'line_start': start_line,
                'line_end': len(text_lines),
                'char_count': len(paragraph_text)
            })
        
        return paragraphs
    
    def _mark_dialogues(self, text: str) -> List[Dict[str, any]]:
        """
        标记对话内容
        
        Args:
            text: 规范化文本
            
        Returns:
            List[Dict]: 对话信息列表
        """
        dialogues = []
        
        for pattern in self.dialogue_patterns:
            for match in re.finditer(pattern, text):
                dialogue_text = match.group()
                start_pos = match.start()
                end_pos = match.end()
                
                # 查找对话所在的行号
                lines_before = text[:start_pos].count('\n')
                
                dialogues.append({
                    'text': dialogue_text,
                    'start_pos': start_pos,
                    'end_pos': end_pos,
                    'line_num': lines_before + 1,
                    'length': len(dialogue_text)
                })
        
        # 按位置排序
        dialogues.sort(key=lambda x: x['start_pos'])
        
        return dialogues
    
    def _calculate_stats(self, text: str, paragraphs: List[Dict], dialogues: List[Dict]) -> Dict[str, any]:
        """
        计算统计信息
        
        Args:
            text: 处理后的文本
            paragraphs: 段落列表
            dialogues: 对话列表
            
        Returns:
            Dict: 统计信息
        """
        return {
            'total_chars': len(text),
            'total_lines': text.count('\n') + 1,
            'total_paragraphs': len(paragraphs),
            'total_dialogues': len(dialogues),
            'avg_paragraph_length': sum(p['char_count'] for p in paragraphs) / len(paragraphs) if paragraphs else 0,
            'dialogue_char_count': sum(d['length'] for d in dialogues),
            'dialogue_ratio': sum(d['length'] for d in dialogues) / len(text) if text else 0
        }
    
    def _chinese_to_number(self, chinese_num: str) -> int:
        """
        中文数字转阿拉伯数字
        
        Args:
            chinese_num: 中文数字字符串
            
        Returns:
            int: 阿拉伯数字
        """
        num_map = {
            '零': 0, '〇': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '百': 100, '千': 1000, '万': 10000
        }
        
        result = 0
        temp = 0
        
        for char in chinese_num:
            if char in num_map:
                num = num_map[char]
                if num == 10:
                    if temp == 0:
                        temp = 1
                    result += temp * num
                    temp = 0
                elif num == 100:
                    temp *= num
                elif num == 1000:
                    temp *= num
                elif num == 10000:
                    result = (result + temp) * num
                    temp = 0
                else:
                    temp = num
        
        result += temp
        return result
    
    def save_processed_text(self, result: Dict[str, any], output_path: Path):
        """
        保存处理后的文本
        
        Args:
            result: 处理结果字典
            output_path: 输出路径
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result['processed_text'])
        
        logger.info(f"处理后文本已保存到: {output_path}") 