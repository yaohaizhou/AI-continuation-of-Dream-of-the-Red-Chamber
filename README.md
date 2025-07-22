# AI续写红楼梦

一个基于LangChain和大语言模型的《红楼梦》智能续写系统，能够模仿曹雪芹的写作风格，进行高质量的文学续写。

## ✨ 特性

- 🎭 **多种续写模式**: 支持基础续写、对话续写、场景描写、诗词创作等多种模式
- 🎨 **风格一致性**: 深度模仿红楼梦的语言风格、人物性格和叙事特点
- 🔧 **灵活配置**: 支持多种模型配置和写作参数调整
- 📊 **质量控制**: 内置续写质量检查和统计分析功能
- 🚀 **批量处理**: 支持批量续写多个文本片段
- 💾 **结果保存**: 自动保存续写结果和元数据
- 🎯 **智能分析**: 自动识别文本中的人物、地点、对话等元素

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

### 5. 开始续写

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

### 命令行工具

项目提供了强大的命令行工具 `main.py`，支持以下功能：

#### 续写故事
```bash
python main.py continue-story [OPTIONS]

选项:
  -f, --context-file PATH    从文件读取上下文
  -c, --context TEXT         直接输入上下文文本
  -t, --type [basic|dialogue|scene|poetry]  续写类型
  -l, --length INTEGER       续写最大长度
  -o, --output TEXT          输出文件名
  -m, --model TEXT           使用的模型 (默认: gpt-4)
  --temperature FLOAT        模型温度参数 (默认: 0.8)
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

你也可以在Python代码中直接使用：

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
├── src/ai_hongloumeng/          # 核心源代码
│   ├── __init__.py              # 包初始化
│   ├── core.py                  # 核心续写逻辑
│   ├── config.py                # 配置管理
│   ├── prompts.py               # 提示词模板
│   └── utils.py                 # 工具函数
├── config/                      # 配置文件
│   └── config.yaml              # 主配置文件
├── data/                        # 数据文件目录
├── output/                      # 输出文件目录
├── tests/                       # 测试文件
├── logs/                        # 日志文件
├── main.py                      # 主程序入口
├── requirements.txt             # 依赖包列表
├── .env.example                 # 环境变量模板
└── README.md                    # 项目说明
```

## 🎯 续写类型说明

### 1. 基础续写 (basic)
适用于一般的故事情节续写，保持原文的叙事风格和节奏。

### 2. 对话续写 (dialogue)  
专门用于续写人物对话场景，会特别注意人物的说话风格和性格特点。

### 3. 场景描写 (scene)
专门用于环境和场景的描写，营造红楼梦特有的诗意氛围。

### 4. 诗词创作 (poetry)
根据情境创作符合红楼梦风格的诗词，包括律诗、绝句等。

## 📊 示例输出

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
# 处理目录中的所有.txt文件
python main.py batch-continue -i texts/ -o results/ --type basic
```

### 自定义提示词
你可以在 `src/ai_hongloumeng/prompts.py` 中自定义提示词模板。

### 质量控制
系统会自动检查续写质量，包括：
- 长度检查
- 重复性检查  
- 格式检查
- 风格一致性评估

## 🐛 常见问题

### Q: 如何获取OpenAI API密钥？
A: 访问 [OpenAI官网](https://platform.openai.com) 注册账户并申请API密钥。

### Q: 可以使用其他语言模型吗？
A: 可以，只要该模型支持OpenAI的API格式，修改 `OPENAI_BASE_URL` 即可。

### Q: 续写质量不满意怎么办？
A: 可以调整以下参数：
- 增加 `temperature` 提高创造性
- 调整提示词模板
- 提供更丰富的上下文
- 使用更高级的模型（如GPT-4）

### Q: 如何提供原著文本？
A: 将红楼梦原文放入 `data/original_hongloumeng.txt`，系统会自动加载。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 🙏 致谢

- 感谢曹雪芹先生创作的不朽名著《红楼梦》
- 感谢OpenAI提供的强大语言模型
- 感谢LangChain社区的优秀工具链

---

**注意**: 本项目仅用于学习和研究目的，生成的内容不代表原著作者观点。