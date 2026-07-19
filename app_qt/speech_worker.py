from PySide6.QtCore import QRunnable

from utils.speech import speak


class SpeakTask(QRunnable):
    """Chạy speak() (tải giọng nói + phát) trong thread pool để không làm đứng UI."""

    def __init__(self, word):
        super().__init__()
        self.word = word

    def run(self):
        try:
            speak(self.word)
        except Exception as exc:
            print("Không phát được âm thanh:", exc)
