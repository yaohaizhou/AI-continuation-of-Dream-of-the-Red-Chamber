"""
太虚幻境判词提取器 - 红楼梦第五回文学分析核心模块

这个模块负责从第五回太虚幻境中提取金陵十二钗的判词预言，
并进行结构化处理和文学分析，为AI续写提供深层文学指导。

Author: AI-HongLouMeng Project
"""

import re
import json
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from loguru import logger


@dataclass
class ProphecyImage:
    """判词画面描述"""
    description: str  # 画面描述
    symbolic_elements: List[str]  # 象征元素
    visual_metaphors: List[str]  # 视觉隐喻


@dataclass
class ProphecyPoem:
    """判词诗句"""
    lines: List[str]  # 诗句行
    literary_devices: List[str]  # 文学手法
    rhyme_scheme: str  # 韵律格式
    emotional_tone: str  # 情感基调


@dataclass
class FateInterpretation:
    """命运解读"""
    character: str  # 角色名
    fate_summary: str  # 命运概述
    key_events: List[str]  # 关键事件
    symbolic_meaning: str  # 象征意义
    timeline_hints: List[str]  # 时间线暗示


@dataclass
class TaixuProphecy:
    """完整的太虚幻境判词"""
    册_type: str  # 册类型：正册/副册/又副册
    characters: List[str]  # 相关角色
    image: ProphecyImage  # 画面描述
    poem: ProphecyPoem  # 判词诗句
    fate_interpretations: List[FateInterpretation]  # 命运解读
    literary_significance: str  # 文学意义
    cross_references: List[str]  # 与其他判词的关联


class TaixuProphecyExtractor:
    """太虚幻境判词提取器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.chapter_5_path = self.data_dir / "processed" / "chapters" / "005.md"
        self.output_path = self.data_dir / "processed" / "taixu_prophecies.json"
        
        # 预定义的角色映射
        self.character_mappings = {
            "玉带林中挂": "林黛玉",
            "金簪雪里埋": "薛宝钗",
            "停机德": "薛宝钗",
            "咏絮才": "林黛玉",
            "榴花开处照宫闱": "贾元春",
            "三春争及初春景": "贾元春",
            "生于末世运偏消": "贾探春",
            "襁褓之间父母违": "史湘云",
            "欲洁何曾洁": "妙玉",
            "子系中山狼": "贾迎春",
            "勘破三春景不长": "贾惜春",
            "凡鸟偏从末世来": "王熙凤",
            "势败休云贵": "贾巧姐",
            "桃李春风结子完": "李纨",
            "情天情海幻情身": "秦可卿"
        }
        
        # 文学象征元素库
        self.symbolic_elements = {
            "玉带": "高洁品格、贵族身份",
            "金簪": "富贵象征、物质依托",
            "林": "孤独、高洁",
            "雪": "寒冷、孤寂、纯洁",
            "弓": "武力、权势",
            "香橼": "芳香易逝",
            "榴花": "繁华盛开",
            "风筝": "身不由己",
            "大海": "离别、漂泊",
            "美玉": "纯洁品质",
            "泥污": "世俗污染",
            "恶狼": "邪恶势力",
            "古庙": "出家修行",
            "青灯": "佛门清苦",
            "冰山": "冷酷无情",
            "雌凤": "女中豪杰",
            "茂兰": "高洁品格",
            "高楼": "地位显赫",
            "悬梁": "自尽结局"
        }
    
    def extract_prophecies_from_chapter5(self) -> Dict[str, Any]:
        """从第五回提取完整的判词信息"""
        logger.info("开始提取太虚幻境判词...")
        
        if not self.chapter_5_path.exists():
            raise FileNotFoundError(f"第五回文件不存在: {self.chapter_5_path}")
        
        # 读取第五回内容
        with open(self.chapter_5_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取太虚幻境部分
        taixu_section = self._extract_taixu_section(content)
        
        # 分别提取三册判词
        prophecies = {
            "metadata": {
                "source": "红楼梦第五回",
                "extraction_date": self._get_current_date(),
                "description": "太虚幻境金陵十二钗判词完整提取",
                "literary_significance": "曹雪芹通过太虚幻境的判词预设了主要角色的命运轨迹，是全书的重要预言"
            },
            "main_册": self._extract_main_prophecies(taixu_section),
            "副册": self._extract_secondary_prophecies(taixu_section),
            "又副册": self._extract_tertiary_prophecies(taixu_section)
        }
        
        logger.info(f"成功提取 {len(prophecies['main_册'])} 个正册判词")
        logger.info(f"成功提取 {len(prophecies['副册'])} 个副册判词")
        logger.info(f"成功提取 {len(prophecies['又副册'])} 个又副册判词")
        
        return prophecies
    
    def _extract_taixu_section(self, content: str) -> str:
        """提取太虚幻境相关部分"""
        # 定位太虚幻境开始和结束
        start_pattern = r"太虚幻境"
        end_pattern = r"宝玉还欲看时.*?又随警幻来至后面"
        
        start_match = re.search(start_pattern, content)
        if not start_match:
            raise ValueError("未找到太虚幻境部分")
        
        # 从太虚幻境开始到判词结束
        taixu_start = start_match.start()
        end_match = re.search(end_pattern, content[taixu_start:], re.DOTALL)
        
        if end_match:
            taixu_end = taixu_start + end_match.end()
            taixu_section = content[taixu_start:taixu_end]
        else:
            # 如果没找到结束标记，取到文件末尾
            taixu_section = content[taixu_start:]
        
        return taixu_section
    
    def _extract_main_prophecies(self, taixu_content: str) -> List[Dict[str, Any]]:
        """提取正册判词"""
        prophecies = []
        
        # 定位正册部分
        main_pattern = r"金陵十二钗正册.*?(?=后面又画着几缕飞云|宝玉还欲看时)"
        main_match = re.search(main_pattern, taixu_content, re.DOTALL)
        
        if not main_match:
            logger.warning("未找到正册判词部分")
            return prophecies
        
        main_content = main_match.group()
        
        # 1. 林黛玉&薛宝钗合册
        daiyu_baochai = self._extract_daiyu_baochai_prophecy(main_content)
        if daiyu_baochai:
            prophecies.append(daiyu_baochai)
        
        # 2. 贾元春
        yuanchun = self._extract_yuanchun_prophecy(main_content)
        if yuanchun:
            prophecies.append(yuanchun)
        
        # 3. 贾探春
        tanchun = self._extract_tanchun_prophecy(main_content)
        if tanchun:
            prophecies.append(tanchun)
        
        # 4. 史湘云
        xiangyun = self._extract_xiangyun_prophecy(main_content)
        if xiangyun:
            prophecies.append(xiangyun)
        
        # 5. 妙玉
        miaoyu = self._extract_miaoyu_prophecy(main_content)
        if miaoyu:
            prophecies.append(miaoyu)
        
        # 6. 贾迎春
        yingchun = self._extract_yingchun_prophecy(main_content)
        if yingchun:
            prophecies.append(yingchun)
        
        # 7. 贾惜春
        xichun = self._extract_xichun_prophecy(main_content)
        if xichun:
            prophecies.append(xichun)
        
        # 8. 王熙凤
        xifeng = self._extract_xifeng_prophecy(main_content)
        if xifeng:
            prophecies.append(xifeng)
        
        # 9. 贾巧姐
        qiaojie = self._extract_qiaojie_prophecy(main_content)
        if qiaojie:
            prophecies.append(qiaojie)
        
        # 10. 李纨
        liwan = self._extract_liwan_prophecy(main_content)
        if liwan:
            prophecies.append(liwan)
        
        # 11. 秦可卿
        qinkeqing = self._extract_qinkeqing_prophecy(main_content)
        if qinkeqing:
            prophecies.append(qinkeqing)
        
        return prophecies
    
    def _extract_daiyu_baochai_prophecy(self, content: str) -> Optional[Dict[str, Any]]:
        """提取林黛玉&薛宝钗合册判词"""
        pattern = r"两株枯木.*?玉带林中挂,金簪雪里埋"
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return None
        
        prophecy = TaixuProphecy(
            册_type="正册",
            characters=["林黛玉", "薛宝钗"],
            image=ProphecyImage(
                description="两株枯木，木上悬着一围玉带；地上又有一堆雪，雪中一股金簪",
                symbolic_elements=["枯木", "玉带", "雪", "金簪"],
                visual_metaphors=["生命凋零", "高洁品格", "寒冷孤寂", "富贵象征"]
            ),
            poem=ProphecyPoem(
                lines=["可叹停机德", "堪怜咏絮才", "玉带林中挂", "金簪雪里埋"],
                literary_devices=["对比", "象征", "谐音", "互文"],
                rhyme_scheme="ABAB",
                emotional_tone="悲叹"
            ),
            fate_interpretations=[
                FateInterpretation(
                    character="林黛玉",
                    fate_summary="香消玉殒，早逝夭折",
                    key_events=["玉带林中挂", "孤高自许", "与宝玉情深"],
                    symbolic_meaning="高洁品格如玉带般珍贵，但终将悬挂在林中凋零",
                    timeline_hints=["青春年华", "与宝钗并提"]
                ),
                FateInterpretation(
                    character="薛宝钗",
                    fate_summary="独守空房，婚姻不幸",
                    key_events=["金簪雪里埋", "停机德", "婚后孤独"],
                    symbolic_meaning="如金簪般贵重，但终将被埋在冰雪中，寓意感情冰冷",
                    timeline_hints=["婚后生活", "与黛玉对比"]
                )
            ],
            literary_significance="通过对比手法展现两种不同的女性命运，体现了作者对才情与品德的双重思考",
            cross_references=["与宝玉的感情纠葛", "金玉良缘vs木石前盟"]
        )
        
        return asdict(prophecy)
    
    def _extract_yuanchun_prophecy(self, content: str) -> Optional[Dict[str, Any]]:
        """提取贾元春判词"""
        pattern = r"一张弓,弓上挂着一个香橼.*?二十年来辨是非.*?虎兕相逢大梦归"
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return None
        
        prophecy = TaixuProphecy(
            册_type="正册",
            characters=["贾元春"],
            image=ProphecyImage(
                description="一张弓，弓上挂着一个香橼",
                symbolic_elements=["弓", "香橼"],
                visual_metaphors=["武力权势", "芳香易逝"]
            ),
            poem=ProphecyPoem(
                lines=["二十年来辨是非", "榴花开处照宫闱", "三春争及初春景", "虎兕相逢大梦归"],
                literary_devices=["时间对比", "宫廷意象", "季节隐喻", "生肖预言"],
                rhyme_scheme="ABCB",
                emotional_tone="哀叹"
            ),
            fate_interpretations=[
                FateInterpretation(
                    character="贾元春",
                    fate_summary="贵妃身份短暂，在虎兔年间去世",
                    key_events=["入宫为妃", "荣华显赫", "虎兔年逝世"],
                    symbolic_meaning="弓箭代表权势，香橼寓意芳华易逝，贵妃身份虽显赫但终究短暂",
                    timeline_hints=["二十年", "虎兔年", "三春对比"]
                )
            ],
            literary_significance="通过宫廷生活反映权势的虚幻和生命的无常",
            cross_references=["与三春姐妹对比", "贾府兴衰的标志"]
        )
        
        return asdict(prophecy)
    
    def _extract_tanchun_prophecy(self, content: str) -> Optional[Dict[str, Any]]:
        """提取贾探春判词"""
        pattern = r"两个人放风筝.*?才自精明志自高.*?千里东风一梦遥"
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return None
        
        prophecy = TaixuProphecy(
            册_type="正册",
            characters=["贾探春"],
            image=ProphecyImage(
                description="两个人放风筝，一片大海，一只大船，船中有一女子掩面泣涕之状",
                symbolic_elements=["风筝", "大海", "大船", "女子掩面"],
                visual_metaphors=["身不由己", "离别漂泊", "远嫁他乡", "思乡之苦"]
            ),
            poem=ProphecyPoem(
                lines=["才自精明志自高", "生于末世运偏消", "清明涕泣江边望", "千里东风一梦遥"],
                literary_devices=["才情描写", "时代背景", "节气暗示", "距离隐喻"],
                rhyme_scheme="AABA",
                emotional_tone="悲壮"
            ),
            fate_interpretations=[
                FateInterpretation(
                    character="贾探春",
                    fate_summary="才情出众但生不逢时，远嫁他乡",
                    key_events=["才能显露", "家族衰落", "远嫁和亲"],
                    symbolic_meaning="风筝随风飘荡，如探春才高志远却身不由己，最终远嫁离家",
                    timeline_hints=["末世时期", "清明时节", "千里之外"]
                )
            ],
            literary_significance="体现了有才华的女性在封建社会中的悲剧命运",
            cross_references=["与迎春惜春对比", "贾府政治联姻"]
        )
        
        return asdict(prophecy)
    
    def _extract_xiangyun_prophecy(self, content: str) -> Optional[Dict[str, Any]]:
        """提取史湘云判词"""
        pattern = r"几缕飞云,一湾逝水.*?富贵又何为.*?湘江水逝楚云飞"
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return None
        
        prophecy = TaixuProphecy(
            册_type="正册",
            characters=["史湘云"],
            image=ProphecyImage(
                description="几缕飞云，一湾逝水",
                symbolic_elements=["飞云", "逝水"],
                visual_metaphors=["自由飘逸", "时光流逝"]
            ),
            poem=ProphecyPoem(
                lines=["富贵又何为", "襁褓之间父母违", "展眼吊斜辉", "湘江水逝楚云飞"],
                literary_devices=["反问修辞", "时间跨越", "地域暗示", "自然意象"],
                rhyme_scheme="ABAB",
                emotional_tone="旷达中带悲凉"
            ),
            fate_interpretations=[
                FateInterpretation(
                    character="史湘云",
                    fate_summary="幼年失亲，虽得富贵但终归飘零",
                    key_events=["幼年丧亲", "进入贾府", "短暂婚姻", "最终孤独"],
                    symbolic_meaning="云水自由却易散，如湘云性格豪爽但命运飘零",
                    timeline_hints=["襁褓时期", "展眼之间", "湘江地域"]
                )
            ],
            literary_significance="通过自然意象表现人生无常和女性命运的不可把控",
            cross_references=["与黛玉的友谊", "大观园诗社"]
        )
        
        return asdict(prophecy)
    
    def _extract_miaoyu_prophecy(self, content: str) -> Optional[Dict[str, Any]]:
        """提取妙玉判词"""
        pattern = r"一块美玉,落在泥污之中.*?欲洁何曾洁.*?终陷淖泥中"
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return None
        
        prophecy = TaixuProphecy(
            册_type="正册",
            characters=["妙玉"],
            image=ProphecyImage(
                description="一块美玉，落在泥污之中",
                symbolic_elements=["美玉", "泥污"],
                visual_metaphors=["纯洁品质", "世俗污染"]
            ),
            poem=ProphecyPoem(
                lines=["欲洁何曾洁", "云空未必空", "可怜金玉质", "终陷淖泥中"],
                literary_devices=["反讽", "禅理", "材质隐喻", "对比"],
                rhyme_scheme="AABB",
                emotional_tone="讽刺悲悯"
            ),
            fate_interpretations=[
                FateInterpretation(
                    character="妙玉",
                    fate_summary="追求纯洁却无法避免世俗污染，最终堕落",
                    key_events=["出家修行", "进入大观园", "内心挣扎", "最终堕落"],
                    symbolic_meaning="美玉代表妙玉的洁癖和高洁，泥污暗示其无法逃脱的世俗命运",
                    timeline_hints=["修行期间", "在贾府时期"]
                )
            ],
            literary_significance="探讨了宗教修行与世俗欲望的矛盾，体现了人性的复杂",
            cross_references=["与宝钗黛玉的茶道", "佛门修行的虚伪"]
        )
        
        return asdict(prophecy)
    
    def _extract_yingchun_prophecy(self, content: str) -> Optional[Dict[str, Any]]:
        """提取贾迎春判词"""
        pattern = r"一恶狼,追扑一美女.*?子系中山狼.*?一载赴黄粱"
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return None
        
        prophecy = TaixuProphecy(
            册_type="正册", 
            characters=["贾迎春"],
            image=ProphecyImage(
                description="一恶狼，追扑一美女，欲啖之意",
                symbolic_elements=["恶狼", "美女"],
                visual_metaphors=["邪恶势力", "柔弱无助"]
            ),
            poem=ProphecyPoem(
                lines=["子系中山狼", "得志便猖狂", "金闺花柳质", "一载赴黄粱"],
                literary_devices=["典故引用", "性格揭示", "身份对比", "时间限制"],
                rhyme_scheme="AABB",
                emotional_tone="愤慨悲愤"
            ),
            fate_interpretations=[
                FateInterpretation(
                    character="贾迎春",
                    fate_summary="嫁给恶人，仅一年就死去",
                    key_events=["被迫婚嫁", "遭受虐待", "一年后死亡"],
                    symbolic_meaning="恶狼代表其夫中山狼，美女象征迎春的善良柔弱，预示其悲惨结局",
                    timeline_hints=["一载时间", "得志猖狂"]
                )
            ],
            literary_significance="通过动物隐喻揭露封建婚姻的残酷和女性的悲惨命运",
            cross_references=["与孙绍祖的婚姻", "贾府政治联姻"]
        )
        
        return asdict(prophecy)
    
    def _extract_xichun_prophecy(self, content: str) -> Optional[Dict[str, Any]]:
        """提取贾惜春判词"""
        pattern = r"一所古庙,里面有一美人在内看经独坐.*?勘破三春景不长.*?独卧青灯古佛旁"
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return None
        
        prophecy = TaixuProphecy(
            册_type="正册",
            characters=["贾惜春"],
            image=ProphecyImage(
                description="一所古庙，里面有一美人在内看经独坐",
                symbolic_elements=["古庙", "美人", "看经"],
                visual_metaphors=["宗教修行", "青春美貌", "独修苦行"]
            ),
            poem=ProphecyPoem(
                lines=["勘破三春景不长", "缁衣顿改昔年妆", "可怜绣户侯门女", "独卧青灯古佛旁"],
                literary_devices=["数字暗示", "对比手法", "身份强调", "环境烘托"],
                rhyme_scheme="AABB",
                emotional_tone="冷静悲凉"
            ),
            fate_interpretations=[
                FateInterpretation(
                    character="贾惜春",
                    fate_summary="看破红尘，出家为尼",
                    key_events=["家族衰落", "姐妹离散", "勘破世情", "出家修行"],
                    symbolic_meaning="古庙代表其最终归宿，看经独坐预示其孤独的修行生活",
                    timeline_hints=["三春景色", "昔年对比"]
                )
            ],
            literary_significance="体现了对家族兴衰的深刻认识和对世俗的彻底决绝",
            cross_references=["与三春姐妹的不同命运", "贾府彻底败落"]
        )
        
        return asdict(prophecy)
    
    def _extract_xifeng_prophecy(self, content: str) -> Optional[Dict[str, Any]]:
        """提取王熙凤判词"""
        pattern = r"一片冰山,上有一只雌凤.*?凡鸟偏从末世来.*?哭向金陵事更哀"
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return None
        
        prophecy = TaixuProphecy(
            册_type="正册",
            characters=["王熙凤"],
            image=ProphecyImage(
                description="一片冰山，上有一只雌凤",
                symbolic_elements=["冰山", "雌凤"],
                visual_metaphors=["冷酷无情", "女中豪杰"]
            ),
            poem=ProphecyPoem(
                lines=["凡鸟偏从末世来", "都知爱慕此生才", "一从二令三人木", "哭向金陵事更哀"],
                literary_devices=["时代背景", "才能认可", "字谜暗示", "地域情感"],
                rhyme_scheme="AABB",
                emotional_tone="悲壮"
            ),
            fate_interpretations=[
                FateInterpretation(
                    character="王熙凤",
                    fate_summary="才能出众但生于末世，最终败落凄惨",
                    key_events=["管理才能", "权势巅峰", "家族败落", "凄惨结局"],
                    symbolic_meaning="雌凤代表其杰出才能，冰山暗示其冷酷和最终的孤立",
                    timeline_hints=["末世时期", "一从二令三人木", "金陵归宿"]
                )
            ],
            literary_significance="通过凤凰意象展现女性的杰出才能与时代悲剧的结合",
            cross_references=["贾府管家", "与贾琏的夫妻关系"]
        )
        
        return asdict(prophecy)
    
    def _extract_qiaojie_prophecy(self, content: str) -> Optional[Dict[str, Any]]:
        """提取贾巧姐判词"""
        pattern = r"一座荒村野店,有一美人在那里纺绩.*?势败休云贵.*?巧得遇恩人"
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return None
        
        prophecy = TaixuProphecy(
            册_type="正册",
            characters=["贾巧姐"],
            image=ProphecyImage(
                description="一座荒村野店，有一美人在那里纺绩",
                symbolic_elements=["荒村野店", "美人", "纺绩"],
                visual_metaphors=["落魄境遇", "贵族出身", "劳作自立"]
            ),
            poem=ProphecyPoem(
                lines=["势败休云贵", "家亡莫论亲", "偶因济村妇", "巧得遇恩人"],
                literary_devices=["劝诫语气", "现实描述", "因果关系", "名字暗示"],
                rhyme_scheme="AABB",
                emotional_tone="劝慰希望"
            ),
            fate_interpretations=[
                FateInterpretation(
                    character="贾巧姐",
                    fate_summary="家族败落后流落乡村，因善行得到帮助",
                    key_events=["家族败落", "流落民间", "劳作自立", "得到救助"],
                    symbolic_meaning="荒村野店代表其落魄处境，纺绩象征其自立自强，终有善报",
                    timeline_hints=["势败家亡", "偶然机缘"]
                )
            ],
            literary_significance="体现了善有善报的因果观念和劳动自立的价值观",
            cross_references=["与刘姥姥的关系", "贾府恩怨报应"]
        )
        
        return asdict(prophecy)
    
    def _extract_liwan_prophecy(self, content: str) -> Optional[Dict[str, Any]]:
        """提取李纨判词"""
        pattern = r"一盆茂兰,旁有一位凤冠霞帔的美人.*?桃李春风结子完.*?枉与他人作笑谈"
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return None
        
        prophecy = TaixuProphecy(
            册_type="正册",
            characters=["李纨"],
            image=ProphecyImage(
                description="一盆茂兰，旁有一位凤冠霞帔的美人",
                symbolic_elements=["茂兰", "凤冠霞帔", "美人"],
                visual_metaphors=["高洁品格", "荣华富贵", "贵妇形象"]
            ),
            poem=ProphecyPoem(
                lines=["桃李春风结子完", "到头谁似一盆兰", "如冰水好空相妒", "枉与他人作笑谈"],
                literary_devices=["植物比喻", "对比手法", "品格赞美", "世态炎凉"],
                rhyme_scheme="AABA",
                emotional_tone="赞叹惋惜"
            ),
            fate_interpretations=[
                FateInterpretation(
                    character="李纨",
                    fate_summary="教子成才，品格高洁，但终成他人笑谈",
                    key_events=["丈夫早逝", "教育贾兰", "儿子成才", "晚年荣华"],
                    symbolic_meaning="茂兰象征其高洁品格，凤冠霞帔预示因子贵而荣，但终成虚幻",
                    timeline_hints=["桃李春风", "结子完时", "到头之际"]
                )
            ],
            literary_significance="展现了封建社会中节妇的典型命运和品格追求的虚幻性",
            cross_references=["与贾兰的母子关系", "大观园诗社领袖"]
        )
        
        return asdict(prophecy)
    
    def _extract_qinkeqing_prophecy(self, content: str) -> Optional[Dict[str, Any]]:
        """提取秦可卿判词"""
        pattern = r"一座高楼,上有一美人悬梁自缢.*?情天情海幻情身.*?造衅开端实在宁"
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return None
        
        prophecy = TaixuProphecy(
            册_type="正册",
            characters=["秦可卿"],
            image=ProphecyImage(
                description="一座高楼，上有一美人悬梁自缢",
                symbolic_elements=["高楼", "美人", "悬梁自缢"],
                visual_metaphors=["地位显赫", "美貌出众", "自尽结局"]
            ),
            poem=ProphecyPoem(
                lines=["情天情海幻情身", "情既相逢必主淫", "漫言不肖皆荣出", "造衅开端实在宁"],
                literary_devices=["情感渲染", "因果揭示", "家族对比", "责任归属"],
                rhyme_scheme="AABB",
                emotional_tone="沉重警示"
            ),
            fate_interpretations=[
                FateInterpretation(
                    character="秦可卿",
                    fate_summary="沉溺情海，最终自缢而死，成为家族败落的开端",
                    key_events=["地位显赫", "情感纠葛", "丑事败露", "悬梁自尽"],
                    symbolic_meaning="高楼代表其显赫地位，自缢暗示其情感悲剧和家族丑闻的开始",
                    timeline_hints=["情海沉浮", "开端时期"]
                )
            ],
            literary_significance="揭示了情欲的危害和家族败落的内在原因",
            cross_references=["与贾珍的关系", "宁国府丑闻", "家族败落预兆"]
        )
        
        return asdict(prophecy)
    
    def _extract_secondary_prophecies(self, taixu_content: str) -> List[Dict[str, Any]]:
        """提取副册判词"""
        prophecies = []
        
        # 香菱判词
        xiangling_pattern = r"一枝桂花,下面有一方池沼.*?根并荷花一茎香.*?致使香魂返故乡"
        xiangling_match = re.search(xiangling_pattern, taixu_content, re.DOTALL)
        
        if xiangling_match:
            xiangling_prophecy = TaixuProphecy(
                册_type="副册",
                characters=["香菱"],
                image=ProphecyImage(
                    description="一枝桂花，下面有一方池沼，其中水涸泥干，莲枯藕败",
                    symbolic_elements=["桂花", "池沼", "水涸泥干", "莲枯藕败"],
                    visual_metaphors=["芳香品质", "生存环境", "资源枯竭", "生命凋零"]
                ),
                poem=ProphecyPoem(
                    lines=["根并荷花一茎香", "平生遭际实堪伤", "自从两地生孤木", "致使香魂返故乡"],
                    literary_devices=["植物比喻", "身世感叹", "地域暗示", "灵魂归宿"],
                    rhyme_scheme="AABA",
                    emotional_tone="悲叹同情"
                ),
                fate_interpretations=[
                    FateInterpretation(
                        character="香菱",
                        fate_summary="被拐卖后遭遇坎坷，最终香消玉殒",
                        key_events=["幼年被拐", "成为妾室", "学诗努力", "最终早逝"],
                        symbolic_meaning="桂花荷花象征其本质美好，但环境恶劣最终凋零",
                        timeline_hints=["两地生活", "返故乡时"]
                    )
                ],
                literary_significance="展现了底层女性的悲惨命运和对美好品质的摧残",
                cross_references=["与薛蟠的关系", "在大观园学诗"]
            )
            prophecies.append(asdict(xiangling_prophecy))
        
        return prophecies
    
    def _extract_tertiary_prophecies(self, taixu_content: str) -> List[Dict[str, Any]]:
        """提取又副册判词"""
        prophecies = []
        
        # 晴雯判词（从又副册文本推测）
        qingwen_pattern = r"霁月难逢,彩云易散.*?风流灵巧招人怨.*?多情公子空牵念"
        qingwen_match = re.search(qingwen_pattern, taixu_content, re.DOTALL)
        
        if qingwen_match:
            qingwen_prophecy = TaixuProphecy(
                册_type="又副册",
                characters=["晴雯"],
                image=ProphecyImage(
                    description="水墨渲染，满纸乌云浊雾",
                    symbolic_elements=["乌云", "浊雾"],
                    visual_metaphors=["命运迷茫", "前路不明"]
                ),
                poem=ProphecyPoem(
                    lines=["霁月难逢", "彩云易散", "心比天高", "身为下贱", "风流灵巧招人怨", "寿夭多因诽谤生", "多情公子空牵念"],
                    literary_devices=["天象比喻", "身份对比", "性格描述", "因果分析"],
                    rhyme_scheme="自由体",
                    emotional_tone="悲愤不平"
                ),
                fate_interpretations=[
                    FateInterpretation(
                        character="晴雯",
                        fate_summary="心高气傲但身份低贱，因谗言而早死",
                        key_events=["伺候宝玉", "性格张扬", "遭受诽谤", "被撵早逝"],
                        symbolic_meaning="霁月彩云象征其美好品质，但易散难逢，命运多舛",
                        timeline_hints=["寿夭时期", "诽谤传播"]
                    )
                ],
                literary_significance="反映了下层女性的悲剧和等级社会的残酷",
                cross_references=["与宝玉的主仆情", "袭人的对比"]
            )
            prophecies.append(asdict(qingwen_prophecy))
        
        # 袭人判词（推测）
        xiren_pattern = r"枉自温柔和顺,空云似桂如兰.*?谁知公子无缘"
        xiren_match = re.search(xiren_pattern, taixu_content, re.DOTALL)
        
        if xiren_match:
            xiren_prophecy = TaixuProphecy(
                册_type="又副册",
                characters=["袭人"],
                image=ProphecyImage(
                    description="一簇鲜花，一床破席",
                    symbolic_elements=["鲜花", "破席"],
                    visual_metaphors=["美好品质", "处境困顿"]
                ),
                poem=ProphecyPoem(
                    lines=["枉自温柔和顺", "空云似桂如兰", "堪羡优伶有福", "谁知公子无缘"],
                    literary_devices=["性格赞美", "品质比喻", "命运对比", "缘分感叹"],
                    rhyme_scheme="AABB",
                    emotional_tone="惋惜同情"
                ),
                fate_interpretations=[
                    FateInterpretation(
                        character="袭人",
                        fate_summary="温柔和顺但最终与宝玉无缘",
                        key_events=["悉心照料", "情深意重", "宝玉出家", "改嫁他人"],
                        symbolic_meaning="鲜花代表其美好品质，破席暗示其最终的困顿处境",
                        timeline_hints=["公子无缘", "优伶对比"]
                    )
                ],
                literary_significance="体现了忠诚品格与现实命运的矛盾",
                cross_references=["与宝玉的情感", "与蒋玉菡的关系"]
            )
            prophecies.append(asdict(xiren_prophecy))
        
        return prophecies
    
    def save_prophecies(self, prophecies: Dict[str, Any]) -> None:
        """保存判词数据到文件"""
        logger.info(f"保存判词数据到: {self.output_path}")
        
        # 确保目录存在
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存为JSON格式
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(prophecies, f, ensure_ascii=False, indent=2)
        
        logger.info(f"判词数据保存完成: {self.output_path}")
    
    def load_prophecies(self) -> Optional[Dict[str, Any]]:
        """加载已保存的判词数据"""
        if not self.output_path.exists():
            logger.warning(f"判词数据文件不存在: {self.output_path}")
            return None
        
        with open(self.output_path, 'r', encoding='utf-8') as f:
            prophecies = json.load(f)
        
        logger.info(f"成功加载判词数据: {self.output_path}")
        return prophecies
    
    def get_character_prophecy(self, character_name: str) -> Optional[Dict[str, Any]]:
        """获取特定角色的判词"""
        prophecies = self.load_prophecies()
        if not prophecies:
            return None
        
        # 在三册中搜索
        for section_name in ["main_册", "副册", "又副册"]:
            section = prophecies.get(section_name, [])
            for prophecy in section:
                if character_name in prophecy.get("characters", []):
                    return prophecy
        
        return None
    
    def get_symbolic_elements(self, character_name: str) -> List[str]:
        """获取角色相关的象征元素"""
        prophecy = self.get_character_prophecy(character_name)
        if not prophecy:
            return []
        
        image = prophecy.get("image", {})
        return image.get("symbolic_elements", [])
    
    def get_fate_summary(self, character_name: str) -> Optional[str]:
        """获取角色命运概述"""
        prophecy = self.get_character_prophecy(character_name)
        if not prophecy:
            return None
        
        fate_interpretations = prophecy.get("fate_interpretations", [])
        for fate in fate_interpretations:
            if fate.get("character") == character_name:
                return fate.get("fate_summary")
        
        return None
    
    def _get_current_date(self) -> str:
        """获取当前日期"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")
    
    def generate_prophecy_report(self) -> str:
        """生成判词分析报告"""
        prophecies = self.load_prophecies()
        if not prophecies:
            return "未找到判词数据"
        
        report = []
        report.append("# 太虚幻境判词分析报告")
        report.append("")
        
        # 基本统计
        main_count = len(prophecies.get("main_册", []))
        secondary_count = len(prophecies.get("副册", []))
        tertiary_count = len(prophecies.get("又副册", []))
        
        report.append("## 统计概览")
        report.append(f"- 正册判词: {main_count}个")
        report.append(f"- 副册判词: {secondary_count}个")
        report.append(f"- 又副册判词: {tertiary_count}个")
        report.append(f"- 总计: {main_count + secondary_count + tertiary_count}个")
        report.append("")
        
        # 主要角色命运概述
        report.append("## 金陵十二钗正册命运概览")
        main_prophecies = prophecies.get("main_册", [])
        for prophecy in main_prophecies:
            characters = prophecy.get("characters", [])
            report.append(f"### {'/'.join(characters)}")
            
            fate_interpretations = prophecy.get("fate_interpretations", [])
            for fate in fate_interpretations:
                character = fate.get("character", "")
                summary = fate.get("fate_summary", "")
                report.append(f"- **{character}**: {summary}")
            
            report.append("")
        
        return "\n".join(report)


def main():
    """主函数，用于测试判词提取功能"""
    extractor = TaixuProphecyExtractor()
    
    try:
        # 提取判词
        prophecies = extractor.extract_prophecies_from_chapter5()
        
        # 保存数据
        extractor.save_prophecies(prophecies)
        
        # 生成报告
        report = extractor.generate_prophecy_report()
        print(report)
        
        # 测试单个角色查询
        daiyu_prophecy = extractor.get_character_prophecy("林黛玉")
        if daiyu_prophecy:
            print("\n林黛玉判词:")
            print(json.dumps(daiyu_prophecy, ensure_ascii=False, indent=2))
        
    except Exception as e:
        logger.error(f"判词提取失败: {e}")
        raise


if __name__ == "__main__":
    main() 