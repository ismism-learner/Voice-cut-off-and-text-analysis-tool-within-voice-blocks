#!/usr/bin/env python3
"""
模拟测试脚本
使用Mock数据测试整个处理流程，无需真实音频文件和API
"""

import sys
from pathlib import Path
import asyncio

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.models.document import Segment, RelationType
from src.core.semantic_analyzer import SemanticAnalyzer
from src.core.logic_reconstructor import LogicReconstructor
from src.api.stt_client import STTClient
from src.api.llm_client import LLMClient


def create_mock_segments():
    """创建模拟的音频段落（已转录好的文本）"""

    # 模拟一个哲学讨论的音频片段
    segments = [
        Segment(
            id="seg_001",
            start_time=0.0,
            end_time=8.5,
            audio_path="mock_audio_001.wav",
            text="我们首先要理解什么是现象学。现象学是研究意识的本质结构。",
            confidence=0.95
        ),
        Segment(
            id="seg_002",
            start_time=8.5,
            end_time=16.2,
            audio_path="mock_audio_002.wav",
            text="但是这个概念很抽象，需要从不同角度来理解。比如胡塞尔的观点。",
            confidence=0.92
        ),
        Segment(
            id="seg_003",
            start_time=16.2,
            end_time=24.8,
            audio_path="mock_audio_003.wav",
            text="胡塞尔认为意识总是关于某物的意识。这是意向性理论的核心。",
            confidence=0.94
        ),
        Segment(
            id="seg_004",
            start_time=24.8,
            end_time=32.5,
            audio_path="mock_audio_004.wav",
            text="回过头来讲，现象学的目标是回到事物本身。",
            confidence=0.91
        ),
        Segment(
            id="seg_005",
            start_time=32.5,
            end_time=40.0,
            audio_path="mock_audio_005.wav",
            text="因此，我们需要悬置自然态度。这叫做现象学还原。",
            confidence=0.93
        ),
        Segment(
            id="seg_006",
            start_time=40.0,
            end_time=48.3,
            audio_path="mock_audio_006.wav",
            text="然而，这种方法论并非没有争议。海德格尔就提出了不同看法。",
            confidence=0.90
        ),
        Segment(
            id="seg_007",
            start_time=48.3,
            end_time=55.0,
            audio_path="mock_audio_007.wav",
            text="总之，现象学为我们提供了理解意识的新方法。",
            confidence=0.96
        ),
    ]

    return segments


def print_separator(title=""):
    """打印分隔线"""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")
    else:
        print(f"{'='*60}\n")


async def test_full_pipeline():
    """测试完整的处理流程"""

    print_separator("开始模拟测试")

    # 1. 创建模拟段落
    print("📝 步骤 1: 创建模拟音频段落")
    segments = create_mock_segments()
    print(f"   ✓ 创建了 {len(segments)} 个模拟段落")
    print(f"   ✓ 总时长: {segments[-1].end_time:.1f} 秒")

    # 2. 语义分析
    print_separator("步骤 2: 语义分析")
    analyzer = SemanticAnalyzer()

    # 检测每个段落的标记词
    print("🔍 检测语义标记词:")
    for seg in segments:
        markers = analyzer.detect_markers(seg.text)
        if markers:
            print(f"   • [{seg.id}] 发现标记词: {[m[0] for m in markers]}")

    # 执行完整的语义分析
    print("\n🔧 执行语义分析和段落优化...")
    analyzed_segments = analyzer.process(segments)
    print(f"   ✓ 优化后段落数: {len(analyzed_segments)}")

    # 显示段落关系
    print("\n🔗 段落关系分析:")
    for seg in analyzed_segments:
        if seg.relations:
            for rel in seg.relations:
                print(f"   • {rel.source_id} → {rel.target_id}: {rel.relation_type.value}")
                print(f"     标记词: {', '.join(rel.marker_words)}")

    # 3. 逻辑重构
    print_separator("步骤 3: 逻辑重构")
    llm_client = LLMClient(provider="mock")
    reconstructor = LogicReconstructor(llm_client)

    print("🤖 提取主题标签...")
    analyzed_segments = await reconstructor.extract_topics_for_segments(analyzed_segments)

    print("📊 主题分布:")
    for seg in analyzed_segments:
        if seg.topics:
            print(f"   • [{seg.id}] {', '.join(seg.topics)}")

    print("\n🧠 分析逻辑结构...")
    document = await reconstructor.reconstruct(analyzed_segments)
    document.source_file = "mock_philosophy_lecture.mp4"

    # 4. 显示结果
    print_separator("处理结果总览")

    print(f"📄 文档信息:")
    print(f"   • 源文件: {document.source_file}")
    print(f"   • 总时长: {document.total_duration:.1f} 秒")
    print(f"   • 段落数量: {document.segment_count}")
    print(f"   • 核心论点数: {len(document.get_core_arguments())}")
    print(f"   • 逻辑链数量: {len(document.logic_chains)}")

    print(f"\n🎯 核心论点:")
    for seg in document.get_core_arguments():
        print(f"   • [{seg.id}] {seg.text}")
        print(f"     重要性: {'⭐' * int(seg.importance_score * 5)}")

    print(f"\n🔗 逻辑链路:")
    for chain in document.logic_chains:
        print(f"   • {chain.chain_type}")
        print(f"     描述: {chain.description}")
        print(f"     包含段落: {len(chain.segments)} 个")

    print(f"\n🌳 主题树:")
    if document.topic_tree:
        print(f"   主题: {document.topic_tree.get('main_topic', '未知')}")
        for subtopic in document.topic_tree.get('subtopics', []):
            if isinstance(subtopic, dict):
                print(f"   ├─ {subtopic.get('name', '未知')}")

    # 5. 详细段落列表
    print_separator("详细段落列表")

    for i, seg in enumerate(document.segments, 1):
        print(f"\n段落 {i}: [{seg.id}]")
        print(f"  时间: {seg.format_timestamp()}")
        print(f"  文本: {seg.text}")
        if seg.markers:
            print(f"  标记词: {', '.join(seg.markers)}")
        if seg.topics:
            print(f"  主题: {', '.join(seg.topics)}")
        print(f"  重要性: {'⭐' * int(seg.importance_score * 5)} ({seg.importance_score:.2f})")
        if seg.is_core_argument:
            print(f"  🎯 核心论点")

    # 6. 导出JSON
    print_separator("导出结果")

    import json
    output_file = "output/test_result.json"
    Path("output").mkdir(exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(document.to_dict(), f, ensure_ascii=False, indent=2)

    print(f"✓ 结果已导出到: {output_file}")

    print_separator("测试完成")

    return document


def test_semantic_analyzer():
    """单独测试语义分析器"""
    print_separator("测试语义分析器")

    analyzer = SemanticAnalyzer()

    # 测试标记词检测
    test_texts = [
        "我们需要理解这个概念。但是这很困难。",
        "首先讨论A，然后讨论B，因此得出结论C。",
        "回过头来讲，我们之前提到的观点很重要。",
        "总之，这是一个复杂的问题。",
    ]

    print("🔍 标记词检测测试:\n")
    for text in test_texts:
        markers = analyzer.detect_markers(text)
        print(f"文本: {text}")
        if markers:
            print(f"标记词: {[(m, rt.value) for m, rt in markers]}")
        else:
            print(f"标记词: 无")
        print()

    # 测试段落切分
    print("✂️ 段落切分测试:\n")
    test_segment = Segment(
        id="test_001",
        start_time=0,
        end_time=10,
        audio_path="test.wav",
        text="现象学很重要。但是它很抽象。因此我们需要举例说明。比如意识的结构。"
    )

    print(f"原始文本: {test_segment.text}\n")
    sub_segments = analyzer.split_by_markers(test_segment)
    print(f"切分结果: {len(sub_segments)} 个子段落")
    for i, seg in enumerate(sub_segments, 1):
        print(f"  {i}. {seg.text}")


def main():
    """主函数"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║     音频语义分割与逻辑重构工具 - 模拟测试               ║
║     Mock Test for Audio Semantic Segmentation Tool        ║
╚═══════════════════════════════════════════════════════════╝
""")

    # 选择测试模式
    print("请选择测试模式:")
    print("1. 完整流程测试（推荐）")
    print("2. 仅测试语义分析器")
    print("3. 全部测试")

    choice = input("\n请输入选项 (1/2/3) [默认: 1]: ").strip() or "1"

    if choice == "1":
        asyncio.run(test_full_pipeline())
    elif choice == "2":
        test_semantic_analyzer()
    elif choice == "3":
        test_semantic_analyzer()
        asyncio.run(test_full_pipeline())
    else:
        print("无效选项，执行完整流程测试")
        asyncio.run(test_full_pipeline())


if __name__ == "__main__":
    main()
