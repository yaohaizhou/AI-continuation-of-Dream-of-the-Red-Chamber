"""
核心AI续写模块
基于LangChain的红楼梦续写核心逻辑
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

from langchain.schema import HumanMessage, SystemMessage
from loguru import logger

from .prompts import PromptTemplates
from .utils import TextProcessor, FileManager, OutputFormatter, validate_continuation_quality

# 使用统一的模型管理器
from ..models import get_llm_manager, get_config

# 添加知识增强模块导入
try:
    from ..knowledge_enhancement.enhanced_prompter import EnhancedPrompter
    from ..knowledge_enhancement.fate_consistency_checker import FateConsistencyChecker
    from ..rag_retrieval.rag_pipeline import RAGPipeline
    from ..long_text_management.context_compressor import ContextCompressor
    from ..long_text_management.chapter_planner import ChapterPlanner
    KNOWLEDGE_MODULES_AVAILABLE = True
except ImportError:
    KNOWLEDGE_MODULES_AVAILABLE = False
    logger.warning("知识增强模块不可用，将使用基础续写功能")


class HongLouMengContinuation:
    """红楼梦AI续写核心类"""
    
    def __init__(self, enable_knowledge_enhancement: bool = True):
        """初始化续写系统"""
        # 使用统一的配置管理器
        self.config = get_config()
        self.llm_manager = get_llm_manager()
        
        # 验证配置
        self.config.validate()
        
        # 初始化基础组件
        self.text_processor = TextProcessor()
        self.file_manager = FileManager()
        self.output_formatter = OutputFormatter()
        self.prompt_templates = PromptTemplates()
        
        # 初始化知识增强模块
        self.enable_knowledge_enhancement = enable_knowledge_enhancement and KNOWLEDGE_MODULES_AVAILABLE
        if self.enable_knowledge_enhancement:
            self._init_knowledge_modules()
        
        # 原文内容缓存
        self._original_text = None
        
        logger.info(f"红楼梦AI续写系统初始化完成 (知识增强: {'开启' if self.enable_knowledge_enhancement else '关闭'})")
    
    def _init_knowledge_modules(self) -> None:
        """初始化知识增强模块"""
        try:
            # RAG检索系统
            self.rag_pipeline = RAGPipeline()
            logger.info("RAG检索系统初始化完成")
            
            # 命运一致性检查器
            self.fate_checker = FateConsistencyChecker()
            logger.info("命运一致性检查器初始化完成")
            
            # 上下文压缩器
            self.context_compressor = ContextCompressor()
            logger.info("上下文压缩器初始化完成")
            
            # 章节规划器
            self.chapter_planner = ChapterPlanner()
            logger.info("章节规划器初始化完成")
            
            # 增强提示词生成器
            self.enhanced_prompter = EnhancedPrompter()
            logger.info("增强提示词生成器初始化完成")
            
        except Exception as e:
            logger.error(f"知识增强模块初始化失败: {e}")
            self.enable_knowledge_enhancement = False
    
    def load_original_text(self, file_path: Optional[Path] = None) -> str:
        """加载原著文本"""
        if file_path is None:
            file_path = Path(self.config.paths.original_text_path)
            
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
        chapter_num: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        续写故事主方法 - 集成知识增强功能
        
        Args:
            context: 续写上下文
            continuation_type: 续写类型
            max_length: 最大长度
            chapter_num: 章节号（用于命运检查）
            **kwargs: 其他参数
        """
        if max_length is None:
            max_length = self.config.writing.max_continuation_length
            
        logger.info(f"开始续写，类型: {continuation_type}, 最大长度: {max_length}, 知识增强: {self.enable_knowledge_enhancement}")
        
        try:
            # 准备上下文
            prepared_context = self._prepare_context(context)
            
            # 知识增强处理
            enhanced_context = prepared_context
            rag_info = {}
            chapter_guidance = {}
            
            if self.enable_knowledge_enhancement:
                # 1. RAG检索相关信息
                rag_info = await self._perform_rag_retrieval(prepared_context, continuation_type)
                
                # 2. 获取章节规划指导（如果提供了章节号）
                if chapter_num:
                    chapter_guidance = self._get_chapter_guidance(chapter_num)
                
                # 3. 生成增强上下文
                enhanced_context = self._build_enhanced_context(
                    prepared_context, rag_info, chapter_guidance
                )
            
            # 根据类型选择不同的续写方法
            if continuation_type == "basic":
                result = await self._enhanced_basic_continuation(enhanced_context, max_length, rag_info)
            elif continuation_type == "dialogue":
                result = await self._enhanced_dialogue_continuation(enhanced_context, rag_info, **kwargs)
            elif continuation_type == "scene":
                result = await self._enhanced_scene_continuation(enhanced_context, rag_info, **kwargs)
            elif continuation_type == "poetry":
                result = await self._enhanced_poetry_continuation(enhanced_context, rag_info, **kwargs)
            else:
                raise ValueError(f"不支持的续写类型: {continuation_type}")
            
            # 知识增强质量检查
            if self.enable_knowledge_enhancement:
                # 命运一致性检查
                fate_check_result = self._check_fate_consistency(
                    result["continuation"], 
                    chapter_num=chapter_num
                )
                result["fate_consistency"] = fate_check_result
                
                # 增强质量评估
                enhanced_quality = self._evaluate_enhanced_quality(
                    context, result["continuation"], rag_info
                )
                result["enhanced_quality"] = enhanced_quality
            
            # 基础验证
            is_valid, issues = validate_continuation_quality(
                context, result["continuation"], min_length=max_length // 10
            )
            
            result["quality_check"] = {
                "is_valid": is_valid,
                "issues": issues
            }
            
            # 添加知识增强信息到结果
            if self.enable_knowledge_enhancement:
                result["knowledge_enhancement"] = {
                    "rag_info": rag_info,
                    "chapter_guidance": chapter_guidance,
                    "enhanced_context_used": len(enhanced_context) > len(prepared_context)
                }
            
            logger.info(f"续写完成，生成{len(result['continuation'])}字 (知识增强: {self.enable_knowledge_enhancement})")
            return result
            
        except Exception as e:
            logger.error(f"续写失败: {e}")
            raise
    
    async def _perform_rag_retrieval(self, context: str, continuation_type: str) -> Dict[str, Any]:
        """执行RAG检索"""
        try:
            if not self.enable_knowledge_enhancement:
                return {}
            
            # 构建检索查询
            query = f"{context} {continuation_type}"
            
            # 执行检索
            search_results = self.rag_pipeline.vectordb.search(
                query_text=query,
                top_k=5,
                metadata_filter={"type": continuation_type} if continuation_type else None
            )
            
            # 提取相关信息
            retrieved_info = {
                "relevant_passages": [result.get("text", "") for result in search_results],
                "character_info": self._extract_character_info_from_results(search_results),
                "scene_info": self._extract_scene_info_from_results(search_results),
                "style_examples": self._extract_style_examples_from_results(search_results),
                "search_results_count": len(search_results)
            }
            
            logger.debug(f"RAG检索完成，获得{len(search_results)}个相关结果")
            return retrieved_info
            
        except Exception as e:
            logger.error(f"RAG检索失败: {e}")
            return {}
    
    def _get_chapter_guidance(self, chapter_num: int) -> Dict[str, Any]:
        """获取章节规划指导"""
        try:
            if not self.enable_knowledge_enhancement:
                return {}
            
            # 加载章节规划
            plan = self.chapter_planner.load_plan()
            if not plan:
                return {}
            
            # 获取特定章节指导
            chapter_plan = self.chapter_planner.get_chapter_plan(chapter_num, plan)
            if not chapter_plan:
                return {}
            
            return {
                "chapter_theme": chapter_plan.theme.value if hasattr(chapter_plan.theme, 'value') else str(chapter_plan.theme),
                "main_characters": chapter_plan.main_characters,
                "key_events": chapter_plan.key_events,
                "symbolic_imagery": chapter_plan.symbolic_imagery,
                "emotional_tone": chapter_plan.emotional_tone,
                "fate_events": chapter_plan.fate_events
            }
            
        except Exception as e:
            logger.error(f"获取章节指导失败: {e}")
            return {}
    
    def _build_enhanced_context(self, 
                               original_context: str, 
                               rag_info: Dict[str, Any], 
                               chapter_guidance: Dict[str, Any]) -> str:
        """构建增强上下文"""
        if not self.enable_knowledge_enhancement:
            return original_context
        
        context_parts = [original_context]
        
        # 添加RAG检索信息
        if rag_info.get("character_info"):
            context_parts.append(f"\n【相关人物信息】\n{rag_info['character_info']}")
        
        if rag_info.get("scene_info"):
            context_parts.append(f"\n【场景背景】\n{rag_info['scene_info']}")
        
        # 添加章节指导信息
        if chapter_guidance.get("key_events"):
            context_parts.append(f"\n【章节要点】\n{'; '.join(chapter_guidance['key_events'])}")
        
        if chapter_guidance.get("symbolic_imagery"):
            context_parts.append(f"\n【建议象征意象】\n{', '.join(chapter_guidance['symbolic_imagery'])}")
        
        return "".join(context_parts)
    
    def _check_fate_consistency(self, continuation: str, chapter_num: Optional[int] = None) -> Dict[str, Any]:
        """检查命运一致性"""
        try:
            if not self.enable_knowledge_enhancement:
                return {"enabled": False}
            
            # 执行命运一致性检查
            consistency_result = self.fate_checker.check_consistency(continuation)
            
            return {
                "enabled": True,
                "overall_score": consistency_result.overall_score,
                "violations": [
                    {
                        "character": v.character,
                        "type": v.violation_type.value,
                        "severity": v.severity,
                        "description": v.description
                    } for v in consistency_result.violations
                ],
                "recommendations": consistency_result.recommendations
            }
            
        except Exception as e:
            logger.error(f"命运一致性检查失败: {e}")
            return {"enabled": False, "error": str(e)}
    
    def _evaluate_enhanced_quality(self, 
                                  context: str, 
                                  continuation: str, 
                                  rag_info: Dict[str, Any]) -> Dict[str, Any]:
        """评估增强质量"""
        if not self.enable_knowledge_enhancement:
            return {"enabled": False}
        
        quality_metrics = {
            "enabled": True,
            "rag_utilization": len(rag_info.get("relevant_passages", [])) > 0,
            "character_consistency": self._check_character_consistency(context, continuation),
            "style_adherence": self._check_style_adherence(continuation),
            "plot_coherence": self._check_plot_coherence(context, continuation)
        }
        
        return quality_metrics
    
    # 增强版续写方法
    async def _enhanced_basic_continuation(self, context: str, max_length: int, rag_info: Dict[str, Any]) -> Dict[str, Any]:
        """基础续写 - 知识增强版"""
        if self.enable_knowledge_enhancement and self.enhanced_prompter:
            # 使用增强提示词
            prompt = self.enhanced_prompter.get_enhanced_prompt(
                context=context,
                prompt_type="basic",
                rag_context=rag_info
            )
        else:
            # 使用传统提示词
            prompt_template = self.prompt_templates.get_basic_continuation_prompt()
            prompt = prompt_template.format(context=context, max_length=max_length)
        
        # 使用统一的LLM管理器
        system_prompt = "你是一位精通红楼梦的古典文学专家和作家。"
        response = await self.llm_manager.simple_acall(
            prompt=prompt,
            system_prompt=system_prompt,
            task="basic_continuation"
        )
        
        return {
            "continuation": response.content,
            "type": "basic",
            "context": context,
            "enhanced": self.enable_knowledge_enhancement,
            "metadata": {
                "model": response.model,
                "temperature": response.metadata.get("temperature"),
                "max_tokens": response.metadata.get("max_tokens"),
                "tokens_used": response.tokens_used,
                "cost": response.cost,
                "duration": response.duration,
                "timestamp": response.timestamp
            }
        }

    async def _enhanced_dialogue_continuation(
        self,
        context: str,
        rag_info: Dict[str, Any] = {},
        character_info: str = "",
        scene_context: str = "",
        dialogue_context: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """对话续写 - 知识增强版"""
        if self.enable_knowledge_enhancement and self.enhanced_prompter:
            # 使用增强提示词
            prompt = self.enhanced_prompter.get_enhanced_prompt(
                context=context,
                prompt_type="dialogue",
                rag_context=rag_info
            )
        else:
            # 使用传统提示词
            prompt_template = self.prompt_templates.get_character_dialogue_prompt()
            prompt = prompt_template.format(
                character_info=character_info or "红楼梦主要人物",
                scene_context=scene_context or context,
                dialogue_context=dialogue_context or "日常对话"
            )
        
        # 使用统一的LLM管理器
        system_prompt = "你是一位精通红楼梦人物对话的专家。"
        response = await self.llm_manager.simple_acall(
            prompt=prompt,
            system_prompt=system_prompt,
            task="dialogue_continuation"
        )
        
        return {
            "continuation": response.content,
            "type": "dialogue",
            "context": context,
            "parameters": {
                "character_info": character_info,
                "scene_context": scene_context,
                "dialogue_context": dialogue_context
            },
            "enhanced": self.enable_knowledge_enhancement,
            "metadata": {
                "model": response.model,
                "tokens_used": response.tokens_used,
                "cost": response.cost,
                "duration": response.duration,
                "timestamp": response.timestamp
            }
        }

    async def _enhanced_scene_continuation(
        self,
        context: str,
        rag_info: Dict[str, Any] = {},
        scene_setting: str = "",
        time: str = "",
        location: str = "",
        characters: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """场景续写 - 知识增强版"""
        if self.enable_knowledge_enhancement and self.enhanced_prompter:
            # 使用增强提示词
            prompt = self.enhanced_prompter.get_enhanced_prompt(
                context=context,
                prompt_type="scene",
                rag_context=rag_info
            )
        else:
            # 使用传统提示词
            prompt_template = self.prompt_templates.get_scene_description_prompt()
            prompt = prompt_template.format(
                scene_setting=scene_setting or "大观园日常",
                time=time or "不详",
                location=location or "大观园",
                characters=characters or "主要人物"
            )
        
        # 使用统一的LLM管理器
        system_prompt = "你是一位精通红楼梦场景描写的专家。"
        response = await self.llm_manager.simple_acall(
            prompt=prompt,
            system_prompt=system_prompt,
            task="scene_continuation"
        )
        
        return {
            "continuation": response.content,
            "type": "scene",
            "context": context,
            "parameters": {
                "scene_setting": scene_setting,
                "time": time,
                "location": location,
                "characters": characters
            },
            "enhanced": self.enable_knowledge_enhancement,
            "metadata": {
                "model": response.model,
                "tokens_used": response.tokens_used,
                "cost": response.cost,
                "duration": response.duration,
                "timestamp": response.timestamp
            }
        }

    async def _enhanced_poetry_continuation(
        self,
        context: str,
        rag_info: Dict[str, Any] = {},
        poetry_type: str = "律诗",
        theme: str = "",
        character: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """诗词续写 - 知识增强版"""
        if self.enable_knowledge_enhancement and self.enhanced_prompter:
            # 使用增强提示词
            prompt = self.enhanced_prompter.get_enhanced_prompt(
                context=context,
                prompt_type="poetry",
                rag_context=rag_info
            )
        else:
            # 使用传统提示词
            prompt_template = self.prompt_templates.get_poetry_creation_prompt()
            prompt = prompt_template.format(
                poetry_type=poetry_type,
                theme=theme or "感怀",
                context=context,
                character=character or "不详"
            )
        
        # 使用统一的LLM管理器
        system_prompt = "你是一位精通古典诗词创作的专家。"
        response = await self.llm_manager.simple_acall(
            prompt=prompt,
            system_prompt=system_prompt,
            task="poetry_continuation"
        )
        
        return {
            "continuation": response.content,
            "type": "poetry",
            "context": context,
            "parameters": {
                "poetry_type": poetry_type,
                "theme": theme,
                "character": character
            },
            "enhanced": self.enable_knowledge_enhancement,
            "metadata": {
                "model": response.model,
                "tokens_used": response.tokens_used,
                "cost": response.cost,
                "duration": response.duration,
                "timestamp": response.timestamp
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
        
        output_path = Path(self.config.paths.output_dir) / output_filename
        
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

    # 辅助方法
    def _extract_character_info_from_results(self, results: List[Dict]) -> str:
        """从检索结果中提取人物信息"""
        character_info = []
        for result in results:
            metadata = result.get("metadata", {})
            if metadata.get("type") == "character":
                character_info.append(result.get("text", ""))
        return "\n".join(character_info[:3])  # 最多3个人物信息
    
    def _extract_scene_info_from_results(self, results: List[Dict]) -> str:
        """从检索结果中提取场景信息"""
        scene_info = []
        for result in results:
            metadata = result.get("metadata", {})
            if metadata.get("type") == "scene":
                scene_info.append(result.get("text", ""))
        return "\n".join(scene_info[:2])  # 最多2个场景信息
    
    def _extract_style_examples_from_results(self, results: List[Dict]) -> str:
        """从检索结果中提取文风示例"""
        style_examples = []
        for result in results:
            text = result.get("text", "")
            if len(text) > 50 and len(text) < 200:  # 适当长度的文风示例
                style_examples.append(text)
        return "\n".join(style_examples[:2])  # 最多2个示例
    
    def _check_character_consistency(self, context: str, continuation: str) -> float:
        """检查人物一致性"""
        # 简单实现：检查人物名称的一致性
        context_characters = self.text_processor.extract_characters(context)
        continuation_characters = self.text_processor.extract_characters(continuation)
        
        if not context_characters:
            return 1.0
        
        consistent_characters = len(set(context_characters) & set(continuation_characters))
        return consistent_characters / len(context_characters)
    
    def _check_style_adherence(self, continuation: str) -> float:
        """检查文风符合度"""
        # 简单实现：检查古典词汇使用
        classical_words = ['却说', '只见', '但见', '原来', '不料', '岂知']
        word_count = sum(1 for word in classical_words if word in continuation)
        return min(word_count / 3, 1.0)  # 期望至少有3个古典词汇
    
    def _check_plot_coherence(self, context: str, continuation: str) -> float:
        """检查情节连贯性"""
        # 简单实现：检查逻辑连接词
        coherence_words = ['于是', '因此', '然后', '接着', '随即', '便']
        word_count = sum(1 for word in coherence_words if word in continuation)
        return min(word_count / 2, 1.0)  # 期望至少有2个连接词