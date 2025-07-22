"""
AI续写红楼梦项目

一个基于LangChain的人工智能续写红楼梦系统
"""

__version__ = "1.0.0"
__author__ = "YaoHai"
__description__ = "AI Continuation of Dream of the Red Chamber using LangChain"

from .core import HongLouMengContinuation
from .config import Config
from .prompts import PromptTemplates

__all__ = [
    "HongLouMengContinuation",
    "Config", 
    "PromptTemplates"
]