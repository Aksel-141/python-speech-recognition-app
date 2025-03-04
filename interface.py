import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from main_window import MainWindow
from config_window import ConfigWindow
from result_window import ResultWindow

class Interface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcription App v0.0.1")
        self.setStyleSheet("background-color: #121212; color: white; font-family: Arial, sans-serif;")

        # Стек віджетів для управління вікнами
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Ініціалізація вікон
        self.main_window = MainWindow(self)
        self.config_window = None  # Ініціалізуємо пізніше
        self.result_window = None  # Ініціалізуємо пізніше

        # Додаємо головне вікно в стек
        self.stack.addWidget(self.main_window)

        # Показуємо на весь екран
        self.showMaximized()

    def switch_to_config(self, file_path=None):
        if not self.config_window:
            self.config_window = ConfigWindow(self, file_path)
            self.stack.addWidget(self.config_window)
        else:
            self.config_window.set_file_path(file_path)
        self.stack.setCurrentWidget(self.config_window)

    def switch_to_result(self, file_path, model_name, language, device):
        if not self.result_window:
            self.result_window = ResultWindow(self, file_path, model_name, language, device)
            self.stack.addWidget(self.result_window)
        else:
            self.result_window.update_content(file_path, model_name, language, device)
        self.stack.setCurrentWidget(self.result_window)

    def switch_to_main(self):
        self.stack.setCurrentWidget(self.main_window)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Interface()
    window.show()
    sys.exit(app.exec())