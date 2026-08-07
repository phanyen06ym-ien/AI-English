"""Thin Controller cho man hinh thong ke.

Cong thuc thong ke da chuyen sang `ui.services.stats_service`; `EMPTY_STATS` va
`StatsWorker` duoc re-export de import cu khong bi vo.
"""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QObject,
    Signal,
    Slot,
)

from ui.services.stats_service import EMPTY_STATS
from ui.ui_logger import get_ui_logger, log_ui_event
from ui.viewmodels.statistics_viewmodel import StatisticsViewModel
from ui.workers.stats_worker import StatsWorker


logger = get_ui_logger("stats_controller")


class StatsController(QObject):
    """Adapter giua QML va `StatisticsViewModel`."""

    statsChanged = Signal(dict)

    def __init__(
        self,
        view_model: StatisticsViewModel,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._view_model = view_model

        self._view_model.StatisticsUpdated.connect(
            self.statsChanged
        )

    @property
    def view_model(self) -> StatisticsViewModel:
        return self._view_model

    @Property("QVariantMap", notify=statsChanged)
    def statistics(self) -> dict:
        return self._view_model.statistics

    def set_user_id(
        self,
        user_id: int | None,
    ) -> None:
        self._view_model.set_user_id(user_id)

    @Slot()
    def clear(self) -> None:
        self._view_model.clear()

    @Slot()
    def refresh(self) -> None:
        log_ui_event(logger, "stats_refresh_requested")

        self._view_model.refresh()


__all__ = [
    "StatsController",
    "StatsWorker",
    "EMPTY_STATS",
]
