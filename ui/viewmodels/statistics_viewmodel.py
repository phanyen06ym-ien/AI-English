"""ViewModel cho man hinh thong ke."""

from __future__ import annotations

from PySide6.QtCore import Property, Signal, Slot

from ui.services.stats_service import (
    StatsService,
    empty_stats,
)
from ui.state import UiState
from ui.ui_logger import log_ui_event
from ui.viewmodels.base_viewmodel import BaseViewModel
from ui.workers.stats_worker import StatsWorker
from utils import perf_monitor


class StatisticsViewModel(BaseViewModel):
    """Dieu phoi tinh thong ke va giu ket qua cho View."""

    StatisticsUpdated = Signal(dict)
    StatisticsFailed = Signal(str)

    def __init__(
        self,
        stats_service: StatsService,
        parent=None,
    ) -> None:
        super().__init__("statistics_viewmodel", parent)

        self._stats_service = stats_service
        self._worker: StatsWorker | None = None
        self._statistics = empty_stats()

    @Property("QVariantMap", notify=StatisticsUpdated)
    def statistics(self) -> dict:
        return self._statistics

    def set_user_id(
        self,
        user_id: int | None,
    ) -> None:
        super().set_user_id(user_id)

        if user_id is None:
            self.clear()

    @Slot()
    def clear(self) -> None:
        """Dat thong ke ve rong."""
        self._statistics = empty_stats()
        self.StatisticsUpdated.emit(
            dict(self._statistics)
        )

    @Slot()
    def refresh(self) -> None:
        """Tinh lai thong ke cho nguoi dung hien tai."""
        perf_monitor.increment("stats_refresh_called")
        log_ui_event(self.logger, "stats_refresh")

        if self.user_id is None:
            self.clear()
            return

        if self._worker is not None:
            perf_monitor.increment("stats_refresh_skipped_busy")
            return

        self.set_state(UiState.LOADING)

        self._worker = StatsWorker(
            self._stats_service,
            int(self.user_id),
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

    def _on_loaded(
        self,
        statistics: dict,
    ) -> None:
        self._statistics = statistics
        self.set_state(UiState.COMPLETED)
        self.StatisticsUpdated.emit(statistics)

    def _on_failed(
        self,
        message: str,
    ) -> None:
        self.logger.warning(
            "stats_failed error=%s",
            message,
        )
        self.StatisticsFailed.emit(message)
        self.set_state(UiState.ERROR)
        self.clear()

    def _on_finished(self) -> None:
        self._worker = None
        self.set_state(UiState.IDLE)

    def shutdown(
        self,
        timeout_ms: int = 3000,
    ) -> None:
        self._await_workers(
            (self._worker,),
            timeout_ms,
        )
