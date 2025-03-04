import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QProgressBar
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtGui import QTextCursor, QTextCharFormat
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from transcription import transcribe_audio

class ResultWindow(QWidget):
    def __init__(self, parent, file_path, model_name, language, device):
        super().__init__()
        self.parent = parent
        self.file_path = file_path
        self.model_name = model_name
        self.language = language
        self.device = device
        self.is_video = file_path.lower().endswith((".mp4", ".mkv", ".avi", ".mov"))
        self.setStyleSheet("background-color: #121212; color: white; font-family: Arial, sans-serif;")
        print(f"Initial is_video: {self.is_video}")

        # Основний layout
        main_layout = QHBoxLayout(self)
        main_layout.addStretch()

        container_widget = QWidget()
        container_widget.setMaximumWidth(int(parent.width() * 0.75))
        container_widget.setMinimumWidth(int(parent.width() * 0.75))
        main_layout.addWidget(container_widget)
        main_layout.addStretch()

        self.layout = QVBoxLayout(container_widget)
        self.layout.setContentsMargins(20, 20, 20, 20)

        # Кнопка "Назад"
        back_btn = QPushButton("Назад")
        back_btn.setStyleSheet("background: #1e90ff; color: white; padding: 5px; border: none; border-radius: 5px;")
        back_btn.clicked.connect(self.back_to_config)
        self.layout.addWidget(back_btn)

        # Заголовок
        header_layout = QHBoxLayout()
        header = QLabel("Результати транскрибування")
        header.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(header)
        export_btn = QPushButton("Export")
        export_btn.setStyleSheet("""
            QPushButton {
                background: #1e90ff; color: white; padding: 5px 15px; border: none; 
                border-radius: 5px; cursor: pointer; float: right; margin-top: 10px;
            }
            QPushButton:hover { background: #0073e6; }
        """)
        header_layout.addWidget(export_btn)
        self.layout.addLayout(header_layout)

        # Прогрес
        self.progress_label = QLabel("Прогрес обробки: Очікування...")
        self.progress_label.setStyleSheet("font-size: 18px; margin-top: 20px;")
        self.layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("QProgressBar { background: #333; border-radius: 5px; } QProgressBar::chunk { background: #007bff; }")
        self.layout.addWidget(self.progress_bar)

        # Медіа віджет (буде додано пізніше в setup_media)
        self.media_widget = None

        # Контролери
        controls_widget = QWidget()
        controls_widget.setStyleSheet("background-color: #000;")
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(10, 10, 10, 10)

        self.timestamp = QLabel("00:00 / 00:00")
        self.timestamp.setStyleSheet("font-size: 12px; color: #999;")
        controls_layout.addWidget(self.timestamp)

        back_btn = QPushButton("⏪")
        back_btn.setStyleSheet("background: none; color: white; border: none; font-size: 16px;")
        back_btn.clicked.connect(lambda: self.seek(-5))
        controls_layout.addWidget(back_btn)

        play_btn = QPushButton("▶️")
        play_btn.setStyleSheet("background: none; color: white; border: none; font-size: 16px;")
        play_btn.clicked.connect(self.toggle_play)
        controls_layout.addWidget(play_btn)

        next_btn = QPushButton("⏩")
        next_btn.setStyleSheet("background: none; color: white; border: none; font-size: 16px;")
        next_btn.clicked.connect(lambda: self.seek(5))
        controls_layout.addWidget(next_btn)

        self.progress_bar_media = QProgressBar()
        self.progress_bar_media.setStyleSheet("QProgressBar { background: #333; height: 5px; border-radius: 5px; } QProgressBar::chunk { background: #007bff; }")
        self.progress_bar_media.setValue(0)
        controls_layout.addWidget(self.progress_bar_media)

        self.speed_label = QLabel("1.00x")
        self.speed_label.setStyleSheet("font-size: 12px; color: #999;")
        self.speed_label.mousePressEvent = self.change_speed
        controls_layout.addWidget(self.speed_label)

        self.layout.addWidget(controls_widget)

        # Вивід тексту
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("background: #222; color: #ccc; border: none; font-size: 14px; margin-top: 10px;")
        self.layout.addWidget(self.output)

        # Ініціалізація плеєра
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)

        self.transcription = []
        self.setup_media()  # Налаштування медіа
        QTimer.singleShot(100, self.run_transcription)

    def setup_media(self):
        """Налаштування медіа віджета залежно від типу файлу."""
        if self.media_widget:
            self.layout.removeWidget(self.media_widget)
            self.media_widget.deleteLater()
            self.media_widget = None

        if self.is_video:
            self.media_widget = QVideoWidget()
            self.media_widget.setStyleSheet("background-color: #000; border-radius: 5px;")
            self.media_widget.setMinimumHeight(300)
            self.player.setVideoOutput(self.media_widget)
        else:
            self.media_widget = QLabel(f"Відтворюється аудіо: {os.path.basename(self.file_path)}")
            self.media_widget.setStyleSheet("font-size: 14px; color: #999; margin-top: 10px;")
            self.player.setVideoOutput(None)  # Без відеовиходу для аудіо

        self.layout.insertWidget(3, self.media_widget)  # Вставляємо перед контролями
        self.player.setSource(QUrl.fromLocalFile(self.file_path))

    def update_content(self, file_path, model_name, language, device):
        """Оновлення вмісту при зміні файлу."""
        self.reset()
        self.file_path = file_path
        self.model_name = model_name
        self.language = language
        self.device = device
        self.is_video = file_path.lower().endswith((".mp4", ".mkv", ".avi", ".mov"))
        print(f"Updated is_video: {self.is_video}")
        self.setup_media()
        QTimer.singleShot(100, self.run_transcription)

    def seek(self, seconds):
        if self.player.isAvailable():
            current_position = self.player.position()
            new_position = current_position + (seconds * 1000)
            self.player.setPosition(max(0, min(new_position, self.player.duration())))

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def update_position(self, position):
        duration = self.player.duration()
        if duration > 0:
            progress = (position / duration) * 100
            self.progress_bar_media.setValue(int(progress))
            minutes = position // 60000
            seconds = (position % 60000) // 1000
            total_minutes = duration // 60000
            total_seconds = (duration % 60000) // 1000
            self.timestamp.setText(f"{minutes:02}:{seconds:02} / {total_minutes:02}:{total_seconds:02}")
            self.highlight_segment(position / 1000)

    def update_duration(self, duration):
        if duration > 0:
            self.progress_bar_media.setMaximum(100)

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

    def run_transcription(self):
        transcription = transcribe_audio(self.file_path, self.model_name, self.language, self.device, self.update_progress)
        if "error" in transcription:
            self.output.setText(f"Помилка: {transcription['error']}")
        else:
            self.transcription = transcription
            text = ""
            for segment in transcription:
                start_pos = len(text)
                segment_text = f"{segment['time']} {segment['text']}\n"
                text += segment_text
                segment['start_pos'] = start_pos
                segment['length'] = len(segment_text)
            self.output.setText(text)

    def highlight_segment(self, current_time):
        vertical_scroll_bar = self.output.verticalScrollBar()
        current_scroll_position = vertical_scroll_bar.value()

        cursor = self.output.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.setCharFormat(QTextCharFormat())

        for segment in self.transcription:
            if segment['start'] <= current_time <= segment['end']:
                cursor.setPosition(segment['start_pos'])
                cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, segment['length'])
                fmt = QTextCharFormat()
                fmt.setBackground(Qt.GlobalColor.yellow)
                cursor.setCharFormat(fmt)
                break

        vertical_scroll_bar.setValue(current_scroll_position)

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

    def reset(self):
        """Скидання стану."""
        self.file_path = None
        self.model_name = None
        self.language = None
        self.device = None
        self.is_video = False
        self.progress_bar.setValue(0)
        self.output.clear()
        self.transcription = []
        self.player.stop()
        self.player.setSource(QUrl())
        self.player.setVideoOutput(None)  # Очищаємо відеовихід
        self.progress_label.setText("Прогрес обробки: Очікування...")
        self.progress_bar_media.setValue(0)
        self.timestamp.setText("00:00 / 00:00")
        self.speed_label.setText("1.00x")

        # Видаляємо медіа віджет
        if self.media_widget:
            self.layout.removeWidget(self.media_widget)
            self.media_widget.deleteLater()
            self.media_widget = None

    def back_to_config(self):
        self.reset()
        self.parent.switch_to_config(self.file_path)