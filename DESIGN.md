# 音频语义分割与逻辑重构工具 - 技术设计文档

## 项目概述

### 核心目标
将长篇哲学类视频/音频内容通过智能分段和语义分析，从跳跃性叙述转换为逻辑系统性的结构化内容。

### 核心特性
- 🎯 **双重分段机制**：音频停顿检测 + 语义标记词识别
- 🔗 **段落关系分析**：识别转折、因果、递进等逻辑关系
- 📊 **多维可视化**：结构化文本、思维导图、时间轴、关系图谱
- 💻 **桌面应用**：跨平台支持（Windows/Mac/Linux）
- ☁️ **云端API**：使用在线STT和LLM服务，降低本地硬件要求

---

## 技术架构

### 整体架构图
```
┌─────────────────────────────────────────────────────────┐
│                    GUI Layer (PyQt6)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ 导入界面  │  │ 处理进度  │  │ 可视化   │  │ 导出    │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                  Core Processing Layer                   │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────┐  │
│  │ Audio       │  │ Transcription│  │ Semantic       │  │
│  │ Segmenter   │→│ Engine       │→│ Analyzer       │  │
│  └─────────────┘  └─────────────┘  └────────────────┘  │
│         ↓                 ↓                  ↓           │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────┐  │
│  │ VAD Engine  │  │ STT API      │  │ LLM API        │  │
│  │ (Silero)    │  │ (阿里云/讯飞)│  │ (千问/GPT)     │  │
│  └─────────────┘  └─────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│              Visualization & Export Layer                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ 结构文本  │  │ 思维导图  │  │ 时间轴   │  │ 关系图  │ │
│  │ (Markdown)│  │ (ECharts)│  │ (Timeline)│  │ (Graph) │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 核心模块设计

### 1. 音频分段模块 (Audio Segmenter)

#### 1.1 功能
- 从视频中提取音频（支持多种格式）
- 基于VAD的静音检测和分段
- 生成带时间戳的音频片段

#### 1.2 技术实现
```python
输入：视频/音频文件
处理：
  1. 音频提取 (ffmpeg-python)
  2. VAD检测 (silero-vad)
  3. 停顿识别 (阈值：1-2秒)
  4. 段落切分
输出：List[AudioSegment] with timestamps
```

#### 1.3 关键参数
- `pause_threshold`: 1.5秒（可调）
- `min_segment_duration`: 0.5秒
- `max_segment_duration`: 30秒（超长段落自动切分）

---

### 2. 语音转文字模块 (Transcription Engine)

#### 2.1 支持的API
| API服务 | 优势 | 适用场景 |
|---------|------|---------|
| 阿里云语音识别 | 中文准确度高，价格适中 | 推荐 |
| 讯飞开放平台 | 方言支持好 | 特殊口音 |
| Azure Speech | 多语言支持 | 外语内容 |

#### 2.2 处理流程
```python
for segment in audio_segments:
    transcript = await stt_api.transcribe(segment.audio)
    segment.text = transcript.text
    segment.confidence = transcript.confidence
```

#### 2.3 优化策略
- **批量处理**：异步并发请求（控制并发数避免限流）
- **错误重试**：3次重试机制
- **结果缓存**：避免重复处理

---

### 3. 语义分析模块 (Semantic Analyzer)

#### 3.1 语义标记词库
```python
SEMANTIC_MARKERS = {
    '转折类': {
        'keywords': ['但是', '然而', '不过', '可是', '反过来说', '相反'],
        'relation_type': 'CONTRAST'
    },
    '递进类': {
        'keywords': ['而且', '并且', '还有', '另外', '此外', '再者'],
        'relation_type': 'ADDITION'
    },
    '因果类': {
        'keywords': ['所以', '因此', '因为', '由于', '导致', '结果'],
        'relation_type': 'CAUSALITY'
    },
    '回溯类': {
        'keywords': ['回过头来讲', '前面说到', '刚才提到', '之前讲过'],
        'relation_type': 'REFERENCE_BACK'
    },
    '总结类': {
        'keywords': ['总之', '综上所述', '总的来说', '概括来说'],
        'relation_type': 'SUMMARY'
    },
    '举例类': {
        'keywords': ['比如', '例如', '譬如', '比方说'],
        'relation_type': 'EXAMPLE'
    }
}
```

#### 3.2 段落关系识别
```python
class ParagraphRelation:
    source_id: int          # 源段落ID
    target_id: int          # 目标段落ID
    relation_type: str      # CONTRAST/CAUSALITY/ADDITION等
    marker_words: List[str] # 识别到的标记词
    confidence: float       # 关系置信度
```

#### 3.3 二次分段算法
```python
# 初始段落（基于音频停顿）
segments_v1 = audio_segmenter.segment(audio)

# 扫描语义标记词
for segment in segments_v1:
    markers = detect_semantic_markers(segment.text)
    if markers:
        # 在标记词位置切分
        sub_segments = split_at_markers(segment, markers)
        segments_v2.extend(sub_segments)
```

---

### 4. 逻辑重构模块 (Logic Reconstructor)

#### 4.1 使用LLM进行深度分析
```python
prompt = f"""
你是一个哲学文本分析专家。请分析以下段落的逻辑关系：

段落列表：
{paragraphs_with_markers}

任务：
1. 识别每个段落的核心观点
2. 分析段落间的逻辑关系（因果/转折/递进/补充）
3. 构建论证链路
4. 识别核心论点和支撑论据

输出JSON格式：
{{
  "core_arguments": [...],
  "supporting_points": [...],
  "logic_chains": [...],
  "paragraph_relations": [...]
}}
"""
```

#### 4.2 主题聚类
- 使用LLM提取每个段落的主题标签
- 基于主题相似度进行聚类
- 构建主题树状结构

#### 4.3 逻辑链重构
```
原始顺序：A → B → C → D → E
跳跃模式：A讲概念 → B举例 → C回到概念 → D转折 → E总结

重构后：
主线1：[A, C] 核心概念
  ├─ 支撑：[B] 举例说明
主线2：[D] 转折观点
总结：[E]
```

---

## 数据模型

### Segment (段落)
```python
@dataclass
class Segment:
    id: str
    start_time: float           # 秒
    end_time: float
    audio_path: str            # 音频片段文件路径
    text: str                  # 转录文本
    markers: List[str]         # 检测到的语义标记词
    topics: List[str]          # 主题标签
    importance_score: float    # 重要性评分 (0-1)
    relations: List[ParagraphRelation]
```

### LogicChain (逻辑链)
```python
@dataclass
class LogicChain:
    chain_id: str
    chain_type: str            # ARGUMENT/EXAMPLE/COUNTER_ARGUMENT
    segments: List[str]        # segment_id列表
    description: str           # 链路描述
```

### Document (文档)
```python
@dataclass
class Document:
    source_file: str
    segments: List[Segment]
    logic_chains: List[LogicChain]
    topic_tree: Dict          # 主题树结构
    created_at: datetime
```

---

## 可视化设计

### 1. 结构化文本输出
```markdown
# 文档标题

## 核心论点
1. [段落A] 主要观点...
   - 支撑论据：[段落B] ...
   - 举例说明：[段落C] ...

## 转折观点
2. [段落D] 但是另一方面...

## 总结
[段落E] 综上所述...

---
## 时间轴
00:00 - 00:45 [段落A] ...
00:45 - 01:20 [段落B] ...
```

### 2. 思维导图 (Mind Map)
使用 ECharts 的树图：
```javascript
{
  type: 'tree',
  data: {
    name: '核心主题',
    children: [
      { name: '观点1', children: [...] },
      { name: '观点2', children: [...] }
    ]
  }
}
```

### 3. 时间轴 (Timeline)
横向时间轴，可点击查看详情：
```
|---A---|----B----|---C---|-------D-------|--E--|
0s     45s      90s    120s           180s   200s
```

### 4. 关系图谱 (Relation Graph)
使用 ECharts 的力导向图：
```javascript
{
  type: 'graph',
  nodes: [{ id: 'A', label: '概念阐述' }, ...],
  edges: [
    { source: 'A', target: 'B', label: '举例' },
    { source: 'B', target: 'C', label: '回溯' }
  ]
}
```

---

## 技术栈

### 桌面应用框架
- **GUI**: PyQt6 / PySide6
- **布局**: QML (可选，更现代的UI)

### 音频处理
- **ffmpeg-python**: 视频/音频格式转换
- **pydub**: 音频片段处理
- **silero-vad**: 语音活动检测

### API集成
- **STT**: 阿里云语音识别 SDK
- **LLM**: 通义千问 API / OpenAI API

### 数据处理
- **spaCy**: 中文NLP处理
- **jieba**: 中文分词
- **networkx**: 图结构分析

### 可视化
- **PyQtGraph**: 基础图表
- **PyEcharts**: 生成HTML可视化（嵌入WebView）
- **Markdown**: 文本输出

### 其他
- **SQLite**: 本地数据存储
- **asyncio**: 异步API调用
- **loguru**: 日志管理

---

## 项目结构

```
voice-logic-reconstructor/
├── src/
│   ├── core/                    # 核心处理模块
│   │   ├── audio_segmenter.py   # 音频分段
│   │   ├── transcriber.py       # 语音转文字
│   │   ├── semantic_analyzer.py # 语义分析
│   │   └── logic_reconstructor.py # 逻辑重构
│   ├── api/                     # API集成
│   │   ├── stt_client.py        # STT API客户端
│   │   └── llm_client.py        # LLM API客户端
│   ├── models/                  # 数据模型
│   │   └── document.py
│   ├── visualization/           # 可视化模块
│   │   ├── text_formatter.py
│   │   ├── mindmap_generator.py
│   │   ├── timeline_generator.py
│   │   └── graph_generator.py
│   └── gui/                     # GUI界面
│       ├── main_window.py
│       ├── widgets/
│       └── resources/
├── config/
│   ├── api_config.yaml          # API配置
│   └── semantic_markers.json    # 语义标记词库
├── tests/
├── requirements.txt
├── main.py                      # 入口文件
└── README.md
```

---

## 开发路线图

### Phase 1: MVP (最小可行产品)
- [x] 项目框架搭建
- [ ] 音频分段基础功能
- [ ] STT API集成
- [ ] 简单的文本输出
- [ ] 基础GUI界面

### Phase 2: 语义分析
- [ ] 语义标记词检测
- [ ] 二次分段逻辑
- [ ] LLM集成
- [ ] 段落关系识别

### Phase 3: 可视化
- [ ] 结构化文本输出
- [ ] 思维导图生成
- [ ] 时间轴展示
- [ ] 关系图谱

### Phase 4: 优化与扩展
- [ ] 批量处理
- [ ] 导出功能（PDF/Word/HTML）
- [ ] 自定义语义标记词
- [ ] 性能优化

---

## API配置指南

### 阿里云语音识别
```yaml
aliyun_stt:
  app_key: "your_app_key"
  access_key_id: "your_access_key_id"
  access_key_secret: "your_access_key_secret"
  region: "cn-shanghai"
```

### 通义千问
```yaml
dashscope:
  api_key: "your_api_key"
  model: "qwen-max"
```

---

## 估算成本（示例）

以1小时音频为例：
- **STT成本**: 阿里云约 ¥0.5-1.0 / 小时
- **LLM成本**: 假设100个段落分析，约 ¥2-5
- **总成本**: ~¥3-6 / 小时音频

---

## 性能指标

- **处理速度**: 1小时音频约需 5-10分钟处理（含API等待）
- **准确率**: STT准确率 >95%（标准普通话）
- **内存占用**: <500MB（不含大型模型）
- **支持格式**: MP4, AVI, MOV, MP3, WAV, FLAC

---

## 下一步计划

1. 搭建项目基础框架
2. 实现音频分段模块
3. 集成STT API
4. 创建简单的PyQt界面
5. 测试端到端流程

---

*文档版本: v1.0*
*最后更新: 2025-11-15*
