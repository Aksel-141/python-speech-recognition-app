# hmm_result.py
import os
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QProgressBar,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
)
from PyQt6.QtCore import Qt, QThread, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from hmm_transcription import HMMTranscriptionWorker


class HMMResultWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.file_path = None
        self.setStyleSheet(
            "background-color: #121212; color: white; font-family: Arial, sans-serif;"
        )
        self.setWindowTitle("HMM Transcription Result")

        # Основний макет
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Верхня панель
        top_layout = QHBoxLayout()

        # Кнопка "Назад"
        self.back_btn = QPushButton("⬅ Назад")
        self.back_btn.setStyleSheet(
            "background: #444; color: white; padding: 8px 12px; border: none; border-radius: 8px; font-size: 14px;"
        )
        self.back_btn.clicked.connect(self.back_to_main)
        top_layout.addWidget(self.back_btn)

        # Кнопка "Вибрати файл"
        self.select_file_btn = QPushButton("Вибрати файл")
        self.select_file_btn.setStyleSheet(
            "background: #444; color: white; padding: 8px 12px; border: none; border-radius: 8px; font-size: 14px;"
        )
        self.select_file_btn.clicked.connect(self.select_file)
        top_layout.addWidget(self.select_file_btn)

        # Мітка файлу
        self.file_label = QLabel("Файл: Не вибрано")
        self.file_label.setStyleSheet("font-size: 18px;")
        top_layout.addWidget(self.file_label)
        top_layout.addStretch()

        # Кнопка "Зберегти як..."
        self.export_btn = QPushButton("Зберегти як...")
        self.export_btn.setStyleSheet(
            "background: #444; color: white; padding: 8px 12px; border: none; border-radius: 8px; font-size: 14px;"
        )
        self.export_btn.clicked.connect(self.export_transcription)
        self.export_btn.setEnabled(False)
        top_layout.addWidget(self.export_btn)
        layout.addLayout(top_layout)

        # Кнопка "Почати транскрибування"
        self.start_btn = QPushButton("Почати транскрибування")
        self.start_btn.setStyleSheet(
            """
            QPushButton {
                background: #1e90ff; color: white; padding: 15px; border: none; 
                border-radius: 8px; font-size: 16px; margin-top: 20px;
            }
            QPushButton:disabled { background: #333; }
            QPushButton:hover { background: #0073e6; }
        """
        )
        self.start_btn.clicked.connect(self.start_transcription_thread)
        self.start_btn.setEnabled(False)
        layout.addWidget(self.start_btn)

        # Прогрес
        self.progress_label = QLabel("Прогрес обробки: Очікування...")
        self.progress_label.setStyleSheet("font-size: 18px; margin-top: 20px;")
        layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background: #333; border-radius: 5px; } QProgressBar::chunk { background: #007bff; }"
        )
        layout.addWidget(self.progress_bar)

        # Список транскрипції
        self.transcription_list = QListWidget()
        self.transcription_list.setStyleSheet(
            "background: #222; color: white; border: none; font-size: 14px; padding: 10px;"
        )
        layout.addWidget(self.transcription_list)

        # Медіаплеєр
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        self.transcription = []
        self.thread = None  # Ініціалізуємо thread як None
        self.worker = None  # Ініціалізуємо worker як None

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Вибрати аудіофайл", "", "Audio Files (*.wav *.mp3)"
        )
        if file_path:
            self.file_path = file_path
            self.file_label.setText(f"Файл: {os.path.basename(file_path)}")
            self.player.setSource(QUrl.fromLocalFile(file_path))
            self.start_btn.setEnabled(True)
            self.transcription_list.clear()
            self.export_btn.setEnabled(False)
            self.progress_label.setText("Прогрес обробки: Очікування...")
            self.progress_bar.setValue(0)

    def start_transcription_thread(self):
        if not self.file_path:
            return
        self.transcription_list.clear()
        self.export_btn.setEnabled(False)
        self.worker = HMMTranscriptionWorker(self.file_path)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_transcription_finished)
        self.worker.error.connect(self.on_transcription_error)
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.cleanup_thread)
        self.thread.start()

    def cleanup_thread(self):
        if self.thread and isinstance(
            self.thread, QThread
        ):  # Перевіряємо, чи thread існує і є QThread
            if self.thread.isRunning():
                self.thread.quit()
                self.thread.wait()
            self.thread.deleteLater()
        if self.worker:
            self.worker.deleteLater()
        self.thread = None
        self.worker = None

    def update_progress(self, message):
        self.progress_label.setText(f"Прогрес обробки: {message}")
        if "Завантаження" in message:
            self.progress_bar.setValue(20)
        elif "Тренування" in message:
            self.progress_bar.setValue(40)
        elif "Розпізнавання" in message:
            self.progress_bar.setValue(60)
        elif "Завершено" in message:
            self.progress_bar.setValue(100)
        elif "Помилка" in message:
            self.progress_bar.setValue(0)

    def on_transcription_finished(self, transcription):
        self.transcription = transcription
        self.transcription_list.clear()
        for segment in transcription:
            item = QListWidgetItem(
                f"{segment['start']:.2f}s - {segment['end']:.2f}s: {segment['text']}"
            )
            self.transcription_list.addItem(item)
        self.cleanup_thread()
        self.export_btn.setEnabled(True)

    def on_transcription_error(self, error):
        self.transcription_list.addItem(f"Помилка: {error}")
        self.cleanup_thread()

    def export_transcription(self):
        if not self.transcription:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Експортувати транскрипцію", "", "Text files (*.txt)"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                for segment in self.transcription:
                    f.write(
                        f"{segment['start']:.2f}s - {segment['end']:.2f}s: {segment['text']}\n"
                    )

    def back_to_main(self):
        if self.parent:
            self.player.stop()
            self.cleanup_thread()
            self.parent.switch_to_main()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = HMMResultWindow()
    window.show()
    sys.exit(app.exec())
