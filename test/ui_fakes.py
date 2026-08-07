"""Fake va helper dung chung cho test GUI layer (Sprint 3).

Muc tieu: chay duoc toan bo Controller / ViewModel / Worker MA KHONG can
YOLO, KHONG can model .pkl, KHONG can ket noi database.
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

import numpy as np

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent),
)

from PySide6.QtCore import QCoreApplication  # noqa: E402

from ai.models import (  # noqa: E402
    ClusterResult,
    DetectionResult,
    ImageAnalysisResult,
    RelatedWord,
    TimingInfo,
)


DEFAULT_TIMEOUT_SECONDS = 10.0


def ensure_app() -> QCoreApplication:
    """Tao QCoreApplication mot lan cho ca test session."""
    app = QCoreApplication.instance()

    if app is None:
        app = QCoreApplication(sys.argv[:1])

    return app


def process_events(
    iterations: int = 5,
) -> None:
    """Bom event loop de queued signal duoc giao."""
    app = ensure_app()

    for _ in range(iterations):
        app.processEvents()


def wait_for(
    predicate,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> bool:
    """Cho toi khi `predicate()` True, van bom event loop trong luc cho."""
    app = ensure_app()
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        app.processEvents()

        if predicate():
            app.processEvents()
            return True

        time.sleep(0.005)

    app.processEvents()
    return predicate()


def make_frame(
    height: int = 8,
    width: int = 8,
):
    """Anh BGR gia lap."""
    return np.zeros(
        (height, width, 3),
        dtype=np.uint8,
    )


def make_detection(
    english: str = "laptop",
    confidence: float = 0.93,
) -> DetectionResult:
    return DetectionResult(
        english=english,
        vietnamese="May tinh xach tay",
        category="Technology",
        level="Medium",
        confidence=confidence,
        box=(1, 2, 6, 7),
    )


def make_analysis(
    success: bool = True,
    detections: list | None = None,
    message: str = "OK",
) -> ImageAnalysisResult:
    if detections is None:
        detections = [make_detection()]

    return ImageAnalysisResult(
        success=success,
        detections=detections,
        related_words=[
            RelatedWord(
                english="mouse",
                vietnamese="Chuot may tinh",
                category="Technology",
                level="Medium",
                distance=0.2,
            )
        ],
        cluster_words=[
            ClusterResult(
                english="keyboard",
                vietnamese="Ban phim",
                category="Technology",
                level="Medium",
                cluster=0,
            )
        ],
        timing=TimingInfo(),
        message=message,
    )


class FakeAIEngine:
    """Thay the `AIEngine` - khong chay YOLO / KNN / KMeans that."""

    def __init__(
        self,
        analysis: ImageAnalysisResult | None = None,
        raise_error: bool = False,
    ) -> None:
        self.analysis = (
            analysis
            if analysis is not None
            else make_analysis()
        )
        self.raise_error = raise_error
        self.analyze_calls = 0
        self.related_calls: list[tuple[str, int]] = []
        self.cluster_calls: list[str] = []

    def analyze_frame(
        self,
        frame,
        include_learning: bool = True,
    ) -> ImageAnalysisResult:
        self.analyze_calls += 1

        if self.raise_error:
            raise RuntimeError("engine failed")

        return self.analysis

    def get_vocabulary_entries(self) -> list[dict]:
        return [
            {
                "english": "laptop",
                "vietnamese": "May tinh xach tay",
                "category": "Technology",
                "level": "Medium",
            },
            {
                "english": "keyboard",
                "vietnamese": "Ban phim",
                "category": "Technology",
                "level": "Medium",
            },
        ]

    def get_related_word_dicts(
        self,
        word: str,
        n: int = 3,
    ) -> list[dict]:
        self.related_calls.append((word, n))
        return [
            {
                "english": "mouse",
                "vietnamese": "Chuot may tinh",
                "category": "Technology",
                "level": "Medium",
                "distance": 0.2,
            }
        ]

    def get_cluster_word_dicts(
        self,
        word: str,
    ) -> list[dict]:
        self.cluster_calls.append(word)
        return [
            {
                "english": "keyboard",
                "vietnamese": "Ban phim",
                "category": "Technology",
                "level": "Medium",
                "cluster": 0,
            }
        ]


class FakeHistoryService:
    """Thay the `HistoryService` - khong cham database."""

    def __init__(
        self,
        rows: list[dict] | None = None,
        fail: bool = False,
    ) -> None:
        self.rows = rows if rows is not None else []
        self.fail = fail
        self.saved: list[tuple] = []
        self.cleared: list[int | None] = []
        self.lock = threading.Lock()

    def save_detection(
        self,
        english,
        vietnamese,
        category,
        confidence,
        user_id=None,
    ) -> bool:
        with self.lock:
            self.saved.append(
                (
                    english,
                    vietnamese,
                    category,
                    confidence,
                    user_id,
                )
            )
        return True

    def save_detections(
        self,
        detections,
        user_id=None,
    ) -> int:
        count = 0

        for detection in detections:
            if self.save_detection(
                detection.english,
                detection.vietnamese,
                detection.category,
                detection.confidence,
                user_id=user_id,
            ):
                count += 1

        return count

    def load_rows(
        self,
        user_id,
        limit=200,
    ) -> list[dict]:
        if self.fail:
            raise RuntimeError("database down")
        return list(self.rows)

    def load_formatted_rows(
        self,
        user_id,
        limit=200,
    ) -> list[dict]:
        from ui.services.history_service import format_history_rows

        return format_history_rows(
            self.load_rows(user_id, limit=limit)
        )

    def clear(
        self,
        user_id,
    ) -> bool:
        self.cleared.append(user_id)
        self.rows = []
        return True


class FakeCamera:
    """Thay the `cv2.VideoCapture`."""

    def __init__(
        self,
        frames: int = 3,
        opened: bool = True,
    ) -> None:
        self._frames_left = frames
        self._opened = opened
        self.released = False

    def isOpened(self) -> bool:
        return self._opened

    def read(self):
        # Ngu mot nhip de khong lam ngap event queue cua GUI thread.
        time.sleep(0.005)

        if self._frames_left > 0:
            self._frames_left -= 1

        return True, make_frame()

    def release(self) -> None:
        self.released = True
