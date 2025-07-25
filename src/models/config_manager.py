"""
统一配置管理器

负责加载和管理项目的所有配置信息
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class LLMConfig:
    """LLM配置"""
    provider: str = "openai"
    model_name: str = "gpt-4"
    temperature: float = 0.8
    max_tokens: int = 2000
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 60
    max_retries: int = 3
    retry_delay: int = 1
    
    # API 配置（从环境变量读取）
    api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    base_url: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    
    # 特定功能配置
    context_compression: Dict[str, Any] = field(default_factory=lambda: {
        "model_name": "gpt-3.5-turbo",
        "temperature": 0.1,
        "max_tokens": 1000
    })
    
    style_conversion: Dict[str, Any] = field(default_factory=lambda: {
        "model_name": "gpt-4",
        "temperature": 0.2,
        "max_tokens": 1500
    })

@dataclass
class WritingConfig:
    """写作配置"""
    max_continuation_length: int = 1000
    style_consistency: bool = True
    character_consistency: bool = True
    enable_chapter_structure: bool = True
    enable_knowledge_enhancement: bool = True

@dataclass
class PathConfig:
    """路径配置"""
    data_dir: str = "data"
    output_dir: str = "output"
    original_text_path: str = "data/raw/hongloumeng_80.md"

@dataclass
class KnowledgeEnhancementConfig:
    """知识增强配置"""
    enable_rag: bool = True
    enable_fate_check: bool = True
    enable_symbolic_advisor: bool = True
    enable_context_compression: bool = True

@dataclass
class RAGConfig:
    """RAG配置"""
    chunk_size: int = 1000
    chunk_overlap: int = 100
    top_k: int = 5
    similarity_threshold: float = 0.7

@dataclass
class StyleConversionConfig:
    """文风转换配置"""
    vocabulary_level: str = "high"
    enable_sentence_restructure: bool = True
    enable_rhetorical_devices: bool = True
    enable_context_optimization: bool = True

@dataclass
class AdvancedConfig:
    """高级配置"""
    enable_memory: bool = False
    use_vector_search: bool = False
    batch_size: int = 5
    enable_caching: bool = True

@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    save_to_file: bool = True
    max_file_size: str = "10 MB"
    backup_count: int = 7
    log_llm_calls: bool = False

@dataclass
class PerformanceConfig:
    """性能配置"""
    enable_parallel_processing: bool = False
    max_concurrent_requests: int = 3
    request_rate_limit: int = 10


class ConfigManager:
    """统一配置管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.config_path = self._get_config_path()
        self._config_data = {}
        self.load_config()
        
        # 初始化各个配置模块
        self.llm = LLMConfig(**self._get_section("llm", {}))
        self.writing = WritingConfig(**self._get_section("writing", {}))
        self.paths = PathConfig(**self._get_section("paths", {}))
        self.knowledge_enhancement = KnowledgeEnhancementConfig(**self._get_section("knowledge_enhancement", {}))
        self.rag = RAGConfig(**self._get_section("rag", {}))
        self.style_conversion = StyleConversionConfig(**self._get_section("style_conversion", {}))
        self.advanced = AdvancedConfig(**self._get_section("advanced", {}))
        self.logging = LoggingConfig(**self._get_section("logging", {}))
        self.performance = PerformanceConfig(**self._get_section("performance", {}))
        
        logger.info("统一配置管理器初始化完成")
    
    def _get_config_path(self) -> Path:
        """获取配置文件路径"""
        # 查找config.yaml文件
        current_dir = Path(__file__).parent
        
        # 向上查找到项目根目录
        for i in range(5):  # 最多向上查找5级
            config_path = current_dir / "config" / "config.yaml"
            if config_path.exists():
                return config_path
            current_dir = current_dir.parent
        
        # 如果找不到，使用默认路径
        default_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
        return default_path
    
    def load_config(self):
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config_data = yaml.safe_load(f) or {}
                logger.info(f"配置文件加载成功: {self.config_path}")
            else:
                logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                self._config_data = {}
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self._config_data = {}
    
    def _get_section(self, section_name: str, default: Dict[str, Any]) -> Dict[str, Any]:
        """获取配置节"""
        return self._config_data.get(section_name, default)
    
    def get_llm_config(self, task: Optional[str] = None) -> LLMConfig:
        """
        获取LLM配置
        
        Args:
            task: 任务类型，如 'context_compression', 'style_conversion'
        """
        if task and hasattr(self.llm, task):
            # 获取特定任务配置
            task_config = getattr(self.llm, task)
            
            # 创建基于基础配置的副本
            config_dict = {
                "provider": self.llm.provider,
                "model_name": task_config.get("model_name", self.llm.model_name),
                "temperature": task_config.get("temperature", self.llm.temperature),
                "max_tokens": task_config.get("max_tokens", self.llm.max_tokens),
                "top_p": self.llm.top_p,
                "frequency_penalty": self.llm.frequency_penalty,
                "presence_penalty": self.llm.presence_penalty,
                "timeout": self.llm.timeout,
                "max_retries": self.llm.max_retries,
                "retry_delay": self.llm.retry_delay,
                "api_key": self.llm.api_key,
                "base_url": self.llm.base_url,
            }
            
            return LLMConfig(**config_dict)
        
        return self.llm
    
    def validate(self) -> bool:
        """验证配置"""
        # 检查必需的API密钥
        if not self.llm.api_key:
            raise ValueError("请设置OPENAI_API_KEY环境变量")
        
        # 检查并创建必需的目录
        data_dir = Path(self.paths.data_dir)
        output_dir = Path(self.paths.output_dir)
        
        data_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("配置验证通过")
        return True
    
    def update_config(self, section: str, updates: Dict[str, Any]):
        """更新配置"""
        if section in self._config_data:
            self._config_data[section].update(updates)
        else:
            self._config_data[section] = updates
        
        # 重新初始化相关配置
        self.load_config()
        logger.info(f"配置已更新: {section}")


# 全局配置实例
_config_manager: Optional[ConfigManager] = None

def get_config() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager 