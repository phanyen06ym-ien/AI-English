from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QModelIndex,
    QObject,
    Qt,
    QThread,
    QThreadPool,
    Signal,
    Slot,
)

from database.history import clear_history, get_history
from app_qt.speech_worker import SpeakTask


class HistoryModel(QAbstractListModel):
    EnglishRole = Qt.UserRole + 1
    VietnameseRole = Qt.UserRole + 2
    CategoryRole = Qt.UserRole + 3
    ConfidenceRole = Qt.UserRole + 4
    DetectedTimeRole = Qt.UserRole + 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []

    def roleNames(self):
        return {
            self.EnglishRole: b"english",
            self.VietnameseRole: b"vietnamese",
            self.CategoryRole: b"category",
            self.ConfidenceRole: b"confidence",
            self.DetectedTimeRole: b"detectedTime",
        }

    def rowCount(self, parent=QModelIndex()):
        return len(self._rows)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = self._rows[index.row()]
        if role == self.EnglishRole:
            return row["english"]
        if role == self.VietnameseRole:
            return row["vietnamese"]
        if role == self.CategoryRole:
            return row["category"]
        if role == self.ConfidenceRole:
            return row["confidence"]
        if role == self.DetectedTimeRole:
            return row["detected_time"]
        return None

    def setRows(self, rows):
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()


class HistoryLoadWorker(QThread):
    """Đọc (và tùy chọn xóa) lịch sử ở luồng nền để không đơ UI khi DB chậm."""

    loaded = Signal(list)

    def __init__(self, clear_first=False, parent=None):
        super().__init__(parent)
        self.clear_first = clear_first

    def run(self):
        if self.clear_first:
            clear_history()
        self.loaded.emit(get_history())


class HistoryController(QObject):
    loadingChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = HistoryModel()
        self._workers = []

    @Property(QObject, constant=True)
    def model(self):
        return self._model

    def _get_loading(self):
        return bool(self._workers)

    loading = Property(bool, _get_loading, notify=loadingChanged)

    def _start(self, clear_first):
        worker = HistoryLoadWorker(clear_first)
        worker.loaded.connect(self._on_loaded)
        worker.finished.connect(lambda w=worker: self._on_finished(w))
        self._workers.append(worker)
        self.loadingChanged.emit(True)
        worker.start()

    @Slot()
    def refresh(self):
        # Một lượt tải đang chạy là đủ; tránh dồn nhiều truy vấn giống nhau.
        if any(not w.clear_first for w in self._workers):
            return
        self._start(clear_first=False)

    @Slot()
    def clearHistory(self):
        if any(w.clear_first for w in self._workers):
            return
        self._start(clear_first=True)

    def _on_loaded(self, rows):
        self._model.setRows([
            {
                "english": row["english"],
                "vietnamese": row["vietnamese"] or row["english"],
                "category": row["category"],
                "confidence": row["confidence"] or 0.0,
                "detected_time": row["detected_time"].strftime("%d/%m %H:%M")
                if row["detected_time"]
                else "",
            }
            for row in rows
        ])

    def _on_finished(self, worker):
        if worker in self._workers:
            self._workers.remove(worker)
        self.loadingChanged.emit(bool(self._workers))

    @Slot(str)
    def speak(self, word):
        QThreadPool.globalInstance().start(SpeakTask(word))
