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


if __name__ == "__main__":
    cli()