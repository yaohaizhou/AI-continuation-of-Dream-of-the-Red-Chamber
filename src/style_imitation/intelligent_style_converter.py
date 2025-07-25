"""
智能文风转换器

将现代化的AI生成文本转换为符合红楼梦原著风格的古典文学文本。

核心功能：
- 词汇层面转换：现代词汇→古典词汇映射
- 句式层面重构：语序调整和助词添加
- 修辞层面增强：比喻、对偶等修辞手法
- 语境层面优化：人物身份和情境适配
"""

import re
import json
import jieba
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict

from .classical_style_analyzer import ClassicalStyleAnalyzer, StyleFeatures
from .style_template_library import StyleTemplateLibrary, DialogueType, NarrativeType

@dataclass
class ConversionResult:
    """转换结果"""
    original_text: str                      # 原始文本
    converted_text: str                     # 转换后文本
    conversion_operations: List[str]        # 转换操作记录
    vocabulary_changes: Dict[str, str]      # 词汇替换记录
    sentence_adjustments: List[str]         # 句式调整记录
    rhetorical_enhancements: List[str]      # 修辞增强记录
    quality_score: float                    # 转换质量评分
    confidence_score: float                 # 转换置信度

@dataclass
class ConversionConfig:
    """转换配置"""
    vocabulary_level: str = "high"          # 词汇转换强度 (low/medium/high)
    sentence_restructure: bool = True       # 是否重构句式
    add_rhetorical_devices: bool = True     # 是否添加修辞
    preserve_meaning: bool = True           # 是否保持语义
    character_context: Optional[str] = None # 人物身份上下文
    scene_context: Optional[str] = None     # 场景上下文

class IntelligentStyleConverter:
    """智能文风转换器"""
    
    def __init__(self, 
                 analyzer: Optional[ClassicalStyleAnalyzer] = None,
                 template_library: Optional[StyleTemplateLibrary] = None):
        self.logger = logging.getLogger(__name__)
        
        # 初始化分析器和模板库
        self.analyzer = analyzer or ClassicalStyleAnalyzer()
        self.template_library = template_library or StyleTemplateLibrary()
        
        # 初始化转换规则
        self._init_conversion_rules()
        
        # 转换历史
        self.conversion_history: List[ConversionResult] = []
        
    def _init_conversion_rules(self):
        """初始化转换规则"""
        
        # 大幅扩展词汇映射规则
        self.vocabulary_mapping = {
            # 基础程度副词
            "很": "甚", "非常": "极", "特别": "分外", "十分": "甚是",
            "特殊": "特异", "普通": "寻常", "一般": "一般", "平常": "平常",
            
            # 动作动词
            "说": "道", "说话": "言语", "说道": "说道", "讲": "讲说",
            "看": "瞧", "看见": "只见", "看到": "瞧见", "观看": "观瞧",
            "听": "听见", "听到": "听得", "注意": "留神", "发现": "发觉",
            "想": "思量", "思考": "思忖", "考虑": "计较", "打算": "盘算",
            "走": "去", "来": "来了", "去": "去了", "回": "回来",
            "跑": "奔跑", "跳": "蹦跳", "站": "立", "坐": "坐下",
            "躺": "卧", "睡": "安寝", "醒": "醒来", "起": "起身",
            "吃": "用", "喝": "饮", "穿": "着", "戴": "戴上",
            "拿": "取", "放": "搁", "给": "与", "送": "送与",
            "买": "买得", "卖": "卖与", "找": "寻", "等": "等候",
            
            # 情感形容词
            "着急": "心焦", "担心": "担忧", "害怕": "惊恐", "恐惧": "恐怖",
            "高兴": "欢喜", "开心": "喜悦", "快乐": "快活", "愉快": "喜悦",
            "生气": "恼怒", "愤怒": "愤慨", "恼火": "恼恨", "气愤": "气恼",
            "伤心": "悲戚", "难过": "难过", "痛苦": "痛楚", "悲伤": "哀伤",
            "惊讶": "惊奇", "奇怪": "奇异", "诧异": "诧异", "震惊": "震骇",
            "紧张": "紧张", "焦虑": "焦心", "不安": "不安", "慌张": "慌乱",
            "兴奋": "兴奋", "激动": "激动", "感动": "感动", "温暖": "温暖",
            
            # 外貌描述
            "漂亮": "标致", "美丽": "娇美", "好看": "好看", "俊美": "俊美",
            "丑陋": "丑恶", "难看": "难看", "美": "美", "俊": "俊俏",
            "瘦": "瘦弱", "胖": "丰腴", "高": "颀长", "矮": "短小",
            "白": "白皙", "黑": "黝黑", "红": "红润", "黄": "蜡黄",
            
            # 性格特征
            "聪明": "伶俐", "笨": "愚钝", "可爱": "可人", "乖巧": "乖觉",
            "顽皮": "顽劣", "老实": "老成", "活泼": "活泼", "文静": "娴静",
            "勇敢": "勇敢", "胆小": "胆怯", "大胆": "大胆", "小心": "小心",
            "善良": "良善", "坏": "不良", "好": "好", "坏蛋": "恶人",
            
            # 疾病健康
            "生病": "身子不好", "病了": "身子抱恙", "感冒": "伤风", 
            "发烧": "发热", "咳嗽": "咳嗽", "头疼": "头疼", "肚子疼": "腹疼",
            "健康": "康健", "虚弱": "虚弱", "强壮": "强健", "累": "乏累",
            
            # 时间词汇
            "现在": "如今", "刚才": "方才", "以前": "从前", "后来": "后来",
            "马上": "立刻", "立即": "即刻", "突然": "忽然", "忽然": "忽地",
            "经常": "时常", "总是": "总是", "偶尔": "偶然", "有时": "有时",
            "早上": "早间", "上午": "上午", "中午": "午间", "下午": "午后",
            "晚上": "晚间", "夜里": "夜间", "深夜": "深夜", "黎明": "黎明",
            
            # 地点场所
            "房间": "屋子", "家": "府第", "学校": "学堂", "医院": "医馆",
            "商店": "铺子", "餐厅": "酒楼", "公园": "园子", "街道": "街市",
            "楼": "楼房", "院子": "院落", "花园": "园子", "书房": "书斋",
            
            # 人物称谓
            "爸爸": "父亲", "妈妈": "母亲", "爷爷": "祖父", "奶奶": "祖母",
            "哥哥": "兄长", "姐姐": "姐姐", "弟弟": "弟弟", "妹妹": "妹妹",
            "叔叔": "叔父", "阿姨": "姨母", "舅舅": "舅父", "姑姑": "姑母",
            "老师": "先生", "同学": "同窗", "朋友": "友人", "客人": "客人",
            
            # 日用物品
            "衣服": "衣裳", "鞋子": "鞋履", "帽子": "帽子", "包": "包袱",
            "书": "书本", "笔": "笔墨", "纸": "纸张", "桌子": "桌案",
            "椅子": "椅子", "床": "床榻", "被子": "被褥", "枕头": "枕头",
            "杯子": "茶杯", "碗": "碗盏", "筷子": "筷子", "勺子": "汤勺",
            
            # 天气自然
            "天气": "天色", "晴天": "晴日", "阴天": "阴日", "雨天": "雨日",
            "风": "风儿", "雨": "雨水", "雪": "雪花", "云": "云彩",
            "太阳": "日头", "月亮": "月儿", "星星": "星辰", "天空": "天空",
            "山": "山峦", "水": "水流", "树": "树木", "花": "花朵",
            
            # 抽象概念
            "事情": "事", "问题": "问题", "办法": "法子", "道理": "道理",
            "原因": "缘故", "结果": "结果", "目的": "目的", "希望": "盼望",
            "梦想": "心愿", "理想": "志向", "计划": "打算", "决心": "决意",
            "信心": "信心", "勇气": "胆气", "力量": "力气", "能力": "本事",
            
            # 连接词语
            "因为": "因为", "所以": "所以", "但是": "但是", "不过": "不过",
            "然而": "然而", "而且": "而且", "并且": "并且", "或者": "或者",
            "如果": "若是", "假如": "假如", "除非": "除非", "只要": "只要",
            "虽然": "虽然", "尽管": "尽管", "无论": "无论", "不管": "不管",
            
            # 语气词和叹词
            "的": "的", "了": "了", "着": "着", "呢": "呢",
            "吧": "吧", "啊": "啊", "呀": "呀", "哦": "哦",
            "哎": "哎", "唉": "唉", "哇": "哇", "咦": "咦",
        }
        
        # 大幅扩展称谓映射规则
        self.addressing_mapping = {
            # 基本人称
            "他": "他", "她": "她", "你": "你", "我": "我",
            "我们": "咱们", "你们": "你们", "他们": "他们",
            
            # 敬称谦称
            "您": "您", "在下": "在下", "小的": "小的", "奴婢": "奴婢",
            "老爷": "老爷", "太太": "太太", "夫人": "夫人", "奶奶": "奶奶",
            "小姐": "姑娘", "公子": "公子", "少爷": "少爷", "大人": "大人",
            
            # 亲属称谓
            "父亲": "父亲", "母亲": "母亲", "儿子": "儿子", "女儿": "女儿",
            "兄长": "兄长", "弟弟": "弟弟", "姐姐": "姐姐", "妹妹": "妹妹",
            "夫君": "夫君", "娘子": "娘子", "相公": "相公", "媳妇": "媳妇",
        }
        
        # 大幅扩展句式模式
        self.sentence_patterns = {
            "只见": [
                "只见{subject}{action}", "只见{subject}正{action}",
                "只见{subject}在{place}{action}", "只见{description}",
                "只见{subject}{attribute}，{action}"
            ],
            "却说": [
                "却说{subject}{action}", "却说{subject}在{place}{action}",
                "却说{time}，{subject}{action}", "却说{subject}因{reason}而{action}",
                "却说{subject}心中{emotion}，{action}"
            ],
            "但见": [
                "但见{description}", "但见{subject}{description}",
                "但见{place}{description}", "但见{attribute}之{subject}",
                "但见{subject}面带{expression}，{action}"
            ],
            "原来": [
                "原来{explanation}", "原来{subject}{reason}",
                "原来如此", "原来{subject}因{reason}", 
                "原来{subject}早已{action}"
            ],
            "岂知": [
                "岂知{unexpected}", "岂知{subject}{unexpected_action}",
                "岂知此{item}{characteristic}", "岂知{situation}"
            ],
            "不料": [
                "不料{unexpected_event}", "不料{subject}{unexpected_action}",
                "不料{subject}竟{action}", "不料事情{change}"
            ],
            "谁知": [
                "谁知{unexpected}", "谁知{subject}{surprising_action}",
                "谁知此{item}{surprise}", "谁知{outcome}"
            ],
        }
        
        # 大幅扩展修辞模式
        self.rhetorical_patterns = {
            "比喻": [
                "{subject}如{object}般{attribute}", "{subject}似{object}样{attribute}",
                "{subject}宛如{object}", "{subject}恰似{object}",
                "{subject}有如{object}一般", "{action}如{comparison}",
                "{description}似{metaphor}一般", "{subject}好比{object}",
            ],
            "对偶": [
                "{phrase1}，{phrase2}", "{action1}对{action2}",
                "{noun1}配{noun2}", "{adj1}而{adj2}",
                "{subject1}{action1}，{subject2}{action2}",
                "{place1}有{item1}，{place2}有{item2}",
            ],
            "排比": [
                "{phrase1}，{phrase2}，{phrase3}", 
                "{action1}，{action2}，{action3}",
                "或{choice1}，或{choice2}，或{choice3}",
                "既{aspect1}，又{aspect2}，还{aspect3}",
            ],
            "反复": [
                "{phrase}了又{phrase}", "{word}又{word}",
                "一{action}再{action}", "{emotion}再{emotion}",
            ],
            "设问": [
                "何为{concept}？", "岂不{statement}？",
                "如何{action}？", "为何{situation}？",
                "难道{doubt}？", "莫非{guess}？",
            ],
            "反问": [
                "岂不{obvious}？", "难道不{clear}？",
                "怎能{impossible}？", "何必{unnecessary}？",
                "哪里{contradiction}？", "焉有{absurd}？",
            ],
            "夸张": [
                "{subject}{extreme_action}", "千{unit}万{unit}",
                "{emotion}如{extreme_comparison}", "一{small_unit}不{negative}",
            ],
            "拟人": [
                "{nature}{human_action}", "{object}也{emotion}",
                "{natural_thing}似{human_behavior}", "{item}在{human_activity}",
            ],
        }
        
        # 扩展助词添加规则
        self.auxiliary_words = {
            "语气助词": ["之", "也", "者", "矣", "乎", "焉", "哉", "耳", "而已"],
            "句中助词": ["所", "其", "以", "于", "与", "为", "则"],
            "连接助词": ["而", "且", "然", "故", "是以", "于是"],
            "时间助词": ["时", "际", "间", "中", "内", "里"],
        }
        
        # 增加情境词汇库
        self.context_vocabularies = {
            "formal": {  # 正式场合
                "preferred": ["恭敬", "谨慎", "庄重", "严肃", "规矩"],
                "avoided": ["随便", "玩笑", "戏谑", "轻浮", "草率"],
                "addressing": ["您", "阁下", "先生", "夫人", "大人"],
            },
            "intimate": {  # 亲密场合
                "preferred": ["亲近", "温柔", "体贴", "关怀", "心疼"],
                "avoided": ["生分", "冷淡", "客套", "疏远", "陌生"],
                "addressing": ["哥哥", "妹妹", "心肝", "宝贝", "亲的"],
            },
            "literary": {  # 文学场合
                "preferred": ["雅致", "文雅", "诗意", "意境", "韵味"],
                "avoided": ["粗俗", "直白", "简陋", "肤浅", "庸俗"],
                "patterns": ["诗词典故", "对偶工整", "意象丰富"],
            },
            "emotional": {  # 情感场合
                "joy": ["欢喜", "喜悦", "高兴", "快活", "愉快"],
                "sorrow": ["悲伤", "哀愁", "忧郁", "凄凉", "黯然"],
                "anger": ["愤怒", "恼怒", "气恼", "愤慨", "怒火"],
                "fear": ["恐惧", "害怕", "惊恐", "胆怯", "畏惧"],
            }
        }
        
        # 增加语言风格库
        self.style_patterns = {
            "classical_openings": [
                "却说", "只见", "但见", "原来", "岂知", "不料", "谁知",
                "忽听", "忽见", "忽然", "忽地", "陡然", "突然", "猛然",
                "当下", "此时", "这时", "那时", "彼时", "适逢", "正值",
            ],
            "classical_transitions": [
                "于是", "因此", "故而", "是以", "然后", "接着", "随即",
                "便", "就", "乃", "遂", "即", "旋即", "顷刻",
                "少顷", "须臾", "片刻", "转眼", "霎时", "顿时",
            ],
            "classical_endings": [
                "而已", "矣", "也", "哉", "乎", "耳", "焉",
                "是也", "然也", "诚然", "固然", "自然", "当然",
            ],
            "descriptive_patterns": [
                "风姿{adj}", "神态{adj}", "举止{adj}", "言语{adj}",
                "容貌{adj}", "身材{adj}", "气质{adj}", "风度{adj}",
                "{color}装", "{material}衣", "{style}髻", "{ornament}钗",
            ],
        }
    
    def convert_text(self, 
                    text: str, 
                    config: Optional[ConversionConfig] = None) -> ConversionResult:
        """转换文本风格"""
        
        if config is None:
            config = ConversionConfig()
            
        self.logger.info(f"开始转换文本，长度: {len(text)}")
        
        # 记录转换操作
        operations = []
        vocabulary_changes = {}
        sentence_adjustments = []
        rhetorical_enhancements = []
        
        # 分句处理
        sentences = self._split_sentences(text)
        converted_sentences = []
        
        for sentence in sentences:
            if not sentence.strip():
                converted_sentences.append(sentence)
                continue
                
            # 1. 词汇层面转换
            sentence_after_vocab = self._convert_vocabulary(sentence, config)
            vocab_changes = self._get_vocabulary_changes(sentence, sentence_after_vocab)
            vocabulary_changes.update(vocab_changes)
            
            # 2. 句式层面重构
            sentence_after_structure = sentence_after_vocab
            if config.sentence_restructure:
                sentence_after_structure = self._restructure_sentence(sentence_after_vocab, config)
                if sentence_after_structure != sentence_after_vocab:
                    sentence_adjustments.append(f"句式调整: {sentence_after_vocab} → {sentence_after_structure}")
            
            # 3. 修辞层面增强
            sentence_after_rhetoric = sentence_after_structure
            if config.add_rhetorical_devices:
                sentence_after_rhetoric = self._enhance_rhetoric(sentence_after_structure, config)
                if sentence_after_rhetoric != sentence_after_structure:
                    rhetorical_enhancements.append(f"修辞增强: {sentence_after_structure} → {sentence_after_rhetoric}")
            
            # 4. 语境层面优化
            final_sentence = self._optimize_context(sentence_after_rhetoric, config)
            
            converted_sentences.append(final_sentence)
            operations.append(f"句子转换: {sentence.strip()} → {final_sentence.strip()}")
        
        # 组合结果
        converted_text = "".join(converted_sentences)
        
        # 计算质量评分
        quality_score = self._calculate_quality_score(text, converted_text)
        confidence_score = self._calculate_confidence_score(len(vocabulary_changes), len(operations))
        
        # 创建转换结果
        result = ConversionResult(
            original_text=text,
            converted_text=converted_text,
            conversion_operations=operations,
            vocabulary_changes=vocabulary_changes,
            sentence_adjustments=sentence_adjustments,
            rhetorical_enhancements=rhetorical_enhancements,
            quality_score=quality_score,
            confidence_score=confidence_score
        )
        
        # 添加到历史记录
        self.conversion_history.append(result)
        
        self.logger.info(f"转换完成，质量评分: {quality_score:.2f}, 置信度: {confidence_score:.2f}")
        
        return result
    
    def _split_sentences(self, text: str) -> List[str]:
        """分句"""
        # 按标点符号分句，保留标点
        pattern = r'([。！？；…]+|[\n\r]+)'
        parts = re.split(pattern, text)
        
        sentences = []
        current_sentence = ""
        
        for i, part in enumerate(parts):
            if re.match(r'[。！？；…\n\r]+', part):
                current_sentence += part
                sentences.append(current_sentence)
                current_sentence = ""
            else:
                current_sentence += part
        
        if current_sentence:
            sentences.append(current_sentence)
            
        return sentences
    
    def _convert_vocabulary(self, sentence: str, config: ConversionConfig) -> str:
        """词汇层面转换"""
        
        # 分词
        words = list(jieba.cut(sentence))
        converted_words = []
        
        for word in words:
            # 查找映射
            if word in self.vocabulary_mapping:
                converted_word = self.vocabulary_mapping[word]
                converted_words.append(converted_word)
            else:
                # 检查是否为现代化词汇，需要转换
                converted_word = self._find_classical_equivalent(word, config)
                converted_words.append(converted_word)
        
        return "".join(converted_words)
    
    def _find_classical_equivalent(self, word: str, config: ConversionConfig) -> str:
        """寻找古典对等词汇 - 增强版"""
        
        # 基于语境和字典查找
        if len(word) == 1:
            return word  # 单字一般保持不变
        
        # 优先使用主词汇映射表
        if word in self.vocabulary_mapping:
            return self.vocabulary_mapping[word]
        
        # 根据配置强度进行更深度的转换
        if config.vocabulary_level == "high":
            # 情感词汇转换 - 扩展版
            emotion_mapping = {
                "激动": "兴奋", "沮丧": "沮丧", "愤怒": "愤慨", "快乐": "快活", 
                "悲伤": "悲戚", "惊讶": "惊奇", "紧张": "紧张", "焦虑": "焦心",
                "满意": "满意", "失望": "失望", "羞愧": "羞愧", "骄傲": "得意",
                "嫉妒": "嫉恨", "感激": "感激", "怨恨": "怨恨", "同情": "怜悯",
            }
            
            # 动作词汇转换 - 扩展版
            action_mapping = {
                "关心": "关怀", "帮助": "帮衬", "保护": "护佑", "决定": "决意", 
                "选择": "拣选", "考虑": "思忖", "讨论": "商议", "争论": "争辩",
                "学习": "习学", "工作": "做事", "休息": "歇息", "玩耍": "嬉戏",
                "研究": "钻研", "探索": "探寻", "发明": "创制", "改进": "改良",
            }
            
            # 状态词汇转换
            state_mapping = {
                "开始": "起头", "结束": "完了", "继续": "接着", "停止": "停下",
                "增加": "添加", "减少": "减少", "变化": "变更", "维持": "保持",
                "成功": "成功", "失败": "失手", "进步": "长进", "退步": "倒退",
            }
            
            # 查找对应映射
            for mapping in [emotion_mapping, action_mapping, state_mapping]:
                if word in mapping:
                    return mapping[word]
        
        # 语境相关转换
        if config.character_context or config.scene_context:
            contextual_word = self._find_contextual_equivalent(word, config)
            if contextual_word != word:
                return contextual_word
        
        return word  # 默认保持原词
    
    def _find_contextual_equivalent(self, word: str, config: ConversionConfig) -> str:
        """根据语境寻找对等词汇"""
        
        # 根据场景上下文选择词汇
        if config.scene_context:
            scene_type = self._classify_scene_type(config.scene_context)
            
            if scene_type == "formal" and scene_type in self.context_vocabularies:
                # 正式场合避免随意词汇
                avoided_words = self.context_vocabularies[scene_type]["avoided"]
                if word in avoided_words:
                    # 寻找更正式的替代词
                    formal_alternatives = {
                        "随便": "随意", "玩笑": "戏言", "草率": "匆忙",
                        "轻浮": "轻率", "戏谑": "戏言"
                    }
                    return formal_alternatives.get(word, word)
            
            elif scene_type == "literary" and scene_type in self.context_vocabularies:
                # 文学场合偏好雅致词汇
                literary_alternatives = {
                    "直白": "直率", "简陋": "简朴", "肤浅": "浅显",
                    "庸俗": "俗气", "粗俗": "粗鄙"
                }
                return literary_alternatives.get(word, word)
        
        # 根据人物身份调整
        if config.character_context:
            character_alternatives = self._get_character_vocabulary(config.character_context, word)
            if character_alternatives:
                return character_alternatives
        
        return word
    
    def _classify_scene_type(self, scene_context: str) -> str:
        """分类场景类型"""
        scene_context_lower = scene_context.lower()
        
        if any(keyword in scene_context_lower for keyword in ["正式", "公务", "官场", "朝廷"]):
            return "formal"
        elif any(keyword in scene_context_lower for keyword in ["私人", "亲密", "家庭", "闺房"]):
            return "intimate"
        elif any(keyword in scene_context_lower for keyword in ["诗词", "文学", "雅集", "文会"]):
            return "literary"
        else:
            return "general"
    
    def _get_character_vocabulary(self, character: str, word: str) -> Optional[str]:
        """获取特定人物的词汇偏好"""
        
        # 人物特定词汇映射
        character_vocabularies = {
            "贾宝玉": {
                "你": "你", "美丽": "娇美", "聪明": "伶俐",
                "妹妹": "妹妹", "姐姐": "姐姐"
            },
            "林黛玉": {
                "哥哥": "宝哥哥", "你": "你", "伤心": "伤感",
                "担心": "担忧", "想": "思量"
            },
            "王熙凤": {
                "你们": "你们", "我说": "我说", "办事": "办事",
                "聪明": "精明", "能干": "能干"
            },
            "贾母": {
                "孩子": "好孩子", "你": "你", "喜欢": "疼爱",
                "生气": "不高兴", "担心": "挂念"
            }
        }
        
        if character in character_vocabularies:
            char_vocab = character_vocabularies[character]
            return char_vocab.get(word)
        
        return None

    def _restructure_sentence(self, sentence: str, config: ConversionConfig) -> str:
        """句式层面重构"""
        
        # 基本的句式调整
        restructured = sentence
        
        # 1. 添加古典开头词
        if self._should_add_classical_start(sentence):
            restructured = self._add_classical_start(restructured)
        
        # 2. 调整语序
        restructured = self._adjust_word_order(restructured)
        
        # 3. 添加助词
        restructured = self._add_auxiliary_words(restructured, config)
        
        return restructured
    
    def _should_add_classical_start(self, sentence: str) -> bool:
        """判断是否应该添加古典开头"""
        # 如果句子较长且没有古典开头词，则添加
        classical_starts = ["只见", "却说", "但见", "原来", "忽然", "忽见"]
        
        for start in classical_starts:
            if sentence.startswith(start):
                return False
        
        # 判断句子类型
        if len(sentence) > 10 and not sentence.startswith(("他", "她", "我", "你")):
            return True
            
        return False
    
    def _add_classical_start(self, sentence: str) -> str:
        """添加古典开头词"""
        
        # 根据句子内容选择合适的开头
        if "看" in sentence or "瞧" in sentence:
            return "只见" + sentence
        elif "说" in sentence or "道" in sentence:
            return "却说" + sentence
        elif "是" in sentence or "有" in sentence:
            return "原来" + sentence
        else:
            return "但见" + sentence
    
    def _adjust_word_order(self, sentence: str) -> str:
        """调整语序"""
        
        # 简单的语序调整规则
        adjusted = sentence
        
        # 处理 "很+形容词" 结构
        pattern = r'很(\w+)'
        adjusted = re.sub(pattern, r'甚是\1', adjusted)
        
        # 处理 "非常+形容词" 结构  
        pattern = r'非常(\w+)'
        adjusted = re.sub(pattern, r'极是\1', adjusted)
        
        return adjusted
    
    def _add_auxiliary_words(self, sentence: str, config: ConversionConfig) -> str:
        """添加助词 - 增强版"""
        
        if config.vocabulary_level != "high":
            return sentence
        
        # 在适当位置添加助词
        enhanced = sentence
        
        # 根据句子类型和语境选择助词
        sentence_type = self._classify_sentence_type(sentence)
        context_type = self._get_context_type(config)
        
        # 在句末添加语气词（概率性和语境相关）
        if sentence_type == "declarative" and context_type == "formal":
            # 正式陈述句可能添加"也"、"矣"
            if not re.search(r'[。！？]$', enhanced):
                return enhanced
            if "。" in enhanced:
                enhanced = enhanced.replace("。", "也。")
        
        elif sentence_type == "interrogative":
            # 疑问句处理
            if "？" in enhanced:
                if context_type == "formal":
                    enhanced = enhanced.replace("？", "乎？")
                elif context_type == "intimate":
                    enhanced = enhanced.replace("？", "么？")
        
        elif sentence_type == "exclamatory":
            # 感叹句处理
            if "！" in enhanced:
                if context_type == "literary":
                    enhanced = enhanced.replace("！", "哉！")
                elif context_type == "emotional":
                    enhanced = enhanced.replace("！", "啊！")
        
        # 在句中添加结构助词
        enhanced = self._add_structural_auxiliaries(enhanced, config)
        
        return enhanced
    
    def _classify_sentence_type(self, sentence: str) -> str:
        """分类句子类型"""
        if "？" in sentence or "吗" in sentence or "呢" in sentence:
            return "interrogative"
        elif "！" in sentence or "啊" in sentence or "哎" in sentence:
            return "exclamatory"
        else:
            return "declarative"
    
    def _get_context_type(self, config: ConversionConfig) -> str:
        """获取语境类型"""
        if config.scene_context:
            return self._classify_scene_type(config.scene_context)
        return "general"
    
    def _add_structural_auxiliaries(self, sentence: str, config: ConversionConfig) -> str:
        """添加结构助词"""
        
        enhanced = sentence
        
        # 适当位置添加"之"、"其"、"所"等
        structural_patterns = [
            (r'(\w+)的(\w+)', r'\1之\2'),  # "他的书" -> "他之书"
            (r'被(\w+)', r'为\1所'),       # "被打" -> "为某所打"
            (r'让(\w+)', r'使\1'),         # "让他" -> "使他"
        ]
        
        for pattern, replacement in structural_patterns:
            if config.vocabulary_level == "high":
                enhanced = re.sub(pattern, replacement, enhanced)
        
        return enhanced

    def _enhance_rhetoric(self, sentence: str, config: ConversionConfig) -> str:
        """修辞层面增强 - 大幅改进版"""
        
        enhanced = sentence
        
        # 1. 智能比喻增强
        enhanced = self._add_intelligent_metaphor(enhanced, config)
        
        # 2. 对偶结构识别和增强
        enhanced = self._add_intelligent_parallelism(enhanced, config)
        
        # 3. 排比结构增强
        enhanced = self._add_ranking_structure(enhanced, config)
        
        # 4. 设问反问增强
        enhanced = self._add_rhetorical_questions(enhanced, config)
        
        # 5. 古典修辞手法
        enhanced = self._add_classical_rhetoric(enhanced, config)
        
        return enhanced
    
    def _add_intelligent_metaphor(self, sentence: str, config: ConversionConfig) -> str:
        """智能比喻增强"""
        
        # 扩展的比喻模式
        metaphor_patterns = {
            # 美貌比喻
            r'(\w+)很美': r'\1如花似玉',
            r'(\w+)美丽': r'\1美如天仙',
            r'(\w+)漂亮': r'\1标致如画',
            
            # 才能比喻
            r'(\w+)很聪明': r'\1伶俐如冰雪',
            r'(\w+)聪明': r'\1智如泉涌',
            r'(\w+)能干': r'\1能干如男儿',
            
            # 情感比喻
            r'(\w+)很着急': r'\1心如火焚',
            r'(\w+)很伤心': r'\1心如刀绞',
            r'(\w+)很高兴': r'\1喜如花开',
            r'(\w+)很生气': r'\1怒如雷霆',
            
            # 状态比喻
            r'(\w+)很累': r'\1累如散架',
            r'(\w+)很忙': r'\1忙如陀螺',
            r'(\w+)很安静': r'\1静如处子',
            
            # 自然比喻
            r'风很大': r'风如怒吼',
            r'雨很大': r'雨如倾盆',
            r'天很黑': r'天黑如墨',
        }
        
        enhanced = sentence
        context_type = self._get_context_type(config)
        
        # 根据语境选择比喻强度
        if config.add_rhetorical_devices and context_type in ["literary", "emotional"]:
            for pattern, replacement in metaphor_patterns.items():
                enhanced = re.sub(pattern, replacement, enhanced)
        
        return enhanced
    
    def _add_intelligent_parallelism(self, sentence: str, config: ConversionConfig) -> str:
        """智能对偶增强"""
        
        enhanced = sentence
        
        # 对偶结构识别和增强
        parallelism_patterns = [
            # 并列结构
            (r'(\w+)和(\w+)', r'\1对\2'),
            (r'既(\w+)又(\w+)', r'既\1又\2'),
            (r'不仅(\w+)而且(\w+)', r'不但\1且\2'),
            
            # 对比结构
            (r'(\w+)不如(\w+)', r'\1不及\2'),
            (r'比(\w+)更(\w+)', r'较\1更\2'),
            
            # 递进结构
            (r'先(\w+)后(\w+)', r'先\1后\2'),
            (r'一(\w+)再(\w+)', r'一\1再\2'),
        ]
        
        if config.add_rhetorical_devices:
            for pattern, replacement in parallelism_patterns:
                enhanced = re.sub(pattern, replacement, enhanced)
        
        return enhanced
    
    def _add_ranking_structure(self, sentence: str, config: ConversionConfig) -> str:
        """添加排比结构"""
        
        enhanced = sentence
        
        # 识别可以形成排比的结构
        ranking_patterns = [
            # 三个并列项
            (r'(\w+)、(\w+)、(\w+)', r'\1，\2，\3'),
            (r'(\w+)，(\w+)，(\w+)', r'或\1，或\2，或\3'),
            
            # 动作排比
            (r'(\w+)了(\w+)，(\w+)了(\w+)', r'\1了\2，\3了\4'),
        ]
        
        if config.add_rhetorical_devices:
            for pattern, replacement in ranking_patterns:
                enhanced = re.sub(pattern, replacement, enhanced)
        
        return enhanced
    
    def _add_rhetorical_questions(self, sentence: str, config: ConversionConfig) -> str:
        """添加设问反问"""
        
        enhanced = sentence
        
        # 将某些陈述句转换为反问句（增强语气）
        rhetorical_patterns = [
            (r'这很明显', r'岂不明显？'),
            (r'这不可能', r'岂能如此？'),
            (r'没有道理', r'哪有此理？'),
            (r'不应该这样', r'焉有此理？'),
        ]
        
        context_type = self._get_context_type(config)
        if config.add_rhetorical_devices and context_type in ["formal", "literary"]:
            for pattern, replacement in rhetorical_patterns:
                enhanced = re.sub(pattern, replacement, enhanced)
        
        return enhanced
    
    def _add_classical_rhetoric(self, sentence: str, config: ConversionConfig) -> str:
        """添加古典修辞手法"""
        
        enhanced = sentence
        
        # 古典修辞模式
        classical_patterns = [
            # 倒装句式
            (r'我很(\w+)', r'\1甚矣'),
            (r'(\w+)很重要', r'重要者\1也'),
            
            # 省略句式
            (r'如果(\w+)的话', r'若\1'),
            (r'虽然(\w+)但是(\w+)', r'虽\1，然\2'),
            
            # 文言虚词
            (r'因为(\w+)', r'因\1故'),
            (r'所以(\w+)', r'故\1'),
        ]
        
        if config.vocabulary_level == "high" and config.add_rhetorical_devices:
            for pattern, replacement in classical_patterns:
                enhanced = re.sub(pattern, replacement, enhanced)
        
        return enhanced

    def _adjust_for_character(self, sentence: str, character: str) -> str:
        """根据人物身份调整语言 - 增强版"""
        
        # 大幅扩展人物语言特点
        character_styles = {
            "贾宝玉": {
                "特点": "温文尔雅，多愁善感",
                "常用词": ["颦儿", "妹妹", "姐姐", "好妹妹", "好姐姐"],
                "语气": "温和委婉",
                "避免": ["粗鄙", "暴躁", "势利"],
                "偏好": ["诗意", "温柔", "体贴"]
            },
            "林黛玉": {
                "特点": "文雅委婉，才华横溢",
                "常用词": ["宝哥哥", "姐妹们", "诗句", "才情"],
                "语气": "细腻敏感",
                "避免": ["粗俗", "直白", "豪爽"],
                "偏好": ["诗词", "典雅", "含蓄"]
            },
            "王熙凤": {
                "特点": "利落直接，机智幽默",
                "常用词": ["你们", "咱们", "我说", "这话"],
                "语气": "爽朗风趣",
                "避免": ["拖沓", "羞涩", "文绉绉"],
                "偏好": ["直率", "机敏", "实用"]
            },
            "贾母": {
                "特点": "威严慈祥，德高望重",
                "常用词": ["好孩子", "我的心肝", "乖孩子", "老婆子"],
                "语气": "慈爱威严",
                "避免": ["轻浮", "失态", "小气"],
                "偏好": ["慈爱", "威严", "智慧"]
            },
            "薛宝钗": {
                "特点": "端庄大方，深明大义",
                "常用词": ["姐妹", "份内", "规矩", "道理"],
                "语气": "稳重得体",
                "避免": ["轻率", "任性", "刻薄"],
                "偏好": ["稳重", "大度", "理智"]
            }
        }
        
        if character in character_styles:
            style = character_styles[character]
            
            # 词汇调整
            for preferred_word in style["常用词"]:
                if preferred_word in sentence:
                    continue  # 已经使用了合适的词汇
            
            # 语气调整
            sentence = self._adjust_tone_for_character(sentence, style)
            
            # 避免不合适的词汇
            sentence = self._remove_inappropriate_words(sentence, style["避免"])
        
        return sentence
    
    def _adjust_tone_for_character(self, sentence: str, style: Dict) -> str:
        """为特定人物调整语气"""
        
        tone = style.get("语气", "")
        
        if tone == "温和委婉":
            # 宝玉式语气：温和委婉
            sentence = re.sub(r'你(\w+)', r'你\1罢', sentence)
            sentence = re.sub(r'不要', r'不必', sentence)
            
        elif tone == "细腻敏感":
            # 黛玉式语气：细腻敏感
            sentence = re.sub(r'很(\w+)', r'极是\1', sentence)
            sentence = re.sub(r'真的', r'当真', sentence)
            
        elif tone == "爽朗风趣":
            # 凤姐式语气：爽朗直接
            sentence = re.sub(r'我觉得', r'我说', sentence)
            sentence = re.sub(r'应该', r'该', sentence)
            
        elif tone == "慈爱威严":
            # 贾母式语气：慈爱威严
            sentence = re.sub(r'你们', r'你们这些孩子', sentence)
            sentence = re.sub(r'好的', r'好了', sentence)
            
        elif tone == "稳重得体":
            # 宝钗式语气：稳重大方
            sentence = re.sub(r'我想', r'我以为', sentence)
            sentence = re.sub(r'可能', r'或者', sentence)
        
        return sentence
    
    def _remove_inappropriate_words(self, sentence: str, avoided_words: List[str]) -> str:
        """移除不合适的词汇"""
        
        # 为避免的词汇寻找替代
        word_alternatives = {
            "粗鄙": "不雅", "暴躁": "急躁", "势利": "现实",
            "粗俗": "不雅", "直白": "直率", "豪爽": "爽快",
            "拖沓": "啰嗦", "羞涩": "害羞", "文绉绉": "文雅",
            "轻浮": "轻率", "失态": "失礼", "小气": "小心",
            "轻率": "草率", "任性": "固执", "刻薄": "严格",
        }
        
        for avoided in avoided_words:
            if avoided in sentence and avoided in word_alternatives:
                sentence = sentence.replace(avoided, word_alternatives[avoided])
        
        return sentence

    def _adjust_for_scene(self, sentence: str, scene: str) -> str:
        """根据场景调整语言 - 增强版"""
        
        # 大幅扩展场景风格
        scene_styles = {
            "正式场合": {
                "特点": "庄重严肃，用词规范",
                "避免": ["俗语", "玩笑", "随便", "轻佻"],
                "偏好": ["敬语", "谦词", "雅言", "规范"],
                "句式": ["完整", "工整", "正式"],
                "称谓": ["尊称", "官称", "敬称"]
            },
            "私人对话": {
                "特点": "亲密自然，用词随意",
                "允许": ["昵称", "俗语", "玩笑", "情话"],
                "偏好": ["亲昵", "自然", "随意", "真情"],
                "句式": ["简洁", "自然", "口语化"],
                "称谓": ["昵称", "爱称", "小名"]
            },
            "诗词场合": {
                "特点": "文雅高深，意境悠远",
                "偏好": ["典故", "对偶", "意象", "韵律"],
                "避免": ["白话", "俗语", "直白", "粗俗"],
                "句式": ["对仗", "押韵", "意境"],
                "风格": ["古典", "雅致", "含蓄"]
            },
            "争论场合": {
                "特点": "激烈辩驳，逻辑严密",
                "偏好": ["反问", "强调", "对比", "举证"],
                "句式": ["反问", "设问", "排比", "对比"],
                "语气": ["坚定", "激烈", "有力"]
            },
            "温情场合": {
                "特点": "温柔体贴，情意绵绵",
                "偏好": ["温柔", "体贴", "关怀", "爱护"],
                "避免": ["冷漠", "严厉", "粗暴", "冷淡"],
                "句式": ["温和", "委婉", "关切"],
                "语气": ["温柔", "体贴", "关爱"]
            }
        }
        
        # 场景匹配
        matched_scene = None
        for scene_type, style_info in scene_styles.items():
            if scene_type in scene or any(keyword in scene for keyword in [scene_type[:2]]):
                matched_scene = style_info
                break
        
        if matched_scene:
            # 根据场景调整用词
            sentence = self._apply_scene_vocabulary(sentence, matched_scene)
            
            # 根据场景调整句式
            sentence = self._apply_scene_syntax(sentence, matched_scene)
        
        return sentence
    
    def _apply_scene_vocabulary(self, sentence: str, scene_style: Dict) -> str:
        """应用场景词汇"""
        
        # 替换不适合的词汇
        if "避免" in scene_style:
            for avoided in scene_style["避免"]:
                if avoided in sentence:
                    # 寻找场景适合的替代词
                    if "偏好" in scene_style and scene_style["偏好"]:
                        # 简单替换（实际应该更智能）
                        replacement_map = {
                            "俗语": "雅言", "玩笑": "戏言", "随便": "随意",
                            "白话": "雅言", "粗俗": "不雅", "直白": "直率",
                        }
                        if avoided in replacement_map:
                            sentence = sentence.replace(avoided, replacement_map[avoided])
        
        return sentence
    
    def _apply_scene_syntax(self, sentence: str, scene_style: Dict) -> str:
        """应用场景句式"""
        
        sentence_patterns = scene_style.get("句式", [])
        
        for pattern in sentence_patterns:
            if pattern == "反问":
                # 将部分陈述句改为反问句
                sentence = re.sub(r'这是对的', r'岂不对？', sentence)
                sentence = re.sub(r'这不对', r'岂能如此？', sentence)
            
            elif pattern == "对仗":
                # 寻找可以对仗的结构
                sentence = re.sub(r'(\w+)和(\w+)', r'\1对\2', sentence)
            
            elif pattern == "委婉":
                # 使句子更委婉
                sentence = re.sub(r'你必须', r'你不妨', sentence)
                sentence = re.sub(r'不行', r'不妥', sentence)
        
        return sentence
    
    def _get_vocabulary_changes(self, original: str, converted: str) -> Dict[str, str]:
        """获取词汇变化记录"""
        
        changes = {}
        
        # 简单的词汇对比（实际应该更复杂）
        orig_words = set(jieba.cut(original))
        conv_words = set(jieba.cut(converted))
        
        # 这里简化处理，实际需要更精确的对应关系
        for orig_word in orig_words:
            if orig_word in self.vocabulary_mapping:
                mapped_word = self.vocabulary_mapping[orig_word]
                if mapped_word in conv_words:
                    changes[orig_word] = mapped_word
        
        return changes
    
    def _calculate_quality_score(self, original: str, converted: str) -> float:
        """计算转换质量评分"""
        
        # 基于多个维度计算质量评分
        
        # 1. 长度变化合理性 (权重: 0.2)
        length_ratio = len(converted) / len(original) if len(original) > 0 else 1.0
        length_score = 1.0 - abs(length_ratio - 1.0) * 0.5  # 理想比例1.0-1.3
        length_score = max(0.0, min(1.0, length_score))
        
        # 2. 古典词汇比例 (权重: 0.3)
        classical_score = self._calculate_classical_ratio(converted)
        
        # 3. 句式复杂度 (权重: 0.2)
        complexity_score = self._calculate_complexity_score(converted)
        
        # 4. 语义保持度 (权重: 0.3)
        semantic_score = self._calculate_semantic_preservation(original, converted)
        
        # 加权平均
        total_score = (length_score * 0.2 + 
                      classical_score * 0.3 + 
                      complexity_score * 0.2 + 
                      semantic_score * 0.3)
        
        return round(total_score, 3)
    
    def _calculate_classical_ratio(self, text: str) -> float:
        """计算古典词汇比例"""
        
        words = list(jieba.cut(text))
        if not words:
            return 0.0
        
        classical_count = 0
        for word in words:
            if len(word) > 1 and self._is_classical_word(word):
                classical_count += 1
        
        return classical_count / len(words)
    
    def _is_classical_word(self, word: str) -> bool:
        """判断是否为古典词汇"""
        
        # 检查是否在古典词汇库中
        classical_indicators = [
            "只见", "却说", "但见", "原来", 
            "甚是", "极是", "颦儿", "怡红院",
            "瞧见", "思量", "伶俐", "标致"
        ]
        
        return word in classical_indicators or word in self.vocabulary_mapping.values()
    
    def _calculate_complexity_score(self, text: str) -> float:
        """计算句式复杂度评分"""
        
        # 基于句长分布和结构复杂度
        sentences = self._split_sentences(text)
        if not sentences:
            return 0.0
        
        total_score = 0.0
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 句长评分（10-30字为最佳）
            length = len(sentence)
            if 10 <= length <= 30:
                length_score = 1.0
            elif length < 10:
                length_score = length / 10.0
            else:
                length_score = 30.0 / length
            
            # 结构复杂度（基于标点和连词）
            complexity_indicators = sentence.count('，') + sentence.count('；') + sentence.count('：')
            complexity_score = min(1.0, complexity_indicators / 3.0)
            
            sentence_score = (length_score + complexity_score) / 2.0
            total_score += sentence_score
        
        return total_score / len(sentences)
    
    def _calculate_semantic_preservation(self, original: str, converted: str) -> float:
        """计算语义保持度"""
        
        # 简化实现：基于关键词保持
        orig_words = set(jieba.cut(original))
        conv_words = set(jieba.cut(converted))
        
        # 移除标点和停用词
        stop_words = {'的', '了', '在', '是', '有', '和', '与', '或', '但', '而'}
        orig_words = {w for w in orig_words if w not in stop_words and len(w) > 1}
        conv_words = {w for w in conv_words if w not in stop_words and len(w) > 1}
        
        if not orig_words:
            return 1.0
        
        # 计算保持的关键概念比例
        preserved_concepts = 0
        for orig_word in orig_words:
            # 直接保持
            if orig_word in conv_words:
                preserved_concepts += 1
            # 通过映射保持
            elif orig_word in self.vocabulary_mapping:
                mapped_word = self.vocabulary_mapping[orig_word]
                if mapped_word in conv_words:
                    preserved_concepts += 1
        
        return preserved_concepts / len(orig_words)
    
    def _calculate_confidence_score(self, vocab_changes: int, total_operations: int) -> float:
        """计算转换置信度"""
        
        # 基于转换操作的数量和复杂度
        if total_operations == 0:
            return 1.0
        
        # 词汇替换的可靠性较高
        vocab_confidence = min(1.0, vocab_changes / (total_operations * 0.7))
        
        # 整体操作的合理性
        operation_confidence = min(1.0, total_operations / 10.0)
        
        return (vocab_confidence + operation_confidence) / 2.0
    
    def batch_convert(self, texts: List[str], config: Optional[ConversionConfig] = None) -> List[ConversionResult]:
        """批量转换文本"""
        
        results = []
        for text in texts:
            result = self.convert_text(text, config)
            results.append(result)
        
        return results
    
    def get_conversion_statistics(self) -> Dict[str, Any]:
        """获取转换统计信息"""
        
        if not self.conversion_history:
            return {}
        
        total_conversions = len(self.conversion_history)
        avg_quality = sum(r.quality_score for r in self.conversion_history) / total_conversions
        avg_confidence = sum(r.confidence_score for r in self.conversion_history) / total_conversions
        
        vocab_changes_count = sum(len(r.vocabulary_changes) for r in self.conversion_history)
        
        return {
            "total_conversions": total_conversions,
            "average_quality_score": round(avg_quality, 3),
            "average_confidence_score": round(avg_confidence, 3),
            "total_vocabulary_changes": vocab_changes_count,
            "average_changes_per_conversion": round(vocab_changes_count / total_conversions, 2)
        }
    
    def save_conversion_history(self, file_path: str):
        """保存转换历史"""
        
        try:
            history_data = [asdict(result) for result in self.conversion_history]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"转换历史已保存到: {file_path}")
            
        except Exception as e:
            self.logger.error(f"保存转换历史失败: {e}")
    
    def generate_conversion_report(self, file_path: str):
        """生成转换报告"""
        
        stats = self.get_conversion_statistics()
        
        report_content = f"""# 智能文风转换器 - 转换报告

## 📊 转换统计

- **总转换次数**: {stats.get('total_conversions', 0)}
- **平均质量评分**: {stats.get('average_quality_score', 0.0):.3f}
- **平均置信度**: {stats.get('average_confidence_score', 0.0):.3f}
- **总词汇替换数**: {stats.get('total_vocabulary_changes', 0)}
- **平均每次替换数**: {stats.get('average_changes_per_conversion', 0.0):.2f}

## 📝 转换示例

"""
        
        # 添加最近几个转换示例
        for i, result in enumerate(self.conversion_history[-3:]):
            report_content += f"""
### 示例 {i+1}

**原文**: {result.original_text[:100]}{'...' if len(result.original_text) > 100 else ''}

**转换后**: {result.converted_text[:100]}{'...' if len(result.converted_text) > 100 else ''}

**质量评分**: {result.quality_score:.3f}
**置信度**: {result.confidence_score:.3f}
**词汇替换**: {len(result.vocabulary_changes)}个

"""
        
        report_content += f"""
## 🔧 转换配置建议

根据当前转换效果，建议的最优配置：
- **词汇转换强度**: {'high' if stats.get('average_quality_score', 0) > 0.8 else 'medium'}
- **句式重构**: 建议启用
- **修辞增强**: 建议启用
- **语义保持**: 建议启用

---
*报告生成时间: {str(self.logger.handlers[0].formatter.formatTime(self.logger.handlers[0], None) if self.logger.handlers else 'Unknown')}*
"""
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.logger.info(f"转换报告已生成: {file_path}")
            
        except Exception as e:
            self.logger.error(f"生成转换报告失败: {e}")

    def _optimize_context(self, sentence: str, config: ConversionConfig) -> str:
        """语境层面优化"""
        
        optimized = sentence
        
        # 根据人物身份调整语言
        if config.character_context:
            optimized = self._adjust_for_character(optimized, config.character_context)
        
        # 根据场景调整语言
        if config.scene_context:
            optimized = self._adjust_for_scene(optimized, config.scene_context)
        
        return optimized


def create_intelligent_converter(analyzer: Optional[ClassicalStyleAnalyzer] = None,
                               template_library: Optional[StyleTemplateLibrary] = None) -> IntelligentStyleConverter:
    """创建智能文风转换器实例"""
    return IntelligentStyleConverter(analyzer, template_library) 