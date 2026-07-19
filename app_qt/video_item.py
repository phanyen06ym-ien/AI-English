from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickPaintedItem


class VideoItem(QQuickPaintedItem):
    """Vẽ trực tiếp QImage lên canvas QML, dùng cho cả webcam realtime và ảnh tĩnh."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = QImage()

    def paint(self, painter):
        if self._image.isNull():
            return

        target = self.boundingRect().size().toSize()
        scaled = self._image.scaled(target, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x = (target.width() - scaled.width()) / 2
        y = (target.height() - scaled.height()) / 2
        painter.drawImage(x, y, scaled)

    @Slot(QImage)
    def setImage(self, image):
        self._image = image
        self.update()
