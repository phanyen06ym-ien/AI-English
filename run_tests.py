"""Diem chay test duy nhat cua du an - Sprint 8.

Truoc Sprint 8, moi bao cao ghi mot lenh khac nhau:

    python -m unittest test.test_ai_engine test.test_config test.test_di ...
    python test/test_knn.py
    python test/benchmark_database.py

Khong ai nho duoc, va de bo sot mot bo test.

Gio chi con:

    python run_tests.py                # chay toan bo bo test tu dong
    python run_tests.py --coverage     # kem do phu
    python run_tests.py --unittest     # dung unittest, khong can pytest
    python run_tests.py --list         # xem co nhung gi

Bao dam cua lenh nay:

- KHONG can YOLO, KHONG can PostgreSQL, KHONG can webcam.
- KHONG ghi de `models/*.pkl`, KHONG tao du lieu that.
- Chay duoc moi luc, tren may bat ky.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent

#: Nguong do phu toi thieu cho cac tang do Sprint 3-7 viet ra.
COVERAGE_THRESHOLD = 80

#: Tang duoc tinh do phu. `ml/`, `detection/`, `dataset/` la ma AI goc,
#: khong nam trong pham vi tai cau truc nen khong dat nguong.
COVERAGE_TARGETS = (
    "core",
    "config",
    "database",
    "ui",
)


def _run(command: list[str]) -> int:
    print("$", " ".join(command))
    print()

    return subprocess.call(command, cwd=str(ROOT))


def run_pytest(
    coverage: bool,
    extra: list[str],
) -> int:
    command = [sys.executable, "-m", "pytest"]

    if coverage:
        for target in COVERAGE_TARGETS:
            command.append(f"--cov={target}")

        command += [
            "--cov-report=term-missing:skip-covered",
            "--cov-report=html:docs/coverage",
            f"--cov-fail-under={COVERAGE_THRESHOLD}",
        ]

    command += extra

    return _run(command)


def run_unittest(extra: list[str]) -> int:
    command = [
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
    ] + extra

    return _run(command)


def list_tests() -> int:
    automated = sorted(
        path.name
        for path in (ROOT / "test").glob("test_*.py")
    )
    manual = sorted(
        path.name
        for path in (ROOT / "test" / "manual").glob("*.py")
        if path.name != "__init__.py"
    )

    print("BO TEST TU DONG (chay bang `python run_tests.py`)")
    print("  Khong can YOLO / database / webcam, khong de lai dau vet.\n")
    for name in automated:
        print(f"  test/{name}")

    print("\nSCRIPT CHAY TAY (khong nam trong bo test tu dong)")
    print("  Can moi truong that, mot so GHI DE model.\n")
    for name in manual:
        print(f"  test/manual/{name}")

    print(
        "\nSau khi chay script ghi de model, khoi phuc bang:"
        "\n  git checkout -- models/"
    )

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Chay bo test tu dong cua AI-English",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="do do phu va xuat bao cao HTML vao docs/coverage",
    )
    parser.add_argument(
        "--unittest",
        action="store_true",
        help="dung unittest thay vi pytest",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="liet ke test tu dong va script chay tay",
    )
    arguments, extra = parser.parse_known_args()

    if arguments.list:
        return list_tests()

    if arguments.unittest:
        if arguments.coverage:
            print(
                "Do phu can pytest-cov. Bo --unittest hoac cai:"
                "\n  pip install -r requirements-dev.txt"
            )
            return 2

        return run_unittest(extra)

    try:
        import pytest  # noqa: F401
    except ImportError:
        print(
            "Khong tim thay pytest, quay ve unittest."
            "\nCai day du bang: pip install -r requirements-dev.txt\n"
        )
        return run_unittest(extra)

    return run_pytest(arguments.coverage, extra)


if __name__ == "__main__":
    raise SystemExit(main())
