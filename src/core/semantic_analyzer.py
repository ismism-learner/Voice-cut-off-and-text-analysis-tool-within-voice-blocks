"""
语义分析模块
负责识别语义标记词、段落关系等
"""

import re
from typing import List, Dict, Tuple
from ..models.document import Segment, ParagraphRelation, RelationType


class SemanticAnalyzer:
    """语义分析器"""

    # 语义标记词库
    SEMANTIC_MARKERS = {
        RelationType.CONTRAST: {
            'keywords': ['但是', '然而', '不过', '可是', '反过来说', '相反', '相对而言', '与此相反'],
        },
        RelationType.ADDITION: {
            'keywords': ['而且', '并且', '还有', '另外', '此外', '再者', '同时', '以及'],
        },
        RelationType.CAUSALITY: {
            'keywords': ['所以', '因此', '因为', '由于', '导致', '结果', '因而', '从而'],
        },
        RelationType.REFERENCE_BACK: {
            'keywords': ['回过头来讲', '前面说到', '刚才提到', '之前讲过', '如前所述', '正如我说的'],
        },
        RelationType.SUMMARY: {
            'keywords': ['总之', '综上所述', '总的来说', '概括来说', '归纳起来', '简而言之'],
        },
        RelationType.EXAMPLE: {
            'keywords': ['比如', '例如', '譬如', '比方说', '举例来说', '就像'],
        },
    }

    def __init__(self, custom_markers: Dict = None):
        """
        初始化语义分析器

        Args:
            custom_markers: 自定义标记词（可选）
        """
        self.markers = self.SEMANTIC_MARKERS.copy()
        if custom_markers:
            # 合并自定义标记词
            for relation_type, config in custom_markers.items():
                if relation_type in self.markers:
                    self.markers[relation_type]['keywords'].extend(config.get('keywords', []))

    def detect_markers(self, text: str) -> List[Tuple[str, RelationType]]:
        """
        检测文本中的语义标记词

        Args:
            text: 文本内容

        Returns:
            [(标记词, 关系类型), ...]
        """
        found_markers = []

        for relation_type, config in self.markers.items():
            for keyword in config['keywords']:
                if keyword in text:
                    found_markers.append((keyword, relation_type))

        return found_markers

    def split_by_markers(self, segment: Segment) -> List[Segment]:
        """
        根据语义标记词切分段落

        Args:
            segment: 原始段落

        Returns:
            切分后的段落列表
        """
        text = segment.text
        markers = self.detect_markers(text)

        if not markers:
            # 没有标记词，返回原段落
            return [segment]

        # 查找标记词位置
        split_points = []
        for marker, relation_type in markers:
            # 使用正则表达式查找标记词位置（避免部分匹配）
            pattern = r'\b' + re.escape(marker) + r'\b'
            for match in re.finditer(pattern, text):
                split_points.append((match.start(), marker, relation_type))

        if not split_points:
            return [segment]

        # 按位置排序
        split_points.sort(key=lambda x: x[0])

        # 执行切分
        sub_segments = []
        last_pos = 0

        for i, (pos, marker, relation_type) in enumerate(split_points):
            # 提取子段落文本
            sub_text = text[last_pos:pos].strip()

            if sub_text:
                # 估算时间戳（简单按字符比例分配）
                char_ratio_start = last_pos / len(text)
                char_ratio_end = pos / len(text)
                duration = segment.duration
                sub_start = segment.start_time + char_ratio_start * duration
                sub_end = segment.start_time + char_ratio_end * duration

                # 创建子段落
                sub_seg = Segment(
                    id=f"{segment.id}_sub{i}",
                    start_time=sub_start,
                    end_time=sub_end,
                    audio_path=segment.audio_path,  # 共享音频文件
                    text=sub_text,
                    markers=[],
                    confidence=segment.confidence
                )
                sub_segments.append(sub_seg)

            last_pos = pos

        # 添加最后一个子段落
        last_text = text[last_pos:].strip()
        if last_text:
            sub_seg = Segment(
                id=f"{segment.id}_sub{len(split_points)}",
                start_time=segment.start_time + (last_pos / len(text)) * segment.duration,
                end_time=segment.end_time,
                audio_path=segment.audio_path,
                text=last_text,
                markers=[marker for _, marker, _ in split_points if _ >= last_pos],
                confidence=segment.confidence
            )
            sub_segments.append(sub_seg)

        return sub_segments if sub_segments else [segment]

    def analyze_relations(self, segments: List[Segment]) -> List[Segment]:
        """
        分析段落间的关系

        Args:
            segments: 段落列表

        Returns:
            添加了关系信息的段落列表
        """
        for i, segment in enumerate(segments):
            # 检测当前段落的标记词
            markers = self.detect_markers(segment.text)
            segment.markers = [marker for marker, _ in markers]

            # 建立与前一段落的关系
            if i > 0 and markers:
                prev_segment = segments[i - 1]
                for marker, relation_type in markers:
                    relation = ParagraphRelation(
                        source_id=prev_segment.id,
                        target_id=segment.id,
                        relation_type=relation_type,
                        marker_words=[marker],
                        confidence=0.8,
                        description=f"通过标记词'{marker}'识别的{relation_type.value}关系"
                    )
                    segment.relations.append(relation)

        return segments

    def refine_segments(self, segments: List[Segment]) -> List[Segment]:
        """
        优化段落（二次分段 + 关系分析）

        Args:
            segments: 初始段落列表

        Returns:
            优化后的段落列表
        """
        # 第一步：根据语义标记词切分
        refined_segments = []
        for segment in segments:
            sub_segments = self.split_by_markers(segment)
            refined_segments.extend(sub_segments)

        # 第二步：分析段落关系
        refined_segments = self.analyze_relations(refined_segments)

        return refined_segments

    def calculate_importance(self, segment: Segment, all_segments: List[Segment]) -> float:
        """
        计算段落重要性

        Args:
            segment: 当前段落
            all_segments: 所有段落

        Returns:
            重要性分数 (0-1)
        """
        score = 0.5  # 基础分数

        # 1. 包含总结类标记词 -> 更重要
        for marker in segment.markers:
            for relation_type, config in self.markers.items():
                if marker in config['keywords']:
                    if relation_type == RelationType.SUMMARY:
                        score += 0.3
                    elif relation_type == RelationType.CAUSALITY:
                        score += 0.2
                    break

        # 2. 被多个段落引用 -> 更重要
        reference_count = sum(
            1 for s in all_segments
            for r in s.relations
            if r.target_id == segment.id or r.source_id == segment.id
        )
        score += min(reference_count * 0.1, 0.3)

        # 3. 文本长度较长 -> 可能更重要
        if len(segment.text) > 100:
            score += 0.1

        return min(score, 1.0)

    def process(self, segments: List[Segment]) -> List[Segment]:
        """
        完整的语义分析流程

        Args:
            segments: 初始段落列表

        Returns:
            处理后的段落列表
        """
        # 优化分段
        refined = self.refine_segments(segments)

        # 计算重要性
        for seg in refined:
            seg.importance_score = self.calculate_importance(seg, refined)

        return refined


# 测试代码
if __name__ == "__main__":
    # 创建测试段落
    seg1 = Segment(
        id="seg_1",
        start_time=0,
        end_time=10,
        audio_path="test.wav",
        text="我们首先要理解哲学的本质。但是这个问题很复杂，需要从多个角度来看。"
    )

    analyzer = SemanticAnalyzer()

    # 检测标记词
    markers = analyzer.detect_markers(seg1.text)
    print(f"检测到的标记词: {markers}")

    # 切分段落
    sub_segs = analyzer.split_by_markers(seg1)
    print(f"切分为 {len(sub_segs)} 个子段落")
    for s in sub_segs:
        print(f"  - {s.text}")
