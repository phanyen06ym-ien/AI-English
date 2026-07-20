from __future__ import annotations

import os
import threading
import time
import tracemalloc
from collections import defaultdict
from contextlib import contextmanager


ENABLED = os.getenv("AI_ENGLISH_PERF", "").strip() == "1"


try:
    import psutil
except Exception:  # pragma: no cover - optional runtime dependency
    psutil = None


try:
    import torch
except Exception:  # pragma: no cover - optional runtime dependency
    torch = None


_lock = threading.Lock()
_counts = defaultdict(int)
_totals = defaultdict(float)
_last_report_at = time.perf_counter()
_started = False
_process = psutil.Process(os.getpid()) if psutil is not None else None


def start() -> None:
    global _started
    if not ENABLED or _started:
        return
    _started = True
    tracemalloc.start()
    if _process is not None:
        _process.cpu_percent(None)
    print("[PERF] instrumentation enabled")
    print(f"[PERF] torch_cuda_available={cuda_available()}")


def cuda_available() -> bool:
    return bool(
        torch is not None
        and getattr(torch, "cuda", None) is not None
        and torch.cuda.is_available()
    )


def cuda_synchronize() -> None:
    if cuda_available():
        torch.cuda.synchronize()


@contextmanager
def timer(name: str, synchronize_cuda: bool = False):
    if not ENABLED:
        yield
        return

    if synchronize_cuda:
        cuda_synchronize()
    started_at = time.perf_counter()
    try:
        yield
    finally:
        if synchronize_cuda:
            cuda_synchronize()
        add_time(name, time.perf_counter() - started_at)


def increment(name: str, amount: int = 1) -> None:
    if not ENABLED:
        return
    with _lock:
        _counts[name] += amount


def add_time(name: str, seconds: float) -> None:
    if not ENABLED:
        return
    with _lock:
        _counts[name] += 1
        _totals[name] += seconds


def maybe_report(interval_seconds: float = 5.0) -> None:
    global _last_report_at
    if not ENABLED:
        return

    now = time.perf_counter()
    if now - _last_report_at < interval_seconds:
        return

    with _lock:
        elapsed = now - _last_report_at
        _last_report_at = now
        counts = dict(_counts)
        totals = dict(_totals)
        _counts.clear()
        _totals.clear()

    current, peak = tracemalloc.get_traced_memory()
    rss_mb = None
    cpu_percent = None
    thread_count = None
    if _process is not None:
        rss_mb = _process.memory_info().rss / (1024 * 1024)
        cpu_percent = _process.cpu_percent(None)
        thread_count = _process.num_threads()

    print("[PERF] ---- 5s summary ----")
    print(
        "[PERF] process "
        f"rss_mb={rss_mb:.1f} "
        f"cpu_percent={cpu_percent:.1f} "
        f"threads={thread_count} "
        f"tracemalloc_current_mb={current / (1024 * 1024):.1f} "
        f"tracemalloc_peak_mb={peak / (1024 * 1024):.1f}"
    )

    for name in sorted(counts):
        count = counts[name]
        total = totals.get(name, 0.0)
        rate = count / elapsed
        if total:
            avg_ms = total / count * 1000.0
            print(
                f"[PERF] {name}: count={count} "
                f"rate={rate:.2f}/s avg_ms={avg_ms:.2f}"
            )
        else:
            print(f"[PERF] {name}: count={count} rate={rate:.2f}/s")
