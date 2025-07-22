"""
工具函数模块
包含文本处理、文件操作等通用工具函数
"""

import re
import jieba
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from loguru import logger


class TextProcessor:
    """文本处理工具类"""
    
    def __init__(self):
        # 初始化分词器
        jieba.initialize()
        
        # 红楼梦特色词汇（可以从专门的词典文件加载）
        self.hongloumeng_words = {
            "人物": ["宝玉", "黛玉", "宝钗", "元春", "探春", "惜春", "迎春", "王熙凤", "贾母", "王夫人"],
            "地点": ["荣国府", "宁国府", "大观园", "潇湘馆", "蘅芜苑", "怡红院", "栊翠庵"],
            "称谓": ["老太太", "太太", "奶奶", "姑娘", "爷", "哥儿", "丫头"]
        }
        
        # 添加红楼梦专用词汇到分词器
        for category in self.hongloumeng_words.values():
            for word in category:
                jieba.add_word(word)
    
    def segment_text(self, text: str) -> List[str]:
        """文本分词"""
        return list(jieba.cut(text))
    
    def extract_characters(self, text: str) -> List[str]:
        """提取文本中的人物名称"""
        characters = []
        for char in self.hongloumeng_words["人物"]:
            if char in text:
                characters.append(char)
        return list(set(characters))
    
    def extract_locations(self, text: str) -> List[str]:
        """提取文本中的地点"""
        locations = []
        for loc in self.hongloumeng_words["地点"]:
            if loc in text:
                locations.append(loc)
        return list(set(locations))
    
    def clean_text(self, text: str) -> str:
        """清理文本，去除多余的空白字符等"""
        # 去除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        # 去除首尾空白
        text = text.strip()
        return text
    
    def split_into_paragraphs(self, text: str) -> List[str]:
        """将文本分割成段落"""
        paragraphs = text.split('\n')
        return [p.strip() for p in paragraphs if p.strip()]
    
    def count_words(self, text: str) -> int:
        """统计字数（中文按字符计算）"""
        # 去除空白字符后计算长度
        clean_text = re.sub(r'\s+', '', text)
        return len(clean_text)
    
    def extract_dialogue(self, text: str) -> List[Dict[str, str]]:
        """提取对话内容"""
        dialogues = []
        # 简单的对话提取模式，可以根据实际需求改进
        pattern = r'[""]([^""]+)[""]'
        matches = re.findall(pattern, text)
        
        for i, match in enumerate(matches):
            dialogues.append({
                "id": i + 1,
                "content": match,
                "speaker": "未知"  # 需要更复杂的逻辑来识别说话者
            })
        
        return dialogues


class FileManager:
    """文件管理工具类"""
    
    @staticmethod
    def read_text_file(file_path: Path, encoding: str = 'utf-8') -> str:
        """读取文本文件"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
            return ""
    
    @staticmethod
    def write_text_file(file_path: Path, content: str, encoding: str = 'utf-8'):
        """写入文本文件"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            logger.info(f"文件写入成功: {file_path}")
        except Exception as e:
            logger.error(f"写入文件失败 {file_path}: {e}")
    
    @staticmethod
    def append_to_file(file_path: Path, content: str, encoding: str = 'utf-8'):
        """追加内容到文件"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'a', encoding=encoding) as f:
                f.write(content)
            logger.info(f"内容追加成功: {file_path}")
        except Exception as e:
            logger.error(f"追加文件失败 {file_path}: {e}")
    
    @staticmethod
    def save_json(file_path: Path, data: Dict[str, Any], encoding: str = 'utf-8'):
        """保存JSON文件"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding=encoding) as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"JSON文件保存成功: {file_path}")
        except Exception as e:
            logger.error(f"保存JSON文件失败 {file_path}: {e}")
    
    @staticmethod
    def load_json(file_path: Path, encoding: str = 'utf-8') -> Dict[str, Any]:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载JSON文件失败 {file_path}: {e}")
            return {}


class OutputFormatter:
    """输出格式化工具类"""
    
    @staticmethod
    def format_continuation_output(
        original_text: str,
        continuation: str,
        metadata: Dict[str, Any]
    ) -> str:
        """格式化续写输出"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        output = f"""# AI续写红楼梦
        
## 生成信息
- 生成时间: {timestamp}
- 模型: {metadata.get('model', 'unknown')}
- 温度: {metadata.get('temperature', 'unknown')}
- 最大长度: {metadata.get('max_tokens', 'unknown')}

## 原文上下文
{original_text}

## 续写内容
{continuation}

## 统计信息
- 原文字数: {len(original_text)}
- 续写字数: {len(continuation)}
- 总字数: {len(original_text) + len(continuation)}
"""
        return output
    
    @staticmethod
    def format_chapter_output(
        title: str,
        content: str,
        summary: str,
        metadata: Dict[str, Any]
    ) -> str:
        """格式化章节输出"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        output = f"""# {title}

## 章节概述
{summary}

## 正文内容
{content}

---
*生成时间: {timestamp}*
*生成模型: {metadata.get('model', 'AI')}*
"""
        return output


def validate_continuation_quality(
    original_text: str,
    continuation: str,
    min_length: int = 100
) -> Tuple[bool, List[str]]:
    """验证续写质量"""
    issues = []
    
    # 检查长度
    if len(continuation) < min_length:
        issues.append(f"续写内容过短，当前{len(continuation)}字，最少需要{min_length}字")
    
    # 检查重复性
    if continuation in original_text:
        issues.append("续写内容与原文重复")
    
    # 检查基本格式
    if not continuation.strip():
        issues.append("续写内容为空")
    
    # 可以添加更多质量检查规则
    
    return len(issues) == 0, issues


def extract_context_window(
    text: str,
    position: int,
    window_size: int = 500
) -> str:
    """提取指定位置的上下文窗口"""
    start = max(0, position - window_size)
    end = min(len(text), position + window_size)
    return text[start:end]