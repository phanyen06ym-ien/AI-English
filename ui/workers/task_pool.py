"""Chinh sach chon giua QThread va QThreadPool.

Van de truoc Sprint 5
---------------------

Du an dung lan lon hai co che ma khong co quy tac:

- `QThread`     : ImageWorker, WebcamWorker, HistoryWorker, StatsWorker, ...
- `QThreadPool` : SpeakTask, goi truc tiep `QThreadPool.globalInstance().start()`
                  tu **Controller** - tuc la Controller lai biet ve thread.

Quy tac Sprint 5
----------------

| Loai tac vu | Co che | Vi du |
|---|---|---|
| Co vong lap dai, can huy giua chung, can emit nhieu signal | `ManagedWorker` (QThread) | Webcam, nhan dien anh, doc lich su |
| Ngan, ban chay va quen, khong can bao cao tien do | `PooledTask` (QRunnable) | Phat am mot tu |

Ly do: mot `QThread` rieng cho moi lan bam nut phat am la lang phi, con dat mot
vong lap webcam vao thread pool se chiem cho cua moi tac vu ngan khac.

`submit()` la diem vao duy nhat cua thread pool, thay cho viec goi thang
`QThreadPool.globalInstance()` rai rac trong Controller.
"""

from __future__ import annotations

from PySide6.QtCore import QRunnable, QThreadPool

from ui.ui_logger import get_ui_logger
from ui.workers.cancellation import (
    CancellationToken,
    OperationCancelledError,
)


logger = get_ui_logger("task_pool")


class PooledTask(QRunnable):
    """Tac vu ngan chay tren `QThreadPool`, co the huy.

    Lop con override `execute()`.
    """

    def __init__(
        self,
        name: str,
        token: CancellationToken | None = None,
    ) -> None:
        super().__init__()

        self._name = name
        self._token = (
            token
            if token is not None
            else CancellationToken()
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def token(self) -> CancellationToken:
        return self._token

    def cancel(self) -> None:
        """Yeu cau huy. Neu tac vu chua bat dau thi no se khong chay."""
        self._token.cancel()

    def execute(self) -> None:
        """Cong viec that su. Lop con phai override."""
        raise NotImplementedError

    def run(self) -> None:
        """Ban cuoi - lop con KHONG duoc override."""
        if self._token.is_cancelled:
            return

        try:
            self.execute()

        except OperationCancelledError:
            return

        except Exception as error:
            logger.warning(
                "pooled_task_failed name=%s error=%s",
                self._name,
                error,
            )


def submit(
    task: QRunnable,
    pool: QThreadPool | None = None,
) -> None:
    """Gui mot tac vu ngan vao thread pool.

    Diem vao duy nhat - Controller khong con goi thang `QThreadPool`.
    """
    target_pool = (
        pool
        if pool is not None
        else QThreadPool.globalInstance()
    )

    target_pool.start(task)


def wait_for_pool(
    timeout_ms: int = 3000,
    pool: QThreadPool | None = None,
) -> bool:
    """Cho moi tac vu ngan ket thuc. Dung khi thoat ung dung."""
    target_pool = (
        pool
        if pool is not None
        else QThreadPool.globalInstance()
    )

    return bool(
        target_pool.waitForDone(timeout_ms)
    )


__all__ = [
    "PooledTask",
    "submit",
    "wait_for_pool",
]
