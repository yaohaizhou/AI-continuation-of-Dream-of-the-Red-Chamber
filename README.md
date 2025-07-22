# AI续写红楼梦

一个基于LangChain和大语言模型的《红楼梦》智能续写系统，集成了完整的文本预处理、分词分析、实体识别和知识图谱构建功能，能够深度理解原著并进行高质量的文学续写。

## ✨ 特性

- 🎭 **多种续写模式**: 支持基础续写、对话续写、场景描写、诗词创作等多种模式
- 🔤 **智能分词系统**: 集成jieba分词器和红楼梦专用词典，准确识别古典文学词汇
- 🏛️ **实体识别**: 自动识别人物、地点、物品等实体，构建知识图谱
- 📚 **文本预处理**: 自动处理章节分割、格式清理、对话标记等
- 👥 **人物关系分析**: 分析人物共现关系，识别对话说话者
- 🎨 **风格一致性**: 深度模仿红楼梦的语言风格、人物性格和叙事特点
- 🔧 **灵活配置**: 支持多种模型配置和写作参数调整
- 📊 **质量控制**: 内置续写质量检查和统计分析功能
- 🚀 **批量处理**: 支持批量续写和数据处理
- 💾 **结果保存**: 自动保存处理结果和元数据
- 📈 **综合报告**: 生成详细的数据分析报告

## 🚀 快速开始

### 1. 环境准备

确保你的系统已安装Python 3.8+:

```bash
python --version
```

### 2. 安装依赖

```bash
# 克隆项目
git clone <your-repo-url>
cd AI-continuation-of-Dream-of-the-Red-Chamber

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置API密钥

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入你的OpenAI API密钥
# OPENAI_API_KEY=your_actual_api_key_here
```

### 4. 初始化项目

```bash
python main.py setup
```

### 5. 数据处理（推荐首次使用）

```bash
# 完整处理红楼梦前80回文本（包括分词、实体识别等）
python main.py process-data --input-file data/raw/hongloumeng_80.md

# 查看处理结果
ls data/processed/
```

### 6. 开始续写

#### 基础续写
```bash
python main.py continue-story -c "话说宝玉那日..." --type basic --length 500
```

#### 从文件续写
```bash
python main.py continue-story -f data/context.txt --type basic --output my_story.txt
```

#### 对话续写
```bash
python main.py continue-story -c "宝玉道：..." --type dialogue
```

#### 场景描写
```bash
python main.py continue-story -c "春日大观园..." --type scene
```

#### 诗词创作
```bash
python main.py continue-story -c "宝玉见花飞..." --type poetry
```

## 📖 使用指南

### 数据处理工具

项目提供了完整的红楼梦文本数据处理工具链：

#### 完整数据处理
```bash
python main.py process-data [OPTIONS]

选项:
  -i, --input-file PATH        红楼梦原文文件路径 [必需]
  -o, --output-dir PATH        输出目录路径 (默认: data/processed)
  -d, --dict-path PATH         自定义词典路径 (可选)
  --skip-tokenization         跳过分词处理
  --skip-entity-recognition   跳过实体识别
  --force                     强制重新处理
```

#### 单独分词处理
```bash
python main.py tokenize [OPTIONS]

选项:
  -i, --input-file PATH        要分词的文本文件 [必需]
  -o, --output-file PATH       分词结果输出文件
  -d, --dict-path PATH         自定义词典路径
  -m, --mode [default|search|all]  分词模式 (默认: default)
```

#### 实体识别
```bash
python main.py recognize-entities [OPTIONS]

选项:
  -i, --input-file PATH        要处理的文本文件 [必需]
  -o, --output-file PATH       实体识别结果输出文件
  -d, --dict-path PATH         自定义词典路径
```

#### 批量处理章节
```bash
python main.py batch-process-chapters [OPTIONS]

选项:
  -d, --chapters-dir PATH      章节文件目录 (默认: data/processed/chapters)
```

### 续写工具

#### 续写故事
```bash
python main.py continue-story [OPTIONS]

选项:
  -f, --context-file PATH      从文件读取上下文
  -c, --context TEXT           直接输入上下文文本
  -t, --type [basic|dialogue|scene|poetry]  续写类型
  -l, --length INTEGER         续写最大长度
  -o, --output TEXT            输出文件名
  -m, --model TEXT             使用的模型 (默认: gpt-4)
  --temperature FLOAT          模型温度参数 (默认: 0.8)
```

#### 批量续写
```bash
python main.py batch-continue -i input_dir -o output_dir --type basic
```

#### 文本分析
```bash
python main.py analyze -t "宝玉听了这话..."
```

### Python API

#### 数据处理API
```python
from src.data_processing import HongLouMengDataPipeline

# 初始化数据处理管道
pipeline = HongLouMengDataPipeline(
    custom_dict_path="data/processed/hongloumeng_dict.txt",
    output_base_dir="data/processed"
)

# 完整处理红楼梦文本
result = pipeline.process_complete_text(
    input_file="data/raw/hongloumeng_80.md",
    include_tokenization=True,
    include_entity_recognition=True
)

# 查看处理结果
print(f"处理了{result['statistics']['chapters']['total_chapters']}个章节")
print(f"识别了{result['statistics']['tokenization']['total_words']:,}个词")
```

#### 分词API
```python
from src.data_processing import HongLouMengTokenizer

# 初始化分词器
tokenizer = HongLouMengTokenizer("data/processed/hongloumeng_dict.txt")

# 分词
words = tokenizer.tokenize("话说宝玉那日...")
print(words)

# 词性标注
words_with_pos = tokenizer.tokenize_with_pos("话说宝玉那日...")
print(words_with_pos)

# 文本分析
analysis = tokenizer.analyze_text("话说宝玉那日...")
print(f"找到{len(analysis['entities']['persons'])}个人物")
```

#### 实体识别API
```python
from src.data_processing import EntityRecognizer

# 初始化实体识别器
recognizer = EntityRecognizer("data/processed/hongloumeng_dict.txt")

# 识别实体
entities = recognizer.recognize_entities("宝玉见黛玉在潇湘馆...")
print(f"识别到人物: {entities['persons']}")
print(f"识别到地点: {entities['locations']}")

# 分析人物共现
co_occurrence = recognizer.analyze_character_co_occurrence(text)
```

#### 续写API
```python
import asyncio
from src.ai_hongloumeng import HongLouMengContinuation

async def main():
    # 初始化续写系统
    continuation = HongLouMengContinuation()
    
    # 进行续写
    result = await continuation.continue_story(
        context="话说宝玉那日...",
        continuation_type="basic",
        max_length=800
    )
    
    print(result["continuation"])
    
    # 保存结果
    continuation.save_continuation(result)

asyncio.run(main())
```

## ⚙️ 配置说明

### 模型配置

在 `config/config.yaml` 中可以调整以下参数：

```yaml
model:
  model_name: "gpt-4"        # 模型名称
  temperature: 0.8           # 创造性 (0.0-1.0)
  max_tokens: 2000          # 最大生成长度
  top_p: 0.9               # 核采样参数

writing:
  max_continuation_length: 1000     # 默认续写长度
  style_consistency: true           # 保持风格一致性
  character_consistency: true       # 保持人物一致性
```

### 支持的模型

- **OpenAI GPT-4**: 推荐，质量最高
- **OpenAI GPT-3.5-turbo**: 速度快，成本低
- **兼容OpenAI API的其他模型**: 通过修改 `OPENAI_BASE_URL` 使用

## 📁 项目结构

```
AI-continuation-of-Dream-of-the-Red-Chamber/
├── src/
│   ├── ai_hongloumeng/              # AI续写核心模块
│   │   ├── __init__.py              # 包初始化
│   │   ├── core.py                  # 核心续写逻辑
│   │   ├── config.py                # 配置管理
│   │   ├── prompts.py               # 提示词模板
│   │   └── utils.py                 # 工具函数
│   ├── data_processing/             # 数据处理模块 ✨新增
│   │   ├── __init__.py              # 模块初始化
│   │   ├── text_preprocessor.py     # 文本预处理
│   │   ├── chapter_splitter.py      # 章节分割
│   │   ├── tokenizer.py             # 分词器
│   │   ├── entity_recognizer.py     # 实体识别
│   │   └── pipeline.py              # 数据处理管道
│   ├── generation/                  # 生成模块 (预留)
│   ├── models/                      # 模型模块 (预留)
│   └── utils/                       # 通用工具 (预留)
├── data/                            # 数据文件目录
│   ├── raw/                         # 原始数据
│   │   └── hongloumeng_80.md        # 红楼梦前80回原文
│   ├── processed/                   # 处理后数据 ✨新增
│   │   ├── chapters/                # 章节文件 (80个.md文件)
│   │   ├── hongloumeng_dict.txt     # 红楼梦专用词典
│   │   ├── tokenization_result.json # 分词结果
│   │   ├── entity_recognition_result.json # 实体识别结果
│   │   ├── word_frequency.json      # 词频统计
│   │   ├── character_co_occurrence.json # 人物共现关系
│   │   └── comprehensive_report.md  # 综合分析报告
│   ├── generated/                   # 生成的续写内容
│   └── example_context.txt          # 示例上下文
├── config/                          # 配置文件
│   └── config.yaml                  # 主配置文件
├── output/                          # 输出文件目录
├── tests/                           # 测试文件
├── logs/                            # 日志文件
├── main.py                          # 主程序入口
├── requirements.txt                 # 依赖包列表
├── .env.example                     # 环境变量模板
└── README.md                        # 项目说明
```

## 🎯 功能详解

### 数据处理功能 ✨

#### 文本预处理
- 编码统一（UTF-8）
- 格式清理和规范化
- 章节自动识别和分割
- 段落分割和对话标记
- 文本统计分析

#### 智能分词
- 集成jieba分词器
- 红楼梦专用词典（289个词汇）
- 支持精确模式、全模式、搜索引擎模式
- 词性标注和实体分类
- 自定义词汇动态添加

#### 实体识别
- **人物识别**: 自动识别红楼梦中的64个主要人物
- **地点识别**: 识别32个重要地点（大观园、潇湘馆等）
- **物品识别**: 识别重要物品（通灵宝玉、金锁等）
- **对话识别**: 自动识别对话内容和说话者
- **人物关系**: 分析人物别名映射和共现关系

#### 知识图谱构建
- 人物关系网络
- 地点层级关系
- 实体统计分析
- 共现关系矩阵

### 续写类型说明

#### 1. 基础续写 (basic)
适用于一般的故事情节续写，保持原文的叙事风格和节奏。

#### 2. 对话续写 (dialogue)  
专门用于续写人物对话场景，会特别注意人物的说话风格和性格特点。

#### 3. 场景描写 (scene)
专门用于环境和场景的描写，营造红楼梦特有的诗意氛围。

#### 4. 诗词创作 (poetry)
根据情境创作符合红楼梦风格的诗词，包括律诗、绝句等。

## 📊 处理结果示例

### 数据处理统计
```
✅ 红楼梦前80回数据处理完成

📚 文本统计：
• 总字符数: 590,050
• 章节数: 80个
• 段落数: 160个

🔤 分词分析：
• 总词数: 410,675
• 独特词汇: 36,491个
• 发现自定义词汇: 16,009个

👥 实体识别：
• 人物实体: 12,880个
• 地点实体: 489个
• 最频繁人物: 宝玉 (2,642次)
• 人物共现: 黛玉-宝玉 (1,571次)
```

### 续写结果示例
```
# AI续写红楼梦

## 生成信息
- 生成时间: 2024-01-15 14:30:25
- 模型: gpt-4
- 温度: 0.8
- 最大长度: 800

## 原文上下文
话说宝玉那日...

## 续写内容
[AI生成的续写内容]

## 统计信息
- 原文字数: 150
- 续写字数: 750
- 总字数: 900
```

## 🔧 高级功能

### 批量处理
```bash
# 批量处理章节文件
python main.py batch-process-chapters

# 批量续写
python main.py batch-continue -i texts/ -o results/ --type basic
```

### 自定义词典
系统支持动态添加自定义词汇：
```python
tokenizer.add_custom_word("新词汇", freq=100, pos='n')
```

### 质量控制
系统会自动检查续写质量，包括：
- 长度检查
- 重复性检查  
- 格式检查
- 风格一致性评估

## 🐛 常见问题

### Q: 如何获取OpenAI API密钥？
A: 访问 [OpenAI官网](https://platform.openai.com) 注册账户并申请API密钥。

### Q: 分词时出现paddle相关错误怎么办？
A: 这是正常现象，系统会自动回退到jieba基础模式，不影响分词效果。

### Q: 如何添加新的红楼梦词汇？
A: 编辑 `data/processed/hongloumeng_dict.txt` 文件，按格式添加：`词汇 频率 词性`

### Q: 续写质量不满意怎么办？
A: 可以调整以下参数：
- 增加 `temperature` 提高创造性
- 调整提示词模板
- 提供更丰富的上下文
- 使用更高级的模型（如GPT-4）

### Q: 如何处理自己的红楼梦文本？
A: 将文本文件放入 `data/raw/` 目录，然后运行：
```bash
python main.py process-data --input-file data/raw/your_text.md
```

## 📋 开发计划

### ✅ 已完成功能
- [x] 基础续写功能
- [x] 多模式续写（对话、场景、诗词）
- [x] 文本预处理管道
- [x] 智能分词系统
- [x] 实体识别功能
- [x] 章节分割处理
- [x] 人物关系分析
- [x] 批量处理功能

### 🚧 开发中
- [ ] 知识图谱可视化
- [ ] Web界面开发
- [ ] 高级文风分析

### 📅 计划中
- [ ] 移动端支持
- [ ] 协作功能
- [ ] 更多古典文学支持

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

### 贡献指南
1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 🙏 致谢

- 感谢曹雪芹先生创作的不朽名著《红楼梦》
- 感谢OpenAI提供的强大语言模型
- 感谢LangChain社区的优秀工具链
- 感谢jieba分词项目提供的中文分词支持

---

**注意**: 本项目仅用于学习和研究目的，生成的内容不代表原著作者观点。AI续写仅供娱乐和学术研究，不能替代人类的文学创作。