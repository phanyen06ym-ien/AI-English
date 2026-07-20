from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QModelIndex,
    QObject,
    Qt,
    QThread,
    Signal,
    Slot,
)

from database.history import (
    clear_history,
    get_history,
)
from utils import perf_monitor


class HistoryModel(QAbstractListModel):
    EnglishRole = Qt.UserRole + 1
    VietnameseRole = Qt.UserRole + 2
    CategoryRole = Qt.UserRole + 3
    ConfidenceRole = Qt.UserRole + 4
    DetectedTimeRole = Qt.UserRole + 5

    def __init__(
        self,
        parent=None,
    ) -> None:
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

    def rowCount(
        self,
        parent=QModelIndex(),
    ) -> int:
        return len(self._rows)

    def data(
        self,
        index,
        role=Qt.DisplayRole,
    ):
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

    def set_rows(
        self,
        rows: list[dict],
    ) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()


class HistoryWorker(QThread):
    loaded = Signal(list)
    failed = Signal(str)

    def __init__(
        self,
        clear_first: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.clear_first = clear_first
        self.user_id = None

    def run(self) -> None:
        try:
            if self.clear_first:
                with perf_monitor.timer("history_clear"):
                    clear_history(
                        self.user_id
                    )

            with perf_monitor.timer("history_refresh_get_history"):
                rows = get_history(
                    user_id=self.user_id,
                    limit=200
                )

            self.loaded.emit(rows)

        except Exception as error:
            self.failed.emit(
                str(error)
            )


class HistoryController(QObject):
    loadingChanged = Signal(bool)
    statusChanged = Signal(str)

    def __init__(
        self,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._model = HistoryModel()
        self._worker = None
        self._loading = False
        self._user_id = None

    def set_user_id(
        self,
        user_id: int | None,
    ) -> None:
        self._user_id = user_id
        self._model.set_rows([])

    @Property(QObject, constant=True)
    def model(self):
        return self._model

    @Property(
        bool,
        notify=loadingChanged,
    )
    def loading(self) -> bool:
        return self._loading

    def _set_loading(
        self,
        value: bool,
    ) -> None:
        if self._loading == value:
            return

        self._loading = value
        self.loadingChanged.emit(value)

    def _start_worker(
        self,
        clear_first: bool,
    ) -> None:
        if self._worker is not None:
            return

        self._set_loading(True)

        self._worker = HistoryWorker(
            clear_first=clear_first
        )
        self._worker.user_id = self._user_id

        self._worker.loaded.connect(
            self._on_loaded
        )

        self._worker.failed.connect(
            self.statusChanged
        )

        self._worker.finished.connect(
            self._on_finished
        )

        self._worker.start()

    @Slot()
    def refresh(self) -> None:
        perf_monitor.increment("history_refresh_called")
        if self._user_id is None:
            self._model.set_rows([])
            self.statusChanged.emit(
                "Vui lòng đăng nhập để xem lịch sử."
            )
            return

        self._start_worker(
            clear_first=False
        )

    @Slot()
    def clearHistory(self) -> None:
        if self._user_id is None:
            self.statusChanged.emit(
                "Vui lòng đăng nhập để xóa lịch sử."
            )
            return

        self._start_worker(
            clear_first=True
        )

    def _on_loaded(
        self,
        rows: list[dict],
    ) -> None:
        formatted_rows = []

        for row in rows:
            detected_time = row.get(
                "detected_time"
            )

            formatted_rows.append(
                {
                    "english": row.get(
                        "english_word",
                        "",
                    ),
                    "vietnamese": (
                        row.get(
                            "vietnamese_meaning"
                        )
                        or row.get(
                            "english_word",
                            "",
                        )
                    ),
                    "category": (
                        row.get("category")
                        or "Unknown"
                    ),
                    "confidence": float(
                        row.get(
                            "confidence",
                            0.0,
                        )
                    ),
                    "detected_time": (
                        detected_time.strftime(
                            "%d/%m/%Y %H:%M"
                        )
                        if detected_time
                        else ""
                    ),
                }
            )

        self._model.set_rows(
            formatted_rows
        )

        self.statusChanged.emit(
            f"Đã tải {len(formatted_rows)} bản ghi."
        )

    def _on_finished(self) -> None:
        self._worker = None
        self._set_loading(False)
