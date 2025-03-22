# hmm_result.py
import os
import numpy as np
import librosa
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
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
    QSpinBox,
    QDoubleSpinBox,
)
from PyQt6.QtCore import Qt, QThread, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from hmm_transcription import HMMTranscriptionWorker


class HMMResultWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.file_path = None
        self.audio_data = None
        self.sample_rate = None
        self.segments = []
        self.setStyleSheet(
            "background-color: #121212; color: white; font-family: Arial, sans-serif;"
        )
        self.setWindowTitle("HMM Transcription Result")

        # Основний макет
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Верхня панель
        top_layout = QHBoxLayout()
        self.back_btn = QPushButton("⬅ Назад")
        self.back_btn.setStyleSheet(
            "background: #444; color: white; padding: 8px 12px; border: none; border-radius: 8px; font-size: 14px;"
        )
        self.back_btn.clicked.connect(self.back_to_main)
        top_layout.addWidget(self.back_btn)

        self.select_file_btn = QPushButton("Вибрати файл")
        self.select_file_btn.setStyleSheet(
            "background: #444; color: white; padding: 8px 12px; border: none; border-radius: 8px; font-size: 14px;"
        )
        self.select_file_btn.clicked.connect(self.select_file)
        top_layout.addWidget(self.select_file_btn)

        self.file_label = QLabel("Файл: Не вибрано")
        self.file_label.setStyleSheet("font-size: 18px;")
        top_layout.addWidget(self.file_label)
        top_layout.addStretch()

        self.export_btn = QPushButton("Зберегти як...")
        self.export_btn.setStyleSheet(
            "background: #444; color: white; padding: 8px 12px; border: none; border-radius: 8px; font-size: 14px;"
        )
        self.export_btn.clicked.connect(self.export_transcription)
        self.export_btn.setEnabled(False)
        top_layout.addWidget(self.export_btn)
        layout.addLayout(top_layout)

        # Налаштування
        settings_layout = QHBoxLayout()
        settings_label = QLabel("Налаштування:")
        settings_label.setStyleSheet("font-size: 16px;")
        settings_layout.addWidget(settings_label)

        self.top_db_spin = QDoubleSpinBox()
        self.top_db_spin.setRange(5.0, 50.0)
        self.top_db_spin.setValue(20.0)
        self.top_db_spin.setSingleStep(1.0)
        self.top_db_spin.setPrefix("top_db: ")
        settings_layout.addWidget(self.top_db_spin)

        self.n_mfcc_spin = QSpinBox()
        self.n_mfcc_spin.setRange(5, 20)
        self.n_mfcc_spin.setValue(13)
        self.n_mfcc_spin.setPrefix("n_mfcc: ")
        settings_layout.addWidget(self.n_mfcc_spin)

        self.min_segment_spin = QDoubleSpinBox()
        self.min_segment_spin.setRange(0.05, 1.0)
        self.min_segment_spin.setValue(0.1)
        self.min_segment_spin.setSingleStep(0.05)
        self.min_segment_spin.setPrefix("min_segment (s): ")
        settings_layout.addWidget(self.min_segment_spin)

        self.min_pause_spin = QDoubleSpinBox()
        self.min_pause_spin.setRange(0.05, 1.0)
        self.min_pause_spin.setValue(0.2)
        self.min_pause_spin.setSingleStep(0.05)
        self.min_pause_spin.setPrefix("min_pause (s): ")
        settings_layout.addWidget(self.min_pause_spin)

        layout.addLayout(settings_layout)

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

        # Візуалізація аудіо
        self.figure, self.ax = plt.subplots(figsize=(10, 2))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: #222;")
        layout.addWidget(self.canvas)

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
        self.thread = None
        self.worker = None

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
            self.load_and_plot_audio()

    def load_and_plot_audio(self):
        self.audio_data, self.sample_rate = librosa.load(self.file_path, sr=None)
        self.ax.clear()
        time = np.linspace(
            0, len(self.audio_data) / self.sample_rate, num=len(self.audio_data)
        )
        self.ax.plot(time, self.audio_data, color="#007bff")
        self.ax.set_title("Аудіохвиля", color="white")
        self.ax.set_xlabel("Час (с)", color="white")
        self.ax.set_ylabel("Амплітуда", color="white")
        self.ax.set_facecolor("#222")
        self.figure.set_facecolor("#121212")
        self.ax.tick_params(colors="white")
        self.canvas.draw()

    def start_transcription_thread(self):
        if not self.file_path:
            return
        self.transcription_list.clear()
        self.export_btn.setEnabled(False)
        self.worker = HMMTranscriptionWorker(
            self.file_path,
            top_db=self.top_db_spin.value(),
            n_mfcc=self.n_mfcc_spin.value(),
            min_segment_length=self.min_segment_spin.value(),
            min_pause_length=self.min_pause_spin.value(),
        )
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_transcription_finished)
        self.worker.error.connect(self.on_transcription_error)
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.cleanup_thread)
        self.thread.start()

    def cleanup_thread(self):
        if self.thread and isinstance(self.thread, QThread):
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
        self.segments = [(seg["start"], seg["end"]) for seg in transcription]
        self.plot_segments()
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

    def plot_segments(self):
        self.ax.clear()
        time = np.linspace(
            0, len(self.audio_data) / self.sample_rate, num=len(self.audio_data)
        )
        self.ax.plot(time, self.audio_data, color="#007bff")
        for start, end in self.segments:
            self.ax.axvspan(start, end, color="yellow", alpha=0.3)
        self.ax.set_title("Аудіохвиля з сегментами", color="white")
        self.ax.set_xlabel("Час (с)", color="white")
        self.ax.set_ylabel("Амплітуда", color="white")
        self.ax.set_facecolor("#222")
        self.figure.set_facecolor("#121212")
        self.ax.tick_params(colors="white")
        self.canvas.draw()

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
