from __future__ import annotations

from collections import Counter

from PySide6.QtCore import (
    QObject,
    QThread,
    Signal,
    Slot,
)

from database.history import get_history
from utils import perf_monitor


EMPTY_STATS = {
    "totalDetections": 0,
    "uniqueWords": 0,
    "mostCommonWord": "",
    "mostDetectedWord": "",
    "averageConfidence": 0.0,
    "categories": {},
}


class StatsWorker(QThread):
    loaded = Signal(dict)
    failed = Signal(str)

    def __init__(
        self,
        user_id: int,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.user_id = user_id

    def run(self) -> None:
        try:
            with perf_monitor.timer("stats_refresh_get_history"):
                history_rows = get_history(
                    user_id=self.user_id,
                    limit=500,
                )

            category_counter = Counter()
            word_counter = Counter()
            confidence_values = []

            for row in history_rows:
                word = row.get("english_word")
                category = (
                    row.get("category")
                    or "Unknown"
                )

                if word:
                    word_counter[word] += 1

                confidence_values.append(
                    float(
                        row.get("confidence")
                        or 0.0
                    )
                )
                category_counter[category] += 1

            most_common_word = ""
            if word_counter:
                most_common_word = (
                    word_counter.most_common(1)[0][0]
                )

            average_confidence = 0.0
            if confidence_values:
                average_confidence = (
                    sum(confidence_values)
                    / len(confidence_values)
                )

            self.loaded.emit(
                {
                    "totalDetections": len(
                        history_rows
                    ),
                    "uniqueWords": len(
                        word_counter
                    ),
                    "mostCommonWord": (
                        most_common_word
                    ),
                    "mostDetectedWord": (
                        most_common_word
                    ),
                    "averageConfidence": float(
                        average_confidence
                    ),
                    "categories": dict(
                        category_counter
                    ),
                }
            )

        except Exception as error:
            self.failed.emit(str(error))


class StatsController(QObject):
    statsChanged = Signal(dict)

    def __init__(
        self,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._user_id = None
        self._worker = None

    def set_user_id(
        self,
        user_id: int | None,
    ) -> None:
        self._user_id = user_id
        if user_id is None:
            self.clear()

    def clear(self) -> None:
        self.statsChanged.emit(dict(EMPTY_STATS))

    @Slot()
    def refresh(self) -> None:
        perf_monitor.increment("stats_refresh_called")

        if self._user_id is None:
            self.clear()
            return

        if self._worker is not None:
            perf_monitor.increment("stats_refresh_skipped_busy")
            return

        self._worker = StatsWorker(
            int(self._user_id)
        )
        self._worker.loaded.connect(
            self.statsChanged
        )
        self._worker.failed.connect(
            self._on_failed
        )
        self._worker.finished.connect(
            self._on_finished
        )
        self._worker.start()

    def _on_failed(
        self,
        message: str,
    ) -> None:
        print(
            f"Khong the tai thong ke: {message}"
        )
        self.clear()

    def _on_finished(self) -> None:
        self._worker = None
