import os
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcription App v0.0.1")
        self.setAcceptDrops(True)
        self.setStyleSheet("background-color: #121212; color: white; font-family: Arial, sans-serif;")

        # Центральний віджет із контейнером
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Головний горизонтальний layout для центрування
        main_layout = QHBoxLayout(central_widget)
        main_layout.addStretch()  # Ліва розтяжка для центрування
        
        # Внутрішній віджет із фіксованою шириною 75-80% від ширини вікна
        container_widget = QWidget()
        container_widget.setMaximumWidth(int(self.width() * 0.75))
        container_widget.setMinimumWidth(int(self.width() * 0.75))
        main_layout.addWidget(container_widget)
        main_layout.addStretch()  # Права розтяжка для центрування
        
        # Внутрішній вертикальний layout для контенту
        layout = QVBoxLayout(container_widget)
        layout.setContentsMargins(20, 20, 20, 20)  # padding: 20px

        header = QLabel("Головна")
        header.setStyleSheet("font-size: 24px; border-bottom: 1px solid #333; padding-bottom: 10px;")
        layout.addWidget(header)

        self.new_transcript_btn = QPushButton("📝 Нове транскрибування")
        self.new_transcript_btn.setStyleSheet("""
            QPushButton {
                background: #1e90ff; color: white; padding: 15px; border: none; 
                border-radius: 8px; font-size: 16px;
            }
            QPushButton:hover { background: #0073e6; }
        """)
        self.new_transcript_btn.clicked.connect(self.open_config_window)
        layout.addWidget(self.new_transcript_btn)

        self.drop_label = QLabel("Перетягніть файл сюди")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet("border: 2px dashed #ccc; border-radius: 10px; padding: 20px; margin-top: 20px;")
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
        from config_window import ConfigWindow
        self.config_window = ConfigWindow(file_path)
        self.config_window.showMaximized()  # Відкриваємо конфігураційне вікно також на весь екран
        self.hide()

    def show(self):
        super().showMaximized()  # Відкриваємо вікно на весь екран

    def resizeEvent(self, event):
        container_widget = self.centralWidget().layout().itemAt(1).widget()
        container_widget.setMaximumWidth(int(self.width() * 0.75))
        container_widget.setMinimumWidth(int(self.width() * 0.75))
        super().resizeEvent(event)