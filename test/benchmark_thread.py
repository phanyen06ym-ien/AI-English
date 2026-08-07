"""Sprint 5 - Do thoi gian GUI thread bi chan.

Do hai thu:

1. **Dang nhap**: thoi gian GUI thread bi chan khi bam "Đăng nhập",
   truoc Sprint 5 (dong bo) so voi sau Sprint 5 (qua `AuthWorker`).
2. **Webcam**: ty le frame bi bo khi GUI ve cham (`FrameGate`).

Phan dang nhap CHI chay cau lenh doc, va co tinh dung mot ten dang nhap khong
ton tai de khong dung toi tai khoan that.

Cach chay:

    python test/benchmark_thread.py
"""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent),
)

from PySide6.QtCore import QCoreApplication  # noqa: E402

from database.connection import close_pool  # noqa: E402
from ui.services.auth_service import AuthService  # noqa: E402
from ui.viewmodels.auth_viewmodel import AuthViewModel  # noqa: E402
from utils.password import hash_password, verify_password  # noqa: E402


#: Ten dang nhap chac chan khong ton tai.
PROBE_USERNAME = "__benchmark_probe_user__"
PROBE_PASSWORD = "khong-quan-trong"

ROUNDS = 5


def _ms(seconds: float) -> float:
    return seconds * 1000.0


def ensure_app() -> QCoreApplication:
    app = QCoreApplication.instance()

    if app is None:
        app = QCoreApplication(sys.argv[:1])

    return app


def process_until(
    predicate,
    timeout: float = 30.0,
) -> bool:
    app = ensure_app()
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        app.processEvents()

        if predicate():
            return True

        time.sleep(0.002)

    return predicate()


def measure_sync_login(
    service: AuthService,
    rounds: int,
) -> list[float]:
    """Cach cu: goi thang tren GUI thread -> GUI dung im ca khoang nay."""
    durations = []

    for _ in range(rounds):
        started_at = time.perf_counter()
        service.login(PROBE_USERNAME, PROBE_PASSWORD)
        durations.append(
            _ms(time.perf_counter() - started_at)
        )

    return durations


def measure_async_login_block(
    service: AuthService,
    rounds: int,
) -> tuple[list[float], list[float]]:
    """Cach moi: do rieng thoi gian GUI bi chan va tong thoi gian hoan tat."""
    ensure_app()

    blocked = []
    total = []

    for _ in range(rounds):
        view_model = AuthViewModel(service)

        started_at = time.perf_counter()
        view_model.login(PROBE_USERNAME, PROBE_PASSWORD)
        blocked.append(
            _ms(time.perf_counter() - started_at)
        )

        process_until(lambda: not view_model.loading)
        total.append(
            _ms(time.perf_counter() - started_at)
        )

        view_model.shutdown()

    return blocked, total


def measure_bcrypt(rounds: int) -> list[float]:
    """Chi phi bcrypt - phan nay co y thiet ke cham, khong toi uu duoc."""
    hashed = hash_password("matkhau123")
    durations = []

    for _ in range(rounds):
        started_at = time.perf_counter()
        verify_password("matkhau123", hashed)
        durations.append(
            _ms(time.perf_counter() - started_at)
        )

    return durations


def summarize(
    label: str,
    durations: list[float],
) -> dict:
    return {
        "label": label,
        "mean_ms": statistics.mean(durations),
        "median_ms": statistics.median(durations),
        "max_ms": max(durations),
    }


def print_row(summary: dict) -> None:
    print(
        f"{summary['label']:<42}"
        f"{summary['mean_ms']:>12.1f}"
        f"{summary['median_ms']:>12.1f}"
        f"{summary['max_ms']:>12.1f}"
    )


def benchmark_frame_gate(
    duration_seconds: float = 2.0,
    gui_draw_ms: float = 25.0,
) -> None:
    """Chay `WebcamWorker` that voi camera gia va mot GUI ve cham."""

    from test.ui_fakes import (
        FakeAIEngine,
        FakeCamera,
        FakeHistoryService,
    )
    from ui.services.detection_service import DetectionService
    from ui.workers.webcam_worker import WebcamWorker

    app = ensure_app()

    service = DetectionService(
        FakeAIEngine(),
        history_service=FakeHistoryService(),
    )

    camera = FakeCamera(frames=10**9)
    worker = WebcamWorker(
        service,
        camera_id=0,
        capture_factory=lambda camera_id: camera,
        max_frames_in_flight=2,
    )

    drawn = {"count": 0}

    def on_frame(image):
        # Gia lap GUI ve cham hon toc do doc frame.
        time.sleep(gui_draw_ms / 1000.0)
        drawn["count"] += 1
        worker.release_frame()

    worker.frameReady.connect(on_frame)
    worker.start()

    deadline = time.monotonic() + duration_seconds

    while time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.001)

    worker.dispose(3000)

    for _ in range(20):
        app.processEvents()

    stats = worker.frame_gate.stats()

    print(
        f"\nBackpressure - GUI ve {gui_draw_ms:.0f} ms/frame, "
        f"chay {duration_seconds:.0f} s"
    )
    print(f"  Frame worker doc duoc : {stats['total']}")
    print(f"  Frame gui toi GUI     : {stats['emitted']}")
    print(f"  Frame bi bo           : {stats['dropped']}")
    print(f"  Ty le bo              : {stats['drop_percent']}%")
    print(f"  Frame GUI ve xong     : {drawn['count']}")
    print(
        "  Khong co FrameGate, so frame bi bo se nam xep hang trong"
        " GUI va do tre tang dan theo thoi gian."
    )


def main() -> int:
    ensure_app()

    service = AuthService()

    print(f"Benchmark thread - {ROUNDS} vong\n")

    try:
        sync_durations = measure_sync_login(service, ROUNDS)
        blocked, total = measure_async_login_block(
            service,
            ROUNDS,
        )
        bcrypt_durations = measure_bcrypt(ROUNDS)

    except Exception as error:
        print(f"Khong ket noi duoc database: {error}")
        return 1

    finally:
        close_pool()

    header = (
        f"{'Phep do':<42}"
        f"{'TB (ms)':>12}"
        f"{'Trung vi':>12}"
        f"{'Max':>12}"
    )
    print(header)
    print("-" * len(header))

    print_row(
        summarize(
            "GUI bi chan - dong bo (truoc Sprint 5)",
            sync_durations,
        )
    )
    print_row(
        summarize(
            "GUI bi chan - qua Worker (sau Sprint 5)",
            blocked,
        )
    )
    print_row(
        summarize(
            "Tong thoi gian hoan tat (sau Sprint 5)",
            total,
        )
    )
    print_row(
        summarize(
            "Chi phi bcrypt.checkpw",
            bcrypt_durations,
        )
    )

    sync_median = statistics.median(sync_durations)
    blocked_median = statistics.median(blocked)

    print()

    if blocked_median > 0:
        print(
            f"GUI bi chan it hon {sync_median / blocked_median:.0f} lan "
            f"({sync_median:.0f} ms -> {blocked_median:.1f} ms)."
        )

    benchmark_frame_gate()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
