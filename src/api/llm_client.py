"""
LLM API客户端
用于段落分析、逻辑重构等任务
"""

import json
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

try:
    import dashscope
    from dashscope import Generation
    from http import HTTPStatus
except ImportError:
    pass


class BaseLLMClient(ABC):
    """LLM客户端基类"""

    @abstractmethod
    async def analyze_paragraphs(self, segments: List[Dict]) -> Dict:
        """
        分析段落的逻辑关系

        Args:
            segments: 段落列表

        Returns:
            分析结果
        """
        pass

    @abstractmethod
    async def extract_topics(self, text: str) -> List[str]:
        """
        提取文本主题

        Args:
            text: 文本内容

        Returns:
            主题列表
        """
        pass


class QwenLLMClient(BaseLLMClient):
    """通义千问客户端"""

    def __init__(self, api_key: str, model: str = "qwen-max"):
        """
        初始化千问客户端

        Args:
            api_key: API密钥
            model: 模型名称
        """
        self.api_key = api_key
        self.model = model
        dashscope.api_key = api_key

    def _call_api(self, prompt: str, system_prompt: str = None) -> str:
        """
        调用API

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词

        Returns:
            模型响应
        """
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})

        response = Generation.call(
            model=self.model,
            messages=messages,
            result_format='message'
        )

        if response.status_code == HTTPStatus.OK:
            return response.output.choices[0].message.content
        else:
            raise RuntimeError(f"LLM API错误: {response}")

    async def analyze_paragraphs(self, segments: List[Dict]) -> Dict:
        """
        分析段落的逻辑关系

        Args:
            segments: 段落列表 [{"id": "seg_1", "text": "...", "markers": [...]}]

        Returns:
            分析结果
        """
        # 构建提示词
        system_prompt = """你是一个哲学文本分析专家，擅长分析论述的逻辑结构。
请仔细分析给定的段落，识别它们之间的逻辑关系。"""

        segments_text = "\n\n".join([
            f"[段落{i+1}] ID: {seg['id']}\n时间: {seg.get('timestamp', 'N/A')}\n"
            f"标记词: {', '.join(seg.get('markers', []))}\n"
            f"内容: {seg['text']}"
            for i, seg in enumerate(segments)
        ])

        prompt = f"""请分析以下段落的逻辑关系：

{segments_text}

请以JSON格式输出分析结果，包括：
1. core_arguments: 核心论点列表（段落ID）
2. supporting_points: 支撑论据列表（段落ID）
3. logic_chains: 逻辑链路（每条链路包含相关段落ID和关系类型）
4. paragraph_relations: 段落间的具体关系（source_id, target_id, relation_type, description）
5. topic_tree: 主题树结构

输出格式示例：
{{
  "core_arguments": ["seg_1", "seg_5"],
  "supporting_points": ["seg_2", "seg_3"],
  "logic_chains": [
    {{
      "chain_id": "chain_1",
      "chain_type": "MAIN_ARGUMENT",
      "segments": ["seg_1", "seg_2", "seg_3"],
      "description": "关于XX的核心论述"
    }}
  ],
  "paragraph_relations": [
    {{
      "source_id": "seg_1",
      "target_id": "seg_2",
      "relation_type": "CAUSALITY",
      "description": "因果关系：A导致B"
    }}
  ],
  "topic_tree": {{
    "main_topic": "核心主题",
    "subtopics": [...]
  }}
}}
"""

        # 调用API
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, self._call_api, prompt, system_prompt)

        # 解析JSON
        try:
            # 尝试提取JSON块
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            result = json.loads(json_str)
            return result
        except json.JSONDecodeError as e:
            # 解析失败，返回默认结构
            return {
                "core_arguments": [],
                "supporting_points": [],
                "logic_chains": [],
                "paragraph_relations": [],
                "topic_tree": {},
                "raw_response": response,
                "error": str(e)
            }

    async def extract_topics(self, text: str) -> List[str]:
        """
        提取文本主题

        Args:
            text: 文本内容

        Returns:
            主题列表
        """
        prompt = f"""请分析以下文本的主题，提取3-5个关键主题词：

{text}

请以JSON数组格式输出，例如：["主题1", "主题2", "主题3"]
"""

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, self._call_api, prompt)

        try:
            # 提取JSON数组
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "[" in response and "]" in response:
                start = response.index("[")
                end = response.rindex("]") + 1
                json_str = response[start:end]
            else:
                json_str = response.strip()

            topics = json.loads(json_str)
            return topics if isinstance(topics, list) else []
        except:
            return []


class MockLLMClient(BaseLLMClient):
    """Mock LLM客户端（用于测试）"""

    async def analyze_paragraphs(self, segments: List[Dict]) -> Dict:
        """模拟分析"""
        await asyncio.sleep(1)

        return {
            "core_arguments": [segments[0]['id']] if segments else [],
            "supporting_points": [seg['id'] for seg in segments[1:3]] if len(segments) > 1 else [],
            "logic_chains": [
                {
                    "chain_id": "chain_1",
                    "chain_type": "MAIN_ARGUMENT",
                    "segments": [seg['id'] for seg in segments[:3]],
                    "description": "主要论述链路（模拟）"
                }
            ],
            "paragraph_relations": [],
            "topic_tree": {
                "main_topic": "哲学讨论（模拟）",
                "subtopics": ["认识论", "本体论"]
            }
        }

    async def extract_topics(self, text: str) -> List[str]:
        """模拟主题提取"""
        await asyncio.sleep(0.3)
        return ["哲学", "认识论", "现象学"]


class LLMClient:
    """LLM客户端管理器"""

    def __init__(self, provider: str = "mock", **config):
        """
        初始化LLM客户端

        Args:
            provider: 提供商（qwen/mock）
            **config: 配置参数
        """
        self.provider = provider
        self.config = config
        self.client = self._create_client()

    def _create_client(self) -> BaseLLMClient:
        """创建具体的客户端实例"""
        if self.provider == "qwen":
            return QwenLLMClient(
                api_key=self.config.get('api_key'),
                model=self.config.get('model', 'qwen-max')
            )
        elif self.provider == "mock":
            return MockLLMClient()
        else:
            raise ValueError(f"不支持的LLM提供商: {self.provider}")

    async def analyze_paragraphs(self, segments: List[Dict]) -> Dict:
        """分析段落"""
        return await self.client.analyze_paragraphs(segments)

    async def extract_topics(self, text: str) -> List[str]:
        """提取主题"""
        return await self.client.extract_topics(text)


# 测试代码
if __name__ == "__main__":
    async def test():
        client = LLMClient(provider="mock")
        segments = [
            {"id": "seg_1", "text": "哲学的本质是什么？", "markers": []},
            {"id": "seg_2", "text": "但是我们需要从另一个角度来看", "markers": ["但是"]},
        ]
        result = await client.analyze_paragraphs(segments)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    asyncio.run(test())
