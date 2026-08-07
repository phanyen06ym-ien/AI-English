"""Lop nen cho moi Repository.

Repository chi lam 3 viec:

1. Giu cau SQL.
2. Truyen tham so.
3. Chuyen tuple tra ve thanh Entity.

Repository KHONG chua business rule, KHONG bat loi de tra ve gia tri rong,
KHONG biet gi ve GUI.
"""

from __future__ import annotations

from typing import Any, Callable, Sequence

from database.connection import database_cursor


class BaseRepository:
    """Ha tang chung: thuc thi SQL va chuyen ket qua thanh entity."""

    def __init__(
        self,
        cursor_factory: Callable[..., Any] = database_cursor,
    ) -> None:
        # Cho phep tiem cursor gia trong test.
        self._cursor_factory = cursor_factory

    def fetch_one(
        self,
        query: str,
        parameters: Sequence[Any] = (),
    ):
        """Chay SELECT va tra ve mot dong, hoac None."""
        with self._cursor_factory() as cursor:
            cursor.execute(query, tuple(parameters))
            return cursor.fetchone()

    def fetch_all(
        self,
        query: str,
        parameters: Sequence[Any] = (),
    ) -> list:
        """Chay SELECT va tra ve moi dong."""
        with self._cursor_factory() as cursor:
            cursor.execute(query, tuple(parameters))
            return list(cursor.fetchall())

    def execute(
        self,
        query: str,
        parameters: Sequence[Any] = (),
    ) -> int:
        """Chay INSERT/UPDATE/DELETE trong mot transaction co commit."""
        with self._cursor_factory(commit=True) as cursor:
            cursor.execute(query, tuple(parameters))
            return int(
                getattr(cursor, "rowcount", 0) or 0
            )

    def execute_returning(
        self,
        query: str,
        parameters: Sequence[Any] = (),
    ):
        """Chay INSERT ... RETURNING trong mot transaction co commit."""
        with self._cursor_factory(commit=True) as cursor:
            cursor.execute(query, tuple(parameters))
            return cursor.fetchone()
