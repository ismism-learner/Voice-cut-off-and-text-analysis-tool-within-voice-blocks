# 音频语义分割与逻辑重构工具

## 项目简介

这是一款专为长篇哲学类视频内容设计的智能处理工具，能够将跳跃性的叙述转换为逻辑系统性的结构化内容。

### 核心功能

- **🎯 双重分段机制**
  - 基于音频停顿的VAD分段
  - 基于语义标记词（"但是"、"然而"、"回过头来讲"等）的智能分段

- **🔗 段落关系分析**
  - 自动识别转折、因果、递进、总结等逻辑关系
  - 构建段落间的关系图谱

- **📊 多维可视化**
  - 结构化文本输出
  - 思维导图（规划中）
  - 时间轴展示
  - 关系图谱（规划中）

- **💻 友好的桌面界面**
  - 基于PyQt6的跨平台桌面应用
  - 实时处理进度显示
  - 一键导出结果

### 技术特点

- 使用云端API（阿里云语音识别 + 通义千问），无需高配置电脑
- 异步并发处理，提高处理速度
- 模块化设计，易于扩展和维护

---

## 快速开始

### 环境要求

- Python 3.8+
- FFmpeg（用于音视频处理）

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd Voice-cut-off-and-text-analysis-tool-within-voice-blocks
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **安装FFmpeg**
- **Ubuntu/Debian**: `sudo apt-get install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Windows**: 从 [FFmpeg官网](https://ffmpeg.org/download.html) 下载并配置环境变量

4. **配置API密钥**
```bash
# 复制环境变量配置文件
cp .env.example .env

# 编辑.env文件，填入你的API密钥
# ALIYUN_API_KEY=your_key_here
# DASHSCOPE_API_KEY=your_key_here
```

### 运行应用

```bash
python main.py
```

---

## 使用指南

### 基础流程

1. **选择文件**
   - 点击"选择视频/音频文件"按钮
   - 支持格式：MP4, AVI, MOV, MP3, WAV, FLAC

2. **开始处理**
   - 点击"开始处理"按钮
   - 查看实时进度和状态

3. **查看结果**
   - 切换不同的标签页查看：
     - **段落列表**：所有分段的详细信息
     - **逻辑结构**：逻辑链路分析
     - **详细信息**：文档元数据和统计

4. **导出结果**
   - 点击"导出结果"按钮
   - 选择保存位置和格式（JSON/Markdown）

### 处理流程说明

```
视频/音频输入
    ↓
[1] 音频分段（基于停顿检测）
    ↓
[2] 语音转文字（批量并发）
    ↓
[3] 语义分析（标记词识别 + 二次分段）
    ↓
[4] 逻辑重构（LLM分析 + 关系构建）
    ↓
多维可视化结果
```

---

## 项目结构

```
Voice-cut-off-and-text-analysis-tool-within-voice-blocks/
├── src/                      # 源代码
│   ├── core/                 # 核心处理模块
│   │   ├── audio_segmenter.py    # 音频分段
│   │   ├── transcriber.py        # 语音转文字
│   │   ├── semantic_analyzer.py  # 语义分析
│   │   └── logic_reconstructor.py # 逻辑重构
│   ├── api/                  # API集成
│   │   ├── stt_client.py         # STT客户端
│   │   └── llm_client.py         # LLM客户端
│   ├── models/               # 数据模型
│   │   └── document.py
│   ├── visualization/        # 可视化（规划中）
│   └── gui/                  # GUI界面
│       └── main_window.py
├── config/                   # 配置文件
│   └── api_config.yaml
├── data/                     # 数据目录
│   ├── audio_segments/       # 音频片段缓存
│   └── cache/                # 其他缓存
├── output/                   # 输出结果
├── tests/                    # 测试（待完善）
├── main.py                   # 主入口
├── requirements.txt          # 依赖列表
├── DESIGN.md                 # 技术设计文档
├── .env.example              # 环境变量示例
└── README.md                 # 本文件
```

---

## 配置说明

### API配置

编辑 `config/api_config.yaml` 可以调整：

- **音频处理参数**
  - `pause_threshold`: 停顿阈值（默认1.5秒）
  - `min_segment_duration`: 最小段落时长
  - `max_segment_duration`: 最大段落时长

- **API设置**
  - STT提供商选择（aliyun/mock）
  - LLM提供商选择（qwen/mock）
  - 并发数、重试次数等

### 语义标记词

在 `src/core/semantic_analyzer.py` 中可以自定义语义标记词库：

```python
SEMANTIC_MARKERS = {
    RelationType.CONTRAST: {
        'keywords': ['但是', '然而', '不过', ...]
    },
    # ... 更多类型
}
```

---

## 开发路线图

### ✅ 已完成

- [x] 项目框架搭建
- [x] 音频分段基础功能
- [x] STT API集成（支持mock模式测试）
- [x] 语义标记词检测
- [x] 二次分段逻辑
- [x] LLM集成
- [x] 基础GUI界面
- [x] 结果展示和导出

### 🚧 进行中

- [ ] 完善STT和LLM的真实API集成
- [ ] 优化音频分段算法
- [ ] 增强错误处理和日志

### 📋 计划中

- [ ] 思维导图可视化
- [ ] 关系图谱展示
- [ ] HTML格式导出
- [ ] 批量处理功能
- [ ] 自定义语义标记词界面
- [ ] 处理历史记录
- [ ] 性能优化

---

## 技术栈

### 核心技术

- **GUI**: PyQt6
- **音频处理**: pydub, ffmpeg-python
- **VAD**: Silero VAD (基于PyTorch)
- **STT**: 阿里云语音识别
- **LLM**: 通义千问（DashScope）

### 数据处理

- NumPy, SciPy
- Jieba（中文分词）
- PyEcharts（可视化）

---

## 使用场景

### 主要应用

- 📚 **哲学视频内容整理**：将长篇讲座转换为结构化笔记
- 🎓 **学术研究**：分析学术讲座的论证结构
- 📝 **会议记录**：提取会议的核心观点和逻辑
- 🎬 **视频字幕优化**：生成带逻辑结构的字幕

### 适用内容类型

- 哲学讨论和讲座
- 学术报告和研讨
- 深度访谈
- 知识分享类视频

---

## API成本估算

以1小时音频为例：

- **STT成本**：约 ¥0.5-1.0
- **LLM成本**：约 ¥2-5（假设100个段落分析）
- **总成本**：约 ¥3-6 / 小时

*注：实际成本取决于具体使用量和API定价*

---

## 常见问题

### Q: 如何获取API密钥？

**阿里云语音识别**:
1. 注册[阿里云账号](https://www.aliyun.com/)
2. 开通"智能语音交互"服务
3. 在控制台获取API密钥

**通义千问**:
1. 访问[通义千问开放平台](https://dashscope.aliyun.com/)
2. 注册并开通服务
3. 获取API Key

### Q: 为什么选择云端API而非本地模型？

- ✅ 降低硬件要求（无需GPU）
- ✅ 更高的准确率（特别是中文语音识别）
- ✅ 定期更新和优化
- ❌ 需要网络连接
- ❌ 有一定成本（但相对较低）

### Q: 支持哪些语言？

目前主要支持**中文**。通过调整API配置可支持其他语言，但语义标记词需要相应调整。

### Q: 处理1小时视频需要多久？

取决于网络速度和API响应时间，通常需要**5-10分钟**。

---

## 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements.txt

# 运行测试（待完善）
pytest tests/
```

---

## 许可证

MIT License

---

## 致谢

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- [FFmpeg](https://ffmpeg.org/)
- [阿里云智能语音](https://www.aliyun.com/product/nls)
- [通义千问](https://tongyi.aliyun.com/)

---

## 联系方式

- 项目地址: [GitHub仓库链接]
- 问题反馈: [Issues](链接)

---

**祝使用愉快！如有问题欢迎反馈。**