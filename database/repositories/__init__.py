"""Repository layer.

    Service  ->  Repository  ->  Database

Service khong biet SQL. Repository khong biet business rule.
"""

from __future__ import annotations

from database.repositories.base import BaseRepository
from database.repositories.history_repository import HistoryRepository
from database.repositories.user_repository import UserRepository


__all__ = [
    "BaseRepository",
    "HistoryRepository",
    "UserRepository",
]
