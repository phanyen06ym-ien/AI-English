"""ViewModel cho man hinh webcam realtime."""

from __future__ import annotations

from PySide6.QtCore import Property, Signal, Slot
from PySide6.QtGui import QImage

from ui.services.detection_service import DetectionService
from ui.state import UiState
from ui.ui_logger import log_ui_event
from ui.viewmodels.base_viewmodel import BaseViewModel
from ui.workers.webcam_worker import (
    STATUS_CAMERA_STOPPED,
    WebcamWorker,
)
from config.schema import CameraConfig


class WebcamViewModel(BaseViewModel):
    """Giu trang thai cua luong webcam: start -> detect lien tuc -> stop."""

    FrameUpdated = Signal(QImage)
    DetectionCompleted = Signal(list)
    DetectionFailed = Signal(str)
    RelatedWordsUpdated = Signal(list)
    ClusterWordsUpdated = Signal(list)
    HistoryUpdated = Signal()
    RunningChanged = Signal(bool)

    def __init__(
        self,
        detection_service: DetectionService,
        camera_id: int | None = None,
        capture_factory=None,
        config: CameraConfig | None = None,
        parent=None,
    ) -> None:
        super().__init__("webcam_viewmodel", parent)

        self._detection_service = detection_service
        self._config = (
            config
            if config is not None
            else CameraConfig()
        )
        self._camera_id = (
            camera_id
            if camera_id is not None
            else self._config.camera_id
        )
        self._capture_factory = capture_factory
        self._worker: WebcamWorker | None = None
        self._running = False
        self._results: list[dict] = []
        self._related_words: list[dict] = []
        self._cluster_words: list[dict] = []

    # ------------------------------------------------------------------
    # Trang thai doc duoc
    # ------------------------------------------------------------------

    @Property(bool, notify=RunningChanged)
    def running(self) -> bool:
        return self._running

    @Property(list, notify=DetectionCompleted)
    def detections(self) -> list:
        return self._results

    @Property(list, notify=RelatedWordsUpdated)
    def relatedWords(self) -> list:
        return self._related_words

    @Property(list, notify=ClusterWordsUpdated)
    def clusterWords(self) -> list:
        return self._cluster_words

    def _set_running(
        self,
        value: bool,
    ) -> None:
        if self._running == value:
            return

        self._running = value
        self.RunningChanged.emit(value)

    # ------------------------------------------------------------------
    # Dieu khien
    # ------------------------------------------------------------------

    @Slot()
    def start(self) -> None:
        """Bat webcam."""
        if self._worker is not None:
            return

        log_ui_event(self.logger, "webcam_start_requested")

        self._set_running(True)
        self.set_state(UiState.DETECTING)

        self._worker = WebcamWorker(
            self._detection_service,
            self._camera_id,
            self.user_id,
            capture_factory=self._capture_factory,
            camera_config=self._config,
        )
        self._worker.frameReady.connect(
            self._on_frame_ready
        )
        self._worker.resultsReady.connect(
            self._on_results_ready
        )
        self._worker.relatedReady.connect(
            self._on_related_ready
        )
        self._worker.clusterReady.connect(
            self._on_cluster_ready
        )
        self._worker.statusChanged.connect(
            self.set_status
        )
        self._worker.historySaved.connect(
            self.HistoryUpdated
        )
        self._worker.finished.connect(
            self._on_worker_finished
        )
        self._worker.start()

    @Slot()
    def stop(self) -> None:
        """Yeu cau tat webcam. KHONG chan GUI thread."""
        log_ui_event(self.logger, "webcam_stop_requested")

        if self._worker is None:
            self.set_status(STATUS_CAMERA_STOPPED)
            return

        self._worker.cancel()

    def shutdown(
        self,
        timeout_ms: int = 3000,
    ) -> None:
        """Tat webcam va cho worker ket thuc. Chi goi khi thoat ung dung."""
        if self._worker is None:
            return

        try:
            self._worker.dispose(timeout_ms)
        except RuntimeError:
            self._worker = None

    # ------------------------------------------------------------------
    # Signal tu Worker (chay tren GUI thread nho queued connection)
    # ------------------------------------------------------------------

    def _on_frame_ready(
        self,
        image: QImage,
    ) -> None:
        """Chuyen frame ra View roi tra suat cho `FrameGate`.

        Phai release SAU khi View da nhan, nho vay worker biet GUI da theo kip
        va duoc phep gui frame tiep (NHIEM VU 6 - backpressure).
        """
        try:
            self.FrameUpdated.emit(image)
        finally:
            if self._worker is not None:
                self._worker.release_frame()

    @property
    def frame_stats(self) -> dict:
        """Thong ke backpressure cua phien webcam hien tai."""
        if self._worker is None:
            return {
                "emitted": 0,
                "dropped": 0,
                "in_flight": 0,
                "total": 0,
                "drop_percent": 0,
            }

        return self._worker.frame_gate.stats()

    def _on_results_ready(
        self,
        results: list,
    ) -> None:
        self._results = results
        self.DetectionCompleted.emit(results)

    def _on_related_ready(
        self,
        words: list,
    ) -> None:
        self._related_words = words
        self.RelatedWordsUpdated.emit(words)

    def _on_cluster_ready(
        self,
        words: list,
    ) -> None:
        self._cluster_words = words
        self.ClusterWordsUpdated.emit(words)

    def _on_worker_finished(self) -> None:
        self._worker = None
        self._set_running(False)
        self.set_state(UiState.IDLE)

    # ------------------------------------------------------------------
    # Nguoi dung
    # ------------------------------------------------------------------

    def set_user_id(
        self,
        user_id: int | None,
    ) -> None:
        super().set_user_id(user_id)

        if self._worker is not None:
            self._worker.user_id = user_id
