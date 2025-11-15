"""
主窗口界面
"""

import sys
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QTextEdit, QProgressBar,
        QFileDialog, QTabWidget, QMessageBox, QSplitter
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QFont
except ImportError:
    # 如果PyQt6未安装，提供占位类
    class QMainWindow:
        pass


class ProcessingThread(QThread):
    """处理线程"""
    progress = pyqtSignal(int, int)  # 当前进度, 总数
    status = pyqtSignal(str)  # 状态消息
    finished = pyqtSignal(object)  # 完成信号，传递Document对象
    error = pyqtSignal(str)  # 错误信号

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def run(self):
        """执行处理流程"""
        try:
            from ..core.audio_segmenter import AudioSegmenter
            from ..core.transcriber import Transcriber
            from ..core.semantic_analyzer import SemanticAnalyzer
            from ..core.logic_reconstructor import LogicReconstructor
            from ..api.stt_client import STTClient
            from ..api.llm_client import LLMClient

            # 1. 音频分段
            self.status.emit("正在分析音频并进行分段...")
            segmenter = AudioSegmenter()
            segments = segmenter.process(self.file_path)
            self.progress.emit(1, 4)

            # 2. 语音转文字
            self.status.emit(f"正在转录 {len(segments)} 个音频段落...")
            stt_client = STTClient(provider="mock")  # 使用mock进行演示
            transcriber = Transcriber(stt_client)

            def progress_callback(current, total):
                self.status.emit(f"正在转录: {current}/{total}")

            import asyncio
            segments = asyncio.run(
                transcriber.transcribe_segments(segments, progress_callback=progress_callback)
            )
            self.progress.emit(2, 4)

            # 3. 语义分析
            self.status.emit("正在进行语义分析...")
            analyzer = SemanticAnalyzer()
            segments = analyzer.process(segments)
            self.progress.emit(3, 4)

            # 4. 逻辑重构
            self.status.emit("正在重构逻辑结构...")
            llm_client = LLMClient(provider="mock")  # 使用mock进行演示
            reconstructor = LogicReconstructor(llm_client)
            document = reconstructor.process(segments)
            document.source_file = self.file_path
            self.progress.emit(4, 4)

            self.finished.emit(document)

        except Exception as e:
            import traceback
            self.error.emit(f"处理失败: {str(e)}\n{traceback.format_exc()}")


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.document = None
        self.processing_thread = None
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("音频语义分割与逻辑重构工具")
        self.setGeometry(100, 100, 1200, 800)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # 标题
        title_label = QLabel("音频语义分割与逻辑重构工具")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # 文件选择区域
        file_layout = QHBoxLayout()
        self.file_label = QLabel("未选择文件")
        self.select_file_btn = QPushButton("选择视频/音频文件")
        self.select_file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(QLabel("输入文件:"))
        file_layout.addWidget(self.file_label, 1)
        file_layout.addWidget(self.select_file_btn)
        main_layout.addLayout(file_layout)

        # 处理按钮
        button_layout = QHBoxLayout()
        self.process_btn = QPushButton("开始处理")
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setEnabled(False)
        self.export_btn = QPushButton("导出结果")
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setEnabled(False)
        button_layout.addWidget(self.process_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # 状态标签
        self.status_label = QLabel("就绪")
        main_layout.addWidget(self.status_label)

        # 结果显示区域（选项卡）
        self.result_tabs = QTabWidget()
        main_layout.addWidget(self.result_tabs, 1)

        # 段落列表标签
        self.segments_text = QTextEdit()
        self.segments_text.setReadOnly(True)
        self.result_tabs.addTab(self.segments_text, "段落列表")

        # 逻辑结构标签
        self.logic_text = QTextEdit()
        self.logic_text.setReadOnly(True)
        self.result_tabs.addTab(self.logic_text, "逻辑结构")

        # 详细信息标签
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.result_tabs.addTab(self.details_text, "详细信息")

    def select_file(self):
        """选择文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频或音频文件",
            "",
            "媒体文件 (*.mp4 *.avi *.mov *.mp3 *.wav *.flac);;所有文件 (*.*)"
        )

        if file_path:
            self.file_label.setText(Path(file_path).name)
            self.file_path = file_path
            self.process_btn.setEnabled(True)

    def start_processing(self):
        """开始处理"""
        if not hasattr(self, 'file_path'):
            return

        # 禁用按钮
        self.process_btn.setEnabled(False)
        self.select_file_btn.setEnabled(False)
        self.export_btn.setEnabled(False)

        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(4)

        # 清空结果显示
        self.segments_text.clear()
        self.logic_text.clear()
        self.details_text.clear()

        # 创建并启动处理线程
        self.processing_thread = ProcessingThread(self.file_path)
        self.processing_thread.progress.connect(self.update_progress)
        self.processing_thread.status.connect(self.update_status)
        self.processing_thread.finished.connect(self.processing_finished)
        self.processing_thread.error.connect(self.processing_error)
        self.processing_thread.start()

    def update_progress(self, current: int, total: int):
        """更新进度"""
        self.progress_bar.setValue(current)

    def update_status(self, message: str):
        """更新状态"""
        self.status_label.setText(message)

    def processing_finished(self, document):
        """处理完成"""
        self.document = document

        # 恢复按钮
        self.process_btn.setEnabled(True)
        self.select_file_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("处理完成！")

        # 显示结果
        self.display_results()

    def processing_error(self, error_message: str):
        """处理错误"""
        self.process_btn.setEnabled(True)
        self.select_file_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("处理失败")

        QMessageBox.critical(self, "错误", error_message)

    def display_results(self):
        """显示结果"""
        if not self.document:
            return

        # 显示段落列表
        segments_html = "<h2>段落列表</h2>\n"
        for i, seg in enumerate(self.document.segments, 1):
            importance_star = "⭐" * int(seg.importance_score * 5)
            core_mark = " [核心论点]" if seg.is_core_argument else ""
            markers_str = ", ".join(seg.markers) if seg.markers else "无"

            segments_html += f"""
            <div style="margin-bottom: 20px; padding: 10px; background-color: #f5f5f5; border-radius: 5px;">
                <h3>段落 {i} {core_mark} {importance_star}</h3>
                <p><strong>时间:</strong> {seg.format_timestamp()}</p>
                <p><strong>标记词:</strong> {markers_str}</p>
                <p><strong>主题:</strong> {", ".join(seg.topics) if seg.topics else "无"}</p>
                <p><strong>内容:</strong> {seg.text}</p>
            </div>
            """

        self.segments_text.setHtml(segments_html)

        # 显示逻辑结构
        logic_html = "<h2>逻辑结构</h2>\n"
        logic_html += f"<p><strong>核心论点数:</strong> {len(self.document.get_core_arguments())}</p>\n"
        logic_html += f"<p><strong>逻辑链数:</strong> {len(self.document.logic_chains)}</p>\n"

        logic_html += "<h3>逻辑链路</h3>\n"
        for chain in self.document.logic_chains:
            logic_html += f"""
            <div style="margin-bottom: 15px; padding: 10px; background-color: #e3f2fd; border-radius: 5px;">
                <h4>{chain.chain_type}</h4>
                <p><strong>描述:</strong> {chain.description}</p>
                <p><strong>包含段落:</strong> {len(chain.segments)} 个</p>
            </div>
            """

        self.logic_text.setHtml(logic_html)

        # 显示详细信息
        details_html = f"""
        <h2>文档详细信息</h2>
        <p><strong>源文件:</strong> {self.document.source_file}</p>
        <p><strong>总时长:</strong> {self.document.total_duration:.2f} 秒</p>
        <p><strong>段落数量:</strong> {self.document.segment_count}</p>
        <p><strong>核心论点数:</strong> {self.document.metadata.get('core_arguments_count', 0)}</p>
        <p><strong>逻辑链数量:</strong> {self.document.metadata.get('logic_chains_count', 0)}</p>
        <p><strong>识别主题数:</strong> {self.document.metadata.get('total_topics', 0)}</p>
        <p><strong>创建时间:</strong> {self.document.created_at}</p>

        <h3>主题树</h3>
        <pre>{self._format_topic_tree(self.document.topic_tree)}</pre>
        """

        self.details_text.setHtml(details_html)

    def _format_topic_tree(self, tree: dict, indent: int = 0) -> str:
        """格式化主题树"""
        if not tree:
            return "暂无主题树"

        result = "  " * indent + f"• {tree.get('main_topic', '未知主题')}\n"
        for subtopic in tree.get('subtopics', []):
            if isinstance(subtopic, dict):
                result += "  " * (indent + 1) + f"- {subtopic.get('name', '未知')}\n"

        return result

    def export_results(self):
        """导出结果"""
        if not self.document:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出结果",
            "result.json",
            "JSON文件 (*.json);;Markdown文件 (*.md);;所有文件 (*.*)"
        )

        if file_path:
            try:
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.document.to_dict(), f, ensure_ascii=False, indent=2)

                QMessageBox.information(self, "成功", f"结果已导出到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")


def main():
    """主函数"""
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
