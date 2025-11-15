"""
语音转文字API客户端
支持多种STT服务提供商
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict
from pathlib import Path

try:
    # 阿里云SDK
    import dashscope
    from dashscope.audio.asr import Recognition
except ImportError:
    pass


class STTResult:
    """STT结果"""
    def __init__(self, text: str, confidence: float = 0.0, metadata: Dict = None):
        self.text = text
        self.confidence = confidence
        self.metadata = metadata or {}


class BaseSTTClient(ABC):
    """STT客户端基类"""

    @abstractmethod
    async def transcribe(self, audio_path: str) -> STTResult:
        """
        转录音频文件

        Args:
            audio_path: 音频文件路径

        Returns:
            STTResult对象
        """
        pass


class AliyunSTTClient(BaseSTTClient):
    """阿里云语音识别客户端"""

    def __init__(self, api_key: str, app_key: str = None):
        """
        初始化阿里云STT客户端

        Args:
            api_key: API密钥
            app_key: 应用Key（可选）
        """
        self.api_key = api_key
        self.app_key = app_key
        dashscope.api_key = api_key

    async def transcribe(self, audio_path: str) -> STTResult:
        """
        转录音频文件

        Args:
            audio_path: 音频文件路径

        Returns:
            STTResult对象
        """
        try:
            # 使用阿里云Paraformer模型
            task_response = Recognition.call(
                model='paraformer-v1',
                file_urls=[f'file://{Path(audio_path).absolute()}'],
                language_hints=['zh']
            )

            if task_response.status_code == 200:
                # 获取任务ID
                task_id = task_response.output.task_id

                # 等待任务完成
                result = Recognition.wait(task=task_id)

                if result.status_code == 200:
                    # 提取文本
                    transcripts = result.output.get('results', [])
                    if transcripts:
                        text = transcripts[0].get('transcription_url', '')
                        # 这里简化处理，实际需要下载并解析结果文件
                        return STTResult(
                            text=text,
                            confidence=0.95,
                            metadata={'task_id': task_id}
                        )

            raise Exception(f"转录失败: {task_response}")

        except Exception as e:
            raise RuntimeError(f"阿里云STT错误: {str(e)}")


class MockSTTClient(BaseSTTClient):
    """Mock STT客户端（用于测试）"""

    async def transcribe(self, audio_path: str) -> STTResult:
        """
        模拟转录

        Args:
            audio_path: 音频文件路径

        Returns:
            STTResult对象
        """
        # 模拟延迟
        await asyncio.sleep(0.5)

        # 返回模拟文本
        return STTResult(
            text="这是一段模拟的转录文本，用于测试系统功能。",
            confidence=0.90,
            metadata={'mock': True}
        )


class STTClient:
    """STT客户端管理器"""

    def __init__(self, provider: str = "mock", **config):
        """
        初始化STT客户端

        Args:
            provider: 提供商（aliyun/mock）
            **config: 配置参数
        """
        self.provider = provider
        self.config = config
        self.client = self._create_client()

    def _create_client(self) -> BaseSTTClient:
        """创建具体的客户端实例"""
        if self.provider == "aliyun":
            return AliyunSTTClient(
                api_key=self.config.get('api_key'),
                app_key=self.config.get('app_key')
            )
        elif self.provider == "mock":
            return MockSTTClient()
        else:
            raise ValueError(f"不支持的STT提供商: {self.provider}")

    async def transcribe(self, audio_path: str) -> STTResult:
        """
        转录音频

        Args:
            audio_path: 音频文件路径

        Returns:
            STTResult对象
        """
        return await self.client.transcribe(audio_path)

    async def transcribe_batch(self, audio_paths: list, max_concurrent: int = 5) -> list:
        """
        批量转录音频

        Args:
            audio_paths: 音频文件路径列表
            max_concurrent: 最大并发数

        Returns:
            STTResult列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def transcribe_with_limit(path):
            async with semaphore:
                return await self.transcribe(path)

        tasks = [transcribe_with_limit(path) for path in audio_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                # 转录失败，返回空结果
                processed_results.append(STTResult(text="", confidence=0.0))
            else:
                processed_results.append(result)

        return processed_results


# 测试代码
if __name__ == "__main__":
    async def test():
        client = STTClient(provider="mock")
        result = await client.transcribe("test.wav")
        print(f"转录结果: {result.text}")
        print(f"置信度: {result.confidence}")

    asyncio.run(test())
