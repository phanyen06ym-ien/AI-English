"""Co che huy tac vu dung chung cho moi worker.

Van de truoc Sprint 5
---------------------

Moi worker tu nghi ra cach dung cua rieng minh:

- `WebcamWorker` co co `_stop_requested`.
- `HistoryWriterWorker` day mot "stop token" vao hang doi.
- `ImageWorker`, `HistoryWorker`, `StatsWorker`, `PreviewLoadWorker`
  **khong huy duoc**: da bat dau la phai chay het.

Giai phap
---------

Mot `CancellationToken` duy nhat, an toan da luong:

    token = CancellationToken()

    # GUI thread
    token.cancel()

    # Worker thread
    token.raise_if_cancelled()      # nem OperationCancelledError
    if token.is_cancelled: ...      # hoac kiem tra thu cong
    token.wait(0.25)                # ngu, tinh day ngay khi bi huy

`token.wait()` thay cho `time.sleep()`: worker dang ngu van phan hoi lenh huy
ngay lap tuc thay vi phai cho het gio.
"""

from __future__ import annotations

import threading


class OperationCancelledError(Exception):
    """Nem ra khi mot tac vu bi huy giua chung.

    Day KHONG phai loi. `ManagedWorker` bat rieng va chuyen worker sang trang
    thai `cancelled`, khong emit signal `failed`.
    """

    def __init__(
        self,
        message: str = "Tác vụ đã bị hủy.",
    ) -> None:
        super().__init__(message)


class CancellationToken:
    """Co huy mot chieu, an toan da luong.

    Da huy thi khong quay lai duoc (tru khi goi `reset()` truoc lan chay moi).
    Dung `threading.Event` de thread dang ngu bi danh thuc ngay khi huy.
    """

    def __init__(self) -> None:
        self._event = threading.Event()

    @property
    def is_cancelled(self) -> bool:
        """True neu da co yeu cau huy."""
        return self._event.is_set()

    def cancel(self) -> None:
        """Yeu cau huy. KHONG chan luong goi."""
        self._event.set()

    def reset(self) -> None:
        """Xoa co huy. Chi goi truoc khi bat dau mot lan chay moi."""
        self._event.clear()

    def raise_if_cancelled(self) -> None:
        """Nem `OperationCancelledError` neu da bi huy."""
        if self._event.is_set():
            raise OperationCancelledError()

    def wait(
        self,
        timeout_seconds: float,
    ) -> bool:
        """Ngu toi da `timeout_seconds`, tinh day ngay khi bi huy.

        Tra ve True neu bi huy trong luc cho.
        """
        return self._event.wait(timeout_seconds)


#: Token khong bao gio bi huy - dung lam gia tri mac dinh.
class _NeverCancelledToken(CancellationToken):
    def cancel(self) -> None:  # pragma: no cover - co y khong lam gi
        return None


NEVER_CANCELLED = _NeverCancelledToken()


__all__ = [
    "CancellationToken",
    "OperationCancelledError",
    "NEVER_CANCELLED",
]
