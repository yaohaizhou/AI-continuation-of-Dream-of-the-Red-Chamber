"""
配置管理模块
管理项目的所有配置信息，包括API密钥、模型参数等
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


@dataclass
class ModelConfig:
    """模型配置"""
    model_name: str = "gpt-4"
    temperature: float = 0.8
    max_tokens: int = 2000
    top_p: float = 0.9


@dataclass
class WritingConfig:
    """写作配置"""
    max_continuation_length: int = 1000
    style_consistency: bool = True
    character_consistency: bool = True
    enable_chapter_structure: bool = True
    

class Config:
    """主配置类"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self._config_data = {}
        self.load_config()
        
        # API配置
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        # 模型配置
        self.model = ModelConfig(**self._config_data.get("model", {}))
        
        # 写作配置
        self.writing = WritingConfig(**self._config_data.get("writing", {}))
        
        # 路径配置
        self.data_dir = Path(self._config_data.get("paths", {}).get("data_dir", "data"))
        self.output_dir = Path(self._config_data.get("paths", {}).get("output_dir", "output"))
        self.original_text_path = self.data_dir / "original_hongloumeng.txt"
        
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        return str(Path(__file__).parent.parent.parent / "config" / "config.yaml")
        
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config_data = yaml.safe_load(f) or {}
        else:
            self._config_data = self._get_default_config()
            self.save_config()
            
    def save_config(self):
        """保存配置文件"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config_data, f, default_flow_style=False, 
                     allow_unicode=True, indent=2)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "model": {
                "model_name": "gpt-4",
                "temperature": 0.8,
                "max_tokens": 2000,
                "top_p": 0.9
            },
            "writing": {
                "max_continuation_length": 1000,
                "style_consistency": True,
                "character_consistency": True,
                "enable_chapter_structure": True
            },
            "paths": {
                "data_dir": "data",
                "output_dir": "output"
            }
        }
    
    def update_config(self, new_config: Dict[str, Any]):
        """更新配置"""
        self._config_data.update(new_config)
        self.save_config()
        self.load_config()  # 重新加载以应用更改
    
    def validate(self) -> bool:
        """验证配置是否有效"""
        if not self.openai_api_key:
            raise ValueError("请设置OPENAI_API_KEY环境变量")
        
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
        return True