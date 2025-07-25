"""
文体风格库

提供分情景的写作模板，包括对话、叙述、描写、诗词等不同类型的
古典文学风格模板，为智能文风转换器提供参考样式。

功能包括：
- 对话模板：不同身份等级的对话样式
- 叙述模板：人物、环境、心理、动作描写
- 场景模板：欢聚、离别、诗词等不同场合
- 修辞模板：比喻、对偶、排比等修辞手法
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

class DialogueType(Enum):
    """对话类型"""
    MASTER_SERVANT = "主仆对话"
    PEER_EXCHANGE = "同辈交流"
    ELDER_YOUNGER = "长幼对话"
    EMOTIONAL_EXPRESSION = "情感表达"

class NarrativeType(Enum):
    """叙述类型"""
    CHARACTER_DESCRIPTION = "人物描写"
    ENVIRONMENT_DESCRIPTION = "环境描写"
    PSYCHOLOGICAL_DESCRIPTION = "心理描写"
    ACTION_DESCRIPTION = "动作描写"

class SceneType(Enum):
    """场景类型"""
    GATHERING = "欢聚场面"
    FAREWELL = "离别场景"
    POETRY_CREATION = "诗词创作"
    DAILY_LIFE = "日常生活"

class RhetoricalType(Enum):
    """修辞类型"""
    METAPHOR = "比喻句式"
    PARALLELISM = "对偶句式"
    ENUMERATION = "排比句式"
    REPETITION = "反复句式"

@dataclass
class DialogueTemplate:
    """对话模板"""
    type: DialogueType
    context: str                    # 使用场景
    examples: List[str]            # 示例句子
    patterns: List[str]            # 句式模式
    vocabulary: List[str]          # 常用词汇
    tone: str                      # 语气特点

@dataclass
class NarrativeTemplate:
    """叙述模板"""
    type: NarrativeType
    context: str
    examples: List[str]
    patterns: List[str]
    vocabulary: List[str]
    style: str                     # 风格特点

@dataclass
class SceneTemplate:
    """场景模板"""
    type: SceneType
    context: str
    examples: List[str]
    patterns: List[str]
    vocabulary: List[str]
    atmosphere: str                # 氛围特点

@dataclass
class RhetoricalTemplate:
    """修辞模板"""
    type: RhetoricalType
    context: str
    examples: List[str]
    patterns: List[str]
    usage_tips: List[str]         # 使用技巧

class StyleTemplateLibrary:
    """文体风格库"""
    
    def __init__(self, style_data_path: str = "data/processed/style_templates.json"):
        self.style_data_path = Path(style_data_path)
        self.logger = logging.getLogger(__name__)
        
        # 初始化模板库
        self.dialogue_templates: Dict[DialogueType, DialogueTemplate] = {}
        self.narrative_templates: Dict[NarrativeType, NarrativeTemplate] = {}
        self.scene_templates: Dict[SceneType, SceneTemplate] = {}
        self.rhetorical_templates: Dict[RhetoricalType, RhetoricalTemplate] = {}
        
        # 构建默认模板
        self._build_default_templates()
        
        # 尝试加载已有的模板数据
        self._load_templates()

    def _build_default_templates(self):
        """构建默认模板库"""
        # 构建对话模板
        self._build_dialogue_templates()
        
        # 构建叙述模板
        self._build_narrative_templates()
        
        # 构建场景模板
        self._build_scene_templates()
        
        # 构建修辞模板
        self._build_rhetorical_templates()

    def _build_dialogue_templates(self):
        """构建对话模板"""
        # 主仆对话
        self.dialogue_templates[DialogueType.MASTER_SERVANT] = DialogueTemplate(
            type=DialogueType.MASTER_SERVANT,
            context="主人与仆人之间的对话，体现等级关系",
            examples=[
                "奴婢遵命，这就去办。",
                "回老爷，事情已经办妥了。",
                "你且去吧，不必多虑。",
                "劳烦姑娘稍候片刻。"
            ],
            patterns=[
                "奴婢{动作}",
                "回{称谓}，{内容}",
                "{称谓}且{动作}",
                "劳烦{称谓}{内容}"
            ],
            vocabulary=["奴婢", "回", "遵命", "劳烦", "且", "稍候"],
            tone="恭敬谦逊"
        )
        
        # 同辈交流
        self.dialogue_templates[DialogueType.PEER_EXCHANGE] = DialogueTemplate(
            type=DialogueType.PEER_EXCHANGE,
            context="同辈之间的交流，语气平等友好",
            examples=[
                "姐姐说的是，妹妹深以为然。",
                "哥哥过谦了，你我兄弟何必客气。",
                "这话倒也有理，咱们仔细商量商量。",
                "妹妹的才情，我是深知的。"
            ],
            patterns=[
                "{称谓}说的是，{回应}",
                "{称谓}过{形容}了，{内容}",
                "这话{评价}，{建议}",
                "{称谓}的{品质}，{感受}"
            ],
            vocabulary=["说的是", "深以为然", "过谦", "仔细", "才情", "深知"],
            tone="平等友好"
        )
        
        # 长幼对话
        self.dialogue_templates[DialogueType.ELDER_YOUNGER] = DialogueTemplate(
            type=DialogueType.ELDER_YOUNGER,
            context="长辈与晚辈的对话，体现长幼有序",
            examples=[
                "老太太请安，孙儿给您请安了。",
                "好孩子，快些起来，不必多礼。",
                "孙儿记住了，定当遵从老太太的教诲。",
                "你这孩子，总是这般懂事。"
            ],
            patterns=[
                "{称谓}请安，{自称}{行为}",
                "好{称谓}，{指示}",
                "{自称}记住了，{承诺}",
                "你这{称谓}，{评价}"
            ],
            vocabulary=["请安", "孙儿", "好孩子", "不必多礼", "教诲", "懂事"],
            tone="尊敬慈爱"
        )
        
        # 情感表达
        self.dialogue_templates[DialogueType.EMOTIONAL_EXPRESSION] = DialogueTemplate(
            type=DialogueType.EMOTIONAL_EXPRESSION,
            context="表达各种情感的对话方式",
            examples=[
                "我心中五味杂陈，不知如何是好。",
                "此情此景，怎不令人黯然神伤？",
                "能得你这一番话，我心中甚是欣慰。",
                "想起往昔时光，不禁泪如雨下。"
            ],
            patterns=[
                "我心中{感受}，{困惑}",
                "此{场景}，怎不{情感}？",
                "能得{内容}，我{感受}",
                "想起{时间}，不禁{反应}"
            ],
            vocabulary=["五味杂陈", "黯然神伤", "甚是欣慰", "泪如雨下", "不禁"],
            tone="委婉含蓄"
        )

    def _build_narrative_templates(self):
        """构建叙述模板"""
        # 人物描写
        self.narrative_templates[NarrativeType.CHARACTER_DESCRIPTION] = NarrativeTemplate(
            type=NarrativeType.CHARACTER_DESCRIPTION,
            context="描写人物外貌、神态、性格",
            examples=[
                "但见她眉目如画，肌肤胜雪，当真是个绝色佳人。",
                "只见宝玉神色黯然，眉宇间似有千般愁绪。",
                "那女子生得花容月貌，举手投足间尽显大家风范。",
                "他面色凝重，双眸中闪过一丝不易察觉的忧色。"
            ],
            patterns=[
                "但见{她/他}{外貌描述}，当真是{总结}",
                "只见{人物}{神态描述}，{详细描述}",
                "那{称谓}生得{外貌}，{举止描述}",
                "{代词}面色{状态}，{眼神描述}"
            ],
            vocabulary=["但见", "只见", "眉目如画", "肌肤胜雪", "花容月貌", "神色黯然"],
            style="工笔重彩"
        )
        
        # 环境描写
        self.narrative_templates[NarrativeType.ENVIRONMENT_DESCRIPTION] = NarrativeTemplate(
            type=NarrativeType.ENVIRONMENT_DESCRIPTION,
            context="描写自然环境、建筑场所",
            examples=[
                "只见那园中风摆柳丝千万缕，雨打芭蕉一两声。",
                "院内假山兀立，池水潺潺，倒也清雅可人。",
                "时值秋日，满园黄花分外香，红叶满阶砌。",
                "楼阁重重，雕梁画栋，尽显富贵华丽之象。"
            ],
            patterns=[
                "只见那{地点}{景象描述}",
                "{地点}内{景物}，{感受}",
                "时值{时间}，{景象}，{补充描述}",
                "{建筑描述}，尽显{特点}"
            ],
            vocabulary=["风摆柳丝", "雨打芭蕉", "假山兀立", "池水潺潺", "雕梁画栋"],
            style="情景交融"
        )
        
        # 心理描写
        self.narrative_templates[NarrativeType.PSYCHOLOGICAL_DESCRIPTION] = NarrativeTemplate(
            type=NarrativeType.PSYCHOLOGICAL_DESCRIPTION,
            context="描写人物内心活动、思想感受",
            examples=[
                "宝玉心下想着，这番话倒也有些道理。",
                "黛玉心中一阵酸楚，眼中不觉含了泪水。",
                "她暗自思忖，此事定有蹊跷，不可不防。",
                "想到此处，他心中五味杂陈，说不出的滋味。"
            ],
            patterns=[
                "{人物}心下想着，{内容}",
                "{人物}心中{感受}，{生理反应}",
                "{代词}暗自思忖，{分析}",
                "想到{内容}，{代词}心中{感受}"
            ],
            vocabulary=["心下想着", "心中", "暗自思忖", "五味杂陈", "不觉"],
            style="细腻入微"
        )
        
        # 动作描写
        self.narrative_templates[NarrativeType.ACTION_DESCRIPTION] = NarrativeTemplate(
            type=NarrativeType.ACTION_DESCRIPTION,
            context="描写人物的行为动作",
            examples=[
                "却说宝玉正在院中闲步，忽见麝月匆匆走来。",
                "凤姐忙起身相迎，笑道：'是什么风把你吹来了？'",
                "黛玉缓缓放下手中的书卷，凝眸望向窗外。",
                "她款款走到妆台前，对镜梳妆，神态悠然。"
            ],
            patterns=[
                "却说{人物}正在{动作}，忽{转折}",
                "{人物}{动作}，{对话}",
                "{人物}{慢动作}，{后续动作}",
                "{代词}{优雅动作}，神态{状态}"
            ],
            vocabulary=["却说", "正在", "忽见", "忙", "缓缓", "款款", "悠然"],
            style="生动传神"
        )

    def _build_scene_templates(self):
        """构建场景模板"""
        # 欢聚场面
        self.scene_templates[SceneType.GATHERING] = SceneTemplate(
            type=SceneType.GATHERING,
            context="描写聚会、庆祝等热闹场面",
            examples=[
                "满堂珠翠，笑语盈盈，好一派富贵景象。",
                "众人围坐，觥筹交错，谈笑风生，甚是热闹。",
                "丝竹声声，歌舞翩翩，真是人间天堂。",
                "那边厢有人吟诗，这边厢有人作对，雅趣盎然。"
            ],
            patterns=[
                "满堂{装饰}，{氛围描述}，好一派{总体感受}",
                "众人{动作}，{活动描述}，甚是{感受}",
                "{音乐}声声，{舞蹈}翩翩，真是{比喻}",
                "那边厢{活动}，这边厢{活动}，{总体感受}"
            ],
            vocabulary=["满堂珠翠", "笑语盈盈", "觥筹交错", "谈笑风生", "雅趣盎然"],
            atmosphere="热闹欢快"
        )
        
        # 离别场景
        self.scene_templates[SceneType.FAREWELL] = SceneTemplate(
            type=SceneType.FAREWELL,
            context="描写分别、离别的场面",
            examples=[
                "执手相看泪眼，竟无语凝噎。",
                "千言万语汇成一句话：珍重，珍重！",
                "纵有千种风情，更与何人说？",
                "人生若只如初见，何事秋风悲画扇。"
            ],
            patterns=[
                "执手{动作}，竟{状态}",
                "千言万语汇成{内容}",
                "纵有{情感}，更与{疑问}？",
                "人生{感慨}，{对比}"
            ],
            vocabulary=["执手", "相看泪眼", "无语凝噎", "千言万语", "珍重"],
            atmosphere="深情不舍"
        )
        
        # 诗词创作
        self.scene_templates[SceneType.POETRY_CREATION] = SceneTemplate(
            type=SceneType.POETRY_CREATION,
            context="描写吟诗作对的场面",
            examples=[
                "众人各展才华，吟风弄月，好不风雅。",
                "你一句，我一句，对得天衣无缝。",
                "诗兴大发，援笔立就，众人无不叹服。",
                "此诗意境深远，用典恰当，实为佳作。"
            ],
            patterns=[
                "众人{活动}，{评价}",
                "你一{单位}，我一{单位}，{效果}",
                "{状态}，{动作}，众人{反应}",
                "此{作品}{评价}，实为{结论}"
            ],
            vocabulary=["各展才华", "吟风弄月", "天衣无缝", "援笔立就", "意境深远"],
            atmosphere="雅致高深"
        )
        
        # 日常生活
        self.scene_templates[SceneType.DAILY_LIFE] = SceneTemplate(
            type=SceneType.DAILY_LIFE,
            context="描写日常起居、生活琐事",
            examples=[
                "晨起梳洗毕，用过早膳，便到园中走走。",
                "午后时分，正是困倦之时，便小憩片刻。",
                "黄昏时候，夕阳西下，是个散步的好时光。",
                "夜深人静，秉烛夜读，别有一番情趣。"
            ],
            patterns=[
                "{时间}{活动}毕，{后续活动}",
                "{时间}时分，正是{状态}，便{动作}",
                "{时间}时候，{环境描述}，是个{活动}的好时光",
                "{时间}，{活动}，别有{感受}"
            ],
            vocabulary=["晨起", "梳洗", "用膳", "小憩", "黄昏", "夕阳西下", "秉烛夜读"],
            atmosphere="自然恬静"
        )

    def _build_rhetorical_templates(self):
        """构建修辞模板"""
        # 比喻句式
        self.rhetorical_templates[RhetoricalType.METAPHOR] = RhetoricalTemplate(
            type=RhetoricalType.METAPHOR,
            context="使用比喻修辞的句式模板",
            examples=[
                "她的眼神如秋水般清澈。",
                "那声音似银铃一样动听。",
                "心情像乱麻一般纷乱。",
                "时光如流水，一去不复返。"
            ],
            patterns=[
                "{主语}如{喻体}般{特征}",
                "那{主语}似{喻体}一样{特征}",
                "{主语}像{喻体}一般{特征}",
                "{主语}如{喻体}，{后续描述}"
            ],
            usage_tips=["选择恰当的喻体", "注意本体与喻体的相似性", "避免过度使用"]
        )
        
        # 对偶句式
        self.rhetorical_templates[RhetoricalType.PARALLELISM] = RhetoricalTemplate(
            type=RhetoricalType.PARALLELISM,
            context="使用对偶修辞的句式模板",
            examples=[
                "花开花落花满天，情深情浅情如海。",
                "晨风送爽迎新日，暮雨含情别旧年。",
                "山重水复疑无路，柳暗花明又一村。",
                "春花秋月何时了，往事知多少。"
            ],
            patterns=[
                "{A}{动词}{A}满{空间}，{B}{形容}{B}如{比喻}",
                "{时间A}{动作A}迎{目标A}，{时间B}{动作B}别{目标B}",
                "{景物A}{状态A}疑{结果A}，{景物B}{状态B}又{结果B}",
                "{事物A}{疑问A}，{事物B}{疑问B}"
            ],
            usage_tips=["保持字数相等", "词性对仗", "意境相呼应"]
        )
        
        # 排比句式
        self.rhetorical_templates[RhetoricalType.ENUMERATION] = RhetoricalTemplate(
            type=RhetoricalType.ENUMERATION,
            context="使用排比修辞的句式模板",
            examples=[
                "她也哭，他也哭，连丫鬟们也哭。",
                "一处处断垣残壁，一声声鸟雀悲鸣，一阵阵秋风萧瑟。",
                "有人欢喜有人愁，有人得意有人忧，有人团聚有人别。",
                "或吟诗，或作画，或抚琴，各有雅趣。"
            ],
            patterns=[
                "{主语A}也{动词}，{主语B}也{动词}，{主语C}也{动词}",
                "一{量词}处{名词A}，一{量词}声{名词B}，一{量词}阵{名词C}",
                "有人{动词A}有人{动词B}，有人{动词C}有人{动词D}，有人{动词E}有人{动词F}",
                "或{动词A}，或{动词B}，或{动词C}，各有{总结}"
            ],
            usage_tips=["保持句式相同", "递进式排列", "营造气势"]
        )
        
        # 反复句式
        self.rhetorical_templates[RhetoricalType.REPETITION] = RhetoricalTemplate(
            type=RhetoricalType.REPETITION,
            context="使用反复修辞的句式模板",
            examples=[
                "问君能有几多愁，恰似一江春水向东流。",
                "一别又一别，一年又一年。",
                "想了又想，念了又念，总是忘不了。",
                "等啊等，盼啊盼，终于等到了这一天。"
            ],
            patterns=[
                "问{对象}能有几多{情感}，恰似{比喻}",
                "一{动词}又一{动词}，一{时间}又一{时间}",
                "{动词A}了又{动词A}，{动词B}了又{动词B}，总是{结果}",
                "{动词A}啊{动词A}，{动词B}啊{动词B}，终于{结果}"
            ],
            usage_tips=["强调关键词语", "表达强烈情感", "增强节奏感"]
        )

    def _load_templates(self):
        """加载模板数据"""
        try:
            if self.style_data_path.exists():
                with open(self.style_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # TODO: 实现从JSON文件加载模板数据的逻辑
                self.logger.info(f"模板数据已从 {self.style_data_path} 加载")
            else:
                self.logger.info("模板数据文件不存在，使用默认模板")
        except Exception as e:
            self.logger.error(f"加载模板数据失败: {e}")

    def save_templates(self):
        """保存模板数据"""
        try:
            # 确保目录存在
            self.style_data_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 转换为可序列化的字典
            def template_to_dict(template):
                d = asdict(template)
                d['type'] = template.type.value  # 将枚举转换为字符串
                return d
            
            data = {
                "dialogue_templates": {k.value: template_to_dict(v) for k, v in self.dialogue_templates.items()},
                "narrative_templates": {k.value: template_to_dict(v) for k, v in self.narrative_templates.items()},
                "scene_templates": {k.value: template_to_dict(v) for k, v in self.scene_templates.items()},
                "rhetorical_templates": {k.value: template_to_dict(v) for k, v in self.rhetorical_templates.items()},
                "library_version": "1.0.0",
                "created_date": "2025-01-24"
            }
            
            with open(self.style_data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"模板数据已保存到 {self.style_data_path}")
        except Exception as e:
            self.logger.error(f"保存模板数据失败: {e}")

    def get_dialogue_template(self, dialogue_type: DialogueType) -> Optional[DialogueTemplate]:
        """获取对话模板"""
        return self.dialogue_templates.get(dialogue_type)

    def get_narrative_template(self, narrative_type: NarrativeType) -> Optional[NarrativeTemplate]:
        """获取叙述模板"""
        return self.narrative_templates.get(narrative_type)

    def get_scene_template(self, scene_type: SceneType) -> Optional[SceneTemplate]:
        """获取场景模板"""
        return self.scene_templates.get(scene_type)

    def get_rhetorical_template(self, rhetorical_type: RhetoricalType) -> Optional[RhetoricalTemplate]:
        """获取修辞模板"""
        return self.rhetorical_templates.get(rhetorical_type)

    def search_templates_by_keyword(self, keyword: str) -> Dict[str, List[Any]]:
        """根据关键词搜索模板"""
        results = {
            "dialogue": [],
            "narrative": [],
            "scene": [],
            "rhetorical": []
        }
        
        # 搜索对话模板
        for template in self.dialogue_templates.values():
            if keyword in template.context or keyword in ' '.join(template.examples):
                results["dialogue"].append(template)
        
        # 搜索叙述模板
        for template in self.narrative_templates.values():
            if keyword in template.context or keyword in ' '.join(template.examples):
                results["narrative"].append(template)
        
        # 搜索场景模板
        for template in self.scene_templates.values():
            if keyword in template.context or keyword in ' '.join(template.examples):
                results["scene"].append(template)
        
        # 搜索修辞模板
        for template in self.rhetorical_templates.values():
            if keyword in template.context or keyword in ' '.join(template.examples):
                results["rhetorical"].append(template)
        
        return results

    def get_template_suggestions(self, text_type: str, emotion: str = "neutral") -> List[Any]:
        """根据文本类型和情感获取模板建议"""
        suggestions = []
        
        if text_type == "dialogue":
            if emotion in ["sad", "melancholy"]:
                suggestions.append(self.dialogue_templates[DialogueType.EMOTIONAL_EXPRESSION])
            elif emotion in ["respectful", "formal"]:
                suggestions.append(self.dialogue_templates[DialogueType.MASTER_SERVANT])
            else:
                suggestions.append(self.dialogue_templates[DialogueType.PEER_EXCHANGE])
        
        elif text_type == "description":
            suggestions.extend([
                self.narrative_templates[NarrativeType.CHARACTER_DESCRIPTION],
                self.narrative_templates[NarrativeType.ENVIRONMENT_DESCRIPTION]
            ])
        
        elif text_type == "scene":
            if emotion in ["happy", "joyful"]:
                suggestions.append(self.scene_templates[SceneType.GATHERING])
            elif emotion in ["sad", "melancholy"]:
                suggestions.append(self.scene_templates[SceneType.FAREWELL])
            else:
                suggestions.append(self.scene_templates[SceneType.DAILY_LIFE])
        
        return suggestions

    def generate_template_report(self) -> str:
        """生成模板库报告"""
        report = f"""
# 文体风格库报告

## 📋 模板统计
- 对话模板: {len(self.dialogue_templates)} 个
- 叙述模板: {len(self.narrative_templates)} 个  
- 场景模板: {len(self.scene_templates)} 个
- 修辞模板: {len(self.rhetorical_templates)} 个
- 总计: {len(self.dialogue_templates) + len(self.narrative_templates) + len(self.scene_templates) + len(self.rhetorical_templates)} 个模板

## 🎭 对话模板类型
"""
        
        for dialogue_type, template in self.dialogue_templates.items():
            report += f"- **{dialogue_type.value}**: {template.context}\n"
            report += f"  - 语气特点: {template.tone}\n"
            report += f"  - 示例数量: {len(template.examples)} 个\n\n"
        
        report += "\n## 📝 叙述模板类型\n"
        for narrative_type, template in self.narrative_templates.items():
            report += f"- **{narrative_type.value}**: {template.context}\n"
            report += f"  - 风格特点: {template.style}\n"
            report += f"  - 示例数量: {len(template.examples)} 个\n\n"
        
        report += "\n## 🎬 场景模板类型\n"
        for scene_type, template in self.scene_templates.items():
            report += f"- **{scene_type.value}**: {template.context}\n"
            report += f"  - 氛围特点: {template.atmosphere}\n"
            report += f"  - 示例数量: {len(template.examples)} 个\n\n"
        
        report += "\n## 🎨 修辞模板类型\n"
        for rhetorical_type, template in self.rhetorical_templates.items():
            report += f"- **{rhetorical_type.value}**: {template.context}\n"
            report += f"  - 使用技巧: {len(template.usage_tips)} 条\n"
            report += f"  - 示例数量: {len(template.examples)} 个\n\n"
        
        return report 