# main_window.py
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent


class MainWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setAcceptDrops(True)
        self.setStyleSheet(
            "background-color: #121212; color: white; font-family: Arial, sans-serif;"
        )

        main_layout = QHBoxLayout(self)
        main_layout.addStretch()

        container_widget = QWidget()
        container_widget.setMaximumWidth(int(parent.width() * 0.75))
        container_widget.setMinimumWidth(int(parent.width() * 0.75))
        main_layout.addWidget(container_widget)
        main_layout.addStretch()

        layout = QVBoxLayout(container_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("Головна")
        header.setStyleSheet(
            "font-size: 24px; border-bottom: 1px solid #333; padding-bottom: 10px;"
        )
        layout.addWidget(header)

        # Кнопка для Whisper-транскрибування
        self.new_transcript_btn = QPushButton("📝 Нове транскрибування")
        self.new_transcript_btn.setStyleSheet(
            """
            QPushButton {
                background: #1e90ff; color: white; padding: 15px; border: none; 
                border-radius: 8px; font-size: 16px;
            }
            QPushButton:hover { background: #0073e6; }
        """
        )
        self.new_transcript_btn.clicked.connect(self.open_config_window)
        layout.addWidget(self.new_transcript_btn)

        # Кнопка для HMM-транскрибування
        self.hmm_transcript_btn = QPushButton("🔍 HMM Транскрибування")
        self.hmm_transcript_btn.setStyleSheet(
            """
            QPushButton {
                background: #1e90ff; color: white; padding: 15px; border: none; 
                border-radius: 8px; font-size: 16px; margin-top: 10px;
            }
            QPushButton:hover { background: #0073e6; }
        """
        )
        self.hmm_transcript_btn.clicked.connect(self.open_hmm_result_window)
        layout.addWidget(self.hmm_transcript_btn)

        self.drop_label = QLabel("Перетягніть файл сюди")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet(
            "border: 2px dashed #ccc; border-radius: 10px; padding: 20px; margin-top: 20px;"
        )
        layout.addWidget(self.drop_label)

        layout.addStretch()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        file_path = event.mimeData().urls()[0].toLocalFile()
        self.drop_label.setText(f"Файл: {os.path.basename(file_path)}")
        self.open_config_window(file_path)

    def open_config_window(self, file_path=None):
        self.parent.switch_to_config(file_path)

    def open_hmm_result_window(self):
        self.parent.switch_to_hmm_result()
