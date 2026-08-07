from __future__ import annotations

import cv2
from PySide6.QtCore import (
    QObject,
    Property,
    QThread,
    QThreadPool,
    Signal,
    Slot,
)
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QFileDialog

from database.history import save_history
from ai.pipeline import AIEngine
from ui.qt_utils import to_qimage
from ui.speech_worker import SpeakTask
from utils.helper import draw_vietnamese_text


class ImageDetectThread(QThread):
    image_ready = Signal(QImage)
    analysis_ready = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        ai_engine: AIEngine,
        image_path: str,
        user_id: int | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.ai_engine = ai_engine
        self.image_path = image_path
        self.user_id = user_id

    def run(self) -> None:
        try:
            image = cv2.imread(self.image_path)

            if image is None:
                self.failed.emit(
                    "Không đọc được ảnh."
                )
                return

            analysis = self.ai_engine.analyze_frame(image)

            if not analysis.success:
                self.failed.emit(analysis.message)
                return

            for result in analysis.detections:
                x1, y1, x2, y2 = result.box
                label = (
                    f"{result.english} - {result.vietnamese} "
                    f"[{result.category}] "
                    f"({result.confidence:.2f})"
                )
                save_history(
                    result.english,
                    result.vietnamese,
                    result.category,
                    result.confidence,
                    user_id=self.user_id,
                )
                cv2.rectangle(
                    image,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2,
                )
                image = draw_vietnamese_text(
                    image,
                    label,
                    (x1, max(y1 - 35, 5)),
                    color=(0, 255, 0),
                    size=28,
                )

            self.image_ready.emit(
                to_qimage(image)
            )
            self.analysis_ready.emit(analysis)

        except Exception as error:
            self.failed.emit(str(error))


class ImageController(QObject):
    imageChanged = Signal(QImage)
    resultsChanged = Signal(list)
    relatedWordsChanged = Signal(list)
    clusterWordsChanged = Signal(list)
    statusChanged = Signal(str)
    busyChanged = Signal(bool)
    selectedImagePathChanged = Signal(str)
    detectionFinished = Signal()

    def __init__(
        self,
        ai_engine: AIEngine,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.ai_engine = ai_engine
        self._busy = False
        self._thread = None
        self._user_id = None
        self._selected_image_path = ""
        self._results = []
        self._related_words = []
        self._cluster_words = []
        self._status_message = ""

    def set_user_id(
        self,
        user_id: int | None,
    ) -> None:
        self._user_id = user_id

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=selectedImagePathChanged)
    def selectedImagePath(self) -> str:
        return self._selected_image_path

    @Property(str, notify=selectedImagePathChanged)
    def displayImageSource(self) -> str:
        return self._selected_image_path

    @Property(str, notify=selectedImagePathChanged)
    def annotatedImageSource(self) -> str:
        return self._selected_image_path

    @Property(list, notify=resultsChanged)
    def detections(self) -> list:
        return self._results

    @Property(list, notify=relatedWordsChanged)
    def relatedWords(self) -> list:
        return self._related_words

    @Property(list, notify=clusterWordsChanged)
    def clusterWords(self) -> list:
        return self._cluster_words

    @Property(str, notify=statusChanged)
    def statusMessage(self) -> str:
        return self._status_message

    def _set_status(
        self,
        message: str,
    ) -> None:
        self._status_message = message
        self.statusChanged.emit(message)

    def _set_busy(
        self,
        value: bool,
    ) -> None:
        if self._busy == value:
            return
        self._busy = value
        self.busyChanged.emit(value)

    def _clear_results(self) -> None:
        self._results = []
        self._related_words = []
        self._cluster_words = []
        self.resultsChanged.emit([])
        self.relatedWordsChanged.emit([])
        self.clusterWordsChanged.emit([])

    @Slot()
    def chooseImage(self) -> None:
        if self._busy:
            return

        image_path, _ = QFileDialog.getOpenFileName(
            None,
            "Chọn ảnh",
            "",
            "Ảnh (*.jpg *.jpeg *.png *.bmp)",
        )

        if not image_path:
            return

        image = cv2.imread(image_path)

        if image is None:
            self._set_status(
                "Không đọc được ảnh."
            )
            return

        self._selected_image_path = image_path
        self.selectedImagePathChanged.emit(image_path)
        self._clear_results()
        self.imageChanged.emit(
            to_qimage(image)
        )
        self._set_status(
            "Đã chọn ảnh. Bấm Nhận diện để chạy YOLO."
        )

    @Slot()
    def detectSelectedImage(self) -> None:
        if self._busy:
            return

        if not self._selected_image_path:
            self._set_status(
                "Vui lòng chọn ảnh trước."
            )
            return

        self._set_busy(True)
        self._set_status(
            "Đang nhận diện..."
        )

        self._thread = ImageDetectThread(
            self.ai_engine,
            self._selected_image_path,
            self._user_id,
        )
        self._thread.image_ready.connect(
            self._on_image_ready
        )
        self._thread.analysis_ready.connect(
            self._on_analysis_ready
        )
        self._thread.failed.connect(
            self._on_failed
        )
        self._thread.finished.connect(
            self._on_finished
        )
        self._thread.start()

    def _on_image_ready(
        self,
        image: QImage,
    ) -> None:
        self.imageChanged.emit(image)

    def _on_analysis_ready(
        self,
        analysis: object,
    ) -> None:
        formatted_results = analysis.detections_as_dicts(
            include_box=False,
        )
        self._results = formatted_results
        self.resultsChanged.emit(formatted_results)

        self._related_words = analysis.related_words_as_dicts()
        self._cluster_words = analysis.cluster_words_as_dicts()

        self.relatedWordsChanged.emit(
            self._related_words
        )
        self.clusterWordsChanged.emit(
            self._cluster_words
        )

        if formatted_results:
            self._set_status(
                f"Phát hiện {len(formatted_results)} vật thể."
            )
        else:
            self._set_status(
                "Không phát hiện vật thể nào."
            )

    def _on_failed(
        self,
        message: str,
    ) -> None:
        self._set_status(message)

    def _on_finished(self) -> None:
        self._thread = None
        self._set_busy(False)
        self.detectionFinished.emit()

    @Slot(str)
    def speak(
        self,
        word: str,
    ) -> None:
        QThreadPool.globalInstance().start(
            SpeakTask(word)
        )
