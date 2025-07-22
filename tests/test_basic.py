"""
基础测试模块
测试AI续写红楼梦的核心功能
"""

import pytest
import asyncio
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_hongloumeng import HongLouMengContinuation, Config
from ai_hongloumeng.utils import TextProcessor, FileManager, validate_continuation_quality


class TestTextProcessor:
    """测试文本处理器"""
    
    def setup_method(self):
        """测试前的准备工作"""
        self.processor = TextProcessor()
    
    def test_segment_text(self):
        """测试文本分词"""
        text = "宝玉听了这话"
        result = self.processor.segment_text(text)
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_extract_characters(self):
        """测试人物提取"""
        text = "宝玉见宝钗来了，便道：'姐姐来了'"
        characters = self.processor.extract_characters(text)
        assert "宝玉" in characters
        assert "宝钗" in characters
    
    def test_extract_locations(self):
        """测试地点提取"""
        text = "大观园里怡红院中"
        locations = self.processor.extract_locations(text)
        assert "大观园" in locations
        assert "怡红院" in locations
    
    def test_count_words(self):
        """测试字数统计"""
        text = "测试文本"
        count = self.processor.count_words(text)
        assert count == 4
    
    def test_clean_text(self):
        """测试文本清理"""
        text = "  测试   文本  \n"
        cleaned = self.processor.clean_text(text)
        assert cleaned == "测试 文本"


class TestConfig:
    """测试配置管理"""
    
    def test_config_creation(self):
        """测试配置创建"""
        config = Config()
        assert config.model.model_name is not None
        assert config.model.temperature >= 0.0
        assert config.model.temperature <= 1.0
    
    def test_config_paths(self):
        """测试路径配置"""
        config = Config()
        assert config.data_dir is not None
        assert config.output_dir is not None


class TestFileManager:
    """测试文件管理器"""
    
    def test_file_operations(self, tmp_path):
        """测试文件操作"""
        test_file = tmp_path / "test.txt"
        test_content = "测试内容"
        
        # 测试写入
        FileManager.write_text_file(test_file, test_content)
        assert test_file.exists()
        
        # 测试读取
        content = FileManager.read_text_file(test_file)
        assert content == test_content


class TestValidation:
    """测试质量验证"""
    
    def test_validate_continuation_quality(self):
        """测试续写质量验证"""
        original = "宝玉听了这话"
        continuation = "心中暗想，这宝钗姐姐果然不同"
        
        is_valid, issues = validate_continuation_quality(original, continuation, min_length=10)
        assert is_valid
        assert len(issues) == 0
    
    def test_validate_short_continuation(self):
        """测试短续写验证"""
        original = "宝玉听了这话"
        continuation = "想"
        
        is_valid, issues = validate_continuation_quality(original, continuation, min_length=10)
        assert not is_valid
        assert len(issues) > 0


class TestHongLouMengContinuation:
    """测试红楼梦续写系统"""
    
    def setup_method(self):
        """测试前的准备工作"""
        # 使用测试配置，避免实际API调用
        pass
    
    def test_initialization(self):
        """测试系统初始化"""
        # 这里只测试不依赖API的部分
        config = Config()
        # 不实际创建HongLouMengContinuation实例，因为需要API密钥
        assert config is not None
    
    def test_character_analysis(self):
        """测试人物分析功能"""
        # 创建一个模拟的续写系统进行测试
        from ai_hongloumeng.utils import TextProcessor
        processor = TextProcessor()
        
        text = "宝玉见宝钗来了，在大观园的怡红院里说道：'姐姐来了'"
        
        # 模拟get_character_analysis的部分功能
        characters = processor.extract_characters(text)
        locations = processor.extract_locations(text)
        word_count = processor.count_words(text)
        
        assert "宝玉" in characters
        assert "宝钗" in characters
        assert "大观园" in locations
        assert "怡红院" in locations
        assert word_count > 0


@pytest.mark.asyncio
async def test_async_functionality():
    """测试异步功能的基础框架"""
    # 这里只测试异步功能的基础框架，不实际调用API
    await asyncio.sleep(0.01)  # 模拟异步操作
    assert True


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])