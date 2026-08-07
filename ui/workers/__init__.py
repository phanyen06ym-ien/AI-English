"""Worker layer.

Quy tac Sprint 3 cho moi Worker trong package nay:

1. Worker KHONG import QML, KHONG import QtWidgets, KHONG cham vao View.
2. Worker chi giao tiep ra ngoai bang Signal.
3. Business logic nam trong `ui.services`, Worker chi dieu phoi thread.
4. Moi Signal deu duoc nhan o GUI thread qua Qt::AutoConnection (queued).

    Worker Thread -> Signal -> ViewModel (GUI Thread) -> Controller -> View

Bo sung Sprint 5:

5. Moi QThread ke thua `ManagedWorker`: vong doi + `CancellationToken` thong nhat.
6. Tac vu ngan dung `PooledTask` tren `QThreadPool`; tac vu dai dung `ManagedWorker`.
7. Luong du lieu nhanh (webcam) di qua `FrameGate` de khong lam tran hang doi GUI.
"""

from __future__ import annotations

from ui.workers.auth_worker import AuthOperation, AuthWorker
from ui.workers.backpressure import (
    DEFAULT_MAX_IN_FLIGHT,
    FrameGate,
)
from ui.workers.cancellation import (
    CancellationToken,
    OperationCancelledError,
)
from ui.workers.history_worker import HistoryWorker
from ui.workers.image_worker import (
    ImageWorker,
    PreviewLoadWorker,
)
from ui.workers.lifecycle import (
    DEFAULT_DISPOSE_TIMEOUT_MS,
    ManagedWorker,
    WorkerState,
)
from ui.workers.speech_worker import SpeakTask
from ui.workers.stats_worker import StatsWorker
from ui.workers.task_pool import (
    PooledTask,
    submit,
    wait_for_pool,
)
from ui.workers.webcam_worker import (
    HistoryWriterWorker,
    WebcamWorker,
)


__all__ = [
    "AuthOperation",
    "AuthWorker",
    "CancellationToken",
    "DEFAULT_DISPOSE_TIMEOUT_MS",
    "DEFAULT_MAX_IN_FLIGHT",
    "FrameGate",
    "HistoryWorker",
    "HistoryWriterWorker",
    "ImageWorker",
    "ManagedWorker",
    "OperationCancelledError",
    "PooledTask",
    "PreviewLoadWorker",
    "SpeakTask",
    "StatsWorker",
    "WebcamWorker",
    "WorkerState",
    "submit",
    "wait_for_pool",
]
