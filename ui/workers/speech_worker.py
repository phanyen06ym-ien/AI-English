"""Worker phat am chay tren QThreadPool.

Sprint 5: chuyen sang `PooledTask` de co the huy va de xu ly loi thong nhat.
Phat am la tac vu ngan, ban roi quen -> dung thread pool, khong dung QThread rieng.
"""

from __future__ import annotations

from ui.workers.cancellation import CancellationToken
from ui.workers.task_pool import PooledTask
from utils.speech import speak


class SpeakTask(PooledTask):
    """Chay phat am trong thread nen de UI khong bi dung."""

    def __init__(
        self,
        word: str,
        speak_fn=speak,
        token: CancellationToken | None = None,
    ) -> None:
        super().__init__(
            "speech_task",
            token=token,
        )

        self.word = word
        self._speak_fn = speak_fn

    def execute(self) -> None:
        self.token.raise_if_cancelled()

        self._speak_fn(self.word)


__all__ = ["SpeakTask"]
