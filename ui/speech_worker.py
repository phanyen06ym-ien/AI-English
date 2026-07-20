from __future__ import annotations

from PySide6.QtCore import QRunnable

from utils.speech import speak


class SpeakTask(QRunnable):
    """
    Chạy phát âm trong thread nền để UI không bị đứng.
    """

    def __init__(
        self,
        word: str,
    ) -> None:
        super().__init__()

        self.word = word

    def run(self) -> None:
        try:
            speak(self.word)

        except Exception as error:
            print(
                f"Không phát được âm thanh: {error}"
            )