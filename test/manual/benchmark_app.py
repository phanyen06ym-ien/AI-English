"""Sprint 8 - Do hieu nang end-to-end cua ung dung.

Do nhung con so nguoi dung THAT SU cam nhan duoc:

1. Thoi gian tu luc bam chay den luc cua so hien ra.
2. Thoi gian nap YOLO va cac model .pkl.
3. Thoi gian mot lan nhan dien anh.
4. FPS cua luong webcam (dung camera gia de do on dinh).
5. Muc dung RAM.

Cach chay:

    python test/benchmark_app.py                # do day du
    python test/benchmark_app.py --skip-yolo    # bo qua phan nang
    python test/benchmark_app.py --rounds 5

Script nay CHI doc. Khong ghi database, khong sinh lai model, khong doi anh.
"""

from __future__ import annotations

import argparse
import gc
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent.parent),
)

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None


def _ms(seconds: float) -> float:
    return seconds * 1000.0


def rss_mb() -> float:
    """RAM dang dung (MB). 0 neu khong co psutil."""
    if psutil is None:
        return 0.0

    import os

    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)


class Timer:
    """Do mot buoc va ghi lai."""

    def __init__(self) -> None:
        self.steps: list[tuple[str, float, float]] = []

    def measure(
        self,
        label: str,
        action,
    ):
        gc.collect()
        before = rss_mb()
        started_at = time.perf_counter()

        result = action()

        elapsed = _ms(time.perf_counter() - started_at)
        after = rss_mb()

        self.steps.append((label, elapsed, after - before))

        return result

    def report(
        self,
        title: str,
    ) -> None:
        print(f"\n{title}")
        header = (
            f"{'Buoc':<42}{'Thoi gian (ms)':>16}{'RAM tang (MB)':>16}"
        )
        print(header)
        print("-" * len(header))

        for label, elapsed, memory in self.steps:
            print(f"{label:<42}{elapsed:>16.0f}{memory:>16.1f}")

        total = sum(step[1] for step in self.steps)
        print("-" * len(header))
        print(f"{'TONG':<42}{total:>16.0f}{rss_mb():>15.1f}*")
        print("* cot cuoi cung o dong TONG la RAM tuyet doi, khong phai muc tang")


# ----------------------------------------------------------------------
# 1. Khoi dong
# ----------------------------------------------------------------------


def benchmark_startup(
    skip_yolo: bool = False,
) -> None:
    """Do tung buoc tu luc chay den luc san sang nhan dien."""
    timer = Timer()

    timer.measure(
        "import torch",
        lambda: __import__("torch"),
    )
    timer.measure(
        "import ultralytics",
        lambda: __import__("ultralytics"),
    )
    timer.measure(
        "import cv2",
        lambda: __import__("cv2"),
    )
    timer.measure(
        "import PySide6.QtQuick",
        lambda: __import__("PySide6.QtQuick"),
    )
    timer.measure(
        "nap cau hinh (load_config)",
        _load_config,
    )
    timer.measure(
        "nap tu vung (vocabulary)",
        _load_vocabulary,
    )
    timer.measure(
        "nap model k-NN (.pkl)",
        _load_knn,
    )
    timer.measure(
        "nap model K-Means (.pkl)",
        _load_kmeans,
    )

    if not skip_yolo:
        timer.measure(
            "nap YOLO (ObjectDetector)",
            _load_yolo,
        )

    timer.report("1. KHOI DONG")


def _load_config():
    from config import load_config

    return load_config()


def _load_vocabulary():
    from ai.vocabulary import all_words

    return all_words()


def _load_knn():
    from ai.knn import get_related_words

    return get_related_words("laptop", 3)


def _load_kmeans():
    from ai.kmeans import get_words_in_same_cluster

    return get_words_in_same_cluster("laptop")


def _load_yolo():
    from ai.detector import ObjectDetector

    return ObjectDetector()


# ----------------------------------------------------------------------
# 2. Nhan dien anh
# ----------------------------------------------------------------------


def find_test_image() -> Path | None:
    """Tim mot anh bat ky trong dataset de do."""
    root = Path(__file__).resolve().parent.parent.parent

    for candidate in (
        root / "dataset" / "test_images",
        root / "dataset" / "images",
        root / "assets",
    ):
        if not candidate.exists():
            continue

        for pattern in ("*.jpg", "*.jpeg", "*.png"):
            found = sorted(candidate.rglob(pattern))
            if found:
                return found[0]

    return None


def benchmark_image_detection(
    rounds: int,
) -> None:
    """Do mot lan nhan dien anh that qua AIEngine."""
    image_path = find_test_image()

    print("\n2. NHAN DIEN ANH")

    if image_path is None:
        print("  Bo qua: khong tim thay anh mau trong dataset/")
        return

    import cv2

    from ai.pipeline import AIEngine

    frame = cv2.imread(str(image_path))

    if frame is None:
        print(f"  Bo qua: khong doc duoc {image_path.name}")
        return

    engine = AIEngine.create_default()

    # Lan dau gom ca chi phi khoi dong -> do rieng.
    started_at = time.perf_counter()
    first = engine.analyze_frame(frame)
    first_ms = _ms(time.perf_counter() - started_at)

    durations = []
    timings = []

    for _ in range(rounds):
        started_at = time.perf_counter()
        result = engine.analyze_frame(frame)
        durations.append(_ms(time.perf_counter() - started_at))
        timings.append(result.timing)

    print(f"  Anh          : {image_path.name} {frame.shape[1]}x{frame.shape[0]}")
    print(f"  Vat the      : {len(first.detections)}")
    print(f"  Lan dau      : {first_ms:.0f} ms (gom khoi dong)")
    print(f"  Trung vi     : {statistics.median(durations):.0f} ms")
    print(f"  Min / Max    : {min(durations):.0f} / {max(durations):.0f} ms")

    if timings:
        print("  Chi tiet (trung vi):")
        for field in (
            "yolo_ms",
            "vocabulary_ms",
            "knn_ms",
            "kmeans_ms",
        ):
            values = [
                getattr(timing, field)
                for timing in timings
            ]
            print(
                f"    {field:<16}{statistics.median(values):>8.1f} ms"
            )


# ----------------------------------------------------------------------
# 3. Webcam FPS
# ----------------------------------------------------------------------


def benchmark_webcam_fps(
    duration_seconds: float = 3.0,
) -> None:
    """Do FPS luong webcam bang camera gia (loai bo bien dong phan cung)."""
    print("\n3. FPS WEBCAM (camera gia)")

    from PySide6.QtCore import QCoreApplication

    from test.ui_fakes import (
        FakeAIEngine,
        FakeCamera,
        FakeHistoryService,
    )
    from ui.services.detection_service import DetectionService
    from ui.workers.webcam_worker import WebcamWorker

    app = QCoreApplication.instance() or QCoreApplication(sys.argv[:1])

    worker = WebcamWorker(
        DetectionService(
            FakeAIEngine(),
            history_service=FakeHistoryService(),
        ),
        camera_id=0,
        capture_factory=lambda camera_id: FakeCamera(frames=10**9),
    )

    received = {"count": 0}

    def on_frame(image):
        received["count"] += 1
        worker.release_frame()

    worker.frameReady.connect(on_frame)

    memory_before = rss_mb()
    worker.start()

    deadline = time.monotonic() + duration_seconds

    while time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.001)

    worker.dispose(3000)

    for _ in range(20):
        app.processEvents()

    stats = worker.frame_gate.stats()
    fps = received["count"] / duration_seconds

    print(f"  Frame giao dien ve xong : {received['count']}")
    print(f"  FPS                     : {fps:.1f}")
    print(f"  Frame bi bo (backpressure): {stats['dropped']}")
    print(f"  RAM tang                : {rss_mb() - memory_before:.1f} MB")


# ----------------------------------------------------------------------
# 4. Bo test tu dong
# ----------------------------------------------------------------------


def benchmark_test_suite() -> None:
    """Do thoi gian chay toan bo bo test tu dong."""
    import subprocess

    print("\n4. BO TEST TU DONG")

    root = Path(__file__).resolve().parent.parent.parent
    started_at = time.perf_counter()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "test",
            "-t",
            ".",
            "-p",
            "test_*.py",
        ],
        cwd=str(root),
        capture_output=True,
        text=True,
    )

    elapsed = time.perf_counter() - started_at
    tail = result.stderr.strip().splitlines()[-3:]

    print(f"  Thoi gian : {elapsed:.2f} s")

    for line in tail:
        print(f"  {line}")


# ----------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--skip-yolo", action="store_true")
    parser.add_argument("--skip-suite", action="store_true")
    arguments = parser.parse_args()

    print("=" * 74)
    print("AI-ENGLISH - BENCHMARK HIEU NANG (Sprint 8)")
    print("=" * 74)
    print(f"RAM ban dau: {rss_mb():.1f} MB")

    benchmark_startup(skip_yolo=arguments.skip_yolo)

    if not arguments.skip_yolo:
        benchmark_image_detection(max(1, arguments.rounds))

    benchmark_webcam_fps()

    if not arguments.skip_suite:
        benchmark_test_suite()

    print(f"\nRAM cuoi cung: {rss_mb():.1f} MB")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
