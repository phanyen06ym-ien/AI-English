"""Thin Controller cho man hinh lich su.

`HistoryModel` va `HistoryWorker` da chuyen sang ViewModel/Worker layer; import
cu van chay nho re-export o cuoi file.
"""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QObject,
    Signal,
    Slot,
)

from ui.services.dialog_service import DialogService
from ui.ui_logger import get_ui_logger, log_button_click
from ui.viewmodels.history_viewmodel import (
    HistoryModel,
    HistoryViewModel,
)
from ui.workers.history_worker import HistoryWorker


logger = get_ui_logger("history_controller")


class HistoryController(QObject):
    """Adapter giua QML va `HistoryViewModel`."""

    loadingChanged = Signal(bool)
    statusChanged = Signal(str)

    def __init__(
        self,
        view_model: HistoryViewModel,
        dialog_service: DialogService | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._view_model = view_model
        self._dialog_service = dialog_service

        self._view_model.LoadingChanged.connect(
            self.loadingChanged
        )
        self._view_model.StatusMessageChanged.connect(
            self._on_status_changed
        )

    def _on_status_changed(
        self,
        message: str,
    ) -> None:
        self.statusChanged.emit(message)

        if self._dialog_service is not None:
            self._dialog_service.publish(message)

    @property
    def view_model(self) -> HistoryViewModel:
        return self._view_model

    @Property(QObject, constant=True)
    def model(self):
        return self._view_model.model

    @Property(bool, notify=loadingChanged)
    def loading(self) -> bool:
        return self._view_model.loading

    def set_user_id(
        self,
        user_id: int | None,
    ) -> None:
        self._view_model.set_user_id(user_id)

    @Slot()
    def refresh(self) -> None:
        self._view_model.refresh()

    @Slot()
    def clearHistory(self) -> None:
        log_button_click(logger, "clear_history")

        self._view_model.clearHistory()


__all__ = [
    "HistoryController",
    "HistoryModel",
    "HistoryWorker",
]
