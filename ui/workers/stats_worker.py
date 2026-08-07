"""Worker tinh thong ke.

Sprint 3: cong thuc chuyen sang `StatsService`.
Sprint 5: chuyen sang `ManagedWorker`.
"""

from __future__ import annotations

from PySide6.QtCore import Signal

from ui.services.stats_service import (
    STATS_HISTORY_LIMIT,
    StatsService,
)
from ui.workers.cancellation import CancellationToken
from ui.workers.lifecycle import ManagedWorker


class StatsWorker(ManagedWorker):
    """Tinh thong ke cua mot nguoi dung tren thread nen."""

    loaded = Signal(dict)

    def __init__(
        self,
        stats_service: StatsService,
        user_id: int | None,
        limit: int = STATS_HISTORY_LIMIT,
        token: CancellationToken | None = None,
        parent=None,
    ) -> None:
        super().__init__(
            "stats_worker",
            token=token,
            parent=parent,
        )

        self._stats_service = stats_service
        self.user_id = user_id
        self.limit = limit

    def execute(self) -> None:
        self.token.raise_if_cancelled()

        stats = self._stats_service.compute_for_user(
            self.user_id,
            limit=self.limit,
        )

        self.token.raise_if_cancelled()

        self.loaded.emit(stats)
