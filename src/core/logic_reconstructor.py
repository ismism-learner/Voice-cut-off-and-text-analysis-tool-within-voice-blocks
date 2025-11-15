"""
逻辑重构模块
负责分析段落的深层逻辑关系，构建逻辑链路
"""

import asyncio
from typing import List, Dict
from ..models.document import Segment, LogicChain, Document
from ..api.llm_client import LLMClient


class LogicReconstructor:
    """逻辑重构器"""

    def __init__(self, llm_client: LLMClient = None):
        """
        初始化逻辑重构器

        Args:
            llm_client: LLM客户端实例
        """
        self.llm_client = llm_client or LLMClient(provider="mock")

    async def extract_topics_for_segments(self, segments: List[Segment]) -> List[Segment]:
        """
        为每个段落提取主题标签

        Args:
            segments: 段落列表

        Returns:
            添加了主题标签的段落列表
        """
        for segment in segments:
            if segment.text:
                try:
                    topics = await self.llm_client.extract_topics(segment.text)
                    segment.topics = topics
                except Exception as e:
                    print(f"提取主题失败: {e}")
                    segment.topics = []

        return segments

    async def analyze_logic_structure(self, segments: List[Segment]) -> Dict:
        """
        分析整体逻辑结构

        Args:
            segments: 段落列表

        Returns:
            分析结果字典
        """
        # 准备段落数据
        segments_data = []
        for seg in segments:
            segments_data.append({
                'id': seg.id,
                'text': seg.text,
                'timestamp': seg.format_timestamp(),
                'markers': seg.markers,
                'topics': seg.topics
            })

        # 调用LLM进行分析
        try:
            analysis_result = await self.llm_client.analyze_paragraphs(segments_data)
            return analysis_result
        except Exception as e:
            print(f"逻辑分析失败: {e}")
            return {
                'core_arguments': [],
                'supporting_points': [],
                'logic_chains': [],
                'paragraph_relations': [],
                'topic_tree': {}
            }

    def build_logic_chains(self, analysis_result: Dict) -> List[LogicChain]:
        """
        构建逻辑链

        Args:
            analysis_result: LLM分析结果

        Returns:
            逻辑链列表
        """
        chains = []

        for chain_data in analysis_result.get('logic_chains', []):
            chain = LogicChain(
                chain_id=chain_data.get('chain_id', ''),
                chain_type=chain_data.get('chain_type', 'UNKNOWN'),
                segments=chain_data.get('segments', []),
                description=chain_data.get('description', ''),
                importance=chain_data.get('importance', 0.5)
            )
            chains.append(chain)

        return chains

    def mark_core_arguments(self, segments: List[Segment], core_ids: List[str]) -> List[Segment]:
        """
        标记核心论点

        Args:
            segments: 段落列表
            core_ids: 核心论点ID列表

        Returns:
            更新后的段落列表
        """
        for segment in segments:
            if segment.id in core_ids:
                segment.is_core_argument = True
                segment.importance_score = max(segment.importance_score, 0.9)

        return segments

    def build_topic_tree(self, segments: List[Segment], topic_tree_data: Dict) -> Dict:
        """
        构建主题树

        Args:
            segments: 段落列表
            topic_tree_data: 主题树数据（来自LLM）

        Returns:
            完整的主题树结构
        """
        # 如果LLM提供了主题树，使用它
        if topic_tree_data:
            return topic_tree_data

        # 否则，基于段落主题构建简单的主题树
        topic_segments = {}
        for seg in segments:
            for topic in seg.topics:
                if topic not in topic_segments:
                    topic_segments[topic] = []
                topic_segments[topic].append(seg.id)

        return {
            'main_topic': '文档主题',
            'subtopics': [
                {
                    'name': topic,
                    'segments': seg_ids
                }
                for topic, seg_ids in topic_segments.items()
            ]
        }

    async def reconstruct(self, segments: List[Segment]) -> Document:
        """
        执行完整的逻辑重构流程

        Args:
            segments: 段落列表

        Returns:
            Document对象
        """
        # 1. 提取主题
        print("正在提取段落主题...")
        segments = await self.extract_topics_for_segments(segments)

        # 2. 分析逻辑结构
        print("正在分析逻辑结构...")
        analysis_result = await self.analyze_logic_structure(segments)

        # 3. 构建逻辑链
        print("正在构建逻辑链...")
        logic_chains = self.build_logic_chains(analysis_result)

        # 4. 标记核心论点
        core_argument_ids = analysis_result.get('core_arguments', [])
        segments = self.mark_core_arguments(segments, core_argument_ids)

        # 5. 构建主题树
        topic_tree = self.build_topic_tree(
            segments,
            analysis_result.get('topic_tree', {})
        )

        # 6. 创建Document对象
        document = Document(
            source_file="",  # 由外部设置
            segments=segments,
            logic_chains=logic_chains,
            topic_tree=topic_tree,
            metadata={
                'core_arguments_count': len(core_argument_ids),
                'logic_chains_count': len(logic_chains),
                'total_topics': len(set(topic for seg in segments for topic in seg.topics))
            }
        )

        return document

    def process(self, segments: List[Segment]) -> Document:
        """
        同步接口：执行逻辑重构

        Args:
            segments: 段落列表

        Returns:
            Document对象
        """
        return asyncio.run(self.reconstruct(segments))


# 测试代码
if __name__ == "__main__":
    from ..models.document import Segment

    async def test():
        # 创建测试段落
        segments = [
            Segment(
                id="seg_1",
                start_time=0,
                end_time=5,
                audio_path="test1.wav",
                text="哲学的本质是对世界的根本思考。",
                markers=[]
            ),
            Segment(
                id="seg_2",
                start_time=5,
                end_time=10,
                audio_path="test2.wav",
                text="但是不同的哲学家有不同的理解。",
                markers=["但是"]
            ),
        ]

        # 执行重构
        reconstructor = LogicReconstructor()
        document = await reconstructor.reconstruct(segments)

        print(f"文档包含 {document.segment_count} 个段落")
        print(f"识别出 {len(document.logic_chains)} 条逻辑链")
        print(f"主题树: {document.topic_tree}")

    asyncio.run(test())
