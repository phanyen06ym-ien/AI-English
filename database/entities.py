"""Entity cua tang du lieu.

Truoc Sprint 4, tang tren nhan `row[0]`, `row[1]`, `row[2]`... tu cursor. Doi thu
tu cot trong cau SELECT la vo het cac tang phia tren ma khong co canh bao nao.

Sprint 4 dinh nghia entity co dinh kieu. Repository chiu trach nhiem chuyen tu
tuple sang entity, tang tren khong bao gio thay tuple tho.

Schema database KHONG doi.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Sequence


DEFAULT_CATEGORY = "Unknown"


@dataclass(frozen=True)
class User:
    """Mot nguoi dung trong bang `users`."""

    id: int
    username: str
    fullname: str
    password_hash: str = ""

    @classmethod
    def from_row(
        cls,
        row: Sequence[Any],
        include_password: bool = True,
    ) -> "User":
        """Tao tu tuple theo dung thu tu cot: id, username, fullname, password."""
        return cls(
            id=int(row[0]),
            username=str(row[1] or ""),
            fullname=str(row[2] or ""),
            password_hash=(
                str(row[3] or "")
                if include_password and len(row) > 3
                else ""
            ),
        )

    def to_public_dict(self) -> dict[str, Any]:
        """Dict cong khai - KHONG kem mat khau."""
        return {
            "id": self.id,
            "username": self.username,
            "fullname": self.fullname,
        }


@dataclass(frozen=True)
class HistoryEntry:
    """Mot ban ghi trong bang `history`."""

    id: int | None
    user_id: int | None
    english_word: str
    vietnamese_meaning: str
    category: str
    confidence: float
    detected_time: datetime | None

    @classmethod
    def from_row(
        cls,
        row: Sequence[Any],
    ) -> "HistoryEntry":
        """Tao tu tuple theo dung thu tu cot cua cau SELECT hien co."""
        return cls(
            id=row[0],
            user_id=row[1],
            english_word=str(row[2] or ""),
            vietnamese_meaning=(
                row[3]
                if row[3] is not None
                else ""
            ),
            category=(
                row[4]
                if row[4] is not None
                else DEFAULT_CATEGORY
            ),
            confidence=float(row[5] or 0.0),
            detected_time=row[6],
        )

    def to_dict(self) -> dict[str, Any]:
        """Dict theo dung key ma tang Service dang dung tu Sprint 2.

        Giu nguyen ten key de khong pha vo `format_history_rows()` va
        `compute_statistics()`.
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "english_word": self.english_word,
            "vietnamese_meaning": self.vietnamese_meaning,
            "category": self.category,
            "confidence": self.confidence,
            "detected_time": self.detected_time,
        }


__all__ = [
    "User",
    "HistoryEntry",
    "DEFAULT_CATEGORY",
]
