# result_windw.py
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
    QMessageBox,
    QDialog,
    QApplication,
)
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtGui import QFont, QMovie
from PyQt6.QtCore import Qt, QUrl, QThread, pyqtSignal, QObject
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from transcription import transcribe_audio


class TranscriptionWorker(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, file_path, model_name, language, device):
        super().__init__()
        self.file_path = file_path
        self.model_name = model_name
        self.language = language
        self.device = device
        self._stop_requested = False

    def stop(self):
        self._stop_requested = True  # Метод для встановлення прапора зупинки

    def run(self):
        transcription = transcribe_audio(
            self.file_path,
            self.model_name,
            self.language,
            self.device,
            self.update_progress,
            # stop_flag=lambda: self._stop_requested,
        )
        if "error" in transcription:
            self.error.emit(transcription["error"])
        elif self._stop_requested:
            self.error.emit("Транскрибування перервано користувачем")
        else:
            self.finished.emit(transcription)

    def update_progress(self, message):
        self.progress.emit(message)



class ResultWindow(QWidget):
    def __init__(self, parent, file_path, model_name, language, device):
        super().__init__()
        self.parent = parent
        self.file_path = file_path
        self.model_name = model_name
        self.language = language
        self.device = device
        self.is_video = file_path.lower().endswith((".mp4", ".mkv", ".avi", ".mov"))
        self.setStyleSheet(
            "background-color: #121212; color: white; font-family: Arial, sans-serif;"
        )
        self.setWindowTitle("Result Window")
        # print(f"Initial is_video: {self.is_video}")

        # Основний макет
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(10)

        # 1. Верхня панель із кнопкою "Назад", назвою файлу та кнопкою "Export"
        top_layout = QHBoxLayout()
        back_btn = QPushButton("⬅ Назад")
        back_btn.setStyleSheet(
            """
            QPushButton {
                background: #444; color: white; padding: 8px 12px; border: none; 
                border-radius: 8px; font-size: 14px; min-width: 80px;
            }
            QPushButton:hover { background: #555; }
        """
        )
        back_btn.clicked.connect(self.back_to_config)
        top_layout.addWidget(back_btn)

        file_name_label = QLabel(os.path.basename(self.file_path))
        file_name_label.setStyleSheet(
            "font-size: 18px; color: white; margin-left: 10px;"
        )
        top_layout.addWidget(file_name_label)
        top_layout.addStretch()
        self.export_btn = QPushButton("Зберегти як..")
        self.export_btn.clicked.connect(self.export_transcription)
        self.export_btn.setStyleSheet(
            """
            QPushButton {
                background: #444; color: white; padding: 8px 12px; border: none; 
                border-radius: 8px; font-size: 14px; min-width: 80px;
            }
            QPushButton:hover { background: #555; }
        """
        )
        self.export_btn.setEnabled(False)  # Вимкнути кнопку за замовчуванням
        top_layout.addWidget(self.export_btn)
        self.main_layout.addLayout(top_layout)

        # 2. Область перегляду
        self.media_layout = QVBoxLayout()
        self.main_layout.addLayout(self.media_layout)

        # 3. Нижня панель із контролями
        bottom_layout = QHBoxLayout()
        self.timestamp = QLabel("00:00 / 00:00")
        self.timestamp.setStyleSheet("font-size: 12px; color: #999;")
        bottom_layout.addWidget(self.timestamp)

        back_btn = QPushButton("⏪")
        back_btn.setStyleSheet(
            """
            QPushButton {
                background: #444; color: white; border: none; 
                font-size: 16px; padding: 5px; border-radius: 8px;
            }
            QPushButton:hover { background: #555; }
        """
        )
        back_btn.clicked.connect(lambda: self.seek(-5))
        bottom_layout.addWidget(back_btn)

        self.play_btn = QPushButton("▶️")
        self.play_btn.setStyleSheet(
            """
            QPushButton {
                background: #444; color: white; border: none; 
                font-size: 16px; padding: 5px; border-radius: 8px;
            }
            QPushButton:hover { background: #555; }
        """
        )
        self.play_btn.clicked.connect(self.toggle_play)
        bottom_layout.addWidget(self.play_btn)

        next_btn = QPushButton("⏩")
        next_btn.setStyleSheet(
            """
            QPushButton {
                background: #444; color: white; border: none; 
                font-size: 16px; padding: 5px; border-radius: 8px;
            }
            QPushButton:hover { background: #555; }
        """
        )
        next_btn.clicked.connect(lambda: self.seek(5))
        bottom_layout.addWidget(next_btn)

        self.progress_bar_media = QProgressBar()
        self.progress_bar_media.setStyleSheet(
            """
            QProgressBar { 
                background: #333; 
                height: 5px; 
                border-radius: 5px; 
            } 
            QProgressBar::chunk { 
                background: #007bff; 
            }
        """
        )
        self.progress_bar_media.setValue(0)
        bottom_layout.addWidget(self.progress_bar_media, stretch=1)

        self.speed_label = QLabel("1.00x")
        self.speed_label.setStyleSheet("font-size: 12px; color: #999;")
        self.speed_label.mousePressEvent = self.change_speed
        bottom_layout.addWidget(self.speed_label)
        self.main_layout.addLayout(bottom_layout)

        # 4. Прогрес транскрипції
        progress_layout = QVBoxLayout()
        self.progress_label = QLabel("Прогрес обробки: Очікування...")
        self.progress_label.setStyleSheet("font-size: 18px; margin-top: 20px;")
        progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background: #333; border-radius: 5px; } QProgressBar::chunk { background: #007bff; }"
        )
        progress_layout.addWidget(self.progress_bar)
        self.main_layout.addLayout(progress_layout)

        # 5. Розділ транскрипції
        self.transcription_list = QListWidget()
        self.transcription_list.setStyleSheet(
            """
            QListWidget {
                background: #222; 
                color: white; 
                border: none; 
                font-size: 14px; 
                padding: 10px;
            }
            QListWidget::item { 
                background: #333; 
                padding: 5px; 
                margin-bottom: 5px; 
                border-radius: 5px; 
            }
        """
        )
        self.main_layout.addWidget(self.transcription_list)

        # Ініціалізація медіаплеєра
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)

        self.transcription = []
        self.setup_media()  # Викликаємо після ініціалізації player
        self.start_transcription_thread()

    def setup_media(self):
        """Налаштування медіа віджета залежно від типу файлу."""
        # Видаляємо старий медіа віджет, якщо він існує
        if hasattr(self, "media_widget") and self.media_widget:
            if (
                self.media_layout.indexOf(self.media_widget) != -1
            ):  # Перевіряємо, чи віджет у layout
                self.media_layout.removeWidget(self.media_widget)
            if (
                isinstance(self.media_widget, QWidget)
                and not self.media_widget.parent()
            ):
                self.media_widget.deleteLater()
            self.media_widget = None

        # Видаляємо quote_label, якщо існує
        if hasattr(self, "quote_label") and self.quote_label:
            if (
                self.media_layout.indexOf(self.quote_label) != -1
            ):  # Перевіряємо, чи віджет у layout
                self.media_layout.removeWidget(self.quote_label)
            if isinstance(self.quote_label, QWidget) and not self.quote_label.parent():
                self.quote_label.deleteLater()
            self.quote_label = None

        if self.is_video:
            self.media_widget = QVideoWidget()
            self.media_widget.setStyleSheet(
                "background-color: #000; border-radius: 5px;"
            )
            self.media_widget.setMinimumHeight(300)
            self.player.setVideoOutput(self.media_widget)
            self.media_layout.addWidget(self.media_widget)

            # Накладений текст (цитата)
            self.quote_label = QLabel("Субтитри...")
            self.quote_label.setStyleSheet(
                "background: transparent; color: white; font-size: 16px; padding: 10px;"
            )
            self.quote_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.media_layout.addWidget(
                self.quote_label,
                alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
            )
        else:
            self.media_widget = QLabel(
                f"Відтворюється аудіо: {os.path.basename(self.file_path)}"
            )
            self.media_widget.setStyleSheet(
                "font-size: 14px; color: #999; margin-top: 10px;"
            )
            self.media_layout.addWidget(self.media_widget)

        self.player.setSource(QUrl.fromLocalFile(self.file_path))

    def save_as_text(self, file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            for segment in self.transcription:
                f.write(f"{segment['text']} ")

    def save_as_srt(self, file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(self.transcription, start=1):
                start_time = self.format_time_srt(segment["start"])
                end_time = self.format_time_srt(segment["end"])
                f.write(f"{i}\n{start_time} --> {end_time}\n{segment['text']}\n\n")

    def export_transcription(self):
        if not self.transcription:
            return  # Нічого не робити, якщо транскрипція порожня

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Експортувати транскрипцію",
            "",
            "Text files (*.txt);;SRT files (*.srt)",
        )

        if file_path:
            if selected_filter == "Text files (*.txt)" or file_path.endswith(".txt"):
                self.save_as_text(file_path)
            elif selected_filter == "SRT files (*.srt)" or file_path.endswith(".srt"):
                self.save_as_srt(file_path)

    def start_transcription_thread(self):
        self.worker = TranscriptionWorker(
            self.file_path, self.model_name, self.language, self.device
        )
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_transcription_finished)
        self.worker.error.connect(self.on_transcription_error)
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.quit)
        self.thread.start()

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

    def on_transcription_finished(self, transcription):
        self.transcription = transcription
        for segment in transcription:
            start_pos = len(
                str(self.transcription_list.count())
            )  # Позиція для відстеження
            segment_text = f"{segment['time']} {segment['text']}"
            item = QListWidgetItem(segment_text)
            item.setFont(QFont("Arial", 14))
            self.transcription_list.addItem(item)
            segment["start_pos"] = start_pos  # Зберігаємо позицію для виділення
            segment["length"] = len(segment_text)
        self.thread.quit()
        self.export_btn.setEnabled(True)

    def on_transcription_error(self, error):
        self.transcription_list.addItem(QListWidgetItem(f"Помилка: {error}"))
        self.thread.quit()

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_btn.setText("▶️")
        else:
            self.player.play()
            self.play_btn.setText("⏸️")

    def seek(self, seconds):
        if self.player.isAvailable():
            current_position = self.player.position()
            new_position = current_position + (seconds * 1000)
            self.player.setPosition(max(0, min(new_position, self.player.duration())))

    def update_position(self, position):
        duration = self.player.duration()
        if duration > 0:
            progress = (position / duration) * 100
            self.progress_bar_media.setValue(int(progress))
            minutes = position // 60000
            seconds = (position % 60000) // 1000
            total_minutes = duration // 60000
            total_seconds = (duration % 60000) // 1000
            self.timestamp.setText(
                f"{minutes:02}:{seconds:02} / {total_minutes:02}:{total_seconds:02}"
            )
            self.highlight_segment(position / 1000)

    def update_duration(self, duration):
        if duration > 0:
            self.progress_bar_media.setMaximum(100)

    def highlight_segment(self, current_time):
        for i in range(self.transcription_list.count()):
            item = self.transcription_list.item(i)
            segment = self.transcription[i] if i < len(self.transcription) else None
            if segment and segment["start"] <= current_time <= segment["end"]:
                item.setBackground(Qt.GlobalColor.yellow)
                # Оновлюємо цитату для відео
                if self.is_video and hasattr(self, "quote_label") and self.quote_label:
                    self.quote_label.setText(segment["text"])
            else:
                item.setBackground(Qt.GlobalColor.transparent)

    def format_time_srt(self, seconds):
        hrs, rem = divmod(seconds, 3600)
        mins, rem = divmod(rem, 60)
        secs, ms = divmod(rem, 1)
        ms = int(ms * 1000)
        return f"{int(hrs):02}:{int(mins):02}:{int(secs):02},{ms:03}"

    def change_speed(self, event):
        current_speed = float(self.speed_label.text().replace("x", ""))
        if event.button() == Qt.MouseButton.LeftButton:
            new_speed = min(current_speed + 0.5, 3.0)
        elif event.button() == Qt.MouseButton.RightButton:
            new_speed = max(current_speed - 0.5, 0.5)
        else:
            return
        self.speed_label.setText(f"{new_speed:.2f}x")
        self.player.setPlaybackRate(new_speed)

    def update_content(self, file_path, model_name, language, device):
        self.reset()
        self.file_path = file_path
        self.model_name = model_name
        self.language = language
        self.device = device
        self.is_video = file_path.lower().endswith((".mp4", ".mkv", ".avi", ".mov"))
        # print(f"Updated is_video: {self.is_video}")
        self.setup_media()
        self.start_transcription_thread()

    def reset(self):
        self.file_path = None
        self.model_name = None
        self.language = None
        self.device = None
        self.is_video = False
        self.progress_bar.setValue(0)
        self.transcription_list.clear()
        self.transcription = []
        self.player.stop()
        self.player.setSource(QUrl())
        self.player.setVideoOutput(None)
        self.progress_label.setText("Прогрес обробки: Очікування...")
        self.progress_bar_media.setValue(0)
        self.timestamp.setText("00:00 / 00:00")
        self.speed_label.setText("1.00x")
        self.export_btn.setEnabled(False)

        if hasattr(self, "thread") and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()

        # Видаляємо медіа віджет, якщо він існує
        if hasattr(self, "media_widget") and self.media_widget:
            if self.media_layout.indexOf(self.media_widget) != -1:
                self.media_layout.removeWidget(self.media_widget)
            if (
                isinstance(self.media_widget, QWidget)
                and not self.media_widget.parent()
            ):
                self.media_widget.deleteLater()
            self.media_widget = None

        # Видаляємо quote_label, якщо існує
        if hasattr(self, "quote_label") and self.quote_label:
            if self.media_layout.indexOf(self.quote_label) != -1:
                self.media_layout.removeWidget(self.quote_label)
            if isinstance(self.quote_label, QWidget) and not self.quote_label.parent():
                self.quote_label.deleteLater()
            self.quote_label = None

    def confirm_interrupt_transcription(self):
        if hasattr(self, "thread") and self.thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Перервати транскрибування?",
                "Транскрибування ще триває. Ви дійсно хочете перервати процес?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                if hasattr(self, "worker"):
                    self.worker.stop()
                self.thread.terminate()  # Негайно завершуємо потік
                self.thread.wait()

                # Очищення ресурсів
                self.thread.deleteLater()
                self.worker.deleteLater()

                self.progress_label.setText("Прогрес обробки: Перервано")
                self.progress_bar.setValue(0)
                return True
            return False
        return True

    def back_to_config(self):
        if self.confirm_interrupt_transcription():
            self.reset()
            self.parent.switch_to_config(self.file_path)

    def closeEvent(self, event):
        if not self.confirm_interrupt_transcription():
            event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = ResultWindow(None, "path/to/your/file.mp4", "base", "en", "cpu")
    window.show()
    sys.exit(app.exec())
