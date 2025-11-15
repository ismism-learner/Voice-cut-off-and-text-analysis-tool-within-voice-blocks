"""
语音转文字模块
负责将音频段落转换为文字
"""

import asyncio
from typing import List
from ..models.document import Segment
from ..api.stt_client import STTClient


class Transcriber:
    """转录器"""

    def __init__(self, stt_client: STTClient = None):
        """
        初始化转录器

        Args:
            stt_client: STT客户端实例
        """
        self.stt_client = stt_client or STTClient(provider="mock")

    async def transcribe_segment(self, segment: Segment) -> Segment:
        """
        转录单个段落

        Args:
            segment: 段落对象

        Returns:
            更新后的段落对象
        """
        try:
            result = await self.stt_client.transcribe(segment.audio_path)
            segment.text = result.text
            segment.confidence = result.confidence
        except Exception as e:
            print(f"转录段落 {segment.id} 失败: {e}")
            segment.text = ""
            segment.confidence = 0.0

        return segment

    async def transcribe_segments(self, segments: List[Segment],
                                   max_concurrent: int = 5,
                                   progress_callback=None) -> List[Segment]:
        """
        批量转录段落

        Args:
            segments: 段落列表
            max_concurrent: 最大并发数
            progress_callback: 进度回调函数 callback(current, total)

        Returns:
            转录后的段落列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        completed = 0
        total = len(segments)

        async def transcribe_with_progress(seg):
            nonlocal completed
            async with semaphore:
                result = await self.transcribe_segment(seg)
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
                return result

        tasks = [transcribe_with_progress(seg) for seg in segments]
        transcribed_segments = await asyncio.gather(*tasks)

        return transcribed_segments

    def process(self, segments: List[Segment], max_concurrent: int = 5) -> List[Segment]:
        """
        同步接口：批量转录段落

        Args:
            segments: 段落列表
            max_concurrent: 最大并发数

        Returns:
            转录后的段落列表
        """
        return asyncio.run(self.transcribe_segments(segments, max_concurrent))


# 测试代码
if __name__ == "__main__":
    from ..models.document import Segment

    async def test():
        # 创建测试段落
        segments = [
            Segment(id="seg_1", start_time=0, end_time=5, audio_path="test1.wav"),
            Segment(id="seg_2", start_time=5, end_time=10, audio_path="test2.wav"),
        ]

        # 转录
        transcriber = Transcriber()
        result = await transcriber.transcribe_segments(segments)

        for seg in result:
            print(f"{seg.id}: {seg.text} (confidence: {seg.confidence})")

    asyncio.run(test())
