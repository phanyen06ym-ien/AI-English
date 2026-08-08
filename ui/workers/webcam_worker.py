"""Worker cho luong webcam realtime.

Sprint 3: tach business logic ra Service, doi thread ghi lich su sang QThread.
Sprint 4: ghi lich su di qua `HistoryRepository`.
Sprint 5:

- Chuyen sang `ManagedWorker`: vong doi + `CancellationToken` thong nhat.
  Co `_stop_requested` rieng cua Sprint 3 khong con can nua.
- Them `FrameGate`: bo frame khi GUI ve khong kip, thay vi de hang doi phinh.
- `HistoryWriterWorker` cho co huy thay vi chan mai o `queue.get()`.
"""

from __future__ import annotations

import queue
from time import monotonic

import cv2
from PySide6.QtCore import Signal
from PySide6.QtGui import QImage

from config.schema import AIConfig, CameraConfig, HistoryConfig, ThreadConfig
from ui.qt_utils import to_qimage
from ui.services.detection_service import DetectionService
from ui.services.history_service import (
    HistoryRecordPolicy,
    HistoryService,
)
from ui.workers.backpressure import (
    DEFAULT_MAX_IN_FLIGHT,
    FrameGate,
)
from ui.workers.cancellation import CancellationToken
from ui.workers.lifecycle import (
    DEFAULT_DISPOSE_TIMEOUT_MS,
    ManagedWorker,
)
from utils import perf_monitor


#: Gia tri mac dinh - lay tu cau hinh de chi co MOT nguon su that.
INFERENCE_INTERVAL_SECONDS = CameraConfig.inference_interval_seconds
HISTORY_QUEUE_MAX_SIZE = HistoryConfig.write_queue_size
STOP_WAIT_MS = DEFAULT_DISPOSE_TIMEOUT_MS

#: Chu ky kiem tra co huy khi hang doi lich su dang trong (giay).
HISTORY_POLL_SECONDS = ThreadConfig.poll_interval_seconds

ERROR_CAMERA_OPEN = "Không mở được webcam."
STATUS_CAMERA_RUNNING = "Webcam đang hoạt động."
STATUS_CAMERA_STOPPED = "Webcam đã tắt."
STATUS_NO_OBJECT = "Chưa phát hiện vật thể."


class HistoryWriterWorker(ManagedWorker):
    """Ghi lich su webcam bat dong bo, khong chan vong lap frame."""

    historySaved = Signal()

    #: Ngay ca khi bi huy truoc luc start(), van phai chay de ghi not hang doi.
    ALWAYS_EXECUTE = True

    def __init__(
        self,
        history_service: HistoryService,
        token: CancellationToken | None = None,
        queue_size: int = HISTORY_QUEUE_MAX_SIZE,
        poll_interval_seconds: float = HISTORY_POLL_SECONDS,
        parent=None,
    ) -> None:
        super().__init__(
            "history_writer",
            token=token,
            parent=parent,
        )

        self._history_service = history_service
        self._queue_size = max(1, int(queue_size))
        self._poll_interval_seconds = float(poll_interval_seconds)
        self._queue: queue.Queue = queue.Queue(
            maxsize=self._queue_size
        )

    def enqueue(
        self,
        english: str,
        vietnamese,
        category,
        confidence: float,
        user_id: int | None,
    ) -> bool:
        """Day mot ban ghi vao hang doi. False neu hang doi day.

        Day cung la mot dang backpressure: database cham thi bo ban ghi thay vi
        chan vong lap doc frame.
        """
        try:
            self._queue.put_nowait(
                (
                    english,
                    vietnamese,
                    category,
                    confidence,
                    user_id,
                )
            )
            perf_monitor.increment("history_save_queued")
            return True

        except queue.Full:
            perf_monitor.increment(
                "history_save_dropped_queue_full"
            )
            return False

    def request_stop(self) -> None:
        """Ten cu cua `cancel()`, giu de khong pha code goi san."""
        self.cancel()

    def _write(
        self,
        item: tuple,
    ) -> None:
        (
            english,
            vietnamese,
            category,
            confidence,
            user_id,
        ) = item

        with perf_monitor.timer("webcam_db_save_history_async"):
            saved = self._history_service.save_detection(
                english,
                vietnamese,
                category,
                confidence,
                user_id=user_id,
            )

        if saved:
            perf_monitor.increment("history_saved")
            self.historySaved.emit()

    def _drain_remaining(self) -> None:
        """Ghi not nhung ban ghi da xep hang truoc khi tat.

        Huy khong duoc lam **mat** du lieu nguoi dung da tao ra. So luot duoc
        chan tren bang kich thuoc hang doi nen buoc nay luon ket thuc.
        """
        for _ in range(self._queue_size):
            try:
                item = self._queue.get_nowait()
            except queue.Empty:
                return

            self._write(item)

    def execute(self) -> None:
        """Xu ly hang doi cho toi khi bi huy.

        Sprint 3 dung `queue.get()` chan vo han va mot "stop token" day vao hang
        doi. Neu hang doi day, stop token bi bo va worker treo. Sprint 5 doi sang
        `get(timeout=...)` co kiem tra co huy nen luon thoat duoc.
        """
        while not self.token.is_cancelled:
            try:
                item = self._queue.get(
                    timeout=self._poll_interval_seconds
                )
            except queue.Empty:
                continue

            self._write(item)

        self._drain_remaining()


class WebcamWorker(ManagedWorker):
    """Doc frame webcam, goi DetectionService va emit ket qua."""

    frameReady = Signal(QImage)
    resultsReady = Signal(list)
    relatedReady = Signal(list)
    clusterReady = Signal(list)
    statusChanged = Signal(str)
    historySaved = Signal()

    def __init__(
        self,
        detection_service: DetectionService,
        camera_id: int,
        user_id: int | None = None,
        history_service: HistoryService | None = None,
        capture_factory=None,
        max_frames_in_flight: int | None = None,
        token: CancellationToken | None = None,
        camera_config: CameraConfig | None = None,
        history_config: HistoryConfig | None = None,
        ai_config: AIConfig | None = None,
        thread_config: ThreadConfig | None = None,
        parent=None,
    ) -> None:
        super().__init__(
            "webcam_worker",
            token=token,
            parent=parent,
        )

        self._camera_config = (
            camera_config
            if camera_config is not None
            else CameraConfig()
        )
        self._history_config = (
            history_config
            if history_config is not None
            else HistoryConfig()
        )
        self._ai_config = (
            ai_config
            if ai_config is not None
            else AIConfig()
        )
        self._thread_config = (
            thread_config
            if thread_config is not None
            else ThreadConfig()
        )
        self._inference_interval_seconds = (
            self._camera_config.inference_interval_seconds
        )

        self._detection_service = detection_service
        self._history_service = (
            history_service
            if history_service is not None
            else detection_service.history_service
        )
        self.camera_id = camera_id
        self.user_id = user_id

        self._capture_factory = (
            capture_factory
            if capture_factory is not None
            else self._default_capture_factory
        )

        self._last_inference_at = 0.0
        self._last_primary_word = ""
        self._last_results: list[dict] = []
        self._policy = HistoryRecordPolicy.from_config(
            self._ai_config,
            self._history_config,
        )
        self._history_writer: HistoryWriterWorker | None = None
        self._frame_gate = FrameGate(
            max_frames_in_flight
            if max_frames_in_flight is not None
            else self._camera_config.max_frames_in_flight
        )

    # ------------------------------------------------------------------
    # Backpressure
    # ------------------------------------------------------------------

    @property
    def frame_gate(self) -> FrameGate:
        return self._frame_gate

    def release_frame(self) -> None:
        """GUI Thread goi sau khi ve xong mot frame."""
        self._frame_gate.release()

    # ------------------------------------------------------------------
    # Camera
    # ------------------------------------------------------------------

    @staticmethod
    def _default_capture_factory(camera_id: int):
        with perf_monitor.timer("camera_open_dshow"):
            camera = cv2.VideoCapture(
                camera_id,
                cv2.CAP_DSHOW,
            )

        if camera.isOpened():
            return camera

        camera.release()

        with perf_monitor.timer("camera_open_default"):
            return cv2.VideoCapture(camera_id)

    # ------------------------------------------------------------------
    # History writer
    # ------------------------------------------------------------------

    def _start_history_writer(self) -> None:
        if self._history_writer is not None:
            return

        self._history_writer = HistoryWriterWorker(
            self._history_service,
            queue_size=self._history_config.write_queue_size,
            poll_interval_seconds=(
                self._thread_config.poll_interval_seconds
            ),
        )
        self._history_writer.historySaved.connect(
            self.historySaved
        )
        self._history_writer.start()

    def _stop_history_writer(self) -> None:
        if self._history_writer is None:
            return

        self._history_writer.dispose(
            self._thread_config.dispose_timeout_ms
        )
        self._history_writer = None

    def _record_history(
        self,
        results: list[dict],
    ) -> None:
        if self._history_writer is None:
            return

        for result in results:
            self._history_writer.enqueue(
                result.get("english", ""),
                result.get("vietnamese"),
                result.get("category"),
                float(
                    result.get("confidence")
                    or 0.0
                ),
                self.user_id,
            )

    # ------------------------------------------------------------------
    # Word suggestion
    # ------------------------------------------------------------------

    def _emit_word_suggestions(
        self,
        primary_word: str,
        analysis,
    ) -> None:
        if not primary_word:
            self.relatedReady.emit([])
            self.clusterReady.emit([])
            self._last_primary_word = ""
            return

        if primary_word == self._last_primary_word:
            return

        self._last_primary_word = primary_word

        perf_monitor.increment("related_emit")
        self.relatedReady.emit(
            analysis.related_words_as_dicts()
        )

        perf_monitor.increment("cluster_emit")
        self.clusterReady.emit(
            analysis.cluster_words_as_dicts()
        )

    # ------------------------------------------------------------------
    # Vong lap chinh
    # ------------------------------------------------------------------

    def _process_inference(
        self,
        frame,
        now: float,
    ) -> None:
        perf_monitor.increment("inference_attempt")

        outcome = self._detection_service.analyze_camera_frame(
            frame,
            self._policy,
            now=now,
        )

        if not outcome.success:
            perf_monitor.increment("status_emit")
            self.statusChanged.emit(outcome.message)
            self._emit_word_suggestions(
                "",
                outcome.analysis,
            )
            return

        results = outcome.results
        self._last_results = results

        perf_monitor.increment("results_emit")
        self.resultsReady.emit(results)

        if results:
            self._record_history(outcome.recordable)

            perf_monitor.increment("status_emit")
            self.statusChanged.emit(
                f"Phát hiện {len(results)} vật thể."
            )
            self._emit_word_suggestions(
                results[0]["english"],
                outcome.analysis,
            )
        else:
            perf_monitor.increment("status_emit")
            self.statusChanged.emit(STATUS_NO_OBJECT)
            self._emit_word_suggestions(
                "",
                outcome.analysis,
            )

    def _emit_frame(
        self,
        display_frame,
    ) -> None:
        """Emit frame neu GUI con theo kip, nguoc lai bo frame."""
        if not self._frame_gate.try_acquire():
            perf_monitor.increment("frame_dropped_backpressure")
            return

        image = to_qimage(display_frame)

        with perf_monitor.timer("frame_ready_emit"):
            self.frameReady.emit(image)

        perf_monitor.increment("frame_emit")

    def execute(self) -> None:
        perf_monitor.start()

        self._frame_gate.reset()
        self._start_history_writer()

        camera = self._capture_factory(self.camera_id)

        if camera is None or not camera.isOpened():
            if camera is not None:
                camera.release()
            self._stop_history_writer()
            self.statusChanged.emit(ERROR_CAMERA_OPEN)
            return

        self.statusChanged.emit(STATUS_CAMERA_RUNNING)

        try:
            while not self.token.is_cancelled:
                with perf_monitor.timer("camera_read_frame"):
                    success, frame = camera.read()

                if not success:
                    continue

                perf_monitor.increment("camera_frames_read")
                now = monotonic()

                if (
                    now - self._last_inference_at
                    >= self._inference_interval_seconds
                ):
                    self._last_inference_at = now
                    self._process_inference(frame, now)

                    if self.token.is_cancelled:
                        break

                display_frame = self._detection_service.annotate_camera_frame(
                    frame,
                    self._last_results,
                )

                self._emit_frame(display_frame)
                perf_monitor.maybe_report()

        finally:
            camera.release()
            self._stop_history_writer()
            self.statusChanged.emit(STATUS_CAMERA_STOPPED)

            self.logger.info(
                "backpressure emitted=%s dropped=%s (%s%%)",
                self._frame_gate.emitted,
                self._frame_gate.dropped,
                self._frame_gate.stats()["drop_percent"],
            )

    # ------------------------------------------------------------------
    # Ten cu cua Sprint 3 - giu de khong pha code goi san
    # ------------------------------------------------------------------

    def request_stop(self) -> None:
        """Yeu cau dung, KHONG chan GUI thread. Alias cua `cancel()`."""
        self.cancel()

    def stop(
        self,
        timeout_ms: int = STOP_WAIT_MS,
    ) -> bool:
        """Dung va cho worker ket thuc. Alias cua `dispose()`."""
        return self.dispose(timeout_ms)
