"""
统一LLM管理器

提供统一的LLM调用接口，支持不同任务的配置和调用
"""

import time
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, BaseMessage
from langchain.callbacks import get_openai_callback

from .config_manager import ConfigManager, LLMConfig, get_config

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """LLM响应结果"""
    content: str                    # 响应内容
    model: str                      # 使用的模型
    task: Optional[str] = None      # 任务类型
    tokens_used: int = 0            # 使用的token数
    cost: float = 0.0               # 调用成本
    duration: float = 0.0           # 调用耗时
    timestamp: str = ""             # 时间戳
    metadata: Dict[str, Any] = None # 其他元数据

@dataclass 
class LLMCallStats:
    """LLM调用统计"""
    total_calls: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    total_duration: float = 0.0
    success_count: int = 0
    error_count: int = 0
    tasks: Dict[str, int] = None
    
    def __post_init__(self):
        if self.tasks is None:
            self.tasks = {}


class LLMManager:
    """统一LLM管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.config_manager = get_config()
        self._llm_instances: Dict[str, ChatOpenAI] = {}
        self._call_stats = LLMCallStats()
        
        logger.info("统一LLM管理器初始化完成")
    
    def _get_llm_instance(self, task: Optional[str] = None) -> ChatOpenAI:
        """获取LLM实例（支持缓存）"""
        
        # 获取配置
        llm_config = self.config_manager.get_llm_config(task)
        
        # 创建缓存key
        cache_key = f"{llm_config.model_name}_{llm_config.temperature}_{llm_config.max_tokens}"
        
        if cache_key not in self._llm_instances:
            # 创建新的LLM实例
            try:
                self._llm_instances[cache_key] = ChatOpenAI(
                    model=llm_config.model_name,
                    temperature=llm_config.temperature,
                    max_tokens=llm_config.max_tokens,
                    top_p=llm_config.top_p,
                    frequency_penalty=llm_config.frequency_penalty,
                    presence_penalty=llm_config.presence_penalty,
                    openai_api_key=llm_config.api_key,
                    openai_api_base=llm_config.base_url,
                    request_timeout=llm_config.timeout,
                    max_retries=llm_config.max_retries
                )
                
                logger.info(f"创建LLM实例: {llm_config.model_name} (任务: {task or 'default'})")
                
            except Exception as e:
                logger.error(f"创建LLM实例失败: {e}")
                raise
        
        return self._llm_instances[cache_key]
    
    async def acall(
        self,
        messages: List[BaseMessage],
        task: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """异步调用LLM"""
        return await self._call_llm(messages, task, system_prompt, is_async=True, **kwargs)
    
    def call(
        self,
        messages: List[BaseMessage],
        task: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """同步调用LLM"""
        return self._call_llm(messages, task, system_prompt, is_async=False, **kwargs)
    
    def simple_call(
        self,
        prompt: str,
        task: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """简单文本调用"""
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        return self.call(messages, task, **kwargs)
    
    async def simple_acall(
        self,
        prompt: str,
        task: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """简单文本异步调用"""
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        return await self.acall(messages, task, **kwargs)
    
    def _call_llm(
        self,
        messages: List[BaseMessage],
        task: Optional[str] = None,
        system_prompt: Optional[str] = None,
        is_async: bool = False,
        **kwargs
    ) -> LLMResponse:
        """内部LLM调用方法"""
        
        start_time = time.time()
        llm_config = self.config_manager.get_llm_config(task)
        
        try:
            # 获取LLM实例
            llm = self._get_llm_instance(task)
            
            # 准备消息
            if system_prompt and not any(isinstance(msg, SystemMessage) for msg in messages):
                messages = [SystemMessage(content=system_prompt)] + messages
            
            # 调用LLM
            with get_openai_callback() as cb:
                if is_async:
                    response = llm.ainvoke(messages, **kwargs)
                else:
                    response = llm.invoke(messages, **kwargs)
                
                content = response.content
                tokens_used = cb.total_tokens
                cost = cb.total_cost
            
            duration = time.time() - start_time
            
            # 创建响应对象
            llm_response = LLMResponse(
                content=content,
                model=llm_config.model_name,
                task=task,
                tokens_used=tokens_used,
                cost=cost,
                duration=duration,
                timestamp=datetime.now().isoformat(),
                metadata={
                    "temperature": llm_config.temperature,
                    "max_tokens": llm_config.max_tokens,
                    "message_count": len(messages)
                }
            )
            
            # 更新统计
            self._update_stats(llm_response, success=True)
            
            # 记录日志
            if self.config_manager.logging.log_llm_calls:
                logger.info(f"LLM调用成功: {task or 'default'}, "
                           f"模型: {llm_config.model_name}, "
                           f"耗时: {duration:.2f}s, "
                           f"Token: {tokens_used}")
            
            return llm_response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # 更新错误统计
            self._update_stats(None, success=False)
            
            logger.error(f"LLM调用失败: {e}, 任务: {task or 'default'}, "
                        f"耗时: {duration:.2f}s")
            raise
    
    def _update_stats(self, response: Optional[LLMResponse], success: bool):
        """更新调用统计"""
        self._call_stats.total_calls += 1
        
        if success and response:
            self._call_stats.success_count += 1
            self._call_stats.total_tokens += response.tokens_used
            self._call_stats.total_cost += response.cost
            self._call_stats.total_duration += response.duration
            
            # 任务统计
            task = response.task or "default"
            self._call_stats.tasks[task] = self._call_stats.tasks.get(task, 0) + 1
        else:
            self._call_stats.error_count += 1
    
    def get_stats(self) -> LLMCallStats:
        """获取调用统计"""
        return self._call_stats
    
    def reset_stats(self):
        """重置统计"""
        self._call_stats = LLMCallStats()
        logger.info("LLM调用统计已重置")
    
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        # 这里可以根据provider返回支持的模型
        return [
            "gpt-4", 
            "gpt-4-turbo-preview", 
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]
    
    def warmup(self, tasks: Optional[List[str]] = None):
        """预热LLM实例"""
        logger.info("开始预热LLM实例...")
        
        tasks_to_warmup = tasks or ["default", "context_compression", "style_conversion"]
        
        for task in tasks_to_warmup:
            try:
                # 创建实例并进行简单调用
                llm = self._get_llm_instance(task)
                
                # 简单的预热调用
                test_messages = [HumanMessage(content="Hello")]
                try:
                    llm.invoke(test_messages)
                    logger.info(f"任务 {task} 预热成功")
                except:
                    logger.warning(f"任务 {task} 预热失败，但实例已创建")
                    
            except Exception as e:
                logger.error(f"任务 {task} 预热失败: {e}")
        
        logger.info("LLM实例预热完成")
    
    def clear_cache(self):
        """清理缓存的LLM实例"""
        self._llm_instances.clear()
        logger.info("LLM实例缓存已清理")


# 全局LLM管理器实例
_llm_manager: Optional[LLMManager] = None

def get_llm_manager() -> LLMManager:
    """获取全局LLM管理器实例"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager 