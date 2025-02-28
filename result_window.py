import os
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QProgressBar
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from transcription import transcribe_audio

class ResultWindow(QMainWindow):
    def __init__(self, file_path, model_name, language, device):
        super().__init__()
        self.setWindowTitle("Результати транскрибування")
        self.setAcceptDrops(True)
        self.file_path = file_path
        self.is_video = file_path.lower().endswith((".mp4", ".mkv", ".avi"))
        self.setStyleSheet("background-color: #121212; color: white; font-family: Arial, sans-serif;")

        # Центральний віджет із контейнером
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Головний горизонтальний layout для центрування
        main_layout = QHBoxLayout(central_widget)  # Змінив на QHBoxLayout для горизонтального центрування
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

        # Кнопка "Назад"
        back_btn = QPushButton("Назад")
        back_btn.setStyleSheet("background: #1e90ff; color: white; padding: 5px; border: none; border-radius: 5px;")
        back_btn.clicked.connect(self.back_to_config)
        layout.addWidget(back_btn)

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
        layout.addLayout(header_layout)

        # Прогрес обробки
        self.progress_label = QLabel("Прогрес обробки: Очікування...")
        self.progress_label.setStyleSheet("font-size: 18px; margin-top: 20px;")
        layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("QProgressBar { background: #333; border-radius: 5px; } QProgressBar::chunk { background: #007bff; }")
        layout.addWidget(self.progress_bar)

        # Вивід тексту
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("background: #222; color: #ccc; border: none; font-size: 14px; margin-top: 10px;")

        if self.is_video:
            # Віджет для відео
            self.player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.player.setAudioOutput(self.audio_output)
            self.video_widget = QVideoWidget()
            self.video_widget.setStyleSheet("background-color: #000; border-radius: 5px;")
            self.video_widget.setMinimumHeight(300)
            self.player.setVideoOutput(self.video_widget)
            self.player.setSource(QUrl.fromLocalFile(self.file_path))
            layout.addWidget(self.video_widget)
            layout.addWidget(self.output)
        else:
            # Віджет для аудіо
            self.player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.player.setAudioOutput(self.audio_output)
            self.audio_widget = QVideoWidget()
            self.audio_widget.setStyleSheet("background-color: #000; border-radius: 5px;")  # Додано стиль для видимості
            self.audio_widget.setMinimumHeight(50)  # Менша висота для аудіо
            self.player.setVideoOutput(self.audio_widget)
            self.player.setSource(QUrl.fromLocalFile(self.file_path))
            layout.addWidget(self.audio_widget)
            layout.addWidget(self.output)

        # Елементи керування аудіо/відео
        controls_widget = QWidget()
        controls_widget.setStyleSheet("background-color: #000; border-top: 1px solid #333;")
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(10, 10, 10, 10)
        
        self.timestamp = QLabel("00:00:00 / 00:00:00")
        self.timestamp.setStyleSheet("font-size: 12px; color: #999;")
        controls_layout.addWidget(self.timestamp)

        back_btn = QPushButton("⏪")
        back_btn.setStyleSheet("background: none; color: white; border: none; font-size: 16px;")
        back_btn.clicked.connect(lambda: self.seek(-5))  # Перемотка назад на 5 секунд
        controls_layout.addWidget(back_btn)

        play_btn = QPushButton("▶️")
        play_btn.setStyleSheet("background: none; color: white; border: none; font-size: 16px;")
        play_btn.clicked.connect(self.toggle_play)
        controls_layout.addWidget(play_btn)

        next_btn = QPushButton("⏩")
        next_btn.setStyleSheet("background: none; color: white; border: none; font-size: 16px;")
        next_btn.clicked.connect(lambda: self.seek(5))  # Перемотка вперед на 5 секунд
        controls_layout.addWidget(next_btn)

        self.progress_bar_media = QProgressBar()
        self.progress_bar_media.setStyleSheet("QProgressBar { background: #333; height: 5px; border-radius: 5px; } QProgressBar::chunk { background: #007bff; }")
        self.progress_bar_media.setValue(0)
        controls_layout.addWidget(self.progress_bar_media)

        speed_label = QLabel("1.00x")
        speed_label.setStyleSheet("font-size: 12px; color: #999;")
        controls_layout.addWidget(speed_label)

        layout.addWidget(controls_widget)

        # З'єднуємо сигнали для оновлення прогрес-бару та часу
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)

        self.transcription = []
        QTimer.singleShot(100, lambda: self.run_transcription(model_name, language, device))

    def seek(self, seconds):
        if self.player.isAvailable():
            current_position = self.player.position()
            new_position = current_position + (seconds * 1000)  # Переводимо секунди в мілісекунди
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

    def run_transcription(self, model_name, language, device):
        transcription = transcribe_audio(self.file_path, model_name, language, device, self.update_progress)
        if "error" in transcription:
            self.output.setText(f"Помилка: {transcription['error']}")
        else:
            self.transcription = transcription
            text = "\n".join([f"{seg['time']} {seg['text']}" for seg in transcription])
            self.output.setText(text)

    def back_to_config(self):
        from config_window import ConfigWindow
        self.config_window = ConfigWindow(self.file_path)
        self.config_window.showMaximized()
        self.close()

    def show(self):
        super().showMaximized()
    
    def resizeEvent(self, event):
        container_widget = self.centralWidget().layout().itemAt(1).widget()
        container_widget.setMaximumWidth(int(self.width() * 0.75))
        container_widget.setMinimumWidth(int(self.width() * 0.75))
        super().resizeEvent(event)