"""Fake cho tang du lieu (Sprint 4).

Muc tieu: chay duoc Repository va Service MA KHONG can PostgreSQL that.

`FakeCursorFactory` gia lap dung giao dien ma `BaseRepository` su dung:

    with cursor_factory(commit=...) as cursor:
        cursor.execute(query, parameters)
        cursor.fetchone() / cursor.fetchall()
        cursor.rowcount
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent),
)

from database.exceptions import (  # noqa: E402
    ConnectionFailedError,
    IntegrityError,
)


class FakeCursor:
    """Cursor gia: ghi lai cau lenh va tra ve du lieu da nap san."""

    def __init__(
        self,
        factory: "FakeCursorFactory",
    ) -> None:
        self._factory = factory
        self.rowcount = 0
        self._result: list = []

    def execute(
        self,
        query: str,
        parameters=(),
    ) -> None:
        self._factory.executed.append(
            (
                " ".join(query.split()),
                tuple(parameters),
            )
        )

        if self._factory.raise_error is not None:
            raise self._factory.raise_error

        self._result = list(
            self._factory.next_result()
        )
        self.rowcount = self._factory.rowcount

    def fetchone(self):
        if not self._result:
            return None
        return self._result[0]

    def fetchall(self):
        return list(self._result)

    def close(self) -> None:
        pass


class FakeCursorFactory:
    """Thay the `database_cursor` trong test."""

    def __init__(
        self,
        results=None,
        rowcount: int = 1,
        raise_error: Exception | None = None,
    ) -> None:
        #: Danh sach ket qua tra ve lan luot cho tung `execute()`.
        self.results = list(results) if results else []
        self.rowcount = rowcount
        self.raise_error = raise_error

        self.executed: list[tuple[str, tuple]] = []
        self.commits: list[bool] = []
        self.rollbacks = 0
        self._result_index = 0

    def next_result(self) -> list:
        if self._result_index < len(self.results):
            result = self.results[self._result_index]
            self._result_index += 1
            return result

        if self.results:
            return self.results[-1]

        return []

    @contextmanager
    def __call__(
        self,
        commit: bool = False,
    ):
        cursor = FakeCursor(self)

        try:
            yield cursor
            self.commits.append(commit)

        except Exception:
            self.rollbacks += 1
            raise

        finally:
            cursor.close()

    # --------------------------------------------------------------
    # Tien ich cho test
    # --------------------------------------------------------------

    def last_query(self) -> str:
        return self.executed[-1][0] if self.executed else ""

    def last_parameters(self) -> tuple:
        return self.executed[-1][1] if self.executed else ()

    def committed(self) -> bool:
        return any(self.commits)


def failing_factory(
    error: Exception | None = None,
) -> FakeCursorFactory:
    """Factory luon nem loi database."""
    return FakeCursorFactory(
        raise_error=(
            error
            if error is not None
            else ConnectionFailedError("mat ket noi")
        )
    )


def integrity_factory() -> FakeCursorFactory:
    """Factory nem loi vi pham rang buoc."""
    return FakeCursorFactory(
        raise_error=IntegrityError("trung username")
    )
