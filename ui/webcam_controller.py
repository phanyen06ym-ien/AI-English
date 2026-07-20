from __future__ import annotations

import queue
import threading
from time import monotonic

import cv2
from PySide6.QtCore import (
    QObject,
    Property,
    QThread,
    Signal,
    Slot,
)
from PySide6.QtGui import QImage

from database.history import save_history
from detection.classify import classify_word
from ml.kmeans import get_words_in_same_cluster
from ml.knn import get_related_words
from ui.qt_utils import to_qimage
from utils.config import CAMERA_ID, CONFIDENCE
from utils.helper import draw_vietnamese_text
from utils import perf_monitor


INFERENCE_INTERVAL_SECONDS = 0.25
HISTORY_COOLDOWN_SECONDS = 5.0


class WebcamThread(QThread):
    frame_ready = Signal(QImage)
    results_ready = Signal(list)
    related_ready = Signal(list)
    cluster_ready = Signal(list)
    status_changed = Signal(str)
    history_saved = Signal()

    def __init__(
        self,
        detector,
        camera_id: int,
        user_id: int | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.detector = detector
        self.camera_id = camera_id
        self.user_id = user_id
        self._running = False
        self._last_inference_at = 0.0
        self._last_saved_by_class = {}
        self._last_primary_word = ""
        self._related_cache = {}
        self._cluster_cache = {}
        self._last_results = []
        self._history_queue = queue.Queue(maxsize=20)
        self._history_stop_token = object()
        self._history_worker = None

    def _start_history_worker(self) -> None:
        if self._history_worker is not None:
            return

        self._history_worker = threading.Thread(
            target=self._history_worker_loop,
            name="webcam-history-writer",
            daemon=True,
        )
        self._history_worker.start()

    def _stop_history_worker(self) -> None:
        if self._history_worker is None:
            return

        try:
            self._history_queue.put_nowait(
                self._history_stop_token
            )
        except queue.Full:
            pass

        self._history_worker.join(timeout=1.0)
        self._history_worker = None

    def _history_worker_loop(self) -> None:
        while True:
            item = self._history_queue.get()

            if item is self._history_stop_token:
                return

            (
                class_name,
                vietnamese,
                category,
                confidence,
                user_id,
            ) = item

            with perf_monitor.timer("webcam_db_save_history_async"):
                saved = save_history(
                    class_name,
                    vietnamese,
                    category,
                    confidence,
                    user_id=user_id,
                )

            if saved:
                perf_monitor.increment("history_saved")
                self.history_saved.emit()

    def _format_detection(
        self,
        detected_object: dict,
    ) -> dict:
        class_name = detected_object["class_name"]
        word_info = classify_word(class_name)
        confidence = float(
            detected_object["confidence"]
        )
        box = tuple(detected_object["box"])

        vietnamese = (
            word_info.get("vietnamese")
            or class_name
        )
        category = (
            word_info.get("category")
            or "Unknown"
        )
        level = (
            word_info.get("level")
            or "Unknown"
        )

        return {
            "english": class_name,
            "vietnamese": vietnamese,
            "category": category,
            "level": level,
            "confidence": confidence,
            "box": box,
            "text": (
                f"{class_name} - {vietnamese} "
                f"[{category} - {level}] "
                f"({confidence:.2f})"
            ),
        }

    def _save_history_if_allowed(
        self,
        result: dict,
        now: float,
    ) -> None:
        class_name = result["english"]
        confidence = float(
            result.get("confidence") or 0.0
        )

        if confidence < CONFIDENCE:
            return

        last_saved_at = (
            self._last_saved_by_class.get(
                class_name,
                0.0,
            )
        )

        if now - last_saved_at < HISTORY_COOLDOWN_SECONDS:
            return

        try:
            self._history_queue.put_nowait(
                (
                    class_name,
                    result.get("vietnamese"),
                    result.get("category"),
                    confidence,
                    self.user_id,
                )
            )
            self._last_saved_by_class[class_name] = now
            perf_monitor.increment("history_save_queued")
        except queue.Full:
            perf_monitor.increment("history_save_dropped_queue_full")

    def _emit_word_suggestions(
        self,
        primary_word: str,
    ) -> None:
        if not primary_word:
            self.related_ready.emit([])
            self.cluster_ready.emit([])
            self._last_primary_word = ""
            return

        if primary_word == self._last_primary_word:
            return

        self._last_primary_word = primary_word

        if primary_word not in self._related_cache:
            with perf_monitor.timer("knn_related_words"):
                self._related_cache[primary_word] = (
                    get_related_words(
                        primary_word,
                        n=3,
                    )
                )

        if primary_word not in self._cluster_cache:
            with perf_monitor.timer("kmeans_cluster_words"):
                self._cluster_cache[primary_word] = (
                    get_words_in_same_cluster(
                        primary_word
                    )
                )

        perf_monitor.increment("related_emit")
        self.related_ready.emit(
            self._related_cache[primary_word]
        )
        perf_monitor.increment("cluster_emit")
        self.cluster_ready.emit(
            self._cluster_cache[primary_word]
        )

    def _draw_results(
        self,
        frame,
        results: list[dict],
    ):
        with perf_monitor.timer("draw_bounding_boxes"):
            for result in results:
                x1, y1, x2, y2 = result["box"]
                label = result["text"]

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 180, 0),
                    2,
                )

                frame = draw_vietnamese_text(
                    frame,
                    label,
                    (x1, max(y1 - 35, 5)),
                    color=(0, 180, 0),
                    size=24,
                )

        return frame

    def run(self) -> None:
        perf_monitor.start()
        self._start_history_worker()
        with perf_monitor.timer("camera_open_dshow"):
            camera = cv2.VideoCapture(
                self.camera_id,
                cv2.CAP_DSHOW,
            )

        if not camera.isOpened():
            camera.release()
            with perf_monitor.timer("camera_open_default"):
                camera = cv2.VideoCapture(
                    self.camera_id
                )

        if not camera.isOpened():
            self.status_changed.emit(
                "Không mở được webcam."
            )
            return

        self._running = True
        self.status_changed.emit(
            "Webcam đang hoạt động."
        )

        try:
            while self._running:
                with perf_monitor.timer("camera_read_frame"):
                    success, frame = camera.read()

                if not success:
                    continue

                perf_monitor.increment("camera_frames_read")
                now = monotonic()

                if (
                    now - self._last_inference_at
                    >= INFERENCE_INTERVAL_SECONDS
                ):
                    self._last_inference_at = now
                    perf_monitor.increment("inference_attempt")
                    detected_objects = self.detector.detect(
                        frame
                    )

                    results = [
                        self._format_detection(obj)
                        for obj in detected_objects
                    ]
                    results.sort(
                        key=lambda item: item["confidence"],
                        reverse=True,
                    )
                    self._last_results = results
                    perf_monitor.increment("results_emit")
                    self.results_ready.emit(results)

                    if results:
                        for result in results:
                            self._save_history_if_allowed(
                                result,
                                now,
                            )
                        perf_monitor.increment("status_emit")
                        self.status_changed.emit(
                            f"Phát hiện {len(results)} vật thể."
                        )
                        self._emit_word_suggestions(
                            results[0]["english"]
                        )
                    else:
                        perf_monitor.increment("status_emit")
                        self.status_changed.emit(
                            "Chưa phát hiện vật thể."
                        )
                        self._emit_word_suggestions("")

                display_frame = self._draw_results(
                    frame,
                    self._last_results,
                )
                image = to_qimage(display_frame)
                with perf_monitor.timer("frame_ready_emit"):
                    self.frame_ready.emit(image)
                perf_monitor.increment("frame_emit")
                perf_monitor.maybe_report()

        finally:
            camera.release()
            self._stop_history_worker()
            self.status_changed.emit(
                "Webcam đã tắt."
            )

    def stop(self) -> None:
        self._running = False
        self.wait(3000)


class WebcamController(QObject):
    frameChanged = Signal(QImage)
    statusChanged = Signal(str)
    runningChanged = Signal(bool)
    resultsChanged = Signal(list)
    relatedWordsChanged = Signal(list)
    clusterWordsChanged = Signal(list)
    historySaved = Signal()

    def __init__(
        self,
        detector,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.detector = detector
        self._thread = None
        self._running = False
        self._user_id = None
        self._results = []
        self._related_words = []
        self._cluster_words = []

    @Property(bool, notify=runningChanged)
    def running(self) -> bool:
        return self._running

    @Property(list, notify=resultsChanged)
    def detections(self) -> list:
        return self._results

    @Property(list, notify=relatedWordsChanged)
    def relatedWords(self) -> list:
        return self._related_words

    @Property(list, notify=clusterWordsChanged)
    def clusterWords(self) -> list:
        return self._cluster_words

    def set_user_id(
        self,
        user_id: int | None,
    ) -> None:
        self._user_id = user_id

    @Slot()
    def start(self) -> None:
        if self._thread is not None:
            return

        self._running = True
        self.runningChanged.emit(True)

        self._thread = WebcamThread(
            self.detector,
            CAMERA_ID,
            self._user_id,
        )
        self._thread.frame_ready.connect(
            self.frameChanged
        )
        self._thread.results_ready.connect(
            self._on_results_ready
        )
        self._thread.related_ready.connect(
            self._on_related_ready
        )
        self._thread.cluster_ready.connect(
            self._on_cluster_ready
        )
        self._thread.status_changed.connect(
            self.statusChanged
        )
        self._thread.history_saved.connect(
            self.historySaved
        )
        self._thread.finished.connect(
            self._on_finished
        )
        self._thread.start()

    @Slot()
    def stop(self) -> None:
        if self._thread is not None:
            self._thread.stop()
        else:
            self.statusChanged.emit(
                "Webcam đã tắt."
            )

    def _on_results_ready(
        self,
        results: list,
    ) -> None:
        self._results = results
        self.resultsChanged.emit(results)

    def _on_related_ready(
        self,
        words: list,
    ) -> None:
        self._related_words = words
        self.relatedWordsChanged.emit(words)

    def _on_cluster_ready(
        self,
        words: list,
    ) -> None:
        self._cluster_words = words
        self.clusterWordsChanged.emit(words)

    def _on_finished(self) -> None:
        self._thread = None
        self._running = False
        self.runningChanged.emit(False)
