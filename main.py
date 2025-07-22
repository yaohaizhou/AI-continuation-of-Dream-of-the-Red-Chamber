#!/usr/bin/env python3
"""
AI续写红楼梦 - 主程序入口
基于LangChain的红楼梦续写系统
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from loguru import logger

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_hongloumeng import HongLouMengContinuation, Config
from ai_hongloumeng.utils import FileManager
from ai_hongloumeng.prompts import PromptTemplates
from data_processing import HongLouMengDataPipeline
from knowledge_enhancement import EnhancedPrompter, TaixuProphecyExtractor, FateConsistencyChecker
from rag_retrieval import RAGPipeline, create_rag_pipeline

# 初始化控制台
console = Console()

# 配置日志
logger.remove()  # 移除默认的日志处理器
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}"
)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """AI续写红楼梦 - 基于LangChain的智能续写系统"""
    console.print(Panel.fit(
        "[bold red]AI续写红楼梦[/bold red]\n"
        "[dim]基于LangChain的红楼梦智能续写系统[/dim]",
        border_style="red"
    ))


@cli.command()
@click.option('--context-file', '-f', type=click.Path(exists=True), help='包含上下文的文件路径')
@click.option('--context', '-c', type=str, help='直接输入的上下文文本')
@click.option('--type', '-t', 
              type=click.Choice(['basic', 'dialogue', 'scene', 'poetry']), 
              default='basic', help='续写类型')
@click.option('--length', '-l', type=int, default=800, help='续写最大长度')
@click.option('--output', '-o', type=str, help='输出文件名')
@click.option('--model', '-m', type=str, default='gpt-4', help='使用的模型')
@click.option('--temperature', type=float, default=0.8, help='模型温度参数')
def continue_story(context_file, context, type, length, output, model, temperature):
    """续写红楼梦故事"""
    asyncio.run(_continue_story_async(
        context_file, context, type, length, output, model, temperature
    ))


async def _continue_story_async(context_file, context, type, length, output, model, temperature):
    """异步续写故事"""
    try:
        # 获取上下文
        if context_file:
            file_manager = FileManager()
            context = file_manager.read_text_file(Path(context_file))
            console.print(f"[green]从文件加载上下文: {context_file}[/green]")
        elif not context:
            console.print("[red]错误: 请提供上下文文本或文件[/red]")
            return
        
        # 创建配置
        config = Config()
        config.model.model_name = model
        config.model.temperature = temperature
        config.writing.max_continuation_length = length
        
        # 初始化续写系统
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("初始化AI续写系统...", total=None)
            continuation_system = HongLouMengContinuation(config)
            progress.update(task, description="系统初始化完成")
        
        # 显示上下文预览
        context_preview = context[:200] + "..." if len(context) > 200 else context
        console.print(Panel(
            f"[bold]上下文预览:[/bold]\n{context_preview}",
            title="输入文本",
            border_style="blue"
        ))
        
        # 进行续写
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("AI续写中...", total=None)
            
            # 根据类型设置参数
            kwargs = {}
            if type == "dialogue":
                kwargs = {
                    "character_info": "红楼梦主要人物",
                    "scene_context": "大观园日常",
                    "dialogue_context": "人物对话"
                }
            elif type == "scene":
                kwargs = {
                    "scene_setting": "大观园场景",
                    "time": "春日午后",
                    "location": "大观园",
                    "characters": "主要人物"
                }
            elif type == "poetry":
                kwargs = {
                    "poetry_type": "律诗",
                    "theme": "春日感怀",
                    "character": "宝玉"
                }
            
            result = await continuation_system.continue_story(
                context=context,
                continuation_type=type,
                max_length=length,
                **kwargs
            )
            
            progress.update(task, description="续写完成")
        
        # 显示结果
        console.print(Panel(
            result["continuation"],
            title=f"[bold green]AI续写结果 ({type})[/bold green]",
            border_style="green"
        ))
        
        # 显示统计信息
        metadata = result["metadata"]
        stats_text = f"""
[bold]生成统计:[/bold]
• 模型: {metadata['model']}
• 温度: {metadata.get('temperature', 'N/A')}
• 使用Token: {metadata.get('tokens_used', 'N/A')}
• 成本: ${metadata.get('cost', 0):.6f}
• 续写字数: {len(result['continuation'])}字
        """
        console.print(Panel(stats_text.strip(), title="统计信息", border_style="yellow"))
        
        # 质量检查
        quality = result.get("quality_check", {})
        if not quality.get("is_valid", True):
            console.print(Panel(
                f"[red]质量警告:[/red]\n" + "\n".join(f"• {issue}" for issue in quality.get("issues", [])),
                title="质量检查",
                border_style="red"
            ))
        
        # 保存结果
        if output or click.confirm("是否保存结果到文件?"):
            output_path = continuation_system.save_continuation(result, output)
            console.print(f"[green]结果已保存到: {output_path}[/green]")
            
    except Exception as e:
        console.print(f"[red]续写失败: {e}[/red]")
        logger.error(f"续写失败: {e}")


@cli.command()
@click.option('--input-dir', '-i', type=click.Path(exists=True), required=True, help='输入文件目录')
@click.option('--output-dir', '-o', type=click.Path(), help='输出目录')
@click.option('--type', '-t', 
              type=click.Choice(['basic', 'dialogue', 'scene', 'poetry']), 
              default='basic', help='续写类型')
@click.option('--length', '-l', type=int, default=800, help='续写最大长度')
def batch_continue(input_dir, output_dir, type, length):
    """批量续写多个文本文件"""
    asyncio.run(_batch_continue_async(input_dir, output_dir, type, length))


async def _batch_continue_async(input_dir, output_dir, type, length):
    """异步批量续写"""
    try:
        input_path = Path(input_dir)
        output_path = Path(output_dir) if output_dir else Path("output")
        
        # 查找所有文本文件
        text_files = list(input_path.glob("*.txt"))
        if not text_files:
            console.print("[red]在输入目录中未找到.txt文件[/red]")
            return
        
        console.print(f"[green]找到{len(text_files)}个文本文件[/green]")
        
        # 初始化系统
        continuation_system = HongLouMengContinuation()
        file_manager = FileManager()
        
        # 读取所有文件内容
        contexts = []
        for file_path in text_files:
            content = file_manager.read_text_file(file_path)
            contexts.append(content)
        
        # 批量续写
        with Progress(console=console) as progress:
            task = progress.add_task("批量续写中...", total=len(contexts))
            
            results = await continuation_system.batch_continuation(
                contexts=contexts,
                continuation_type=type,
                max_length=length
            )
            
            progress.update(task, completed=len(contexts))
        
        # 保存结果
        output_path.mkdir(exist_ok=True)
        successful_count = 0
        
        for i, (result, file_path) in enumerate(zip(results, text_files)):
            if "error" not in result:
                output_filename = f"{file_path.stem}_continued.txt"
                output_file_path = output_path / output_filename
                
                formatted_output = continuation_system.output_formatter.format_continuation_output(
                    original_text=result["context"],
                    continuation=result["continuation"],
                    metadata=result["metadata"]
                )
                
                file_manager.write_text_file(output_file_path, formatted_output)
                successful_count += 1
                
        console.print(f"[green]批量续写完成! 成功处理{successful_count}/{len(text_files)}个文件[/green]")
        console.print(f"[green]结果保存在: {output_path}[/green]")
        
    except Exception as e:
        console.print(f"[red]批量续写失败: {e}[/red]")
        logger.error(f"批量续写失败: {e}")


@cli.command()
@click.option('--text', '-t', type=str, required=True, help='要分析的文本')
def analyze(text):
    """分析文本中的红楼梦元素"""
    try:
        continuation_system = HongLouMengContinuation()
        analysis = continuation_system.get_character_analysis(text)
        
        # 显示分析结果
        result_text = f"""
[bold]文本分析结果:[/bold]

[bold blue]人物:[/bold blue]
{', '.join(analysis['characters']) if analysis['characters'] else '未识别到红楼梦人物'}

[bold blue]地点:[/bold blue]
{', '.join(analysis['locations']) if analysis['locations'] else '未识别到红楼梦地点'}

[bold blue]对话数量:[/bold blue]
{len(analysis['dialogues'])}段对话

[bold blue]字数统计:[/bold blue]
{analysis['word_count']}字
        """
        
        console.print(Panel(result_text.strip(), title="文本分析", border_style="cyan"))
        
        # 显示对话详情
        if analysis['dialogues']:
            dialogue_text = "\n".join([
                f"{i+1}. {dialogue['content'][:50]}..." 
                for i, dialogue in enumerate(analysis['dialogues'][:5])
            ])
            console.print(Panel(dialogue_text, title="对话预览 (前5段)", border_style="magenta"))
            
    except Exception as e:
        console.print(f"[red]分析失败: {e}[/red]")
        logger.error(f"分析失败: {e}")


@cli.command()
def setup():
    """初始化项目设置"""
    try:
        # 创建必要的目录
        directories = ["data", "output", "config", "logs"]
        for dir_name in directories:
            Path(dir_name).mkdir(exist_ok=True)
            console.print(f"[green]✓[/green] 创建目录: {dir_name}")
        
        # 创建示例配置文件
        config = Config()
        console.print(f"[green]✓[/green] 创建配置文件: {config.config_path}")
        
        # 创建示例环境变量文件
        env_content = """# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# 可选：如果使用其他兼容的API服务
# OPENAI_BASE_URL=https://your-custom-api-endpoint.com/v1
"""
        
        env_path = Path(".env")
        if not env_path.exists():
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(env_content)
            console.print(f"[green]✓[/green] 创建环境变量文件: .env")
        else:
            console.print(f"[yellow]![/yellow] 环境变量文件已存在: .env")
        
        console.print(Panel(
            "[bold green]项目初始化完成![/bold green]\n\n"
            "[bold]下一步:[/bold]\n"
            "1. 编辑 .env 文件，填入你的 OpenAI API Key\n"
            "2. (可选) 将红楼梦原文放入 data/original_hongloumeng.txt\n"
            "3. 运行: python main.py continue-story --help 查看使用方法",
            title="设置完成",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(f"[red]初始化失败: {e}[/red]")
        logger.error(f"初始化失败: {e}")


@cli.command()
@click.option('--input-file', '-i', type=click.Path(exists=True), required=True, 
              help='红楼梦原文文件路径')
@click.option('--output-dir', '-o', type=click.Path(), default='data/processed', 
              help='输出目录路径')
@click.option('--dict-path', '-d', type=click.Path(), 
              help='自定义词典路径（可选）')
@click.option('--skip-tokenization', is_flag=True, 
              help='跳过分词处理')
@click.option('--skip-entity-recognition', is_flag=True, 
              help='跳过实体识别')
@click.option('--force', is_flag=True, 
              help='强制重新处理（即使输出文件已存在）')
def process_data(input_file, output_dir, dict_path, skip_tokenization, skip_entity_recognition, force):
    """完整处理红楼梦文本数据：预处理、分词、实体识别"""
    try:
        console.print(Panel.fit(
            "[bold blue]开始红楼梦数据处理[/bold blue]",
            border_style="blue"
        ))
        
        # 初始化数据处理管道
        pipeline = HongLouMengDataPipeline(
            custom_dict_path=dict_path,
            output_base_dir=output_dir
        )
        
        # 显示管道信息
        pipeline_info = pipeline.get_pipeline_info()
        console.print(f"[green]输出目录: {pipeline_info['output_base_dir']}[/green]")
        if dict_path:
            console.print(f"[green]自定义词典: {dict_path}[/green]")
        
        # 开始处理
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("数据处理中...", total=None)
            
            result = pipeline.process_complete_text(
                input_file=input_file,
                include_tokenization=not skip_tokenization,
                include_entity_recognition=not skip_entity_recognition,
                force_reprocess=force
            )
            
            progress.update(task, description="数据处理完成")
        
        # 显示处理结果
        if 'error' in result:
            console.print(f"[red]处理失败: {result['error']}[/red]")
            return
        
        # 显示统计信息
        stats_text = "[bold]处理统计:[/bold]\n"
        
        if 'preprocessing' in result['statistics']:
            stats = result['statistics']['preprocessing']
            stats_text += f"• 总字符数: {stats['total_chars']:,}\n"
            stats_text += f"• 段落数: {stats['total_paragraphs']:,}\n"
            stats_text += f"• 对话数: {stats['total_dialogues']:,}\n"
        
        if 'chapters' in result['statistics']:
            stats = result['statistics']['chapters']
            stats_text += f"• 章节数: {stats['total_chapters']}\n"
        
        if 'tokenization' in result['statistics']:
            stats = result['statistics']['tokenization']
            stats_text += f"• 总词数: {stats['total_words']:,}\n"
            stats_text += f"• 独特词汇: {stats['unique_words']:,}\n"
            stats_text += f"• 自定义词汇: {stats['custom_words_found']}\n"
        
        console.print(Panel(stats_text.strip(), title="处理统计", border_style="green"))
        
        # 显示输出文件
        files_text = "[bold]生成的文件:[/bold]\n"
        for file_type, file_path in result['output_files'].items():
            files_text += f"• {file_type}: {file_path}\n"
        
        console.print(Panel(files_text.strip(), title="输出文件", border_style="yellow"))
        
        console.print("[green]✓ 数据处理完成！[/green]")
        
    except Exception as e:
        console.print(f"[red]数据处理失败: {e}[/red]")
        logger.error(f"数据处理失败: {e}")


@cli.command()
@click.option('--input-file', '-i', type=click.Path(exists=True), required=True,
              help='要分词的文本文件')
@click.option('--output-file', '-o', type=click.Path(),
              help='分词结果输出文件')
@click.option('--dict-path', '-d', type=click.Path(),
              help='自定义词典路径')
@click.option('--mode', '-m', type=click.Choice(['default', 'search', 'all']),
              default='default', help='分词模式')
def tokenize(input_file, output_file, dict_path, mode):
    """对文本进行分词处理"""
    try:
        from data_processing import HongLouMengTokenizer
        
        console.print(Panel.fit(
            f"[bold cyan]文本分词处理[/bold cyan]\n模式: {mode}",
            border_style="cyan"
        ))
        
        # 初始化分词器
        tokenizer = HongLouMengTokenizer(dict_path)
        
        # 处理文件
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("分词处理中...", total=None)
            
            result = tokenizer.tokenize_file(input_file, output_file)
            
            progress.update(task, description="分词处理完成")
        
        # 显示结果
        analysis = result['analysis']
        
        stats_text = f"""[bold]分词统计:[/bold]
• 总词数: {analysis['word_count']:,}
• 独特词汇: {analysis['unique_words']:,}
• 自定义词汇发现: {len(analysis['custom_words_found'])}
• 人物实体: {len(analysis['entities']['persons'])}
• 地点实体: {len(analysis['entities']['locations'])}
• 对象实体: {len(analysis['entities']['objects'])}
"""
        
        console.print(Panel(stats_text.strip(), title="分词结果", border_style="green"))
        console.print(f"[green]分词结果已保存到: {result['output_file']}[/green]")
        
    except Exception as e:
        console.print(f"[red]分词处理失败: {e}[/red]")
        logger.error(f"分词处理失败: {e}")


@cli.command()
@click.option('--input-file', '-i', type=click.Path(exists=True), required=True,
              help='要进行实体识别的文本文件')
@click.option('--output-file', '-o', type=click.Path(),
              help='实体识别结果输出文件')
@click.option('--dict-path', '-d', type=click.Path(),
              help='自定义词典路径')
def recognize_entities(input_file, output_file, dict_path):
    """对文本进行实体识别"""
    try:
        from data_processing import EntityRecognizer
        
        console.print(Panel.fit(
            "[bold magenta]实体识别处理[/bold magenta]",
            border_style="magenta"
        ))
        
        # 初始化实体识别器
        recognizer = EntityRecognizer(dict_path)
        
        # 读取文件
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # 处理实体识别
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("实体识别中...", total=None)
            
            entities = recognizer.recognize_entities(text)
            stats = recognizer.get_entity_statistics(text)
            
            progress.update(task, description="实体识别完成")
        
        # 保存结果
        if output_file:
            recognizer.export_entities(text, output_file)
        
        # 显示结果
        stats_text = f"""[bold]实体识别统计:[/bold]
• 人物: {stats['entity_counts']['persons']}个
• 地点: {stats['entity_counts']['locations']}个
• 物品: {stats['entity_counts']['objects']}个
• 对话: {stats['entity_counts']['dialogues']}段
• 称谓: {stats['entity_counts']['titles']}个

[bold]实体密度（每千字）:[/bold]
• 人物: {stats['entity_density']['persons']}
• 地点: {stats['entity_density']['locations']}
"""
        
        console.print(Panel(stats_text.strip(), title="实体识别结果", border_style="green"))
        
        if output_file:
            console.print(f"[green]实体识别结果已保存到: {output_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]实体识别失败: {e}[/red]")
        logger.error(f"实体识别失败: {e}")


@cli.command()
@click.option('--chapters-dir', '-d', type=click.Path(exists=True),
              default='data/processed/chapters', help='章节文件目录')
def batch_process_chapters(chapters_dir):
    """批量处理所有章节文件"""
    try:
        from data_processing import HongLouMengDataPipeline
        
        console.print(Panel.fit(
            "[bold yellow]批量处理章节[/bold yellow]",
            border_style="yellow"
        ))
        
        # 初始化管道
        pipeline = HongLouMengDataPipeline()
        
        # 批量处理
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("批量处理章节中...", total=None)
            
            results = pipeline.batch_process_chapters()
            
            progress.update(task, description="批量处理完成")
        
        # 显示结果
        success_count = len([r for r in results if 'error' not in r])
        total_count = len(results)
        
        console.print(f"[green]批量处理完成: {success_count}/{total_count} 个章节处理成功[/green]")
        
        if success_count < total_count:
            error_count = total_count - success_count
            console.print(f"[yellow]警告: {error_count} 个章节处理失败[/yellow]")
        
    except Exception as e:
        console.print(f"[red]批量处理失败: {e}[/red]")
        logger.error(f"批量处理失败: {e}")


@cli.command()
@click.option('--context', '-c', required=True, help='续写的上下文')
@click.option('--prompt-type', '-t', type=click.Choice(['basic', 'dialogue', 'scene', 'poetry']),
              default='basic', help='提示词类型')
@click.option('--max-length', '-l', type=int, default=500, help='续写长度')
@click.option('--traditional', is_flag=True, help='使用传统提示词（不使用知识增强）')
def enhanced_continue(context, prompt_type, max_length, traditional):
    """使用知识增强功能进行续写演示"""
    console.print(Panel.fit(
        f"[bold green]知识增强续写演示[/bold green]\n"
        f"上下文: {context}\n"
        f"类型: {prompt_type}\n"
        f"长度: {max_length}字\n"
        f"模式: {'传统' if traditional else '知识增强'}",
        title="🌟 知识增强续写"
    ))
    
    try:
        # 初始化提示词模板
        prompt_templates = PromptTemplates(enable_knowledge_enhancement=not traditional)
        
        if traditional:
            console.print("[yellow]使用传统提示词模式[/yellow]")
        else:
            console.print("[green]使用知识增强模式[/green]")
            
        # 获取写作建议
        suggestions = prompt_templates.get_writing_suggestions(context)
        
        if suggestions['knowledge_enhanced']:
            console.print("\n📊 知识分析结果:")
            console.print(f"  识别人物: {suggestions['characters']}")
            console.print(f"  识别地点: {suggestions['locations']}")
            console.print(f"  建议风格: {suggestions['suggested_style']}")
            if suggestions.get('character_relationships'):
                console.print(f"  人物关系: {suggestions['character_relationships']}")
        
        # 生成增强提示词
        enhanced_prompt = prompt_templates.get_enhanced_prompt(
            context=context,
            prompt_type=prompt_type,
            max_length=max_length
        )
        
        console.print(f"\n✨ 生成的{'传统' if traditional else '知识增强'}提示词:")
        console.print(Panel(
            enhanced_prompt[:800] + "..." if len(enhanced_prompt) > 800 else enhanced_prompt,
            title="📝 提示词内容",
            expand=False
        ))
        
        console.print(f"\n📏 提示词统计:")
        console.print(f"  总长度: {len(enhanced_prompt)} 字符")
        console.print(f"  约 {len(enhanced_prompt) // 100} 百字符")
        
        if not traditional and suggestions['knowledge_enhanced']:
            console.print("\n🎯 知识增强优势:")
            console.print("  ✅ 自动识别文本中的人物和地点")
            console.print("  ✅ 提供人物关系和性格背景")
            console.print("  ✅ 建议适合的写作风格")
            console.print("  ✅ 推荐场景相关角色")
            console.print("  ✅ 包含专业词汇指导")
        
        console.print(f"\n💡 提示: 这个提示词可以直接发送给AI模型进行续写")
        
    except Exception as e:
        console.print(f"[red]知识增强续写演示失败: {e}[/red]")
        logger.error(f"知识增强续写演示失败: {e}")


@cli.command()
@click.option('--extract', is_flag=True, help='重新提取判词（如果已存在会覆盖）')
@click.option('--character', '-c', help='查询指定角色的判词')
@click.option('--report', is_flag=True, help='生成判词分析报告')
@click.option('--save-report', help='保存报告到指定文件')
def taixu_prophecy(extract, character, report, save_report):
    """太虚幻境判词提取与分析"""
    console.print(Panel.fit(
        "[bold magenta]太虚幻境判词分析系统[/bold magenta]\n"
        "从红楼梦第五回提取金陵十二钗判词\n"
        "为AI续写提供文学深度指导",
        title="🔮 太虚幻境"
    ))
    
    try:
        extractor = TaixuProphecyExtractor()
        
        # 检查是否需要提取判词
        existing_prophecies = extractor.load_prophecies()
        should_extract = extract or not existing_prophecies
        
        if should_extract:
            console.print("[yellow]开始提取太虚幻境判词...[/yellow]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("提取判词中...", total=None)
                
                # 提取判词
                prophecies = extractor.extract_prophecies_from_chapter5()
                progress.update(task, description="保存判词数据...")
                
                # 保存数据
                extractor.save_prophecies(prophecies)
                progress.update(task, description="提取完成!")
            
            console.print("[green]✅ 判词提取完成![/green]")
            
            # 显示统计信息
            main_count = len(prophecies.get("main_册", []))
            secondary_count = len(prophecies.get("副册", []))
            tertiary_count = len(prophecies.get("又副册", []))
            
            console.print(f"\n📊 提取统计:")
            console.print(f"  正册判词: [bold]{main_count}[/bold] 个")
            console.print(f"  副册判词: [bold]{secondary_count}[/bold] 个")
            console.print(f"  又副册判词: [bold]{tertiary_count}[/bold] 个")
            console.print(f"  总计: [bold]{main_count + secondary_count + tertiary_count}[/bold] 个")
        
        else:
            console.print("[green]使用已存在的判词数据[/green]")
        
        # 查询指定角色的判词
        if character:
            console.print(f"\n🔍 查询角色: [bold]{character}[/bold]")
            
            character_prophecy = extractor.get_character_prophecy(character)
            if character_prophecy:
                console.print(Panel(
                    f"**角色**: {', '.join(character_prophecy['characters'])}\n"
                    f"**册别**: {character_prophecy['册_type']}\n"
                    f"**画面**: {character_prophecy['image']['description']}\n"
                    f"**判词**: {' / '.join(character_prophecy['poem']['lines'])}\n"
                    f"**命运**: {extractor.get_fate_summary(character) or '未找到'}\n"
                    f"**象征**: {', '.join(extractor.get_symbolic_elements(character))}",
                    title=f"📜 {character}的判词",
                    expand=False
                ))
            else:
                console.print(f"[red]未找到 {character} 的判词信息[/red]")
        
        # 生成分析报告
        if report or save_report:
            console.print("\n📝 生成判词分析报告...")
            
            report_content = extractor.generate_prophecy_report()
            
            if save_report:
                # 保存报告到文件
                report_path = Path(save_report)
                report_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                
                console.print(f"[green]报告已保存到: {report_path}[/green]")
            
            if report:
                # 显示报告内容（截取前1000字符）
                display_content = report_content[:1000] + "..." if len(report_content) > 1000 else report_content
                console.print(Panel(
                    display_content,
                    title="📊 判词分析报告",
                    expand=False
                ))
        
        # 显示一些示例查询建议
        if not character and not report and not save_report:
            console.print("\n💡 使用建议:")
            console.print("  查看林黛玉判词: [bold]python main.py taixu-prophecy -c 林黛玉[/bold]")
            console.print("  查看薛宝钗判词: [bold]python main.py taixu-prophecy -c 薛宝钗[/bold]")
            console.print("  生成分析报告: [bold]python main.py taixu-prophecy --report[/bold]")
            console.print("  保存分析报告: [bold]python main.py taixu-prophecy --save-report reports/prophecy.md[/bold]")
            console.print("  重新提取判词: [bold]python main.py taixu-prophecy --extract[/bold]")
        
        console.print(f"\n🎭 太虚幻境判词系统已准备就绪！")
        console.print("这些判词将为AI续写提供深层的文学指导和命运一致性检验。")
        
    except FileNotFoundError as e:
        console.print(f"[red]文件未找到: {e}[/red]")
        console.print("请确保 data/processed/chapters/005.md 文件存在")
        logger.error(f"文件未找到: {e}")
    except Exception as e:
        console.print(f"[red]太虚幻境分析失败: {e}[/red]")
        logger.error(f"太虚幻境分析失败: {e}")


@cli.command()
@click.option('--text', '-t', required=True, help='要检验的续写文本')
@click.option('--characters', '-c', help='指定检查的角色（逗号分隔）')
@click.option('--detailed', is_flag=True, help='生成详细报告')
@click.option('--save-report', help='保存报告到指定文件')
@click.option('--guidance', is_flag=True, help='显示命运指导建议')
def fate_check(text, characters, detailed, save_report, guidance):
    """命运一致性检验 - 基于太虚幻境判词验证续写内容"""
    console.print(Panel.fit(
        f"[bold cyan]命运一致性检验系统[/bold cyan]\n"
        f"基于太虚幻境判词验证续写内容的一致性\n"
        f"检测违背原著设定的内容并提供指导建议",
        title="🎭 命运检验"
    ))
    
    try:
        # 初始化检验器
        checker = FateConsistencyChecker()
        
        # 解析角色参数
        character_list = None
        if characters:
            character_list = [char.strip() for char in characters.split(',')]
            console.print(f"[yellow]指定检查角色: {', '.join(character_list)}[/yellow]")
        
        console.print(f"\n📝 检验文本:")
        console.print(Panel(
            text[:200] + "..." if len(text) > 200 else text,
            title="续写内容",
            expand=False
        ))
        
        # 进行一致性检验
        console.print("\n🔍 正在进行命运一致性检验...")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("分析中...", total=None)
            
            # 执行检验
            score = checker.check_consistency(text, character_list)
            progress.update(task, description="检验完成!")
        
        # 显示评分结果
        score_emoji = "🎉" if score.overall_score >= 90 else "✅" if score.overall_score >= 70 else "⚠️" if score.overall_score >= 50 else "❌"
        console.print(f"\n📊 总体评分: {score_emoji} [bold]{score.overall_score}/100[/bold]")
        
        # 显示角色评分
        if score.character_scores:
            console.print("\n👥 角色一致性评分:")
            for character, char_score in score.character_scores.items():
                char_emoji = "✅" if char_score >= 80 else "⚠️" if char_score >= 60 else "❌"
                console.print(f"  {char_emoji} {character}: [bold]{char_score}/100[/bold]")
        
        # 显示方面评分
        if score.aspect_scores:
            console.print("\n📈 各方面评分:")
            for aspect, aspect_score in score.aspect_scores.items():
                aspect_emoji = "✅" if aspect_score >= 80 else "⚠️" if aspect_score >= 60 else "❌"
                console.print(f"  {aspect_emoji} {aspect}: {aspect_score}/100")
        
        # 显示检测到的问题
        if score.violations:
            console.print("\n🚨 检测到的问题:")
            
            critical_violations = [v for v in score.violations if v.severity == "critical"]
            warning_violations = [v for v in score.violations if v.severity == "warning"]
            suggestion_violations = [v for v in score.violations if v.severity == "suggestion"]
            
            if critical_violations:
                console.print("\n  ❌ [bold red]严重问题[/bold red]:")
                for violation in critical_violations:
                    console.print(f"    • {violation.character}: {violation.description}")
            
            if warning_violations:
                console.print("\n  ⚠️ [bold yellow]警告事项[/bold yellow]:")
                for violation in warning_violations:
                    console.print(f"    • {violation.character}: {violation.description}")
            
            if suggestion_violations:
                console.print("\n  💡 [bold blue]优化建议[/bold blue]:")
                for violation in suggestion_violations:
                    console.print(f"    • {violation.character}: {violation.description}")
        else:
            console.print("\n✨ [green]未发现明显问题，续写内容与判词预言基本一致！[/green]")
        
        # 显示改进建议
        if score.recommendations:
            console.print("\n📋 改进建议:")
            for i, recommendation in enumerate(score.recommendations, 1):
                console.print(f"  {i}. {recommendation}")
        
        # 显示命运指导
        if guidance and score.character_scores:
            console.print("\n🔮 命运指导建议:")
            for character in score.character_scores.keys():
                fate_guidance = checker.get_fate_guidance(character, text)
                if fate_guidance:
                    console.print(Panel(
                        f"**判词暗示**: {fate_guidance.prophecy_hint}\n"
                        f"**建议发展**: {fate_guidance.suggested_development}\n"
                        f"**象征元素**: {', '.join(fate_guidance.symbolic_elements[:3])}\n"
                        f"**情感基调**: {fate_guidance.emotional_tone}",
                        title=f"🎭 {character}的命运指导",
                        expand=False
                    ))
        
        # 保存详细报告
        if save_report or detailed:
            report_content = checker.generate_consistency_report(score, detailed=True)
            
            if save_report:
                report_path = Path(save_report)
                report_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                
                console.print(f"\n[green]详细报告已保存到: {report_path}[/green]")
            
            if detailed:
                console.print("\n📄 详细报告:")
                console.print(Panel(
                    report_content[:1500] + "..." if len(report_content) > 1500 else report_content,
                    title="命运一致性检验详细报告",
                    expand=False
                ))
        
        # 评分等级说明
        console.print("\n📚 评分等级说明:")
        console.print("  🎉 90-100分: 完全符合判词预言")
        console.print("  ✅ 70-89分: 基本符合，轻微不一致")
        console.print("  ⚠️ 50-69分: 部分符合，存在问题")
        console.print("  ❌ 50分以下: 严重违背判词预言")
        
        # 使用建议
        if not guidance and not detailed and not save_report:
            console.print("\n💡 使用建议:")
            console.print("  查看命运指导: [bold]python main.py fate-check -t '文本' --guidance[/bold]")
            console.print("  生成详细报告: [bold]python main.py fate-check -t '文本' --detailed[/bold]")
            console.print("  保存分析报告: [bold]python main.py fate-check -t '文本' --save-report reports/fate.md[/bold]")
            console.print("  指定检查角色: [bold]python main.py fate-check -t '文本' -c '林黛玉,薛宝钗'[/bold]")
        
        console.print(f"\n🎭 命运一致性检验完成！")
        
    except FileNotFoundError as e:
        console.print(f"[red]文件未找到: {e}[/red]")
        console.print("请确保已运行 python main.py taixu-prophecy --extract 提取判词数据")
        logger.error(f"文件未找到: {e}")
    except Exception as e:
        console.print(f"[red]命运一致性检验失败: {e}[/red]")
        logger.error(f"命运一致性检验失败: {e}")


# ============================================================================
# RAG智能检索系统命令
# ============================================================================

@cli.group()
def rag():
    """RAG智能检索系统 - 基于Qwen3向量化的语义检索"""
    pass


@rag.command()
@click.option('--reset', is_flag=True, help='重置现有向量数据库')
@click.option('--api-key', help='DashScope API密钥')
@click.option('--chunk-strategy', default='semantic', 
              type=click.Choice(['semantic', 'paragraph', 'chapter', 'hybrid']),
              help='文本分块策略')
@click.option('--chunk-size', default=512, help='分块大小')
@click.option('--batch-size', default=32, help='批处理大小')
def build(reset, api_key, chunk_strategy, chunk_size, batch_size):
    """构建RAG知识库 - 处理章节文本并创建向量索引"""
    try:
        console.print(Panel.fit("🚀 RAG知识库构建", style="bold green"))
        
        if api_key:
            import os
            os.environ['DASHSCOPE_API_KEY'] = api_key
            console.print("✅ API密钥已设置")
        
        # 创建RAG管道
        pipeline = create_rag_pipeline(
            chunk_strategy=chunk_strategy,
            chunk_config={'chunk_size': chunk_size},
            embedding_config={'batch_size': batch_size}
        )
        
        console.print(f"📋 配置信息:")
        console.print(f"  分块策略: {chunk_strategy}")
        console.print(f"  分块大小: {chunk_size}")
        console.print(f"  批处理大小: {batch_size}")
        
        # 构建知识库
        console.print(f"\n🔨 开始构建知识库...")
        stats = pipeline.build_knowledge_base(reset_existing=reset)
        
        # 显示构建结果
        console.print(f"\n✅ 知识库构建完成!")
        console.print(f"📊 构建统计:")
        console.print(f"  处理文档: {stats['documents_processed']} 个")
        console.print(f"  文本块数: {stats['chunks_created']} 个")
        console.print(f"  向量数量: {stats['embeddings_generated']} 个")
        console.print(f"  处理时间: {stats['processing_time']:.2f} 秒")
        
        if stats.get('errors'):
            console.print(f"⚠️ 错误数量: {len(stats['errors'])}")
        
        # 显示数据库统计
        db_stats = stats['database_stats']
        console.print(f"\n📈 数据库统计:")
        console.print(f"  总文档数: {db_stats['total_documents']}")
        console.print(f"  存储路径: {db_stats['db_path']}")
        
    except Exception as e:
        console.print(f"[red]知识库构建失败: {e}[/red]")
        logger.error(f"知识库构建失败: {e}")


@rag.command()
@click.option('--query', '-q', required=True, help='检索查询文本')
@click.option('--type', 'search_type', default='hybrid',
              type=click.Choice(['semantic', 'text', 'hybrid', 'auto']),
              help='检索类型')
@click.option('--results', '-n', default=5, help='返回结果数量')
@click.option('--characters', '-c', help='人物过滤（逗号分隔）')
@click.option('--semantic-weight', default=0.7, help='语义检索权重（hybrid模式）')
@click.option('--text-weight', default=0.3, help='文本检索权重（hybrid模式）')
@click.option('--threshold', default=0.7, help='相似度阈值')
def search(query, search_type, results, characters, semantic_weight, text_weight, threshold):
    """RAG智能检索 - 语义/文本/混合检索"""
    try:
        console.print(Panel.fit(f"🔍 RAG智能检索: {search_type.upper()}", style="bold blue"))
        
        # 创建RAG管道
        pipeline = create_rag_pipeline()
        
        # 处理人物过滤
        character_filter = None
        if characters:
            character_filter = [c.strip() for c in characters.split(',')]
            console.print(f"👥 人物过滤: {character_filter}")
        
        console.print(f"🔎 查询: {query}")
        console.print(f"📊 参数: 类型={search_type}, 数量={results}, 阈值={threshold}")
        
        # 执行检索
        search_results = pipeline.search(
            query=query,
            search_type=search_type,
            n_results=results,
            character_filter=character_filter,
            semantic_weight=semantic_weight,
            text_weight=text_weight
        )
        
        # 显示结果
        console.print(f"\n📋 检索结果 ({len(search_results['documents'])} 个):")
        
        for i, (doc, sim, meta) in enumerate(zip(
            search_results['documents'],
            search_results['similarities'], 
            search_results['metadatas']
        )):
            console.print(f"\n📄 结果 {i+1}:")
            console.print(f"  📊 相似度: {sim:.3f}")
            
            if meta.get('characters'):
                console.print(f"  👥 人物: {', '.join(meta['characters'])}")
            
            if meta.get('source_id'):
                console.print(f"  📖 来源: {meta['source_id']}")
            
            # 文本预览
            preview = doc[:200] + "..." if len(doc) > 200 else doc
            console.print(f"  📝 内容: {preview}")
            
            # 混合检索显示详细分数
            if search_type == 'hybrid' and 'semantic_scores' in search_results:
                sem_score = search_results['semantic_scores'][i]
                text_score = search_results['text_scores'][i]
                console.print(f"    🔍 语义: {sem_score:.3f} | 📝 文本: {text_score:.3f}")
        
        if not search_results['documents']:
            console.print("❌ 未找到匹配的结果，建议：")
            console.print("  - 降低相似度阈值")
            console.print("  - 尝试不同的检索类型")
            console.print("  - 检查查询内容是否准确")
            
    except Exception as e:
        console.print(f"[red]检索失败: {e}[/red]")
        logger.error(f"检索失败: {e}")


@rag.command()
@click.option('--query', default='宝玉和黛玉的关系', help='测试查询')
def test(query):
    """快速测试RAG系统"""
    try:
        console.print(Panel.fit("🧪 RAG系统快速测试", style="bold magenta"))
        
        # 创建RAG管道
        pipeline = create_rag_pipeline()
        
        # 执行快速测试
        pipeline.quick_test(query)
        
    except Exception as e:
        console.print(f"[red]测试失败: {e}[/red]")
        logger.error(f"测试失败: {e}")


@rag.command()
@click.option('--output-dir', default='exports/rag_export', help='导出目录')
def export(output_dir):
    """导出RAG知识库"""
    try:
        console.print(Panel.fit("📦 导出RAG知识库", style="bold cyan"))
        
        # 创建RAG管道
        pipeline = create_rag_pipeline()
        
        # 导出知识库
        pipeline.export_knowledge_base(output_dir)
        
        console.print(f"✅ 知识库已导出到: {output_dir}")
        
    except Exception as e:
        console.print(f"[red]导出失败: {e}[/red]")
        logger.error(f"导出失败: {e}")


@rag.command()
def status():
    """查看RAG系统状态"""
    try:
        console.print(Panel.fit("📊 RAG系统状态", style="bold yellow"))
        
        # 创建RAG管道
        pipeline = create_rag_pipeline()
        
        # 获取系统状态
        status_info = pipeline.get_system_status()
        
        console.print("🔧 管道配置:")
        pipeline_config = status_info['pipeline_config']
        console.print(f"  向量模型: {pipeline_config['embedding_model']}")
        console.print(f"  分块策略: {pipeline_config['chunk_strategy']}")
        console.print(f"  分块大小: {pipeline_config['chunk_size']}")
        console.print(f"  数据库路径: {pipeline_config['db_path']}")
        
        console.print("\n📈 数据库统计:")
        db_stats = status_info['database_stats']
        console.print(f"  总文档数: {db_stats['total_documents']}")
        console.print(f"  距离度量: {db_stats['distance_metric']}")
        
        if db_stats.get('top_characters'):
            console.print("\n👥 主要人物分布:")
            for char, count in db_stats['top_characters'][:5]:
                console.print(f"  {char}: {count} 个文本块")
        
        console.print(f"\n📝 文本块统计:")
        console.print(f"  对话块: {db_stats.get('dialogue_chunks', 0)}")
        console.print(f"  章节头: {db_stats.get('chapter_chunks', 0)}")
        
    except Exception as e:
        console.print(f"[red]状态查询失败: {e}[/red]")
        logger.error(f"状态查询失败: {e}")


if __name__ == "__main__":
    cli()