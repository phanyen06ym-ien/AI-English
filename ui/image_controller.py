"""Thin Controller cho man hinh anh tinh.

Sau Sprint 3 file nay KHONG con:

- goi `AIEngine`            -> `ImageViewModel` -> `DetectionService`
- goi `save_history()`      -> `HistoryService`
- goi `cv2` / `draw_*`      -> `AnnotationService`
- tao/quan ly QThread       -> `ImageWorker` / `PreviewLoadWorker`

Controller chi con 3 viec:

1. Nhan event tu QML (Slot).
2. Goi ViewModel.
3. Chuyen tiep Signal cua ViewModel sang dung ten legacy ma QML dang bind.

Toan bo Property / Signal / Slot public duoc giu NGUYEN TEN de khong phai sua QML.
"""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QObject,
    Signal,
    Slot,
)
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QFileDialog

from ui.services.dialog_service import DialogService
from ui.ui_logger import get_ui_logger, log_button_click
from ui.viewmodels.image_viewmodel import ImageViewModel
from ui.workers.speech_worker import SpeakTask
from ui.workers.task_pool import submit


logger = get_ui_logger("image_controller")

FILE_DIALOG_TITLE = "Chọn ảnh"
FILE_DIALOG_FILTER = "Ảnh (*.jpg *.jpeg *.png *.bmp)"


def open_image_file_dialog() -> str:
    """Mo hop thoai chon file. Day la viec cua View, khong phai ViewModel."""
    image_path, _ = QFileDialog.getOpenFileName(
        None,
        FILE_DIALOG_TITLE,
        "",
        FILE_DIALOG_FILTER,
    )

    return image_path


class ImageController(QObject):
    """Adapter giua QML va `ImageViewModel`."""

    imageChanged = Signal(QImage)
    resultsChanged = Signal(list)
    relatedWordsChanged = Signal(list)
    clusterWordsChanged = Signal(list)
    statusChanged = Signal(str)
    busyChanged = Signal(bool)
    selectedImagePathChanged = Signal(str)
    detectionFinished = Signal()
    progressChanged = Signal(int)

    def __init__(
        self,
        view_model: ImageViewModel,
        dialog_service: DialogService | None = None,
        file_picker=open_image_file_dialog,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._view_model = view_model
        self._dialog_service = dialog_service
        self._file_picker = file_picker

        self._connect_view_model()

    # ------------------------------------------------------------------
    # Signal mapping: ViewModel (chuan hoa) -> Controller (legacy cho QML)
    # ------------------------------------------------------------------

    def _connect_view_model(self) -> None:
        self._view_model.PreviewUpdated.connect(
            self.imageChanged
        )
        self._view_model.DetectionCompleted.connect(
            self.resultsChanged
        )
        self._view_model.RelatedWordsUpdated.connect(
            self.relatedWordsChanged
        )
        self._view_model.ClusterWordsUpdated.connect(
            self.clusterWordsChanged
        )
        self._view_model.StatusMessageChanged.connect(
            self._on_status_changed
        )
        self._view_model.BusyChanged.connect(
            self.busyChanged
        )
        self._view_model.SelectedImageChanged.connect(
            self.selectedImagePathChanged
        )
        self._view_model.DetectionFinished.connect(
            self.detectionFinished
        )
        self._view_model.ProgressChanged.connect(
            self._on_progress_changed
        )
        self._view_model.ErrorRaised.connect(
            self._on_error
        )

    def _on_status_changed(
        self,
        message: str,
    ) -> None:
        self.statusChanged.emit(message)

        if self._dialog_service is not None:
            self._dialog_service.publish(message)

    def _on_progress_changed(
        self,
        percent: int,
    ) -> None:
        self.progressChanged.emit(percent)

        if self._dialog_service is not None:
            self._dialog_service.updateProgress(percent)

    def _on_error(
        self,
        message: str,
    ) -> None:
        if self._dialog_service is not None:
            self._dialog_service.showError(message)

    # ------------------------------------------------------------------
    # Property doc tu ViewModel
    # ------------------------------------------------------------------

    @property
    def view_model(self) -> ImageViewModel:
        return self._view_model

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._view_model.busy

    @Property(str, notify=selectedImagePathChanged)
    def selectedImagePath(self) -> str:
        return self._view_model.selectedImagePath

    @Property(str, notify=selectedImagePathChanged)
    def displayImageSource(self) -> str:
        return self._view_model.selectedImagePath

    @Property(str, notify=selectedImagePathChanged)
    def annotatedImageSource(self) -> str:
        return self._view_model.selectedImagePath

    @Property(list, notify=resultsChanged)
    def detections(self) -> list:
        return self._view_model.detections

    @Property(list, notify=relatedWordsChanged)
    def relatedWords(self) -> list:
        return self._view_model.relatedWords

    @Property(list, notify=clusterWordsChanged)
    def clusterWords(self) -> list:
        return self._view_model.clusterWords

    @Property(str, notify=statusChanged)
    def statusMessage(self) -> str:
        return self._view_model.statusMessage

    @Property(int, notify=progressChanged)
    def progress(self) -> int:
        return self._view_model.progress

    # ------------------------------------------------------------------
    # Slot goi tu QML
    # ------------------------------------------------------------------

    def set_user_id(
        self,
        user_id: int | None,
    ) -> None:
        self._view_model.set_user_id(user_id)

    @Slot()
    def chooseImage(self) -> None:
        log_button_click(logger, "choose_image")

        if self._view_model.busy:
            return

        image_path = self._file_picker()

        if not image_path:
            return

        self._view_model.selectImage(image_path)

    @Slot()
    def detectSelectedImage(self) -> None:
        log_button_click(logger, "detect_selected_image")

        self._view_model.detectSelectedImage()

    @Slot()
    def cancelDetection(self) -> None:
        log_button_click(logger, "cancel_detection")

        self._view_model.cancel()

    @Slot(str)
    def speak(
        self,
        word: str,
    ) -> None:
        log_button_click(logger, "speak_word")

        submit(
            SpeakTask(word)
        )
