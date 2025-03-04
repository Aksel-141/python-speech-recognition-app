#config_window.py
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QFileDialog
from PyQt6.QtGui import QPixmap

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

        # Верхній рядок із кнопкою "Назад" та назвою
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

        header = QLabel("Конфігурація обробки файлу")
        header.setStyleSheet("font-size: 24px; color: white; margin-left: 10px;")
        top_layout.addWidget(header)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # Секція "Файли"
        files_label = QLabel("Файли")
        files_label.setStyleSheet("font-size: 18px; margin-top: 20px;")
        layout.addWidget(files_label)

        file_display_layout = QHBoxLayout()
        self.file_icon = QLabel()
        self.file_icon.setPixmap(QPixmap("path/to/audio_icon.png"))  # Замініть на реальний шлях до іконки
        self.file_icon.setFixedSize(20, 20)
        file_display_layout.addWidget(self.file_icon)

        self.file_list = QLabel("Немає вибраного файлу" if not file_path else f"{os.path.basename(file_path)}")
        self.file_list.setStyleSheet("background: #222; padding: 10px; border-radius: 5px; color: white;")
        file_display_layout.addWidget(self.file_list)

        clear_all_btn = QPushButton("Очистити")
        clear_all_btn.setStyleSheet("color: #1e90ff; background: none; border: none;")
        clear_all_btn.clicked.connect(self.clear_file)
        file_display_layout.addWidget(clear_all_btn)
        file_display_layout.addStretch()
        layout.addLayout(file_display_layout)

        select_file_btn = QPushButton("Вибрати файл")
        select_file_btn.setStyleSheet("""
            QPushButton {
                background: #444; color: white; padding: 8px 12px; border: none; 
                border-radius: 8px; font-size: 14px; min-width: 100px;
            }
            QPushButton:hover { background: #555; }
        """)
        select_file_btn.clicked.connect(self.select_file)
        layout.addWidget(select_file_btn)

        # Секція "Налаштування транскрибування"
        options_label = QLabel("Опції транскрибування")
        options_label.setStyleSheet("font-size: 18px; margin-top: 20px;")
        layout.addWidget(options_label)

        # Модель
        model_layout = QHBoxLayout()
        model_icon = QLabel()
        model_icon.setPixmap(QPixmap("path/to/model_icon.png"))  # Замініть на реальний шлях до іконки
        model_icon.setFixedSize(20, 20)
        model_layout.addWidget(model_icon)
        model_label = QLabel("Модель:")
        model_label.setStyleSheet("font-size: 14px; color: white;")
        model_layout.addWidget(model_label)
        self.model_select = QComboBox()
        self.model_select.addItems(["base", "small", "medium", "turbo", "tiny"])
        self.model_select.setCurrentText("base")
        self.model_select.setStyleSheet("""
            background: #333; color: white; border: 1px solid #444; 
            padding: 5px; border-radius: 5px;
        """)
        model_layout.addWidget(self.model_select)
        layout.addLayout(model_layout)

        # Мова
        language_layout = QHBoxLayout()
        language_icon = QLabel()
        language_icon.setPixmap(QPixmap("path/to/language_icon.png"))  # Замініть на реальний шлях до іконки
        language_icon.setFixedSize(20, 20)
        language_layout.addWidget(language_icon)
        language_label = QLabel("Мова транскрибування:")
        language_label.setStyleSheet("font-size: 14px; color: white;")
        language_layout.addWidget(language_label)
        self.language_select = QComboBox()
        self.language_select.addItems(["auto", "uk", "en"])
        self.language_select.setCurrentText("uk")
        self.language_select.setStyleSheet("""
            background: #333; color: white; border: 1px solid #444; 
            padding: 5px; border-radius: 5px;
        """)
        language_layout.addWidget(self.language_select)
        layout.addLayout(language_layout)

        # Пристрій
        device_layout = QHBoxLayout()
        device_icon = QLabel()
        device_icon.setPixmap(QPixmap("path/to/device_icon.png"))  # Замініть на реальний шлях до іконки
        device_icon.setFixedSize(20, 20)
        device_layout.addWidget(device_icon)
        device_label = QLabel("Пристрій:")
        device_label.setStyleSheet("font-size: 14px; color: white;")
        device_layout.addWidget(device_label)
        self.device_select = QComboBox()
        self.device_select.addItems(["cpu", "cuda"])
        self.device_select.setStyleSheet("""
            background: #333; color: white; border: 1px solid #444; 
            padding: 5px; border-radius: 5px;
        """)
        device_layout.addWidget(self.device_select)
        layout.addLayout(device_layout)


        # Кнопка "Почати транскрибувати"
        self.start_btn = QPushButton("Почати транскрибування")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: #444; color: white; padding: 15px; border: none; 
                border-radius: 8px; font-size: 16px; margin-top: 20px;
            }
            QPushButton:disabled { background: #333; }
            QPushButton:hover { background: #555; }
        """)
        self.start_btn.clicked.connect(self.start_transcription)
        self.start_btn.setEnabled(bool(file_path))
        layout.addWidget(self.start_btn)

        layout.addStretch()

    def set_file_path(self, file_path):
        self.file_path = file_path
        self.file_list.setText("Немає вибраного файлу" if not file_path else f"{os.path.basename(file_path)}")
        self.start_btn.setEnabled(bool(file_path))

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Вибрати файл", "", "Audio/Video Files (*.*)")
        if file_path:
            self.file_path = file_path
            self.file_list.setText(f"{os.path.basename(file_path)}")
            self.start_btn.setEnabled(True)

    def clear_file(self):
        self.file_path = None
        self.file_list.setText("Немає вибраного файлу")
        self.start_btn.setEnabled(False)

    def start_transcription(self):
        if not self.file_path:
            return
        self.parent.switch_to_result(self.file_path, self.model_select.currentText(), 
                                    self.language_select.currentText(), self.device_select.currentText())

    def back_to_main(self):
        self.parent.switch_to_main()