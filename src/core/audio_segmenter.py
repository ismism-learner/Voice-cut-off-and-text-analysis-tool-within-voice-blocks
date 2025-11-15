"""
音频分段模块
基于VAD（Voice Activity Detection）进行音频分段
"""

import os
import uuid
from typing import List, Tuple, TYPE_CHECKING
from pathlib import Path
import subprocess

if TYPE_CHECKING:
    from pydub import AudioSegment as PyAudioSegment
else:
    try:
        import torch
        from pydub import AudioSegment as PyAudioSegment
        from pydub.silence import detect_nonsilent
    except ImportError:
        # 在实际运行时需要安装这些依赖
        PyAudioSegment = None

from ..models.document import Segment


class AudioSegmenter:
    """音频分段器"""

    def __init__(self,
                 pause_threshold: float = 1.5,
                 min_segment_duration: float = 0.5,
                 max_segment_duration: float = 30.0,
                 silence_thresh: int = -40,
                 output_dir: str = "data/audio_segments"):
        """
        初始化音频分段器

        Args:
            pause_threshold: 停顿阈值（秒）
            min_segment_duration: 最小段落时长（秒）
            max_segment_duration: 最大段落时长（秒）
            silence_thresh: 静音阈值（dBFS）
            output_dir: 输出目录
        """
        self.pause_threshold = pause_threshold
        self.min_segment_duration = min_segment_duration
        self.max_segment_duration = max_segment_duration
        self.silence_thresh = silence_thresh
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_audio_from_video(self, video_path: str, output_path: str = None) -> str:
        """
        从视频中提取音频

        Args:
            video_path: 视频文件路径
            output_path: 输出音频路径

        Returns:
            提取的音频文件路径
        """
        if output_path is None:
            output_path = str(self.output_dir / f"{Path(video_path).stem}.wav")

        # 使用ffmpeg提取音频
        command = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # 不包含视频
            '-acodec', 'pcm_s16le',  # 16-bit PCM
            '-ar', '16000',  # 16kHz采样率
            '-ac', '1',  # 单声道
            '-y',  # 覆盖输出文件
            output_path
        ]

        try:
            subprocess.run(command, check=True, capture_output=True)
            return output_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"音频提取失败: {e.stderr.decode()}")

    def detect_pauses(self, audio: PyAudioSegment) -> List[Tuple[int, int]]:
        """
        检测音频中的非静音段落

        Args:
            audio: 音频对象

        Returns:
            非静音段落列表 [(start_ms, end_ms), ...]
        """
        # 将停顿阈值转换为毫秒
        min_silence_len = int(self.pause_threshold * 1000)

        # 检测非静音段落
        nonsilent_ranges = detect_nonsilent(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=self.silence_thresh
        )

        return nonsilent_ranges

    def merge_short_segments(self, segments: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        合并过短的段落

        Args:
            segments: 段落列表

        Returns:
            合并后的段落列表
        """
        if not segments:
            return []

        min_duration_ms = int(self.min_segment_duration * 1000)
        merged = []
        current_start, current_end = segments[0]

        for start, end in segments[1:]:
            if current_end - current_start < min_duration_ms:
                # 当前段落太短，尝试合并
                current_end = end
            else:
                merged.append((current_start, current_end))
                current_start, current_end = start, end

        # 添加最后一个段落
        merged.append((current_start, current_end))

        return merged

    def split_long_segments(self, segments: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        切分过长的段落

        Args:
            segments: 段落列表

        Returns:
            切分后的段落列表
        """
        max_duration_ms = int(self.max_segment_duration * 1000)
        split_segments = []

        for start, end in segments:
            duration = end - start
            if duration > max_duration_ms:
                # 切分为多个段落
                num_splits = int(duration / max_duration_ms) + 1
                split_duration = duration / num_splits

                for i in range(num_splits):
                    split_start = int(start + i * split_duration)
                    split_end = int(start + (i + 1) * split_duration)
                    split_segments.append((split_start, split_end))
            else:
                split_segments.append((start, end))

        return split_segments

    def segment_audio(self, audio_path: str) -> List[Segment]:
        """
        对音频进行分段

        Args:
            audio_path: 音频文件路径

        Returns:
            段落列表
        """
        # 加载音频
        audio = PyAudioSegment.from_file(audio_path)

        # 检测非静音段落
        nonsilent_ranges = self.detect_pauses(audio)

        # 合并短段落
        merged_ranges = self.merge_short_segments(nonsilent_ranges)

        # 切分长段落
        final_ranges = self.split_long_segments(merged_ranges)

        # 创建Segment对象并保存音频片段
        segments = []
        for idx, (start_ms, end_ms) in enumerate(final_ranges):
            # 生成唯一ID
            segment_id = f"seg_{uuid.uuid4().hex[:8]}"

            # 提取音频片段
            segment_audio = audio[start_ms:end_ms]
            segment_path = str(self.output_dir / f"{segment_id}.wav")
            segment_audio.export(segment_path, format="wav")

            # 创建Segment对象
            segment = Segment(
                id=segment_id,
                start_time=start_ms / 1000.0,
                end_time=end_ms / 1000.0,
                audio_path=segment_path
            )
            segments.append(segment)

        return segments

    def process(self, input_file: str) -> List[Segment]:
        """
        处理视频或音频文件

        Args:
            input_file: 输入文件路径

        Returns:
            段落列表
        """
        # 检查文件类型
        file_ext = Path(input_file).suffix.lower()

        if file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.flv']:
            # 视频文件，先提取音频
            audio_path = self.extract_audio_from_video(input_file)
        elif file_ext in ['.wav', '.mp3', '.flac', '.m4a']:
            # 音频文件，直接处理
            audio_path = input_file
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")

        # 进行音频分段
        segments = self.segment_audio(audio_path)

        return segments


# 测试代码
if __name__ == "__main__":
    segmenter = AudioSegmenter()
    # segments = segmenter.process("path/to/video.mp4")
    # print(f"共分割为 {len(segments)} 个段落")
