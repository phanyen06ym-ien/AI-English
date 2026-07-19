from PySide6.QtCore import QObject, QThread, Property, QThreadPool, Signal, Slot
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QFileDialog

from app_qt.qt_utils import to_qimage
from app_qt.speech_worker import SpeakTask
from detection.image_detect import detect_image


class ImageDetectThread(QThread):
    imageReady = Signal(QImage)
    resultsReady = Signal(list)
    failed = Signal(str)

    def __init__(self, detector, path, parent=None):
        super().__init__(parent)
        self.detector = detector
        self.path = path

    def run(self):
        image, results = detect_image(
            self.path, detector=self.detector, show_window=False
        )
        if image is None:
            self.failed.emit("Không đọc được ảnh")
            return

        self.imageReady.emit(to_qimage(image))
        self.resultsReady.emit(results)


class ImageController(QObject):
    imageChanged = Signal(QImage)
    resultsChanged = Signal(list)
    statusChanged = Signal(str)
    busyChanged = Signal(bool)
    detectionFinished = Signal()

    def __init__(self, detector, parent=None):
        super().__init__(parent)
        self.detector = detector
        self._busy = False
        self._thread = None

    def _get_busy(self):
        return self._busy

    busy = Property(bool, _get_busy, notify=busyChanged)

    def _set_busy(self, value):
        if self._busy != value:
            self._busy = value
            self.busyChanged.emit(value)

    @Slot()
    def chooseImage(self):
        if self._busy:
            return

        path, _ = QFileDialog.getOpenFileName(
            None, "Chọn ảnh", "", "Ảnh (*.jpg *.jpeg *.png *.bmp)"
        )
        if not path:
            return

        self._set_busy(True)
        self._thread = ImageDetectThread(self.detector, path)
        self._thread.imageReady.connect(self._on_image_ready)
        self._thread.resultsReady.connect(self._on_results_ready)
        self._thread.failed.connect(self._on_failed)
        self._thread.finished.connect(self._on_finished)
        self._thread.start()

    def _on_image_ready(self, qimage):
        self.imageChanged.emit(qimage)

    def _on_results_ready(self, results):
        self.resultsChanged.emit([
            {
                "english": item["english"],
                "text": "{} — {} [{}] ({:.2f})".format(
                    item["english"],
                    item["vietnamese"] or item["english"],
                    item["category"],
                    item["confidence"],
                ),
            }
            for item in results
        ])

    def _on_failed(self, message):
        self.statusChanged.emit(message)

    def _on_finished(self):
        self._thread = None
        self._set_busy(False)
        self.detectionFinished.emit()

    @Slot(str)
    def speak(self, word):
        QThreadPool.globalInstance().start(SpeakTask(word))
