"""ViewModel cho man hinh nhan dien anh tinh."""

from __future__ import annotations

from PySide6.QtCore import Property, Signal, Slot
from PySide6.QtGui import QImage

from ui.services.detection_service import DetectionService
from ui.state import UiState
from ui.ui_logger import log_ui_event
from ui.viewmodels.base_viewmodel import BaseViewModel
from ui.workers.image_worker import (
    ImageWorker,
    PreviewLoadWorker,
)


STATUS_SELECT_FIRST = "Vui lòng chọn ảnh trước."
STATUS_IMAGE_LOADING = "Đang tải ảnh..."
STATUS_IMAGE_SELECTED = "Đã chọn ảnh. Bấm Nhận diện để chạy YOLO."
STATUS_DETECTING = "Đang nhận diện..."
STATUS_NO_OBJECT = "Không phát hiện vật thể nào."
STATUS_CANCELLED = "Đã hủy nhận diện."


class ImageViewModel(BaseViewModel):
    """Giu trang thai cua luong: chon anh -> nhan dien -> hien ket qua."""

    PreviewUpdated = Signal(QImage)
    DetectionStarted = Signal()
    DetectionCompleted = Signal(list)
    DetectionFailed = Signal(str)
    DetectionFinished = Signal()
    RelatedWordsUpdated = Signal(list)
    ClusterWordsUpdated = Signal(list)
    SelectedImageChanged = Signal(str)
    ProgressChanged = Signal(int)

    def __init__(
        self,
        detection_service: DetectionService,
        parent=None,
    ) -> None:
        super().__init__("image_viewmodel", parent)

        self._detection_service = detection_service
        self._selected_image_path = ""
        self._results: list[dict] = []
        self._related_words: list[dict] = []
        self._cluster_words: list[dict] = []
        self._progress = 0
        self._detect_worker: ImageWorker | None = None
        self._preview_worker: PreviewLoadWorker | None = None

    # ------------------------------------------------------------------
    # Trang thai doc duoc
    # ------------------------------------------------------------------

    @Property(str, notify=SelectedImageChanged)
    def selectedImagePath(self) -> str:
        return self._selected_image_path

    @Property(list, notify=DetectionCompleted)
    def detections(self) -> list:
        return self._results

    @Property(list, notify=RelatedWordsUpdated)
    def relatedWords(self) -> list:
        return self._related_words

    @Property(list, notify=ClusterWordsUpdated)
    def clusterWords(self) -> list:
        return self._cluster_words

    @Property(int, notify=ProgressChanged)
    def progress(self) -> int:
        return self._progress

    def _set_progress(
        self,
        value: int,
    ) -> None:
        self._progress = int(value)
        self.ProgressChanged.emit(self._progress)

    def _clear_results(self) -> None:
        self._results = []
        self._related_words = []
        self._cluster_words = []
        self.DetectionCompleted.emit([])
        self.RelatedWordsUpdated.emit([])
        self.ClusterWordsUpdated.emit([])

    # ------------------------------------------------------------------
    # Chon anh
    # ------------------------------------------------------------------

    @Slot(str)
    def selectImage(
        self,
        image_path: str,
    ) -> None:
        """Nhan duong dan anh tu View va tai anh xem truoc ngoai GUI thread."""
        if self.ui_state.is_busy():
            return

        if not image_path:
            return

        log_ui_event(self.logger, "select_image")

        self.set_state(UiState.LOADING)
        self.set_status(STATUS_IMAGE_LOADING)
        self._set_progress(0)

        self._preview_worker = PreviewLoadWorker(
            self._detection_service,
            image_path,
        )
        self._preview_worker.previewReady.connect(
            lambda image, path=image_path: self._on_preview_ready(
                path,
                image,
            )
        )
        self._preview_worker.failed.connect(
            self._on_preview_failed
        )
        self._preview_worker.cancelled.connect(
            self._on_worker_cancelled
        )
        self._preview_worker.finished.connect(
            self._on_preview_finished
        )
        self._preview_worker.start()

    def _on_preview_ready(
        self,
        image_path: str,
        image: QImage,
    ) -> None:
        self._selected_image_path = image_path
        self.SelectedImageChanged.emit(image_path)

        self._clear_results()
        self.PreviewUpdated.emit(image)

        self.set_state(UiState.COMPLETED)
        self.set_status(STATUS_IMAGE_SELECTED)
        self._set_progress(100)

    def _on_preview_failed(
        self,
        message: str,
    ) -> None:
        self.fail(message)

    def _on_preview_finished(self) -> None:
        self._preview_worker = None
        self.set_state(UiState.IDLE)

    # ------------------------------------------------------------------
    # Nhan dien
    # ------------------------------------------------------------------

    @Slot()
    def detectSelectedImage(self) -> None:
        """Bat dau nhan dien anh dang chon."""
        if self.ui_state.is_busy():
            return

        if not self._selected_image_path:
            self.set_status(STATUS_SELECT_FIRST)
            return

        log_ui_event(self.logger, "detect_image_requested")

        self.set_state(UiState.DETECTING)
        self.set_status(STATUS_DETECTING)
        self._set_progress(0)
        self.DetectionStarted.emit()

        self._detect_worker = ImageWorker(
            self._detection_service,
            self._selected_image_path,
            self.user_id,
        )
        self._detect_worker.imageReady.connect(
            self.PreviewUpdated
        )
        self._detect_worker.analysisReady.connect(
            self._on_analysis_ready
        )
        self._detect_worker.progressChanged.connect(
            self._set_progress
        )
        self._detect_worker.failed.connect(
            self._on_detection_failed
        )
        self._detect_worker.cancelled.connect(
            self._on_worker_cancelled
        )
        self._detect_worker.finished.connect(
            self._on_detection_finished
        )
        self._detect_worker.start()

    def _on_analysis_ready(
        self,
        analysis,
    ) -> None:
        results = analysis.detections_as_dicts(
            include_box=False,
        )
        self._results = results
        self._related_words = analysis.related_words_as_dicts()
        self._cluster_words = analysis.cluster_words_as_dicts()

        self.DetectionCompleted.emit(results)
        self.RelatedWordsUpdated.emit(self._related_words)
        self.ClusterWordsUpdated.emit(self._cluster_words)

        self.set_state(UiState.COMPLETED)

        if results:
            self.set_status(
                f"Phát hiện {len(results)} vật thể."
            )
        else:
            self.set_status(STATUS_NO_OBJECT)

    def _on_detection_failed(
        self,
        message: str,
    ) -> None:
        self.DetectionFailed.emit(message)
        self.fail(message)

    def _on_detection_finished(self) -> None:
        self._detect_worker = None
        self.set_state(UiState.IDLE)
        self.DetectionFinished.emit()

    @Slot()
    def cancel(self) -> None:
        """Huy viec dang chay. KHONG chan GUI thread (Sprint 5).

        Truoc Sprint 5 khong the huy: chon nham anh la phai cho YOLO chay xong.
        """
        if not self.ui_state.is_busy():
            return

        log_ui_event(self.logger, "detection_cancelled")

        self._cancel_workers(
            (
                self._preview_worker,
                self._detect_worker,
            )
        )

        self.set_status(STATUS_CANCELLED)

    def _on_worker_cancelled(self) -> None:
        """Worker bao da dung theo yeu cau - khong phai loi."""
        self.set_state(UiState.IDLE)

    def shutdown(
        self,
        timeout_ms: int = 3000,
    ) -> None:
        self._await_workers(
            (
                self._preview_worker,
                self._detect_worker,
            ),
            timeout_ms,
        )
