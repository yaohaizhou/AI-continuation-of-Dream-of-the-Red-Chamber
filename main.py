#!/usr/bin/env python3
"""
AI续写红楼梦 - 主程序入口
基于LangChain的红楼梦续写系统
"""

import asyncio
import re
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
from knowledge_enhancement import EnhancedPrompter, TaixuProphecyExtractor, FateConsistencyChecker, create_symbolic_imagery_advisor
from rag_retrieval import RAGPipeline, create_rag_pipeline
from long_text_management import ChapterPlanner, ChapterInfoTransfer, create_chapter_info_transfer, ProgressTracker, ProjectStatus, ChapterStatus, create_progress_tracker

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
@click.option('--test-single', is_flag=True, help='只处理001.md文件用于测试')
@click.option('--api-key', help='DashScope API密钥')
@click.option('--chunk-strategy', default='semantic', 
              type=click.Choice(['semantic', 'paragraph', 'chapter', 'hybrid']),
              help='文本分块策略')
@click.option('--chunk-size', default=512, help='分块大小')
@click.option('--batch-size', default=32, help='批处理大小')
def build(reset, test_single, api_key, chunk_strategy, chunk_size, batch_size):
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
        if test_single:
            console.print(f"\n🔨 测试模式：只处理 001.md...")
        else:
            console.print(f"\n🔨 开始构建知识库...")
        stats = pipeline.build_knowledge_base(reset_existing=reset, test_single=test_single)
        
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


@cli.command()
@click.option('--character', '-c', help='指定角色名称')
@click.option('--scene', '-s', help='场景上下文描述')
@click.option('--tone', '-t', help='情感基调 (悲叹/哀愁/凄美/欢快/壮丽)')
@click.option('--style', help='文学风格 (诗词/对话/场景/抒情)')
@click.option('--text', help='待增强的文本内容')
@click.option('--search', help='搜索包含指定象征元素的角色')
@click.option('--stats', is_flag=True, help='显示象征意象建议器统计信息')
def symbolic_suggest(character, scene, tone, style, text, search, stats):
    """象征意象建议器 - 基于太虚幻境判词推荐象征元素"""
    console.print(Panel.fit(
        f"[bold magenta]象征意象建议器[/bold magenta]\n"
        f"基于太虚幻境判词数据，为续写提供智能的象征意象推荐\n"
        f"支持角色专属象征、情境感知推荐、文学手法建议等功能",
        title="🎨 象征意象"
    ))
    
    try:
        # 初始化象征意象建议器
        advisor = create_symbolic_imagery_advisor()
        
        # 显示统计信息
        if stats:
            console.print("\n📊 统计信息:")
            statistics = advisor.get_statistics()
            console.print(Panel(
                f"角色数量: {statistics['total_characters']}\n"
                f"象征元素数量: {statistics['total_symbols']}\n"
                f"角色列表: {', '.join(statistics['character_list'])}\n"
                f"最常见象征: {', '.join([f'{sym}({cnt})' for sym, cnt in statistics['most_common_symbols']])}\n"
                f"情感基调: {', '.join(statistics['emotional_tones'])}",
                title="系统统计"
            ))
            return
        
        # 搜索象征元素
        if search:
            console.print(f"\n🔍 搜索象征元素: {search}")
            results = advisor.search_symbols(search)
            if results:
                for symbol, characters_list in results.items():
                    console.print(f"• {symbol}: {', '.join(characters_list)}")
            else:
                console.print("[yellow]未找到相关象征元素[/yellow]")
            return
        
        # 查看角色象征信息
        if character and not (scene or tone or style or text):
            console.print(f"\n👤 查看角色象征信息: {character}")
            char_info = advisor.get_character_symbols(character)
            if char_info['found']:
                console.print(Panel(
                    f"象征元素: {', '.join(char_info['symbols'])}\n"
                    f"视觉隐喻: {', '.join(char_info['metaphors'])}\n"
                    f"情感基调: {char_info['emotional_tone']}\n"
                    f"命运主题: {char_info['fate_theme']}\n"
                    f"文学手法: {', '.join(char_info['literary_devices'])}",
                    title=f"{character}的象征信息"
                ))
            else:
                console.print(f"[yellow]{char_info['message']}[/yellow]")
            return
        
        # 文学氛围增强
        if text:
            console.print(f"\n📖 文学氛围增强:")
            console.print(f"原文: {text}")
            enhancement = advisor.enhance_literary_atmosphere(text, character)
            console.print(Panel(
                f"检测到的角色: {', '.join(enhancement['detected_characters']) if enhancement['detected_characters'] else '无'}\n"
                f"主要角色: {enhancement['main_character'] or '无'}\n\n"
                f"增强建议:\n" + '\n'.join([f"• {suggestion}" for suggestion in enhancement['enhancement_suggestions']]),
                title="文学氛围增强建议"
            ))
            return
        
        # 象征意象推荐
        console.print(f"\n🎨 象征意象推荐:")
        if character:
            console.print(f"角色: {character}")
        if scene:
            console.print(f"场景: {scene}")
        if tone:
            console.print(f"情感基调: {tone}")
        if style:
            console.print(f"文学风格: {style}")
        
        recommendation = advisor.recommend_symbols(
            character=character,
            scene_context=scene,
            emotional_tone=tone,
            literary_style=style
        )
        
        console.print(Panel(
            f"主要象征: {', '.join(recommendation.primary_symbols)}\n"
            f"次要象征: {', '.join(recommendation.secondary_symbols)}\n"
            f"情感基调: {recommendation.emotional_tone}\n"
            f"文学手法: {', '.join(recommendation.literary_devices)}\n"
            f"使用语境: {recommendation.usage_context}\n"
            f"推荐理由: {recommendation.explanation}\n"
            f"置信度: {recommendation.confidence:.2f}",
            title="象征意象推荐",
            border_style="magenta"
        ))
        
    except Exception as e:
        console.print(f"[red]象征建议失败: {e}[/red]")
        logger.error(f"象征建议失败: {e}")


@cli.command()
@click.option('--generate', is_flag=True, help='生成新的40回章节规划')
@click.option('--load', is_flag=True, help='加载现有的章节规划')
@click.option('--chapter', '-c', type=int, help='查看指定章节的规划')
@click.option('--report', is_flag=True, help='生成规划报告')
@click.option('--save-report', help='保存报告到指定文件')
@click.option('--save-plan', help='保存规划到指定文件')
@click.option('--timeline', is_flag=True, help='显示角色命运时间线')
@click.option('--themes', is_flag=True, help='显示主题分布')
@click.option('--character-arcs', help='查看指定角色的章节弧线')
def plan_chapters(generate, load, chapter, report, save_report, save_plan, timeline, themes, character_arcs):
    """章节规划器 - 基于太虚幻境判词制定后40回规划"""
    console.print(Panel.fit(
        f"[bold blue]红楼梦后40回章节规划器[/bold blue]\n"
        f"基于太虚幻境判词数据，智能规划第81-120回的详细章节安排\n"
        f"包括人物命运、情节发展、时间线设计等完整规划",
        title="📋 章节规划"
    ))
    
    try:
        # 初始化章节规划器
        planner = ChapterPlanner()
        
        # 生成新规划
        if generate:
            console.print("\n🚀 开始生成40回章节规划...")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("分析太虚幻境判词...", total=None)
                
                # 生成总体规划
                overall_plan = planner.generate_overall_plan()
                progress.update(task, description="保存规划数据...")
                
                # 保存规划
                save_path = save_plan if save_plan else None
                planner.save_plan(overall_plan, save_path)
                progress.update(task, description="规划生成完成!")
            
            console.print("[green]✅ 章节规划生成完成![/green]")
            
            # 显示统计信息
            console.print(f"\n📊 规划统计:")
            console.print(f"  规划章节: [bold]{len(overall_plan.chapters)}[/bold] 回 (第81-120回)")
            console.print(f"  预估字数: [bold]{overall_plan.total_estimated_words:,}[/bold] 字")
            console.print(f"  平均章节: [bold]{overall_plan.total_estimated_words // len(overall_plan.chapters):,}[/bold] 字/回")
            console.print(f"  关键转折: [bold]{len(overall_plan.critical_turning_points)}[/bold] 个")
            
            # 命运覆盖情况
            covered_count = sum(1 for covered in overall_plan.fate_coverage.values() if covered)
            total_count = len(overall_plan.fate_coverage)
            console.print(f"  命运覆盖: [bold]{covered_count}/{total_count}[/bold] 个角色")
            
        # 加载现有规划
        elif load or chapter or report or timeline or themes or character_arcs:
            console.print("[yellow]加载现有章节规划...[/yellow]")
            overall_plan = planner.load_plan()
            
            if not overall_plan:
                console.print("[red]❌ 未找到现有规划，请先运行 --generate 生成规划[/red]")
                return
            
            console.print("[green]✅ 规划加载成功![/green]")
            
            # 查看指定章节
            if chapter:
                if 81 <= chapter <= 120:
                    chapter_plan = planner.get_chapter_plan(chapter, overall_plan)
                    if chapter_plan:
                        console.print(f"\n📖 第{chapter}回规划详情:")
                        
                        # 基本信息
                        info_text = f"""[bold]标题:[/bold] {chapter_plan.title}
[bold]主题:[/bold] {chapter_plan.theme.value}
[bold]优先级:[/bold] {chapter_plan.priority.value}
[bold]预估字数:[/bold] {chapter_plan.estimated_length:,} 字
[bold]难度等级:[/bold] {chapter_plan.difficulty_level}
[bold]命运符合度:[/bold] {chapter_plan.fate_compliance:.1%}
[bold]情感基调:[/bold] {chapter_plan.emotional_tone}

[bold]主要人物:[/bold] {', '.join(chapter_plan.main_characters)}
[bold]次要人物:[/bold] {', '.join(chapter_plan.supporting_characters)}

[bold]情节梗概:[/bold]
{chapter_plan.plot_summary}

[bold]象征意象:[/bold] {', '.join(chapter_plan.symbolic_imagery)}
[bold]文学手法:[/bold] {', '.join(chapter_plan.literary_devices)}"""
                        
                        console.print(Panel(info_text, title=f"第{chapter}回", expand=False))
                        
                        # 关键事件
                        if chapter_plan.key_events:
                            console.print(f"\n🎭 关键事件:")
                            for i, event in enumerate(chapter_plan.key_events, 1):
                                console.print(f"  {i}. {event.character}: {event.description}")
                                console.print(f"     判词引用: {event.prophecy_reference}")
                    else:
                        console.print(f"[red]未找到第{chapter}回的规划[/red]")
                else:
                    console.print(f"[red]章节号必须在81-120之间[/red]")
            
            # 显示角色命运时间线
            if timeline:
                console.print(f"\n📅 角色命运时间线:")
                for character, chapter_num in sorted(overall_plan.fate_timeline.items(), key=lambda x: x[1]):
                    console.print(f"  第{chapter_num:3d}回: {character}")
            
            # 显示主题分布
            if themes:
                console.print(f"\n🎭 主题分布:")
                for theme, chapter_nums in overall_plan.thematic_structure.items():
                    console.print(f"  {theme.value}: {len(chapter_nums)} 回 - {chapter_nums}")
            
            # 显示角色弧线
            if character_arcs:
                if character_arcs in overall_plan.character_arcs:
                    chapters = overall_plan.character_arcs[character_arcs]
                    console.print(f"\n👤 {character_arcs} 的章节弧线:")
                    console.print(f"  出现章节: {chapters}")
                    console.print(f"  总计: {len(chapters)} 回")
                    
                    # 查找命运实现章节
                    fate_chapter = overall_plan.fate_timeline.get(character_arcs)
                    if fate_chapter:
                        console.print(f"  命运实现: 第{fate_chapter}回")
                else:
                    console.print(f"[red]未找到角色 '{character_arcs}' 的弧线[/red]")
                    available_chars = list(overall_plan.character_arcs.keys())[:10]
                    console.print(f"[yellow]可用角色: {', '.join(available_chars)}...[/yellow]")
        
        # 生成规划报告
        if report or save_report:
            if 'overall_plan' not in locals():
                overall_plan = planner.load_plan()
                if not overall_plan:
                    console.print("[red]❌ 未找到规划数据，请先生成规划[/red]")
                    return
            
            console.print("\n📝 生成章节规划报告...")
            
            report_content = planner.generate_planning_report(overall_plan)
            
            if save_report:
                # 保存报告到文件
                report_path = Path(save_report)
                report_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                
                console.print(f"[green]报告已保存到: {report_path}[/green]")
            
            if report:
                # 显示报告内容（截取前1500字符）
                display_content = report_content[:1500] + "..." if len(report_content) > 1500 else report_content
                console.print(Panel(
                    display_content,
                    title="📊 章节规划报告",
                    expand=False
                ))
        
        # 默认显示使用建议
        if not any([generate, load, chapter, report, timeline, themes, character_arcs, save_report]):
            console.print("\n💡 使用建议:")
            console.print("  生成新规划: [bold]python main.py plan-chapters --generate[/bold]")
            console.print("  查看第81回: [bold]python main.py plan-chapters -c 81[/bold]")
            console.print("  查看时间线: [bold]python main.py plan-chapters --timeline[/bold]")
            console.print("  查看主题分布: [bold]python main.py plan-chapters --themes[/bold]")
            console.print("  查看角色弧线: [bold]python main.py plan-chapters --character-arcs 林黛玉[/bold]")
            console.print("  生成报告: [bold]python main.py plan-chapters --report[/bold]")
            console.print("  保存报告: [bold]python main.py plan-chapters --save-report reports/planning.md[/bold]")
        
        console.print(f"\n📋 章节规划器已准备就绪！")
        console.print("基于太虚幻境判词的智能规划将为后40回续写提供结构化指导。")
        
    except Exception as e:
        console.print(f"[red]章节规划失败: {e}[/red]")
        logger.error(f"章节规划失败: {e}")


@cli.command()
@click.option('--extract', '-e', type=int, help='从指定章节提取状态信息')
@click.option('--chapter-file', '-f', help='指定章节文件路径')
@click.option('--transfer', '-t', help='传递信息到下一章节，格式：from_chapter,to_chapter')
@click.option('--check-consistency', '-c', help='检查章节一致性，格式：start_chapter,end_chapter')
@click.option('--save-state', '-s', type=int, help='保存指定章节的状态')
@click.option('--load-state', '-l', type=int, help='加载指定章节的状态')
@click.option('--summary', help='显示信息传递摘要，格式：from_chapter,to_chapter')
@click.option('--list-states', is_flag=True, help='列出所有保存的章节状态')
def chapter_transfer(extract, chapter_file, transfer, check_consistency, 
                    save_state, load_state, summary, list_states):
    """章节信息传递机制 - 管理章节间的状态传递和一致性"""
    console.print(Panel.fit(
        f"[bold cyan]章节间信息传递机制[/bold cyan]\n"
        f"处理章节之间的状态传递、信息继承和一致性维护\n"
        f"确保40回续写的连贯性和逻辑一致性",
        title="🔄 信息传递"
    ))
    
    try:
        # 初始化章节信息传递机制
        transfer_manager = create_chapter_info_transfer()
        
        # 提取章节状态
        if extract:
            chapter_num = extract
            if not chapter_file:
                chapter_file = f"data/processed/chapters/{chapter_num:03d}.md"
            
            console.print(f"\n📊 提取第{chapter_num}回状态信息...")
            
            # 检查文件是否存在
            if not Path(chapter_file).exists():
                console.print(f"[red]错误：章节文件不存在 {chapter_file}[/red]")
                return
            
            # 读取章节内容
            with open(chapter_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取章节标题
            title_match = re.match(r'^#\s*(.+)', content)
            chapter_title = title_match.group(1) if title_match else f"第{chapter_num}回"
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("分析章节内容...", total=None)
                
                # 提取状态信息
                chapter_state = transfer_manager.extract_chapter_state(
                    chapter_num, content, chapter_title
                )
                
                progress.update(task, description="保存状态信息...")
                
                # 保存状态
                transfer_manager.save_chapter_state(chapter_state)
                
                progress.update(task, description="状态提取完成!")
            
            # 显示提取结果
            console.print("[green]✅ 状态提取完成![/green]")
            console.print(f"\n📋 提取统计:")
            console.print(f"  人物数量: [bold]{len(chapter_state.character_states)}[/bold] 个")
            console.print(f"  情节线程: [bold]{len(chapter_state.plot_threads)}[/bold] 个")
            console.print(f"  关键对话: [bold]{len(chapter_state.key_dialogues)}[/bold] 段")
            console.print(f"  未解决问题: [bold]{len(chapter_state.unresolved_questions)}[/bold] 个")
            
            # 显示主要人物状态
            if chapter_state.character_states:
                console.print(f"\n👤 主要人物状态:")
                for name, state in list(chapter_state.character_states.items())[:5]:
                    console.print(f"  [bold]{name}[/bold]: {state.status.value} - {state.location}")
        
        # 信息传递
        if transfer:
            try:
                from_ch, to_ch = map(int, transfer.split(','))
            except ValueError:
                console.print("[red]错误：传递格式应为 'from_chapter,to_chapter'，如 '81,82'[/red]")
                return
            
            console.print(f"\n🔄 传递第{from_ch}回信息到第{to_ch}回...")
            
            # 加载源章节状态
            from_state = transfer_manager.load_chapter_state(from_ch)
            if not from_state:
                console.print(f"[red]错误：无法加载第{from_ch}回状态，请先提取状态信息[/red]")
                return
            
            # 获取下一章节规划（如果存在）
            try:
                planner = ChapterPlanner()
                plan = planner.load_plan()
                next_plan = planner.get_chapter_plan(to_ch, plan) if plan else {}
            except:
                next_plan = {}
            
            # 生成传递指导
            guidance = transfer_manager.pass_info_to_next(from_state, next_plan)
            
            console.print("[green]✅ 信息传递完成![/green]")
            
            # 显示传递指导
            console.print(Panel(
                f"传递章节: 第{from_ch}回 → 第{to_ch}回\n"
                f"继承人物: {len(guidance.get('inherited_character_states', {}))} 个\n"
                f"持续情节: {len(guidance.get('continuing_plot_threads', {}))} 个\n"
                f"写作指导: {len(guidance.get('writing_guidelines', []))} 条",
                title="📋 传递摘要",
                border_style="cyan"
            ))
            
            # 显示写作指导
            if guidance.get('writing_guidelines'):
                console.print(f"\n📝 写作指导:")
                for guideline in guidance['writing_guidelines'][:5]:
                    console.print(f"  • {guideline}")
        
        # 一致性检查
        if check_consistency:
            try:
                start_ch, end_ch = map(int, check_consistency.split(','))
            except ValueError:
                console.print("[red]错误：检查格式应为 'start_chapter,end_chapter'，如 '81,85'[/red]")
                return
            
            console.print(f"\n🔍 检查第{start_ch}-{end_ch}回一致性...")
            
            # 加载章节状态
            chapter_states = []
            for ch_num in range(start_ch, end_ch + 1):
                state = transfer_manager.load_chapter_state(ch_num)
                if state:
                    chapter_states.append(state)
            
            if len(chapter_states) < 2:
                console.print("[red]错误：需要至少2个章节的状态信息进行一致性检查[/red]")
                return
            
            # 执行一致性检查
            issues = transfer_manager.maintain_consistency(chapter_states)
            
            if issues:
                console.print(f"[yellow]⚠️  发现 {len(issues)} 个一致性问题:[/yellow]")
                for i, issue in enumerate(issues[:10], 1):
                    console.print(f"  {i}. {issue}")
            else:
                console.print("[green]✅ 未发现一致性问题![/green]")
        
        # 显示传递摘要
        if summary:
            try:
                from_ch, to_ch = map(int, summary.split(','))
            except ValueError:
                console.print("[red]错误：摘要格式应为 'from_chapter,to_chapter'，如 '81,82'[/red]")
                return
            
            summary_data = transfer_manager.get_transfer_summary(from_ch, to_ch)
            
            if 'error' in summary_data:
                console.print(f"[red]{summary_data['error']}[/red]")
            else:
                console.print(Panel(
                    f"传递时间: {summary_data['transfer_timestamp'][:19]}\n"
                    f"源章节: 第{summary_data['from_chapter']}回\n"
                    f"目标章节: 第{summary_data['to_chapter']}回\n"
                    f"人物数量: {summary_data['character_count']}\n"
                    f"情节线程: {summary_data['plot_thread_count']}\n"
                    f"未解决问题: {summary_data['unresolved_count']}",
                    title="📊 传递摘要",
                    border_style="blue"
                ))
        
        # 保存状态
        if save_state:
            console.print(f"[yellow]提示：状态在提取时已自动保存到 data/processed/chapter_states/[/yellow]")
        
        # 加载状态
        if load_state:
            state = transfer_manager.load_chapter_state(load_state)
            if state:
                console.print(f"[green]✅ 成功加载第{load_state}回状态[/green]")
                console.print(f"章节标题: {state.get('chapter_title', '未知')}")
                console.print(f"人物数量: {len(state.get('character_states', {}))}")
            else:
                console.print(f"[red]无法加载第{load_state}回状态[/red]")
        
        # 列出所有状态
        if list_states:
            states_dir = Path("data/processed/chapter_states")
            if states_dir.exists():
                state_files = list(states_dir.glob("chapter_*_state.json"))
                if state_files:
                    console.print(f"\n📁 已保存的章节状态 ({len(state_files)} 个):")
                    for file in sorted(state_files):
                        chapter_num = re.search(r'chapter_(\d+)_state', file.name)
                        if chapter_num:
                            console.print(f"  • 第{int(chapter_num.group(1))}回")
                else:
                    console.print("[yellow]暂无保存的章节状态[/yellow]")
            else:
                console.print("[yellow]状态目录不存在[/yellow]")
        
        # 默认显示使用建议
        if not any([extract, transfer, check_consistency, summary, save_state, load_state, list_states]):
            console.print("\n💡 使用建议:")
            console.print("  提取状态: [bold]python main.py chapter-transfer -e 81[/bold]")
            console.print("  信息传递: [bold]python main.py chapter-transfer -t 81,82[/bold]")
            console.print("  一致性检查: [bold]python main.py chapter-transfer -c 81,85[/bold]")
            console.print("  查看摘要: [bold]python main.py chapter-transfer --summary 81,82[/bold]")
            console.print("  列出状态: [bold]python main.py chapter-transfer --list-states[/bold]")
        
        console.print(f"\n🔄 章节信息传递机制已准备就绪！")
        console.print("提供章节间状态传递、一致性检查和写作指导功能。")
        
    except Exception as e:
        console.print(f"[red]章节信息传递失败: {e}[/red]")
        logger.error(f"章节信息传递失败: {e}")


@cli.command()
@click.option('--init', '-i', is_flag=True, help='初始化项目进度状态')
@click.option('--status', '-s', is_flag=True, help='显示项目状态概览')
@click.option('--start-chapter', '-sc', type=int, help='开始指定章节的续写')
@click.option('--update-chapter', '-uc', type=int, help='更新指定章节的进度')
@click.option('--word-count', '-w', type=int, help='更新章节字数')
@click.option('--percentage', '-p', type=float, help='更新完成百分比')
@click.option('--complete-chapter', '-cc', type=int, help='标记指定章节为已完成')
@click.option('--report', '-r', type=str, help='生成进度报告到指定文件')
@click.option('--backup', '-b', is_flag=True, help='备份项目状态')
@click.option('--list-chapters', '-lc', is_flag=True, help='列出所有章节状态')
@click.option('--session-start', is_flag=True, help='开始工作会话')
@click.option('--session-end', is_flag=True, help='结束工作会话')
def progress(init, status, start_chapter, update_chapter, word_count, percentage, 
            complete_chapter, report, backup, list_chapters, session_start, session_end):
    """进度跟踪和状态管理"""
    try:
        # 创建进度跟踪器
        tracker = create_progress_tracker()
        
        # 初始化项目
        if init:
            console.print("[yellow]正在初始化项目进度状态...[/yellow]")
            project_state = tracker.initialize_project(force=True)
            console.print("[green]✅ 项目状态初始化完成！[/green]")
            console.print(f"项目开始时间: {project_state.start_date.strftime('%Y-%m-%d %H:%M:%S')}")
            console.print(f"章节总数: {project_state.statistics.total_chapters}")
            return
        
        # 显示项目状态
        if status:
            summary = tracker.get_progress_summary()
            console.print(Panel(
                f"""📊 项目状态: {summary['项目状态']}
🎯 总体进度: {summary['总体进度']}
📚 完成章节: {summary['完成章节']}
📝 当前章节: 第{summary['当前章节']}回 """ + (f"({summary['当前章节']})" if summary['当前章节'] else "无") + f"""
📖 总字数: {summary['总字数']}
📊 完成字数比例: {summary['完成字数比例']}
⏱️ 平均每章字数: {summary['平均每章字数']}
🕐 预估完成时间: {summary['预估完成时间']}
🔄 最后更新: {summary['最后更新']}""",
                title="📈 项目进度概览",
                border_style="green"
            ))
            return
        
        # 开始章节
        if start_chapter:
            if tracker.start_chapter(start_chapter):
                console.print(f"[green]✅ 开始第{start_chapter}回续写[/green]")
                console.print(f"开始时间: {tracker.project_state.chapters[start_chapter].start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                console.print(f"[red]❌ 无法开始第{start_chapter}回[/red]")
            return
        
        # 更新章节进度
        if update_chapter:
            updates = {}
            if word_count is not None:
                updates['word_count'] = word_count
            if percentage is not None:
                updates['completion_percentage'] = percentage
            
            if updates:
                if tracker.update_chapter_progress(update_chapter, **updates):
                    console.print(f"[green]✅ 第{update_chapter}回进度已更新[/green]")
                    chapter = tracker.project_state.chapters[update_chapter]
                    console.print(f"当前状态: {chapter.status.value}")
                    if word_count is not None:
                        console.print(f"字数: {chapter.word_count}/{chapter.estimated_words}")
                    console.print(f"完成度: {chapter.completion_percentage:.1f}%")
                else:
                    console.print(f"[red]❌ 更新第{update_chapter}回失败[/red]")
            else:
                console.print("[yellow]请指定要更新的内容（字数或百分比）[/yellow]")
            return
        
        # 完成章节
        if complete_chapter:
            final_words = word_count if word_count else None
            if tracker.complete_chapter(complete_chapter, final_words):
                console.print(f"[green]🎉 第{complete_chapter}回已完成！[/green]")
                chapter = tracker.project_state.chapters[complete_chapter]
                console.print(f"完成时间: {chapter.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
                console.print(f"最终字数: {chapter.word_count}")
                
                # 检查项目是否完成
                if tracker.project_state.project_status == ProjectStatus.COMPLETED:
                    console.print("[bold green]🎊 恭喜！所有章节已完成！[/bold green]")
            else:
                console.print(f"[red]❌ 无法完成第{complete_chapter}回[/red]")
            return
        
        # 生成进度报告
        if report:
            report_content = tracker.generate_progress_report(report)
            console.print(f"[green]✅ 进度报告已生成: {report}[/green]")
            # 显示报告预览
            lines = report_content.split('\n')
            preview = '\n'.join(lines[:20])
            console.print(Panel(
                preview + "\n\n[dim]... (查看完整报告请打开文件)[/dim]",
                title="📋 报告预览",
                border_style="blue"
            ))
            return
        
        # 备份状态
        if backup:
            backup_file = tracker.backup_state()
            if backup_file:
                console.print(f"[green]✅ 状态已备份: {backup_file}[/green]")
            else:
                console.print("[red]❌ 备份失败[/red]")
            return
        
        # 列出章节
        if list_chapters:
            chapters = tracker.get_chapter_list()
            
            # 按状态分组显示
            status_groups = {}
            for chapter in chapters:
                status = chapter['状态']
                if status not in status_groups:
                    status_groups[status] = []
                status_groups[status].append(chapter)
            
            for status, group in status_groups.items():
                console.print(f"\n📋 {status} ({len(group)} 章节):")
                for chapter in group:
                    console.print(f"  • {chapter['章节']} - {chapter['标题']} - {chapter['进度']} - {chapter['字数']}")
            return
        
        # 会话管理
        if session_start:
            tracker.start_session()
            console.print("[green]✅ 工作会话已开始[/green]")
            console.print(f"会话开始时间: {tracker.project_state.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
            return
        
        if session_end:
            tracker.end_session()
            console.print("[green]✅ 工作会话已结束[/green]")
            return
        
        # 默认显示使用建议
        if not any([init, status, start_chapter, update_chapter, complete_chapter, 
                   report, backup, list_chapters, session_start, session_end]):
            console.print("\n💡 使用建议:")
            console.print("  初始化项目: [bold]python main.py progress --init[/bold]")
            console.print("  查看状态: [bold]python main.py progress --status[/bold]")
            console.print("  开始章节: [bold]python main.py progress -sc 81[/bold]")
            console.print("  更新进度: [bold]python main.py progress -uc 81 -w 5000 -p 50[/bold]")
            console.print("  完成章节: [bold]python main.py progress -cc 81 -w 12000[/bold]")
            console.print("  生成报告: [bold]python main.py progress -r reports/progress.md[/bold]")
            console.print("  列出章节: [bold]python main.py progress --list-chapters[/bold]")
        
        console.print(f"\n📊 进度跟踪器已准备就绪！")
        console.print("提供完整的项目进度管理和状态跟踪功能。")
        
    except Exception as e:
        console.print(f"[red]进度管理失败: {e}[/red]")
        logger.error(f"进度管理失败: {e}")


if __name__ == "__main__":
    cli()