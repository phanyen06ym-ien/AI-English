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

from detection.image_detect import detect_image
from ml.kmeans import get_words_in_same_cluster
from ml.knn import get_related_words
from ui.qt_utils import to_qimage
from ui.speech_worker import SpeakTask


class ImageDetectThread(QThread):
    image_ready = Signal(QImage)
    results_ready = Signal(list)
    failed = Signal(str)

    def __init__(
        self,
        detector,
        image_path: str,
        user_id: int | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.detector = detector
        self.image_path = image_path
        self.user_id = user_id

    def run(self) -> None:
        try:
            image, results = detect_image(
                self.image_path,
                detector=self.detector,
                show_window=False,
                user_id=self.user_id,
            )

            if image is None:
                self.failed.emit(
                    "Không đọc được ảnh."
                )
                return

            self.image_ready.emit(
                to_qimage(image)
            )
            self.results_ready.emit(results)

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
        detector,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.detector = detector
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
            self.detector,
            self._selected_image_path,
            self._user_id,
        )
        self._thread.image_ready.connect(
            self._on_image_ready
        )
        self._thread.results_ready.connect(
            self._on_results_ready
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

    def _on_results_ready(
        self,
        results: list,
    ) -> None:
        formatted_results = []

        for item in results:
            english = item.get("english", "")
            vietnamese = item.get("vietnamese") or english
            category = item.get("category") or "Unknown"
            level = item.get("level") or "Unknown"
            confidence = float(
                item.get("confidence", 0.0)
            )

            formatted_results.append(
                {
                    "english": english,
                    "vietnamese": vietnamese,
                    "category": category,
                    "level": level,
                    "confidence": confidence,
                    "text": (
                        f"{english} - {vietnamese} "
                        f"[{category} - {level}] "
                        f"({confidence:.2f})"
                    ),
                }
            )

        formatted_results.sort(
            key=lambda item: item["confidence"],
            reverse=True,
        )
        self._results = formatted_results
        self.resultsChanged.emit(formatted_results)

        if formatted_results:
            primary_word = formatted_results[0]["english"]
            self._related_words = get_related_words(
                primary_word,
                n=3,
            )
            self._cluster_words = get_words_in_same_cluster(
                primary_word
            )
        else:
            self._related_words = []
            self._cluster_words = []

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
