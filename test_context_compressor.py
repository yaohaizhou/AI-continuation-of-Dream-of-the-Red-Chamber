"""
测试上下文压缩器
Test Context Compressor - 演示长文本压缩功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from long_text_management.context_compressor import ContextCompressor, CompressedContext
import json

def test_context_compressor():
    """测试上下文压缩器的基本功能"""
    
    # 模拟几个章节的文本内容
    sample_chapters = [
        """第七十八回 老学士闲征姽婳词 痴公子杜撰芙蓉诔
        
        话说贾政回家，见过贾母，即到房内，见过王夫人，便叫宝玉。宝玉忙走来，
        贾政道："你前日作的那古风如何了？"宝玉道："已经作完了。"贾政道："拿来我看。"
        宝玉答应一声，即去取了来。贾政看了一回，点头道："这个可以。你近来举业如何了？"
        宝玉道："正要禀父亲，近来举业稍有进益。"贾政道："那是再好没有的了。"
        """,
        
        """第七十九回 薛文龙悔娶河东狮 贾迎春误嫁中山狼
        
        话说贾政正在房内，忽见林之孝进来说道："外面有胡老爷前来拜会。"
        贾政听了，即便出去。这胡老爷原是贾政的同年，此时正在工部。
        见面之后，胡老爷笑道："今日特来拜访，有一件事相求。"
        贾政道："有何见教？"胡老爷道："小儿顽劣，欲送入贵府书房，
        跟着宝哥儿一处读书，不知可否？"贾政笑道："这有何不可，只恐家慎微薄，
        不能开导。"两人说笑一回，胡老爷告辞而去。
        """,
        
        """第八十回 美香菱屈受贪夫棒 王道士胡诌妒妇方
        
        话说王夫人见贾政气色比先好些，心内着实欢喜。又见宝玉举业有了进益，
        更加放心。这日正和贾母说话，忽见凤姐走来，满面愁容。
        贾母见了，便问道："你这是怎么了？"凤姐勉强笑道："没有什么，
        只是家务事繁琐，有些乏困。"王夫人道："你身子要紧，
        别太劳累了。"凤姐点头道："媳妇知道了。"
        """
    ]
    
    print("=== 测试上下文压缩器 ===\n")
    
    # 创建压缩器实例
    compressor = ContextCompressor(max_context_length=1000)
    
    # 压缩章节
    print("1. 开始压缩章节...")
    compressed_context = compressor.compress_chapters(sample_chapters, target_chapter=81)
    
    print(f"   原始文本长度: {compressed_context.original_word_count} 字符")
    print(f"   压缩后长度: {compressed_context.compressed_word_count} 字符")
    print(f"   压缩比例: {compressed_context.compression_ratio:.2%}\n")
    
    # 显示压缩结果
    print("2. 压缩结果摘要:")
    for i, summary in enumerate(compressed_context.previous_chapters_summary):
        print(f"   第{summary.chapter_num}回: {summary.title}")
        print(f"   - 关键事件: {summary.key_events}")
        print(f"   - 人物状态: {summary.character_states}")
        print(f"   - 情感基调: {summary.emotional_tone}")
        print()
    
    # 生成续写提示词
    print("3. 生成续写提示词:")
    current_context = "宝玉正在大观园中闲步，忽见黛玉从潇湘馆走出..."
    prompt = compressor.generate_context_prompt(compressed_context, current_context)
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    print()
    
    # 保存压缩结果
    print("4. 保存压缩结果...")
    output_file = "data/compressed_context_example.json"
    compressor.save_compressed_context(compressed_context, output_file)
    print(f"   已保存到: {output_file}")
    
    return compressed_context

def analyze_compression_effectiveness():
    """分析压缩效果"""
    print("\n=== 压缩效果分析 ===")
    
    # 计算不同文本长度的压缩效果
    test_cases = [
        ("短文本", "宝玉说道：'今日天气甚好。'黛玉听了，微微一笑。"),
        ("中等文本", "宝玉来到潇湘馆，见黛玉正在读书。黛玉见他来了，放下书本，笑道：'你今日怎么有空到这里来？'宝玉道：'闲来无事，想起妹妹，便过来看看。'两人说笑一回，颇为欢愉。"),
        ("长文本", """
        话说贾政回到家中，心中颇为忧虑。自从上次在朝中听到风声，便知家中恐有变故。
        这日正在书房中思虑，忽见宝玉走来。贾政见了，问道："你来做什么？"
        宝玉道："儿子想请教父亲一事。"贾政道："什么事？"
        宝玉道："近日读书，有些不解之处，想请父亲指点。"
        贾政听了，心中稍安，道："这样最好，你且说来听听。"
        宝玉于是将所疑之处一一说了。贾政听完，点头道："你这些问题问得很好，
        说明读书用心了。"父子二人就这样谈论起来，直到日暮才罢。
        """)
    ]
    
    compressor = ContextCompressor()
    
    for name, text in test_cases:
        print(f"\n{name} (原长度: {len(text)} 字符):")
        
        # 创建单章摘要
        summary = compressor._create_chapter_summary(text, 1)
        
        # 估算压缩后大小
        compressed_size = compressor._estimate_compressed_size([summary])
        compression_ratio = compressed_size / len(text) if len(text) > 0 else 0
        
        print(f"  压缩后: {compressed_size} 字符")
        print(f"  压缩比: {compression_ratio:.2%}")
        print(f"  关键事件数: {len(summary.key_events)}")
        print(f"  检测到人物数: {len(summary.character_states)}")

if __name__ == "__main__":
    try:
        # 测试基本功能
        compressed_context = test_context_compressor()
        
        # 分析压缩效果
        analyze_compression_effectiveness()
        
        print("\n✅ 测试完成！上下文压缩器运行正常。")
        print("\n📝 下一步建议:")
        print("1. 集成LLM来提升摘要质量")
        print("2. 优化关键信息提取算法")
        print("3. 添加更多的压缩策略")
        print("4. 与现有的知识增强系统集成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc() 