"""
数据模型定义
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum


class RelationType(Enum):
    """段落关系类型"""
    CONTRAST = "转折"          # 转折关系
    ADDITION = "递进"          # 递进关系
    CAUSALITY = "因果"         # 因果关系
    REFERENCE_BACK = "回溯"    # 回溯引用
    SUMMARY = "总结"           # 总结关系
    EXAMPLE = "举例"           # 举例说明
    PARALLEL = "并列"          # 并列关系
    UNKNOWN = "未知"           # 未知关系


@dataclass
class ParagraphRelation:
    """段落关系"""
    source_id: str                      # 源段落ID
    target_id: str                      # 目标段落ID
    relation_type: RelationType         # 关系类型
    marker_words: List[str] = field(default_factory=list)  # 识别到的标记词
    confidence: float = 0.0             # 关系置信度 (0-1)
    description: str = ""               # 关系描述

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'relation_type': self.relation_type.value,
            'marker_words': self.marker_words,
            'confidence': self.confidence,
            'description': self.description
        }


@dataclass
class Segment:
    """音频段落"""
    id: str                             # 段落唯一ID
    start_time: float                   # 开始时间（秒）
    end_time: float                     # 结束时间（秒）
    audio_path: str                     # 音频片段文件路径
    text: str = ""                      # 转录文本
    markers: List[str] = field(default_factory=list)  # 检测到的语义标记词
    topics: List[str] = field(default_factory=list)   # 主题标签
    importance_score: float = 0.5       # 重要性评分 (0-1)
    relations: List[ParagraphRelation] = field(default_factory=list)  # 段落关系
    confidence: float = 0.0             # 转录置信度
    is_core_argument: bool = False      # 是否为核心论点

    @property
    def duration(self) -> float:
        """段落时长"""
        return self.end_time - self.start_time

    def format_timestamp(self) -> str:
        """格式化时间戳"""
        start_min = int(self.start_time // 60)
        start_sec = int(self.start_time % 60)
        end_min = int(self.end_time // 60)
        end_sec = int(self.end_time % 60)
        return f"{start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}"

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'audio_path': self.audio_path,
            'text': self.text,
            'markers': self.markers,
            'topics': self.topics,
            'importance_score': self.importance_score,
            'confidence': self.confidence,
            'is_core_argument': self.is_core_argument,
            'relations': [r.to_dict() for r in self.relations]
        }


@dataclass
class LogicChain:
    """逻辑链"""
    chain_id: str                       # 链路唯一ID
    chain_type: str                     # ARGUMENT/EXAMPLE/COUNTER_ARGUMENT等
    segments: List[str]                 # segment_id列表
    description: str = ""               # 链路描述
    importance: float = 0.5             # 重要性

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'chain_id': self.chain_id,
            'chain_type': self.chain_type,
            'segments': self.segments,
            'description': self.description,
            'importance': self.importance
        }


@dataclass
class Document:
    """文档（处理后的完整结果）"""
    source_file: str                    # 源文件路径
    segments: List[Segment] = field(default_factory=list)  # 所有段落
    logic_chains: List[LogicChain] = field(default_factory=list)  # 逻辑链
    topic_tree: Dict = field(default_factory=dict)  # 主题树结构
    metadata: Dict = field(default_factory=dict)    # 元数据
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间

    @property
    def total_duration(self) -> float:
        """总时长"""
        if not self.segments:
            return 0.0
        return max(seg.end_time for seg in self.segments)

    @property
    def segment_count(self) -> int:
        """段落数量"""
        return len(self.segments)

    def get_segment_by_id(self, segment_id: str) -> Optional[Segment]:
        """根据ID获取段落"""
        for seg in self.segments:
            if seg.id == segment_id:
                return seg
        return None

    def get_core_arguments(self) -> List[Segment]:
        """获取核心论点"""
        return [seg for seg in self.segments if seg.is_core_argument]

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'source_file': self.source_file,
            'total_duration': self.total_duration,
            'segment_count': self.segment_count,
            'segments': [seg.to_dict() for seg in self.segments],
            'logic_chains': [chain.to_dict() for chain in self.logic_chains],
            'topic_tree': self.topic_tree,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }
