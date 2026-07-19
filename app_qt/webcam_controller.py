import cv2

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtGui import QImage

from app_qt.qt_utils import to_qimage
from detection.classify import classify_word
from utils.config import CAMERA_ID
from utils.helper import draw_vietnamese_text, open_camera


class WebcamThread(QThread):
    frameReady = Signal(QImage)
    error = Signal(str)

    def __init__(self, detector, camera_id, parent=None):
        super().__init__(parent)
        self.detector = detector
        self.camera_id = camera_id
        self._running = False

    def run(self):
        cap = open_camera(self.camera_id)
        if not cap.isOpened():
            cap.release()
            self.error.emit("Không mở được webcam")
            return

        self._running = True
        try:
            while self._running:
                ret, frame = cap.read()
                if not ret:
                    continue

                for obj in self.detector.detect(frame):
                    class_name = obj["class_name"]
                    info = classify_word(class_name)
                    vietnamese = info["vietnamese"] or class_name
                    x1, y1, x2, y2 = obj["box"]
                    label = f"{class_name} - {vietnamese} [{info['category']}]"

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    frame = draw_vietnamese_text(
                        frame, label, (x1, max(y1 - 35, 5)), color=(0, 255, 0), size=28
                    )

                self.frameReady.emit(to_qimage(frame))
        finally:
            cap.release()

    def stop(self):
        self._running = False
        self.wait(2000)


class WebcamController(QObject):
    frameReady = Signal(QImage)
    statusChanged = Signal(str)

    def __init__(self, detector, parent=None):
        super().__init__(parent)
        self.detector = detector
        self._thread = None

    @Slot()
    def start(self):
        if self._thread is not None:
            return

        self._thread = WebcamThread(self.detector, CAMERA_ID)
        self._thread.frameReady.connect(self.frameReady)
        self._thread.error.connect(self._on_error)
        self._thread.finished.connect(self._on_finished)
        self._thread.start()

    @Slot()
    def stop(self):
        if self._thread is not None:
            self._thread.stop()
        self.statusChanged.emit("Webcam đã tắt")

    def _on_error(self, message):
        self.statusChanged.emit(message)

    def _on_finished(self):
        self._thread = None
