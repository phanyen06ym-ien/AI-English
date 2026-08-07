"""Compatibility shim.

Quan ly ket noi da chuyen sang `database.connection` trong Sprint 4 (them
connection pool va ranh gioi transaction ro rang). Module nay duoc giu de moi
import cu `from database.db import database_cursor` van chay.
"""

from __future__ import annotations

from database.connection import (
    close_pool,
    database_cursor,
    get_connection,
    get_pool,
)


__all__ = [
    "close_pool",
    "database_cursor",
    "get_connection",
    "get_pool",
]
