"""Vong doi chuan cho moi worker.

    Created ──start()──> Running ──┬──> Finished ──dispose()──> Disposed
                                   ├──> Cancelled ─────────────> Disposed
                                   └──> Failed ────────────────> Disposed

Van de truoc Sprint 5
---------------------

Moi worker tu quan ly vong doi theo cach rieng. Khong ai biet mot worker dang o
trang thai nao, khong co timeout thong nhat, va viec "dispose" chi la gan
`self._worker = None` roi hy vong Python thu don dung luc.

Giai phap
---------

`ManagedWorker` la lop nen duy nhat cho moi QThread trong du an:

- Trang thai co khoa, doc duoc tu GUI thread.
- Mot `CancellationToken` cho moi worker.
- `run()` la ban cuoi: bat `OperationCancelledError` va `Exception` mot cach
  thong nhat, luon phat dung signal.
- `dispose()` bat buoc cancel + wait, khong bao gio de QThread bi huy khi dang
  chay (loi da gap o Sprint 3).

Lop con chi can viet `execute()`.
"""

from __future__ import annotations

import threading
from enum import Enum

from PySide6.QtCore import QThread, Signal

from config.schema import ThreadConfig
from ui.ui_logger import get_ui_logger
from ui.workers.cancellation import (
    CancellationToken,
    OperationCancelledError,
)


#: Thoi gian cho mac dinh khi dung mot worker (ms) - lay tu `ThreadConfig`.
DEFAULT_DISPOSE_TIMEOUT_MS = ThreadConfig.dispose_timeout_ms


class WorkerState(str, Enum):
    """Trang thai vong doi cua mot worker."""

    CREATED = "created"
    RUNNING = "running"
    FINISHED = "finished"
    CANCELLED = "cancelled"
    FAILED = "failed"
    DISPOSED = "disposed"

    def is_active(self) -> bool:
        """True neu worker dang chay."""
        return self is WorkerState.RUNNING

    def is_terminal(self) -> bool:
        """True neu worker da ket thuc mot lan chay."""
        return self in _TERMINAL_STATES


_TERMINAL_STATES = frozenset(
    {
        WorkerState.FINISHED,
        WorkerState.CANCELLED,
        WorkerState.FAILED,
        WorkerState.DISPOSED,
    }
)


class ManagedWorker(QThread):
    """QThread co vong doi va co che huy thong nhat.

    Lop con override `execute()`. KHONG override `run()`.
    """

    #: Trang thai vong doi doi (gia tri cua `WorkerState`).
    stateChanged = Signal(str)

    #: Tac vu that bai vi loi khong luong truoc.
    failed = Signal(str)

    #: Tac vu bi huy theo yeu cau.
    cancelled = Signal()

    #: True neu `execute()` VAN phai chay du worker da bi huy truoc khi start().
    #: Dung cho worker giu hang doi: huy khong duoc lam mat du lieu da xep hang.
    ALWAYS_EXECUTE: bool = False

    def __init__(
        self,
        name: str,
        token: CancellationToken | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._name = name
        self._logger = get_ui_logger(name)
        self._token = (
            token
            if token is not None
            else CancellationToken()
        )
        self._state = WorkerState.CREATED
        self._state_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Trang thai
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return self._name

    @property
    def logger(self):
        return self._logger

    @property
    def token(self) -> CancellationToken:
        return self._token

    @property
    def state(self) -> WorkerState:
        """Doc trang thai. An toan goi tu GUI thread."""
        with self._state_lock:
            return self._state

    @property
    def is_cancelled(self) -> bool:
        return self._token.is_cancelled

    def _set_state(
        self,
        state: WorkerState,
    ) -> None:
        with self._state_lock:
            if self._state is state:
                return
            self._state = state

        self._logger.info(
            "worker_state=%s name=%s",
            state.value,
            self._name,
        )
        self.stateChanged.emit(state.value)

    # ------------------------------------------------------------------
    # Vong chay
    # ------------------------------------------------------------------

    def execute(self) -> None:
        """Cong viec that su cua worker. Lop con phai override."""
        raise NotImplementedError

    def run(self) -> None:
        """Ban cuoi - lop con KHONG duoc override.

        Bao dam moi worker deu ket thuc o dung mot trong ba trang thai:
        finished / cancelled / failed.
        """
        if self._token.is_cancelled and not self.ALWAYS_EXECUTE:
            # Da bi huy truoc khi kip chay - khong duoc bat dau.
            self._set_state(WorkerState.CANCELLED)
            self.cancelled.emit()
            return

        self._set_state(WorkerState.RUNNING)

        try:
            self.execute()

        except OperationCancelledError:
            self._set_state(WorkerState.CANCELLED)
            self.cancelled.emit()
            return

        except Exception as error:
            self._logger.exception(
                "worker_failed name=%s",
                self._name,
            )
            self._set_state(WorkerState.FAILED)
            self.failed.emit(str(error))
            return

        if self._token.is_cancelled:
            self._set_state(WorkerState.CANCELLED)
            self.cancelled.emit()
            return

        self._set_state(WorkerState.FINISHED)

    # ------------------------------------------------------------------
    # Dieu khien
    # ------------------------------------------------------------------

    def cancel(self) -> None:
        """Yeu cau huy. KHONG chan luong goi (thuong la GUI thread)."""
        self._token.cancel()

    def dispose(
        self,
        timeout_ms: int = DEFAULT_DISPOSE_TIMEOUT_MS,
    ) -> bool:
        """Huy va cho worker ket thuc han.

        Bat buoc goi truoc khi bo tham chieu toi worker, neu khong Qt se abort
        voi "QThread: Destroyed while thread is still running".

        Tra ve False neu het thoi gian cho ma worker chua dung.
        """
        self._token.cancel()

        stopped = True

        try:
            if self.isRunning():
                stopped = bool(self.wait(timeout_ms))
        except RuntimeError:
            # Doi tuong Qt da bi huy truoc do.
            return True

        if not stopped:
            self._logger.error(
                "worker_dispose_timeout name=%s timeout_ms=%s",
                self._name,
                timeout_ms,
            )
            return False

        self._set_state(WorkerState.DISPOSED)
        return True


__all__ = [
    "DEFAULT_DISPOSE_TIMEOUT_MS",
    "ManagedWorker",
    "WorkerState",
]
