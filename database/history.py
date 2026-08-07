"""Compatibility shim cho tang lich su.

Truy van SQL da chuyen sang `database.repositories.history_repository`.
Module nay giu lai API cu (`save_history`, `get_history`, `clear_history`,
`delete_history_by_user`) VA giu nguyen hanh vi cu:

    loi database -> tra ve [] hoac False, khong nem exception.

Code moi (`ui.services.history_service`) goi thang `HistoryRepository` de nhan
duoc exception co nghia. Chi nhung script cu con dung module nay.
"""

from __future__ import annotations

import logging
from typing import Optional

from database.exceptions import RepositoryError
from database.repositories.history_repository import HistoryRepository


logger = logging.getLogger(__name__)

_repository = HistoryRepository()


def save_history(
    english_word: str,
    vietnamese_meaning: str | None,
    category: str | None,
    confidence: float,
    user_id: Optional[int] = None,
) -> bool:
    """Luu mot ket qua nhan dien.

    Tra ve:
    - True neu luu thanh cong.
    - False neu database loi hoac `english_word` rong.
    """
    try:
        saved = _repository.add(
            english_word,
            vietnamese_meaning,
            category,
            confidence,
            user_id=user_id,
        )

        if not saved:
            logger.warning(
                "Khong luu lich su vi english_word trong."
            )

        return saved

    except RepositoryError as error:
        logger.error(
            "Khong luu duoc lich su nhan dien: %s",
            error,
        )
        return False


def get_history(
    user_id: Optional[int] = None,
    limit: int = 100,
) -> list[dict]:
    """Lay lich su nhan dien.

    Nếu truyền user_id: chỉ lấy lịch sử của người dùng đó.
    Nếu user_id là None: lấy toàn bộ lịch sử.
    """
    try:
        entries = _repository.list_by_user(
            user_id=user_id,
            limit=limit,
        )

    except RepositoryError as error:
        logger.error(
            "Khong the doc lich su nhan dien: %s",
            error,
        )
        return []

    return [
        entry.to_dict()
        for entry in entries
    ]


def delete_history_by_user(
    user_id: int,
) -> bool:
    """Xoa toan bo lich su cua mot nguoi dung."""
    return clear_history(user_id)


def clear_history(
    user_id: int | None = None,
) -> bool:
    """Xoa lich su nhan dien.

    Nếu user_id là None: xóa toàn bộ lịch sử.
    Nếu có user_id: chỉ xóa lịch sử của người dùng đó.
    """
    try:
        _repository.delete_by_user(user_id)
        return True

    except RepositoryError as error:
        logger.error(
            "Khong the xoa lich su: %s",
            error,
        )
        return False


__all__ = [
    "save_history",
    "get_history",
    "clear_history",
    "delete_history_by_user",
]
