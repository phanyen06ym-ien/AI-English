"""Worker cho luong nhan dien anh tinh.

Sprint 3: tach business logic ra `DetectionService`.
Sprint 5: chuyen sang `ManagedWorker` de co vong doi va co che huy thong nhat.

Truoc Sprint 5, hai worker nay **khong huy duoc**: nguoi dung chon nham anh la
phai cho YOLO chay xong. Gio moi buoc deu kiem tra `token`.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QImage

from ui.qt_utils import to_qimage
from ui.services.detection_service import (
    ERROR_IMAGE_UNREADABLE,
    DetectionService,
)
from ui.workers.cancellation import CancellationToken
from ui.workers.lifecycle import ManagedWorker


class PreviewLoadWorker(ManagedWorker):
    """Doc anh xem truoc tren thread nen de GUI khong bi freeze."""

    previewReady = Signal(QImage)

    def __init__(
        self,
        detection_service: DetectionService,
        image_path: str,
        token: CancellationToken | None = None,
        parent=None,
    ) -> None:
        super().__init__(
            "preview_worker",
            token=token,
            parent=parent,
        )

        self._detection_service = detection_service
        self.image_path = image_path

    def execute(self) -> None:
        self.token.raise_if_cancelled()

        image = self._detection_service.load_image(
            self.image_path
        )

        self.token.raise_if_cancelled()

        if image is None:
            self.failed.emit(ERROR_IMAGE_UNREADABLE)
            return

        self.previewReady.emit(
            to_qimage(image)
        )


class ImageWorker(ManagedWorker):
    """Chay pipeline nhan dien cho mot file anh."""

    imageReady = Signal(QImage)
    analysisReady = Signal(object)
    progressChanged = Signal(int)

    def __init__(
        self,
        detection_service: DetectionService,
        image_path: str,
        user_id: int | None = None,
        token: CancellationToken | None = None,
        parent=None,
    ) -> None:
        super().__init__(
            "image_worker",
            token=token,
            parent=parent,
        )

        self._detection_service = detection_service
        self.image_path = image_path
        self.user_id = user_id

    def _report_progress(
        self,
        percent: int,
    ) -> None:
        """Diem kiem tra huy: goi sau moi buoc cua pipeline."""
        self.token.raise_if_cancelled()
        self.progressChanged.emit(percent)

    def execute(self) -> None:
        self.token.raise_if_cancelled()

        outcome = self._detection_service.analyze_image_file(
            self.image_path,
            user_id=self.user_id,
            progress_callback=self._report_progress,
        )

        self.token.raise_if_cancelled()

        if not outcome.success:
            self.failed.emit(outcome.message)
            return

        self.imageReady.emit(
            to_qimage(outcome.annotated_frame)
        )
        self.analysisReady.emit(outcome.analysis)
