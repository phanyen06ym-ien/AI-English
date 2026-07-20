from __future__ import annotations

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QImage, QPainter
from PySide6.QtQuick import QQuickPaintedItem

from utils import perf_monitor


class VideoItem(QQuickPaintedItem):
    """
    Component dùng để hiển thị QImage trên QML.
    """

    def __init__(
        self,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._image = QImage()

    def paint(
        self,
        painter: QPainter,
    ) -> None:
        perf_monitor.increment("video_item_paint")
        if self._image.isNull():
            return

        target_size = (
            self.boundingRect()
            .size()
            .toSize()
        )

        with perf_monitor.timer("video_item_scale_image"):
            scaled_image = self._image.scaled(
                target_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )

        x = (
            target_size.width()
            - scaled_image.width()
        ) / 2

        y = (
            target_size.height()
            - scaled_image.height()
        ) / 2

        with perf_monitor.timer("video_item_draw_image"):
            painter.drawImage(
                x,
                y,
                scaled_image,
            )

    @Slot(QImage)
    def setImage(
        self,
        image: QImage,
    ) -> None:
        perf_monitor.increment("video_item_set_image")
        self._image = image
        self.update()
