# interface.py
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt6.QtGui import QIcon
from main_window import MainWindow
from config_window import ConfigWindow
from result_window import ResultWindow
from dtw_result import DTWResultWindow  # Імпортуємо нову сторінку


class Interface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Транскрибування аудіо")
        self.setWindowIcon(QIcon("icon.ico"))
        self.setStyleSheet(
            "background-color: #121212; color: white; font-family: Arial, sans-serif;"
        )

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.main_window = MainWindow(self)
        self.config_window = None
        self.result_window = None
        self.hmm_result_window = None  # Додаємо нове вікно

        self.stack.addWidget(self.main_window)
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
            self.result_window = ResultWindow(
                self, file_path, model_name, language, device
            )
            self.stack.addWidget(self.result_window)
        else:
            self.result_window.update_content(file_path, model_name, language, device)
        self.stack.setCurrentWidget(self.result_window)

    def switch_to_hmm_result(self):
        if not self.hmm_result_window:
            self.hmm_result_window = DTWResultWindow(self)
            self.stack.addWidget(self.hmm_result_window)
        self.stack.setCurrentWidget(self.hmm_result_window)

    def switch_to_main(self):
        self.stack.setCurrentWidget(self.main_window)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Interface()
    window.show()
    sys.exit(app.exec())
