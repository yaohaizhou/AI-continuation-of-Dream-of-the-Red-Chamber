"""
核心AI续写模块
基于LangChain的红楼梦续写核心逻辑
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.callbacks import get_openai_callback
from loguru import logger

from .config import Config
from .prompts import PromptTemplates
from .utils import TextProcessor, FileManager, OutputFormatter, validate_continuation_quality


class HongLouMengContinuation:
    """红楼梦AI续写核心类"""
    
    def __init__(self, config: Optional[Config] = None):
        """初始化续写系统"""
        self.config = config or Config()
        self.config.validate()
        
        # 初始化LLM
        self.llm = ChatOpenAI(
            model=self.config.model.model_name,
            temperature=self.config.model.temperature,
            max_tokens=self.config.model.max_tokens,
            openai_api_key=self.config.openai_api_key,
            openai_api_base=self.config.openai_base_url
        )
        
        # 初始化组件
        self.text_processor = TextProcessor()
        self.file_manager = FileManager()
        self.output_formatter = OutputFormatter()
        self.prompt_templates = PromptTemplates()
        
        # 原文内容缓存
        self._original_text = None
        
        logger.info("红楼梦AI续写系统初始化完成")
    
    def load_original_text(self, file_path: Optional[Path] = None) -> str:
        """加载原著文本"""
        if file_path is None:
            file_path = self.config.original_text_path
            
        if not file_path.exists():
            logger.warning(f"原著文件不存在: {file_path}")
            return ""
            
        self._original_text = self.file_manager.read_text_file(file_path)
        logger.info(f"已加载原著文本，共{len(self._original_text)}字")
        return self._original_text
    
    def _prepare_context(self, context_text: str, max_context_length: int = 2000) -> str:
        """准备上下文，确保长度合适"""
        if len(context_text) <= max_context_length:
            return context_text
            
        # 如果太长，取最后的部分作为上下文
        return context_text[-max_context_length:]
    
    async def continue_story(
        self,
        context: str,
        continuation_type: str = "basic",
        max_length: int = None,
        **kwargs
    ) -> Dict[str, Any]:
        """续写故事主方法"""
        if max_length is None:
            max_length = self.config.writing.max_continuation_length
            
        logger.info(f"开始续写，类型: {continuation_type}, 最大长度: {max_length}")
        
        try:
            # 准备上下文
            prepared_context = self._prepare_context(context)
            
            # 根据类型选择不同的续写方法
            if continuation_type == "basic":
                result = await self._basic_continuation(prepared_context, max_length)
            elif continuation_type == "dialogue":
                result = await self._dialogue_continuation(prepared_context, **kwargs)
            elif continuation_type == "scene":
                result = await self._scene_continuation(prepared_context, **kwargs)
            elif continuation_type == "poetry":
                result = await self._poetry_continuation(prepared_context, **kwargs)
            else:
                raise ValueError(f"不支持的续写类型: {continuation_type}")
            
            # 验证续写质量
            is_valid, issues = validate_continuation_quality(
                context, result["continuation"], min_length=max_length // 10
            )
            
            result["quality_check"] = {
                "is_valid": is_valid,
                "issues": issues
            }
            
            logger.info(f"续写完成，生成{len(result['continuation'])}字")
            return result
            
        except Exception as e:
            logger.error(f"续写失败: {e}")
            raise
    
    async def _basic_continuation(self, context: str, max_length: int) -> Dict[str, Any]:
        """基础续写"""
        prompt_template = self.prompt_templates.get_basic_continuation_prompt()
        prompt = prompt_template.format(context=context, max_length=max_length)
        
        with get_openai_callback() as cb:
            messages = [
                SystemMessage(content="你是一位精通红楼梦的古典文学专家和作家。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            continuation = response.content
            
            return {
                "continuation": continuation,
                "type": "basic",
                "context": context,
                "metadata": {
                    "model": self.config.model.model_name,
                    "temperature": self.config.model.temperature,
                    "max_tokens": self.config.model.max_tokens,
                    "tokens_used": cb.total_tokens,
                    "cost": cb.total_cost,
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    async def _dialogue_continuation(
        self,
        context: str,
        character_info: str = "",
        scene_context: str = "",
        dialogue_context: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """对话续写"""
        prompt_template = self.prompt_templates.get_character_dialogue_prompt()
        prompt = prompt_template.format(
            character_info=character_info or "红楼梦主要人物",
            scene_context=scene_context or context,
            dialogue_context=dialogue_context or "日常对话"
        )
        
        with get_openai_callback() as cb:
            messages = [
                SystemMessage(content="你是一位精通红楼梦人物对话的专家。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            continuation = response.content
            
            return {
                "continuation": continuation,
                "type": "dialogue",
                "context": context,
                "parameters": {
                    "character_info": character_info,
                    "scene_context": scene_context,
                    "dialogue_context": dialogue_context
                },
                "metadata": {
                    "model": self.config.model.model_name,
                    "tokens_used": cb.total_tokens,
                    "cost": cb.total_cost,
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    async def _scene_continuation(
        self,
        context: str,
        scene_setting: str = "",
        time: str = "",
        location: str = "",
        characters: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """场景续写"""
        prompt_template = self.prompt_templates.get_scene_description_prompt()
        prompt = prompt_template.format(
            scene_setting=scene_setting or "大观园日常",
            time=time or "不详",
            location=location or "大观园",
            characters=characters or "主要人物"
        )
        
        with get_openai_callback() as cb:
            messages = [
                SystemMessage(content="你是一位精通红楼梦场景描写的专家。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            continuation = response.content
            
            return {
                "continuation": continuation,
                "type": "scene",
                "context": context,
                "parameters": {
                    "scene_setting": scene_setting,
                    "time": time,
                    "location": location,
                    "characters": characters
                },
                "metadata": {
                    "model": self.config.model.model_name,
                    "tokens_used": cb.total_tokens,
                    "cost": cb.total_cost,
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    async def _poetry_continuation(
        self,
        context: str,
        poetry_type: str = "律诗",
        theme: str = "",
        character: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """诗词续写"""
        prompt_template = self.prompt_templates.get_poetry_creation_prompt()
        prompt = prompt_template.format(
            poetry_type=poetry_type,
            theme=theme or "感怀",
            context=context,
            character=character or "不详"
        )
        
        with get_openai_callback() as cb:
            messages = [
                SystemMessage(content="你是一位精通古典诗词创作的专家。"),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            continuation = response.content
            
            return {
                "continuation": continuation,
                "type": "poetry",
                "context": context,
                "parameters": {
                    "poetry_type": poetry_type,
                    "theme": theme,
                    "character": character
                },
                "metadata": {
                    "model": self.config.model.model_name,
                    "tokens_used": cb.total_tokens,
                    "cost": cb.total_cost,
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    def save_continuation(
        self,
        result: Dict[str, Any],
        output_filename: Optional[str] = None
    ) -> Path:
        """保存续写结果"""
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"continuation_{timestamp}.txt"
        
        output_path = self.config.output_dir / output_filename
        
        # 格式化输出
        formatted_output = self.output_formatter.format_continuation_output(
            original_text=result["context"],
            continuation=result["continuation"],
            metadata=result["metadata"]
        )
        
        # 保存文件
        self.file_manager.write_text_file(output_path, formatted_output)
        
        # 同时保存JSON格式的元数据
        json_path = output_path.with_suffix('.json')
        self.file_manager.save_json(json_path, result)
        
        logger.info(f"续写结果已保存到: {output_path}")
        return output_path
    
    def get_character_analysis(self, text: str) -> Dict[str, Any]:
        """分析文本中的人物信息"""
        characters = self.text_processor.extract_characters(text)
        locations = self.text_processor.extract_locations(text)
        dialogues = self.text_processor.extract_dialogue(text)
        
        return {
            "characters": characters,
            "locations": locations,
            "dialogues": dialogues,
            "word_count": self.text_processor.count_words(text)
        }
    
    async def batch_continuation(
        self,
        contexts: List[str],
        continuation_type: str = "basic",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """批量续写"""
        logger.info(f"开始批量续写，共{len(contexts)}个文本段落")
        
        tasks = [
            self.continue_story(context, continuation_type, **kwargs)
            for context in contexts
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"第{i+1}个续写失败: {result}")
                processed_results.append({
                    "error": str(result),
                    "context": contexts[i]
                })
            else:
                processed_results.append(result)
        
        logger.info(f"批量续写完成，成功{len([r for r in processed_results if 'error' not in r])}个")
        return processed_results