"""ViewModel cho man hinh lich su nhan dien."""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QModelIndex,
    QObject,
    Qt,
    Signal,
    Slot,
)

from ui.services.history_service import HistoryService
from ui.state import UiState
from ui.ui_logger import log_ui_event
from ui.viewmodels.base_viewmodel import BaseViewModel
from ui.workers.history_worker import HistoryWorker
from utils import perf_monitor


STATUS_LOGIN_TO_VIEW = "Vui lòng đăng nhập để xem lịch sử."
STATUS_LOGIN_TO_CLEAR = "Vui lòng đăng nhập để xóa lịch sử."


class HistoryModel(QAbstractListModel):
    """List model cho ListView lich su. Chi trinh bay, khong co business logic."""

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

        self._rows: list[dict] = []

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


class HistoryViewModel(BaseViewModel):
    """Dieu phoi tai / xoa lich su va cap nhat HistoryModel."""

    HistoryUpdated = Signal(list)
    HistoryFailed = Signal(str)
    LoadingChanged = Signal(bool)

    def __init__(
        self,
        history_service: HistoryService,
        parent=None,
    ) -> None:
        super().__init__("history_viewmodel", parent)

        self._history_service = history_service
        self._model = HistoryModel()
        self._worker: HistoryWorker | None = None

    @Property(QObject, constant=True)
    def model(self):
        return self._model

    @Property(bool, notify=LoadingChanged)
    def loading(self) -> bool:
        return self.ui_state is UiState.LOADING

    def set_user_id(
        self,
        user_id: int | None,
    ) -> None:
        super().set_user_id(user_id)
        self._model.set_rows([])

    def _set_loading(
        self,
        value: bool,
    ) -> None:
        was_loading = self.ui_state is UiState.LOADING

        self.set_state(
            UiState.LOADING
            if value
            else UiState.IDLE
        )

        if was_loading != value:
            self.LoadingChanged.emit(value)

    def _start_worker(
        self,
        clear_first: bool,
    ) -> None:
        if self._worker is not None:
            return

        self._set_loading(True)

        self._worker = HistoryWorker(
            self._history_service,
            user_id=self.user_id,
            clear_first=clear_first,
        )
        self._worker.loaded.connect(
            self._on_loaded
        )
        self._worker.failed.connect(
            self._on_failed
        )
        self._worker.finished.connect(
            self._on_finished
        )
        self._worker.start()

    @Slot()
    def refresh(self) -> None:
        """Tai lai lich su."""
        perf_monitor.increment("history_refresh_called")
        log_ui_event(self.logger, "history_refresh")

        if self.user_id is None:
            self._model.set_rows([])
            self.set_status(STATUS_LOGIN_TO_VIEW)
            return

        self._start_worker(clear_first=False)

    @Slot()
    def clearHistory(self) -> None:
        """Xoa lich su roi tai lai."""
        log_ui_event(self.logger, "history_clear")

        if self.user_id is None:
            self.set_status(STATUS_LOGIN_TO_CLEAR)
            return

        self._start_worker(clear_first=True)

    def _on_loaded(
        self,
        rows: list,
    ) -> None:
        self._model.set_rows(rows)
        self.HistoryUpdated.emit(rows)
        self.set_status(
            f"Đã tải {len(rows)} bản ghi."
        )

    def _on_failed(
        self,
        message: str,
    ) -> None:
        self.HistoryFailed.emit(message)
        self.set_status(message)

    def _on_finished(self) -> None:
        self._worker = None
        self._set_loading(False)

    def shutdown(
        self,
        timeout_ms: int = 3000,
    ) -> None:
        self._await_workers(
            (self._worker,),
            timeout_ms,
        )
