"""Repository cho bang `history`.

Cau SQL giu NGUYEN VAN so voi Sprint 3, ke ca gioi han `max(1, min(limit, 500))`.

Khac biet duy nhat: khi database loi, Repository **nem** `RepositoryError` thay vi
tra ve `[]` / `False`. Nho vay tang tren phan biet duoc "khong co du lieu" voi
"database hong".
"""

from __future__ import annotations

from database.entities import HistoryEntry
from database.repositories.base import BaseRepository


#: Gioi han an toan cua cau SELECT - giu nguyen tu Sprint 3.
MIN_LIMIT = 1
MAX_LIMIT = 500

HISTORY_COLUMNS = """
    id,
    user_id,
    english_word,
    vietnamese_meaning,
    category,
    confidence,
    detected_time
"""

SQL_INSERT_HISTORY = """
    INSERT INTO history (
        user_id,
        english_word,
        vietnamese_meaning,
        category,
        confidence,
        detected_time
    )
    VALUES (
        %s,
        %s,
        %s,
        %s,
        %s,
        CURRENT_TIMESTAMP
    );
"""

SQL_SELECT_ALL = f"""
    SELECT
        {HISTORY_COLUMNS}
    FROM history
    ORDER BY detected_time DESC
    LIMIT %s;
"""

SQL_SELECT_BY_USER = f"""
    SELECT
        {HISTORY_COLUMNS}
    FROM history
    WHERE user_id = %s
    ORDER BY detected_time DESC
    LIMIT %s;
"""

SQL_DELETE_ALL = "DELETE FROM history;"

SQL_DELETE_BY_USER = """
    DELETE FROM history
    WHERE user_id = %s;
"""


def clamp_limit(
    limit: int,
) -> int:
    """Ep gioi han truy van ve khoang an toan."""
    return max(
        MIN_LIMIT,
        min(int(limit), MAX_LIMIT),
    )


class HistoryRepository(BaseRepository):
    """Truy cap bang `history`."""

    def add(
        self,
        english_word: str,
        vietnamese_meaning: str | None,
        category: str | None,
        confidence: float,
        user_id: int | None = None,
    ) -> bool:
        """Them mot ban ghi nhan dien.

        Tra ve False neu `english_word` rong (khong phai loi database).
        Nem `RepositoryError` neu database loi.
        """
        normalized_english = (english_word or "").strip()

        if not normalized_english:
            return False

        normalized_vietnamese = (
            vietnamese_meaning.strip()
            if vietnamese_meaning
            else ""
        )
        normalized_category = (
            category.strip()
            if category
            else "Unknown"
        )

        self.execute(
            SQL_INSERT_HISTORY,
            (
                user_id,
                normalized_english,
                normalized_vietnamese,
                normalized_category,
                float(confidence),
            ),
        )

        return True

    def list_by_user(
        self,
        user_id: int | None = None,
        limit: int = 100,
    ) -> list[HistoryEntry]:
        """Doc lich su. `user_id=None` nghia la lay toan bo."""
        safe_limit = clamp_limit(limit)

        if user_id is None:
            rows = self.fetch_all(
                SQL_SELECT_ALL,
                (safe_limit,),
            )
        else:
            rows = self.fetch_all(
                SQL_SELECT_BY_USER,
                (
                    user_id,
                    safe_limit,
                ),
            )

        return [
            HistoryEntry.from_row(row)
            for row in rows
        ]

    def delete_by_user(
        self,
        user_id: int | None = None,
    ) -> int:
        """Xoa lich su. `user_id=None` nghia la xoa toan bo.

        Tra ve so dong da xoa.
        """
        if user_id is None:
            return self.execute(SQL_DELETE_ALL)

        return self.execute(
            SQL_DELETE_BY_USER,
            (user_id,),
        )
