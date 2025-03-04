import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QFileDialog

class ConfigWindow(QWidget):
    def __init__(self, parent, file_path=None):
        super().__init__()
        self.parent = parent
        self.file_path = file_path
        self.setAcceptDrops(True)
        self.setStyleSheet("background-color: #121212; color: white; font-family: Arial, sans-serif;")

        main_layout = QHBoxLayout(self)
        main_layout.addStretch()

        container_widget = QWidget()
        container_widget.setMaximumWidth(int(parent.width() * 0.75))
        container_widget.setMinimumWidth(int(parent.width() * 0.75))
        main_layout.addWidget(container_widget)
        main_layout.addStretch()

        layout = QVBoxLayout(container_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # Верхній рядок із кнопкою "Назад"
        top_layout = QHBoxLayout()
        back_btn = QPushButton("⬅ Назад")
        back_btn.setStyleSheet("""
            QPushButton {
                background: #444; color: white; padding: 8px 12px; border: none; 
                border-radius: 8px; font-size: 14px; min-width: 80px;
            }
            QPushButton:hover { background: #555; }
        """)
        back_btn.clicked.connect(self.back_to_main)
        top_layout.addWidget(back_btn)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # Заголовок
        header = QLabel("Конфігурація обробки файлу")
        header.setStyleSheet("font-size: 24px; border-bottom: 1px solid #333; padding-bottom: 10px; margin-top: 10px;")
        layout.addWidget(header)

        # Секція "Файли"
        files_label = QLabel("Файли")
        files_label.setStyleSheet("font-size: 18px; margin-top: 20px;")
        layout.addWidget(files_label)

        self.file_list = QLabel("Немає вибраного файлу" if not file_path else f"🎵 {os.path.basename(file_path)}")
        self.file_list.setStyleSheet("background: #222; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.file_list)

        select_file_btn = QPushButton("Вибрати файл")
        select_file_btn.setStyleSheet("""
            QPushButton {
                background: #1e90ff; color: white; padding: 8px 12px; border: none; 
                border-radius: 8px; font-size: 14px; min-width: 100px;
            }
            QPushButton:hover { background: #0073e6; }
        """)
        select_file_btn.clicked.connect(self.select_file)
        layout.addWidget(select_file_btn)

        # Секція "Налаштування транскрибування"
        options_label = QLabel("Налаштування транскрибування")
        options_label.setStyleSheet("font-size: 18px; margin-top: 20px;")
        layout.addWidget(options_label)

        model_label = QLabel("Модель:")
        model_label.setStyleSheet("font-size: 14px; color: white;")
        self.model_select = QComboBox()
        self.model_select.addItems(["base", "small", "medium", "turbo"])
        self.model_select.setCurrentText("base")
        self.model_select.setStyleSheet("""
            background: #333; color: white; border: 1px solid #444; 
            padding: 5px; border-radius: 5px;
        """)
        layout.addWidget(model_label)
        layout.addWidget(self.model_select)

        language_label = QLabel("Мова файлу:")
        language_label.setStyleSheet("font-size: 14px; color: white;")
        self.language_select = QComboBox()
        self.language_select.addItems(["auto", "uk", "en"])
        self.language_select.setCurrentText("uk")
        self.language_select.setStyleSheet("""
            background: #333; color: white; border: 1px solid #444; 
            padding: 5px; border-radius: 5px;
        """)
        layout.addWidget(language_label)
        layout.addWidget(self.language_select)

        device_label = QLabel("Використовувати:")
        device_label.setStyleSheet("font-size: 14px; color: white;")
        self.device_select = QComboBox()
        self.device_select.addItems(["cpu", "cuda"])
        self.device_select.setStyleSheet("""
            background: #333; color: white; border: 1px solid #444; 
            padding: 5px; border-radius: 5px;
        """)
        layout.addWidget(device_label)
        layout.addWidget(self.device_select)

        # Кнопка "Почати транскрибувати"
        self.start_btn = QPushButton("Почати транскрибувати")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: #1e90ff; color: white; padding: 15px; border: none; 
                border-radius: 8px; font-size: 16px; margin-top: 20px;
            }
            QPushButton:disabled { background: #444; }
            QPushButton:hover { background: #0073e6; }
        """)
        self.start_btn.clicked.connect(self.start_transcription)
        self.start_btn.setEnabled(bool(file_path))
        layout.addWidget(self.start_btn)

        layout.addStretch()

    def set_file_path(self, file_path):
        self.file_path = file_path
        self.file_list.setText("Немає вибраного файлу" if not file_path else f"🎵 {os.path.basename(file_path)}")
        self.start_btn.setEnabled(bool(file_path))

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Вибрати файл", "", "Audio/Video Files (*.*)")
        if file_path:
            self.file_path = file_path
            self.file_list.setText(f"🎵 {os.path.basename(file_path)}")
            self.start_btn.setEnabled(True)

    def start_transcription(self):
        if not self.file_path:
            return
        self.parent.switch_to_result(self.file_path, self.model_select.currentText(), 
                                    self.language_select.currentText(), self.device_select.currentText())

    def back_to_main(self):
        self.parent.switch_to_main()