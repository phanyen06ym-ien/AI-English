"""Worker doc / xoa lich su nhan dien.

Sprint 4: goi `HistoryService` (tren Repository), nhan `RepositoryError` co nghia.
Sprint 5: chuyen sang `ManagedWorker`; loi va huy do lop nen xu ly thong nhat.
"""

from __future__ import annotations

from PySide6.QtCore import Signal

from ui.services.history_service import (
    HISTORY_PAGE_LIMIT,
    HistoryService,
)
from ui.workers.cancellation import CancellationToken
from ui.workers.lifecycle import ManagedWorker


class HistoryWorker(ManagedWorker):
    """Tai lich su (co the xoa truoc) tren thread nen."""

    loaded = Signal(list)

    def __init__(
        self,
        history_service: HistoryService,
        user_id: int | None = None,
        clear_first: bool = False,
        limit: int = HISTORY_PAGE_LIMIT,
        token: CancellationToken | None = None,
        parent=None,
    ) -> None:
        super().__init__(
            "history_worker",
            token=token,
            parent=parent,
        )

        self._history_service = history_service
        self.user_id = user_id
        self.clear_first = clear_first
        self.limit = limit

    def execute(self) -> None:
        self.token.raise_if_cancelled()

        if self.clear_first:
            self._history_service.clear(self.user_id)

        self.token.raise_if_cancelled()

        rows = self._history_service.load_formatted_rows(
            self.user_id,
            limit=self.limit,
        )

        self.token.raise_if_cancelled()

        self.loaded.emit(rows)
