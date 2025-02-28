import os
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QFileDialog

class ConfigWindow(QMainWindow):
    def __init__(self, file_path=None):
        super().__init__()
        self.setWindowTitle("Конфігурація обробки файлу")
        self.setAcceptDrops(True)  # Додаємо підтримку drag-and-drop
        self.setStyleSheet("background-color: #121212; color: white; font-family: Arial, sans-serif;")
        self.file_path = file_path  # Додаємо визначення атрибуту file_path

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

        back_btn = QPushButton("Назад")
        back_btn.setStyleSheet("background: #1e90ff; color: white; padding: 5px; border: none; border-radius: 5px;")
        back_btn.clicked.connect(self.back_to_main)
        layout.addWidget(back_btn)

        header = QLabel("Конфігурація обробки файлу")
        header.setStyleSheet("font-size: 24px; border-bottom: 1px solid #333; padding-bottom: 10px;")
        layout.addWidget(header)

        files_label = QLabel("Файли")
        files_label.setStyleSheet("font-size: 18px; margin-top: 20px;")
        layout.addWidget(files_label)

        self.file_list = QLabel("Немає вибраного файлу" if not file_path else f"🎵 {os.path.basename(file_path)}")
        self.file_list.setStyleSheet("background: #222; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.file_list)

        select_file_btn = QPushButton("Вибрати файл")
        select_file_btn.setStyleSheet("background: #1e90ff; color: white; padding: 5px; border: none; border-radius: 5px;")
        select_file_btn.clicked.connect(self.select_file)
        layout.addWidget(select_file_btn)

        options_label = QLabel("Налаштування транскрибування")
        options_label.setStyleSheet("font-size: 18px; margin-top: 20px;")
        layout.addWidget(options_label)

        model_label = QLabel("Модель:")
        self.model_select = QComboBox()
        self.model_select.addItems(["base", "small", "medium", "turbo"])
        self.model_select.setCurrentText("base")
        self.model_select.setStyleSheet("background: #333; color: white; border: 1px solid #444; padding: 5px; border-radius: 5px;")
        layout.addWidget(model_label)
        layout.addWidget(self.model_select)

        language_label = QLabel("Мова файлу:")
        self.language_select = QComboBox()
        self.language_select.addItems(["auto", "uk", "en"])
        self.language_select.setCurrentText("uk")
        self.language_select.setStyleSheet("background: #333; color: white; border: 1px solid #444; padding: 5px; border-radius: 5px;")
        layout.addWidget(language_label)
        layout.addWidget(self.language_select)

        device_label = QLabel("Використовувати:")
        self.device_select = QComboBox()
        self.device_select.addItems(["cpu", "cuda"])
        self.device_select.setStyleSheet("background: #333; color: white; border: 1px solid #444; padding: 5px; border-radius: 5px;")
        layout.addWidget(device_label)
        layout.addWidget(self.device_select)

        self.start_btn = QPushButton("Почати транскрибувати")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: #1e90ff; color: white; padding: 15px; border: none; 
                border-radius: 5px; font-size: 16px; margin-top: 20px;
            }
            QPushButton:disabled { background: #444; }
            QPushButton:hover { background: #0073e6; }
        """)
        self.start_btn.clicked.connect(self.start_transcription)
        self.start_btn.setEnabled(bool(file_path))
        layout.addWidget(self.start_btn)

        layout.addStretch()

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Вибрати файл", "", "Audio/Video Files (*.*)")
        if file_path:
            self.file_path = file_path  # Визначаємо атрибут file_path
            self.file_list.setText(f"🎵 {os.path.basename(file_path)}")
            self.start_btn.setEnabled(True)

    def start_transcription(self):
        if not self.file_path:
            return
        from result_window import ResultWindow
        self.result_window = ResultWindow(self.file_path, self.model_select.currentText(), 
                                         self.language_select.currentText(), self.device_select.currentText())
        self.result_window.showMaximized()  # Відкриваємо результат на весь екран
        self.hide()

    def back_to_main(self):
        from main_window import MainWindow
        self.main_window = MainWindow()
        self.main_window.showMaximized()  # Відкриваємо головне вікно на весь екран
        self.close()

    def show(self):
        super().showMaximized()  # Відкриваємо вікно на весь екран

    def resizeEvent(self, event):
        container_widget = self.centralWidget().layout().itemAt(1).widget()
        container_widget.setMaximumWidth(int(self.width() * 0.75))
        container_widget.setMinimumWidth(int(self.width() * 0.75))
        super().resizeEvent(event)