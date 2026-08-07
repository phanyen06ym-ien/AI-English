"""Service tinh thong ke tu lich su nhan dien.

Truoc Sprint 3 toan bo phep dem nay nam trong `StatsWorker.run()`.
Cong thuc duoc giu nguyen 100% de so lieu tren GUI khong doi.
"""

from __future__ import annotations

from collections import Counter
from typing import Any


DEFAULT_CATEGORY = "Unknown"

#: So ban ghi toi da dung de tinh thong ke.
STATS_HISTORY_LIMIT = 500

EMPTY_STATS: dict[str, Any] = {
    "totalDetections": 0,
    "uniqueWords": 0,
    "mostCommonWord": "",
    "mostDetectedWord": "",
    "averageConfidence": 0.0,
    "categories": {},
}


def empty_stats() -> dict[str, Any]:
    """Ban sao moi cua thong ke rong."""
    return dict(EMPTY_STATS)


def compute_statistics(
    history_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Tinh thong ke tu danh sach row lich su."""
    category_counter: Counter = Counter()
    word_counter: Counter = Counter()
    confidence_values: list[float] = []

    for row in history_rows:
        word = row.get("english_word")
        category = (
            row.get("category")
            or DEFAULT_CATEGORY
        )

        if word:
            word_counter[word] += 1

        confidence_values.append(
            float(
                row.get("confidence")
                or 0.0
            )
        )
        category_counter[category] += 1

    most_common_word = ""
    if word_counter:
        most_common_word = (
            word_counter.most_common(1)[0][0]
        )

    average_confidence = 0.0
    if confidence_values:
        average_confidence = (
            sum(confidence_values)
            / len(confidence_values)
        )

    return {
        "totalDetections": len(history_rows),
        "uniqueWords": len(word_counter),
        "mostCommonWord": most_common_word,
        "mostDetectedWord": most_common_word,
        "averageConfidence": float(average_confidence),
        "categories": dict(category_counter),
    }


class StatsService:
    """Doc lich su va tra ve thong ke da tinh san."""

    def __init__(
        self,
        history_service,
    ) -> None:
        self._history_service = history_service

    def compute_for_user(
        self,
        user_id: int | None,
        limit: int = STATS_HISTORY_LIMIT,
    ) -> dict[str, Any]:
        """Tinh thong ke cho mot nguoi dung."""
        rows = self._history_service.load_rows(
            user_id,
            limit=limit,
        )

        return compute_statistics(rows)
