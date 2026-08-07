"""Sprint 4 - Do hieu nang tang du lieu.

So sanh hai che do:

1. `direct`  - moi cau lenh mo mot ket noi moi (hanh vi TRUOC Sprint 4).
2. `pooled`  - dung `ThreadedConnectionPool` (hanh vi SAU Sprint 4).

Script nay CHI chay cau lenh doc (`SELECT`). Khong ghi, khong xoa, khong doi
schema.

Cach chay:

    python test/benchmark_database.py
    python test/benchmark_database.py --rounds 10
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent),
)

from database.connection import (  # noqa: E402
    close_pool,
    database_cursor,
    get_connection,
)
from database.repositories.history_repository import (  # noqa: E402
    HistoryRepository,
)


PROBE_QUERY = "SELECT 1;"


def _ms(seconds: float) -> float:
    return seconds * 1000.0


def measure_direct(rounds: int) -> list[float]:
    """Mo ket noi moi cho moi cau lenh - cach cu."""
    durations = []

    for _ in range(rounds):
        started_at = time.perf_counter()

        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(PROBE_QUERY)
            cursor.fetchone()
            cursor.close()
        finally:
            connection.close()

        durations.append(
            _ms(time.perf_counter() - started_at)
        )

    return durations


def measure_pooled(rounds: int) -> list[float]:
    """Dung ket noi tu pool - cach moi."""
    durations = []

    for _ in range(rounds):
        started_at = time.perf_counter()

        with database_cursor() as cursor:
            cursor.execute(PROBE_QUERY)
            cursor.fetchone()

        durations.append(
            _ms(time.perf_counter() - started_at)
        )

    return durations


def measure_repository_read(
    rounds: int,
    limit: int = 200,
) -> list[float]:
    """Do mot lan doc lich su that qua Repository."""
    repository = HistoryRepository()
    durations = []

    for _ in range(rounds):
        started_at = time.perf_counter()
        repository.list_by_user(user_id=None, limit=limit)
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
        "rounds": len(durations),
        "first_ms": durations[0] if durations else 0.0,
        "mean_ms": statistics.mean(durations) if durations else 0.0,
        "median_ms": statistics.median(durations) if durations else 0.0,
        "min_ms": min(durations) if durations else 0.0,
        "max_ms": max(durations) if durations else 0.0,
        "total_ms": sum(durations),
    }


def print_row(summary: dict) -> None:
    print(
        f"{summary['label']:<28}"
        f"{summary['first_ms']:>10.1f}"
        f"{summary['mean_ms']:>10.1f}"
        f"{summary['median_ms']:>10.1f}"
        f"{summary['min_ms']:>10.1f}"
        f"{summary['max_ms']:>10.1f}"
        f"{summary['total_ms']:>12.1f}"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--rounds",
        type=int,
        default=8,
    )
    arguments = parser.parse_args()

    rounds = max(2, arguments.rounds)

    print(f"Benchmark tang du lieu - {rounds} vong, chi doc\n")

    try:
        direct = summarize(
            "Direct (truoc Sprint 4)",
            measure_direct(rounds),
        )
        pooled = summarize(
            "Pooled (sau Sprint 4)",
            measure_pooled(rounds),
        )
        repository = summarize(
            "Repository.list_by_user",
            measure_repository_read(rounds),
        )

    except Exception as error:
        print(f"Khong ket noi duoc database: {error}")
        return 1

    finally:
        close_pool()

    header = (
        f"{'Che do':<28}"
        f"{'lan 1':>10}"
        f"{'TB':>10}"
        f"{'trung vi':>10}"
        f"{'min':>10}"
        f"{'max':>10}"
        f"{'tong':>12}"
    )
    print(header)
    print("-" * len(header))

    for summary in (direct, pooled, repository):
        print_row(summary)

    print()

    if pooled["median_ms"] > 0:
        speedup = (
            direct["median_ms"] / pooled["median_ms"]
        )
        saved = direct["total_ms"] - pooled["total_ms"]
        print(
            f"Nhanh hon {speedup:.1f} lan theo trung vi, "
            f"tiet kiem {saved:.0f} ms tren {rounds} cau lenh."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
