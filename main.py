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
from knowledge_enhancement import EnhancedPrompter

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


if __name__ == "__main__":
    cli()