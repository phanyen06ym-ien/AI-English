"""Chong tran hang doi giua Worker Thread va GUI Thread.

Van de truoc Sprint 5
---------------------

`WebcamWorker` doc frame va emit `frameReady` khong gioi han. Signal di qua
`QueuedConnection` nen moi lan emit la mot su kien duoc xep vao hang doi cua GUI
thread. Neu GUI ve cham hon toc do doc frame:

- Hang doi phinh khong gioi han -> ton RAM.
- GUI hien frame **cu**, do tre tang dan (nguoi dung thay hinh "tre" so voi thuc te).
- Truong hop xau: GUI khong bao gio duoi kip, do tre tang mai.

Giai phap
---------

`FrameGate` gioi han so frame **dang bay** (da emit nhung GUI chua xu ly xong).
Vuot han muc thi **bo frame moi nhat** thay vi xep them vao hang doi.

    Worker Thread                      GUI Thread
    -------------                      ----------
    if gate.try_acquire():
        emit frameReady(image) ──────> slot nhan frame
                                         gate.release()
    else:
        gate dem "dropped"

Bo frame la dung trong video truc tiep: nguoi dung can hinh **moi nhat**, khong
can xem lai hinh cu. Ket qua nhan dien KHONG bi anh huong vi AI chay theo nhip
rieng (`INFERENCE_INTERVAL_SECONDS`), khong chay tren tung frame.
"""

from __future__ import annotations

import threading

from config.schema import CameraConfig


#: So frame toi da duoc phep "dang bay" giua worker va GUI.
DEFAULT_MAX_IN_FLIGHT = CameraConfig.max_frames_in_flight


class FrameGate:
    """Dem so frame dang bay va quyet dinh co emit tiep hay khong."""

    def __init__(
        self,
        max_in_flight: int = DEFAULT_MAX_IN_FLIGHT,
    ) -> None:
        self._max_in_flight = max(1, int(max_in_flight))
        self._lock = threading.Lock()
        self._in_flight = 0
        self._emitted = 0
        self._dropped = 0

    @property
    def max_in_flight(self) -> int:
        return self._max_in_flight

    @property
    def in_flight(self) -> int:
        with self._lock:
            return self._in_flight

    @property
    def emitted(self) -> int:
        with self._lock:
            return self._emitted

    @property
    def dropped(self) -> int:
        with self._lock:
            return self._dropped

    def try_acquire(self) -> bool:
        """Goi tu Worker Thread truoc khi emit frame.

        True  -> duoc phep emit.
        False -> GUI dang ban, bo frame nay.
        """
        with self._lock:
            if self._in_flight >= self._max_in_flight:
                self._dropped += 1
                return False

            self._in_flight += 1
            self._emitted += 1
            return True

    def release(self) -> None:
        """Goi tu GUI Thread sau khi xu ly xong mot frame."""
        with self._lock:
            if self._in_flight > 0:
                self._in_flight -= 1

    def reset(self) -> None:
        """Xoa bo dem. Goi khi bat dau mot phien webcam moi."""
        with self._lock:
            self._in_flight = 0
            self._emitted = 0
            self._dropped = 0

    def stats(self) -> dict[str, int]:
        """Thong ke de dua vao bao cao hieu nang."""
        with self._lock:
            total = self._emitted + self._dropped

            return {
                "emitted": self._emitted,
                "dropped": self._dropped,
                "in_flight": self._in_flight,
                "total": total,
                "drop_percent": (
                    int(round(self._dropped * 100 / total))
                    if total
                    else 0
                ),
            }


__all__ = [
    "DEFAULT_MAX_IN_FLIGHT",
    "FrameGate",
]
