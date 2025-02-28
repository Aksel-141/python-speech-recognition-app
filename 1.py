import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QComboBox, QFileDialog, QTextEdit, 
                             QProgressBar, QSlider)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
import whisper
import json
import logging
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

# Твій код форматування часу
def format_time(seconds):
    hrs, rem = divmod(seconds, 3600)
    mins, secs = divmod(rem, 60)
    return f"{int(hrs):02}:{int(mins):02}:{int(secs):02}"

# Твій код транскрибування (трохи адаптований)
def transcribe_audio(file_path, model_name, language="uk", device="cpu", progress_callback=None):
    try:
        os.environ["WHISPER_MODELS_DIR"] = os.path.abspath("models")
        if progress_callback:
            progress_callback("Завантаження моделі розпізнавання аудіо..")
        model = whisper.load_model(model_name, device=device, download_root=os.environ["WHISPER_MODELS_DIR"])

        if language == "auto":
            if progress_callback:
                progress_callback("Автоматичне розпізнавання мови..")
            result = model.transcribe(file_path, task="detect-language")
            language = result['language']
            if progress_callback:
                progress_callback(f"Виявлена мова: {language}")

        if progress_callback:
            progress_callback("Транскрибування аудіо..")
        result = model.transcribe(file_path, language=language, fp16=True)
        
        transcription = []
        for segment in result['segments']:
            transcription.append({
                "start": segment['start'],
                "end": segment['end'],
                "time": f"{format_time(segment['start'])} - {format_time(segment['end'])}",
                "text": segment['text']
            })
        
        if progress_callback:
            progress_callback("Завершено")
        return transcription
    except Exception as e:
        if progress_callback:
            progress_callback(f"Помилка: {str(e)}")
        return {"error": str(e)}

# Головне вікно
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcription App v0.0.1")
        self.setGeometry(100, 100, 600, 400)
        self.setAcceptDrops(True)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        header = QLabel("Головна")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)

        self.new_transcript_btn = QPushButton("📝 Нове транскрибування")
        self.new_transcript_btn.clicked.connect(self.open_config_window)
        layout.addWidget(self.new_transcript_btn)

        self.drop_label = QLabel("Перетягніть файл сюди")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet("border: 2px dashed gray; padding: 20px;")
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
        self.config_window = ConfigWindow(file_path)
        self.config_window.show()
        self.hide()

# Вікно конфігурації
class ConfigWindow(QMainWindow):
    def __init__(self, file_path=None):
        super().__init__()
        self.setWindowTitle("Конфігурація обробки файлу")
        self.setGeometry(100, 100, 600, 500)
        self.file_path = file_path

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        back_btn = QPushButton("Назад")
        back_btn.clicked.connect(self.back_to_main)
        layout.addWidget(back_btn)

        header = QLabel("Конфігурація обробки файлу")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(header)

        # Секція файлів
        files_label = QLabel("Файли")
        layout.addWidget(files_label)
        self.file_list = QLabel("Немає вибраного файлу" if not file_path else f"🎵 {os.path.basename(file_path)}")
        layout.addWidget(self.file_list)
        select_file_btn = QPushButton("Вибрати файл")
        select_file_btn.clicked.connect(self.select_file)
        layout.addWidget(select_file_btn)

        # Налаштування транскрибування
        options_label = QLabel("Налаштування транскрибування")
        layout.addWidget(options_label)

        model_label = QLabel("Модель:")
        self.model_select = QComboBox()
        self.model_select.addItems(["base", "small", "medium", "turbo"])
        self.model_select.setCurrentText("base")
        layout.addWidget(model_label)
        layout.addWidget(self.model_select)

        language_label = QLabel("Мова файлу:")
        self.language_select = QComboBox()
        self.language_select.addItems(["auto", "uk", "en"])
        self.language_select.setCurrentText("uk")
        layout.addWidget(language_label)
        layout.addWidget(self.language_select)

        device_label = QLabel("Використовувати:")
        self.device_select = QComboBox()
        self.device_select.addItems(["cpu", "cuda"])
        layout.addWidget(device_label)
        layout.addWidget(self.device_select)

        self.start_btn = QPushButton("Почати транскрибувати")
        self.start_btn.clicked.connect(self.start_transcription)
        self.start_btn.setEnabled(bool(file_path))
        layout.addWidget(self.start_btn)

        layout.addStretch()

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Вибрати файл", "", "Audio/Video Files (*.*)")
        if file_path:
            self.file_path = file_path
            self.file_list.setText(f"🎵 {os.path.basename(file_path)}")
            self.start_btn.setEnabled(True)

    def start_transcription(self):
        if not self.file_path:
            return
        self.result_window = ResultWindow(self.file_path, self.model_select.currentText(), 
                                         self.language_select.currentText(), self.device_select.currentText())
        self.result_window.show()
        self.hide()

    def back_to_main(self):
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()

# Вікно результатів
class ResultWindow(QMainWindow):
    def __init__(self, file_path, model_name, language, device):
        super().__init__()
        self.setWindowTitle("Результати транскрибування")
        self.setGeometry(100, 100, 800, 600)
        self.file_path = file_path

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        back_btn = QPushButton("Назад")
        back_btn.clicked.connect(self.back_to_config)
        layout.addWidget(back_btn)

        header = QLabel("Результати транскрибування")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(header)

        self.progress_label = QLabel("Прогрес обробки: Очікування...")
        layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        self.transcription = []
        QTimer.singleShot(100, lambda: self.run_transcription(model_name, language, device))

    def update_progress(self, message):
        self.progress_label.setText(f"Прогрес обробки: {message}")
        if "Завантаження" in message:
            self.progress_bar.setValue(20)
        elif "Автоматичне" in message:
            self.progress_bar.setValue(40)
        elif "Транскрибування" in message:
            self.progress_bar.setValue(60)
        elif "Завершено" in message:
            self.progress_bar.setValue(100)
        elif "Помилка" in message:
            self.progress_bar.setValue(0)

    def run_transcription(self, model_name, language, device):
        transcription = transcribe_audio(self.file_path, model_name, language, device, self.update_progress)
        if "error" in transcription:
            self.output.setText(f"Помилка: {transcription['error']}")
        else:
            self.transcription = transcription
            text = "\n".join([f"{seg['time']} {seg['text']}" for seg in transcription])
            self.output.setText(text)

    def back_to_config(self):
        self.config_window = ConfigWindow(self.file_path)
        self.config_window.show()
        self.close()

# Запуск програми
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())