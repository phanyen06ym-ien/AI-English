from __future__ import annotations

from typing import Optional

from database.db import database_cursor
from utils import perf_monitor


def save_history(
    english_word: str,
    vietnamese_meaning: str | None,
    category: str | None,
    confidence: float,
    user_id: Optional[int] = None,
) -> bool:
    """
    Lưu một kết quả nhận dạng vào bảng history.

    Trả về:
    - True nếu lưu thành công.
    - False nếu database lỗi.
    """
    normalized_english = english_word.strip()
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

    if not normalized_english:
        print(
            "Không lưu lịch sử vì english_word trống."
        )
        return False

    query = """
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

    try:
        with database_cursor(commit=True) as cursor:
            with perf_monitor.timer("db_insert_history_execute"):
                cursor.execute(
                    query,
                    (
                        user_id,
                        normalized_english,
                        normalized_vietnamese,
                        normalized_category,
                        float(confidence),
                    ),
                )

        return True

    except Exception as error:
        print(
            "Không lưu được lịch sử nhận dạng: "
            f"{error}"
        )
        return False


def get_history(
    user_id: Optional[int] = None,
    limit: int = 100,
) -> list[dict]:
    """
    Lấy lịch sử nhận dạng.

    Nếu truyền user_id:
        chỉ lấy lịch sử của người dùng đó.

    Nếu user_id là None:
        lấy toàn bộ lịch sử.
    """
    safe_limit = max(1, min(limit, 500))

    if user_id is None:
        query = """
            SELECT
                id,
                user_id,
                english_word,
                vietnamese_meaning,
                category,
                confidence,
                detected_time
            FROM history
            ORDER BY detected_time DESC
            LIMIT %s;
        """

        parameters = (safe_limit,)

    else:
        query = """
            SELECT
                id,
                user_id,
                english_word,
                vietnamese_meaning,
                category,
                confidence,
                detected_time
            FROM history
            WHERE user_id = %s
            ORDER BY detected_time DESC
            LIMIT %s;
        """

        parameters = (
            user_id,
            safe_limit,
        )

    try:
        with database_cursor() as cursor:
            with perf_monitor.timer("db_select_history_execute"):
                cursor.execute(
                    query,
                    parameters,
                )

            with perf_monitor.timer("db_select_history_fetch"):
                rows = cursor.fetchall()

    except Exception as error:
        print(
            "Không thể đọc lịch sử nhận dạng: "
            f"{error}"
        )
        return []

    return [
        {
            "id": row[0],
            "user_id": row[1],
            "english_word": row[2],
            "vietnamese_meaning": row[3],
            "category": row[4],
            "confidence": float(row[5] or 0.0),
            "detected_time": row[6],
        }
        for row in rows
    ]


def delete_history_by_user(
    user_id: int,
) -> bool:
    """
    Xóa toàn bộ lịch sử của một người dùng.
    """
    return clear_history(user_id)


def clear_history(
    user_id: int | None = None,
) -> bool:
    """
    Xóa lịch sử nhận dạng.

    Nếu user_id là None:
        xóa toàn bộ lịch sử.

    Nếu có user_id:
        chỉ xóa lịch sử của người dùng đó.
    """
    if user_id is None:
        query = "DELETE FROM history;"
        parameters = ()

    else:
        query = """
            DELETE FROM history
            WHERE user_id = %s;
        """
        parameters = (user_id,)

    try:
        with database_cursor(
            commit=True
        ) as cursor:
            cursor.execute(
                query,
                parameters,
            )

        return True

    except Exception as error:
        print(
            f"Không thể xóa lịch sử: {error}"
        )
        return False
