"""
太虚幻境象征意象建议器

基于红楼梦太虚幻境判词数据，为续写提供智能的象征意象推荐，
增强文学性和意境营造。

Author: AI-HongLouMeng Project
Date: 2025-07-23
"""

import json
import re
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class SymbolMapping:
    """象征映射数据结构"""
    character: str
    symbols: List[str]
    metaphors: List[str]
    emotional_tone: str
    fate_theme: str
    literary_devices: List[str]


@dataclass
class ImageryRecommendation:
    """象征意象推荐结果"""
    primary_symbols: List[str]  # 主要象征元素
    secondary_symbols: List[str]  # 次要象征元素
    emotional_tone: str  # 情感基调
    literary_devices: List[str]  # 建议的文学手法
    usage_context: str  # 使用语境
    explanation: str  # 推荐理由
    confidence: float  # 推荐置信度


class SymbolicImageryAdvisor:
    """太虚幻境象征意象建议器
    
    基于太虚幻境判词数据，为文学续写提供智能的象征意象推荐，
    支持角色专属象征、情境感知推荐、文学手法建议等功能。
    """
    
    def __init__(self, taixu_data_path: str = "data/processed/taixu_prophecies.json"):
        """初始化象征意象建议器
        
        Args:
            taixu_data_path: 太虚幻境判词数据文件路径
        """
        self.taixu_data_path = Path(taixu_data_path)
        self.prophecies = {}
        self.symbol_mappings = {}
        self.symbol_index = {}  # 象征元素索引
        self.character_index = {}  # 角色象征索引
        
        # 加载数据
        self._load_prophecies()
        self._build_symbol_mappings()
        self._build_indexes()
        
        logger.info(f"象征意象建议器初始化完成，加载 {len(self.symbol_mappings)} 个角色的象征数据")
    
    def _load_prophecies(self) -> None:
        """加载太虚幻境判词数据"""
        try:
            if not self.taixu_data_path.exists():
                logger.error(f"太虚幻境数据文件不存在: {self.taixu_data_path}")
                self.prophecies = {}
                return
                
            with open(self.taixu_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.prophecies = data
                
            logger.info(f"成功加载太虚幻境判词数据: {self.taixu_data_path}")
                
        except Exception as e:
            logger.error(f"加载太虚幻境数据失败: {e}")
            self.prophecies = {}
    
    def _build_symbol_mappings(self) -> None:
        """构建角色象征映射"""
        self.symbol_mappings = {}
        
        if not self.prophecies:
            logger.warning("太虚幻境数据为空，无法构建象征映射")
            return
            
        # 处理正册、副册、又副册
        for ce_key in ["main_册", "副册", "又副册"]:
            if ce_key not in self.prophecies:
                continue
                
            ce_data = self.prophecies[ce_key]
            if not isinstance(ce_data, list):
                continue
                
            for entry in ce_data:
                if not isinstance(entry, dict):
                    continue
                    
                # 获取角色列表
                characters = entry.get("characters", [])
                if not characters:
                    continue
                    
                # 提取象征数据
                image = entry.get("image", {})
                poem = entry.get("poem", {})
                fate_interp = entry.get("fate_interpretations", [])
                
                symbols = image.get("symbolic_elements", [])
                metaphors = image.get("visual_metaphors", [])
                emotional_tone = poem.get("emotional_tone", "")
                literary_devices = poem.get("literary_devices", [])
                
                # 为每个角色创建映射
                for character in characters:
                    fate_theme = ""
                    if fate_interp:
                        fate_info = next((f for f in fate_interp if f.get("character") == character), fate_interp[0])
                        fate_theme = fate_info.get("fate_summary", "")
                    
                    mapping = SymbolMapping(
                        character=character,
                        symbols=symbols,
                        metaphors=metaphors,
                        emotional_tone=emotional_tone,
                        fate_theme=fate_theme,
                        literary_devices=literary_devices
                    )
                    
                    self.symbol_mappings[character] = mapping
        
        logger.info(f"构建角色象征映射完成，覆盖 {len(self.symbol_mappings)} 个角色")
    
    def _build_indexes(self) -> None:
        """构建象征元素和角色索引"""
        self.symbol_index = {}  # symbol -> [characters]
        self.character_index = {}  # character -> symbols
        
        for character, mapping in self.symbol_mappings.items():
            # 角色索引
            all_symbols = mapping.symbols + mapping.metaphors
            self.character_index[character] = all_symbols
            
            # 象征索引
            for symbol in all_symbols:
                if symbol not in self.symbol_index:
                    self.symbol_index[symbol] = []
                self.symbol_index[symbol].append(character)
        
        logger.info(f"构建索引完成: {len(self.symbol_index)} 个象征元素, {len(self.character_index)} 个角色")
    
    def recommend_symbols(self, 
                         character: Optional[str] = None,
                         scene_context: Optional[str] = None,
                         emotional_tone: Optional[str] = None,
                         literary_style: Optional[str] = None) -> ImageryRecommendation:
        """推荐象征意象
        
        Args:
            character: 目标角色名称
            scene_context: 场景上下文描述
            emotional_tone: 期望的情感基调 (悲叹/哀愁/凄美等)
            literary_style: 文学风格 (诗词/对话/场景等)
            
        Returns:
            ImageryRecommendation: 象征意象推荐结果
        """
        try:
            # 基于角色的象征推荐
            character_symbols = self._get_character_symbols(character) if character else []
            
            # 基于情感基调的象征推荐
            tone_symbols = self._get_tone_symbols(emotional_tone) if emotional_tone else []
            
            # 基于场景上下文的象征推荐
            context_symbols = self._get_context_symbols(scene_context) if scene_context else []
            
            # 合并和排序推荐结果
            primary_symbols = character_symbols[:3]  # 角色专属象征优先
            secondary_symbols = list(set(tone_symbols + context_symbols))[:5]
            
            # 确定情感基调
            final_tone = emotional_tone or (
                self.symbol_mappings[character].emotional_tone if character in self.symbol_mappings else "中性"
            )
            
            # 推荐文学手法
            literary_devices = self._get_literary_devices(character, literary_style)
            
            # 生成使用语境和解释
            usage_context = self._generate_usage_context(character, scene_context, literary_style)
            explanation = self._generate_explanation(character, primary_symbols, secondary_symbols)
            
            # 计算推荐置信度
            confidence = self._calculate_confidence(character, scene_context, emotional_tone)
            
            recommendation = ImageryRecommendation(
                primary_symbols=primary_symbols,
                secondary_symbols=secondary_symbols,
                emotional_tone=final_tone,
                literary_devices=literary_devices,
                usage_context=usage_context,
                explanation=explanation,
                confidence=confidence
            )
            
            logger.info(f"生成象征推荐: 角色={character}, 主要象征={len(primary_symbols)}, 置信度={confidence:.2f}")
            return recommendation
            
        except Exception as e:
            logger.error(f"象征推荐失败: {e}")
            return self._get_default_recommendation()
    
    def _get_character_symbols(self, character: str) -> List[str]:
        """获取角色专属象征"""
        if not character or character not in self.symbol_mappings:
            return []
            
        mapping = self.symbol_mappings[character]
        return mapping.symbols + mapping.metaphors
    
    def _get_tone_symbols(self, emotional_tone: str) -> List[str]:
        """基于情感基调获取象征"""
        if not emotional_tone:
            return []
            
        tone_mapping = {
            "悲叹": ["枯木", "凋零", "秋风", "落花", "残月"],
            "哀愁": ["雨", "云", "泪", "柳絮", "孤雁"],
            "凄美": ["雪", "梅花", "明月", "竹", "清泉"],
            "欢快": ["春风", "花开", "彩蝶", "莺歌", "绿柳"],
            "壮丽": ["高山", "大海", "长河", "明珠", "金辉"]
        }
        
        return tone_mapping.get(emotional_tone, [])
    
    def _get_context_symbols(self, scene_context: str) -> List[str]:
        """基于场景上下文获取象征"""
        if not scene_context:
            return []
            
        symbols = []
        context_lower = scene_context.lower()
        
        # 场景关键词映射
        scene_mappings = {
            "园林": ["花", "树", "水", "石", "亭"],
            "房间": ["灯", "帘", "床", "镜", "香"],
            "春天": ["花开", "柳絮", "燕", "雨", "绿"],
            "秋天": ["枫叶", "菊花", "雁", "霜", "金"],
            "夜晚": ["月", "星", "灯", "影", "梦"],
            "离别": ["柳", "泪", "帆", "路", "云"]
        }
        
        for keyword, related_symbols in scene_mappings.items():
            if keyword in scene_context:
                symbols.extend(related_symbols)
        
        return symbols
    
    def _get_literary_devices(self, character: str, literary_style: str) -> List[str]:
        """获取推荐的文学手法"""
        devices = []
        
        # 角色专属文学手法
        if character and character in self.symbol_mappings:
            devices.extend(self.symbol_mappings[character].literary_devices)
        
        # 文学风格推荐
        style_devices = {
            "诗词": ["对仗", "押韵", "意象", "比兴"],
            "对话": ["语调", "称谓", "语气", "暗示"],
            "场景": ["渲染", "对比", "烘托", "象征"],
            "抒情": ["比喻", "拟人", "夸张", "排比"]
        }
        
        if literary_style in style_devices:
            devices.extend(style_devices[literary_style])
        
        return list(set(devices))[:4]  # 去重并限制数量
    
    def _generate_usage_context(self, character: str, scene_context: str, literary_style: str) -> str:
        """生成使用语境说明"""
        contexts = []
        
        if character:
            contexts.append(f"适用于{character}相关的情节")
            
        if scene_context:
            contexts.append(f"适用于{scene_context}场景")
            
        if literary_style:
            contexts.append(f"适用于{literary_style}风格的续写")
        
        return "；".join(contexts) if contexts else "通用语境"
    
    def _generate_explanation(self, character: str, primary: List[str], secondary: List[str]) -> str:
        """生成推荐理由说明"""
        explanations = []
        
        if character and character in self.symbol_mappings:
            mapping = self.symbol_mappings[character]
            explanations.append(f"基于{character}在太虚幻境判词中的象征设定")
            
            if mapping.fate_theme:
                explanations.append(f"符合'{mapping.fate_theme}'的命运主题")
        
        if primary:
            explanations.append(f"主要象征'{', '.join(primary[:2])}'等体现角色特质")
            
        if secondary:
            explanations.append(f"辅助象征'{', '.join(secondary[:2])}'等增强文学氛围")
        
        return "；".join(explanations) if explanations else "基于通用文学象征规律推荐"
    
    def _calculate_confidence(self, character: str, scene_context: str, emotional_tone: str) -> float:
        """计算推荐置信度"""
        confidence = 0.5  # 基础置信度
        
        # 角色匹配度
        if character and character in self.symbol_mappings:
            confidence += 0.3
        
        # 场景匹配度
        if scene_context:
            confidence += 0.1
            
        # 情感匹配度
        if emotional_tone:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _get_default_recommendation(self) -> ImageryRecommendation:
        """获取默认推荐结果"""
        return ImageryRecommendation(
            primary_symbols=["花", "月", "风"],
            secondary_symbols=["云", "水", "竹"],
            emotional_tone="中性",
            literary_devices=["比喻", "象征"],
            usage_context="通用文学创作",
            explanation="基于红楼梦常用文学意象的通用推荐",
            confidence=0.3
        )
    
    def get_character_symbols(self, character: str) -> Dict[str, any]:
        """获取指定角色的完整象征信息
        
        Args:
            character: 角色名称
            
        Returns:
            Dict: 角色象征信息
        """
        if character not in self.symbol_mappings:
            return {
                "character": character,
                "found": False,
                "message": f"未找到角色 '{character}' 的象征数据"
            }
        
        mapping = self.symbol_mappings[character]
        return {
            "character": character,
            "found": True,
            "symbols": mapping.symbols,
            "metaphors": mapping.metaphors,
            "emotional_tone": mapping.emotional_tone,
            "fate_theme": mapping.fate_theme,
            "literary_devices": mapping.literary_devices
        }
    
    def search_symbols(self, query: str) -> Dict[str, List[str]]:
        """搜索包含指定象征元素的角色
        
        Args:
            query: 象征元素查询词
            
        Returns:
            Dict: 搜索结果
        """
        results = {}
        query_lower = query.lower()
        
        for symbol, characters in self.symbol_index.items():
            if query_lower in symbol.lower():
                results[symbol] = characters
        
        return results
    
    def enhance_literary_atmosphere(self, text: str, target_character: str = None) -> Dict[str, any]:
        """增强文本的文学意境营造
        
        Args:
            text: 待增强的文本
            target_character: 目标角色（可选）
            
        Returns:
            Dict: 增强建议
        """
        # 检测文本中的角色
        detected_characters = []
        for character in self.symbol_mappings.keys():
            if character in text:
                detected_characters.append(character)
        
        # 确定主要角色
        main_character = target_character or (detected_characters[0] if detected_characters else None)
        
        # 生成象征推荐
        recommendation = self.recommend_symbols(
            character=main_character,
            scene_context=text[:100],  # 使用文本前100字符作为场景上下文
            literary_style="场景"
        )
        
        return {
            "original_text": text,
            "detected_characters": detected_characters,
            "main_character": main_character,
            "symbol_recommendations": recommendation,
            "enhancement_suggestions": [
                f"考虑融入象征元素：{', '.join(recommendation.primary_symbols)}",
                f"建议情感基调：{recommendation.emotional_tone}",
                f"推荐文学手法：{', '.join(recommendation.literary_devices)}",
                f"使用语境：{recommendation.usage_context}"
            ]
        }
    
    def get_statistics(self) -> Dict[str, any]:
        """获取象征意象建议器统计信息"""
        return {
            "total_characters": len(self.symbol_mappings),
            "total_symbols": len(self.symbol_index),
            "character_list": list(self.symbol_mappings.keys()),
            "most_common_symbols": self._get_most_common_symbols(5),
            "emotional_tones": list(set(m.emotional_tone for m in self.symbol_mappings.values() if m.emotional_tone)),
            "data_source": str(self.taixu_data_path)
        }
    
    def _get_most_common_symbols(self, top_n: int = 5) -> List[Tuple[str, int]]:
        """获取最常见的象征元素"""
        symbol_counts = {}
        for mapping in self.symbol_mappings.values():
            for symbol in mapping.symbols + mapping.metaphors:
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        return sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]


def create_symbolic_imagery_advisor(taixu_data_path: str = None) -> SymbolicImageryAdvisor:
    """创建象征意象建议器实例
    
    Args:
        taixu_data_path: 太虚幻境数据路径（可选）
        
    Returns:
        SymbolicImageryAdvisor: 象征意象建议器实例
    """
    default_path = "data/processed/taixu_prophecies.json"
    data_path = taixu_data_path or default_path
    
    return SymbolicImageryAdvisor(data_path)


if __name__ == "__main__":
    # 演示用法
    advisor = create_symbolic_imagery_advisor()
    
    # 获取林黛玉的象征信息
    daiyu_symbols = advisor.get_character_symbols("林黛玉")
    print("林黛玉象征信息:", daiyu_symbols)
    
    # 推荐象征意象
    recommendation = advisor.recommend_symbols(
        character="林黛玉",
        scene_context="秋日园林",
        emotional_tone="凄美"
    )
    print("象征推荐:", recommendation)
    
    # 增强文学氛围
    enhancement = advisor.enhance_literary_atmosphere(
        "宝玉走进潇湘馆，见黛玉正在看书。",
        target_character="林黛玉"
    )
    print("文学增强:", enhancement) 