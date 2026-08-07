"""Thin Controller cho man hinh webcam.

Sau Sprint 3 file nay KHONG con:

- vong lap doc frame, `cv2.VideoCapture`      -> `WebcamWorker`
- nguong confidence + cooldown lich su        -> `HistoryRecordPolicy`
- goi `save_history()`                        -> `HistoryService`
- ve bounding box                             -> `AnnotationService`
- goi `AIEngine`                              -> `DetectionService`

Property / Signal / Slot public giu nguyen ten de QML khong phai sua.
"""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QObject,
    Signal,
    Slot,
)
from PySide6.QtGui import QImage

from ui.services.dialog_service import DialogService
from ui.ui_logger import get_ui_logger, log_button_click
from ui.viewmodels.webcam_viewmodel import WebcamViewModel


logger = get_ui_logger("webcam_controller")


class WebcamController(QObject):
    """Adapter giua QML va `WebcamViewModel`."""

    frameChanged = Signal(QImage)
    statusChanged = Signal(str)
    runningChanged = Signal(bool)
    resultsChanged = Signal(list)
    relatedWordsChanged = Signal(list)
    clusterWordsChanged = Signal(list)
    historySaved = Signal()

    def __init__(
        self,
        view_model: WebcamViewModel,
        dialog_service: DialogService | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._view_model = view_model
        self._dialog_service = dialog_service

        self._connect_view_model()

    def _connect_view_model(self) -> None:
        self._view_model.FrameUpdated.connect(
            self.frameChanged
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
        self._view_model.HistoryUpdated.connect(
            self.historySaved
        )
        self._view_model.RunningChanged.connect(
            self.runningChanged
        )
        self._view_model.StatusMessageChanged.connect(
            self._on_status_changed
        )

    def _on_status_changed(
        self,
        message: str,
    ) -> None:
        self.statusChanged.emit(message)

        if self._dialog_service is not None:
            self._dialog_service.publish(message)

    # ------------------------------------------------------------------
    # Property
    # ------------------------------------------------------------------

    @property
    def view_model(self) -> WebcamViewModel:
        return self._view_model

    @Property(bool, notify=runningChanged)
    def running(self) -> bool:
        return self._view_model.running

    @Property(list, notify=resultsChanged)
    def detections(self) -> list:
        return self._view_model.detections

    @Property(list, notify=relatedWordsChanged)
    def relatedWords(self) -> list:
        return self._view_model.relatedWords

    @Property(list, notify=clusterWordsChanged)
    def clusterWords(self) -> list:
        return self._view_model.clusterWords

    # ------------------------------------------------------------------
    # Slot goi tu QML
    # ------------------------------------------------------------------

    def set_user_id(
        self,
        user_id: int | None,
    ) -> None:
        self._view_model.set_user_id(user_id)

    @Slot()
    def start(self) -> None:
        log_button_click(logger, "webcam_start")

        self._view_model.start()

    @Slot()
    def stop(self) -> None:
        log_button_click(logger, "webcam_stop")

        self._view_model.stop()

    def shutdown(self) -> None:
        """Dung webcam va cho worker ket thuc khi thoat ung dung."""
        self._view_model.shutdown()
