"""Service cho lich su nhan dien.

Sprint 3 gom business logic tu Controller/Worker ve day.
Sprint 4 doi tang duoi tu `database.history` (ham thu tuc, nuot loi) sang
`HistoryRepository` (entity + exception co nghia).

Chinh sach loi (NHIEM VU 5 - Sprint 4)
--------------------------------------

| Thao tac | Khi database loi |
|---|---|
| GHI lich su khi dang nhan dien | Ghi log, bo qua, KHONG lam hong ket qua AI |
| DOC lich su | Nem `RepositoryError` -> Worker emit `failed` -> GUI bao loi |
| XOA lich su | Nem `RepositoryError` -> Worker emit `failed` -> GUI bao loi |

Ly do: nguoi dung bam "Làm mới" ma database hong thi phai duoc bao. Con lich su
ghi nen trong luc nhan dien that bai thi khong duoc lam hong luong nhan dien.
"""

from __future__ import annotations

import logging
from typing import Any

from database.entities import HistoryEntry
from database.exceptions import RepositoryError
from database.repositories.history_repository import HistoryRepository
from utils.config import CONFIDENCE
from utils import perf_monitor


logger = logging.getLogger(__name__)


#: Khoang thoi gian toi thieu giua 2 lan luu cung mot tu (giay).
HISTORY_COOLDOWN_SECONDS = 5.0

#: So ban ghi toi da cho man hinh lich su.
HISTORY_PAGE_LIMIT = 200

DEFAULT_CATEGORY = "Unknown"
DATETIME_FORMAT = "%d/%m/%Y %H:%M"


class HistoryRecordPolicy:
    """Luat quyet dinh mot detection co duoc ghi lich su hay khong.

    Tach ra khoi `WebcamThread` tu Sprint 3 de Worker khong con giu business rule.
    """

    def __init__(
        self,
        min_confidence: float = CONFIDENCE,
        cooldown_seconds: float = HISTORY_COOLDOWN_SECONDS,
    ) -> None:
        self.min_confidence = float(min_confidence)
        self.cooldown_seconds = float(cooldown_seconds)
        self._last_saved_by_class: dict[str, float] = {}

    def should_record(
        self,
        class_name: str,
        confidence: float,
        now: float,
    ) -> bool:
        """True neu detection vuot nguong va da qua cooldown."""
        if not class_name:
            return False

        if float(confidence) < self.min_confidence:
            return False

        last_saved_at = self._last_saved_by_class.get(
            class_name,
            0.0,
        )

        return (
            now - last_saved_at
            >= self.cooldown_seconds
        )

    def mark_recorded(
        self,
        class_name: str,
        now: float,
    ) -> None:
        """Ghi nhan moc thoi gian da luu cho mot tu."""
        self._last_saved_by_class[class_name] = now

    def reset(self) -> None:
        """Xoa toan bo moc cooldown."""
        self._last_saved_by_class.clear()


def format_history_rows(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Chuyen row lich su sang dict ma HistoryModel dang dung.

    Giu nguyen key va quy tac fallback tu Sprint 2.
    """
    formatted_rows: list[dict[str, Any]] = []

    for row in rows:
        detected_time = row.get("detected_time")

        formatted_rows.append(
            {
                "english": row.get(
                    "english_word",
                    "",
                ),
                "vietnamese": (
                    row.get("vietnamese_meaning")
                    or row.get(
                        "english_word",
                        "",
                    )
                ),
                "category": (
                    row.get("category")
                    or DEFAULT_CATEGORY
                ),
                "confidence": float(
                    row.get(
                        "confidence",
                        0.0,
                    )
                ),
                "detected_time": (
                    detected_time.strftime(DATETIME_FORMAT)
                    if detected_time
                    else ""
                ),
            }
        )

    return formatted_rows


class HistoryService:
    """Diem truy cap duy nhat cua GUI toi lich su nhan dien.

    Service nay KHONG chua cau SQL nao. Moi truy van nam trong
    `HistoryRepository`.
    """

    def __init__(
        self,
        repository: HistoryRepository | None = None,
    ) -> None:
        self._repository = (
            repository
            if repository is not None
            else HistoryRepository()
        )

    @property
    def repository(self) -> HistoryRepository:
        return self._repository

    # ------------------------------------------------------------------
    # Ghi - best effort, khong lam hong luong nhan dien
    # ------------------------------------------------------------------

    def save_detection(
        self,
        english: str,
        vietnamese: str | None,
        category: str | None,
        confidence: float,
        user_id: int | None = None,
    ) -> bool:
        """Luu mot ket qua nhan dien. False neu that bai."""
        try:
            with perf_monitor.timer("history_service_save"):
                return self._repository.add(
                    english,
                    vietnamese,
                    category,
                    float(confidence),
                    user_id=user_id,
                )

        except RepositoryError as error:
            logger.error(
                "Khong luu duoc lich su [%s]: %s",
                error.error_code,
                error,
            )
            return False

    def save_detections(
        self,
        detections,
        user_id: int | None = None,
    ) -> int:
        """Luu mot danh sach `DetectionResult`, tra ve so ban ghi da luu."""
        saved = 0

        for detection in detections:
            if self.save_detection(
                detection.english,
                detection.vietnamese,
                detection.category,
                detection.confidence,
                user_id=user_id,
            ):
                saved += 1

        return saved

    # ------------------------------------------------------------------
    # Doc / Xoa - nghiem ngat, loi phai bao len GUI
    # ------------------------------------------------------------------

    def load_entries(
        self,
        user_id: int | None,
        limit: int = HISTORY_PAGE_LIMIT,
    ) -> list[HistoryEntry]:
        """Doc lich su duoi dang entity co dinh kieu."""
        with perf_monitor.timer("history_service_load"):
            return self._repository.list_by_user(
                user_id=user_id,
                limit=limit,
            )

    def load_rows(
        self,
        user_id: int | None,
        limit: int = HISTORY_PAGE_LIMIT,
    ) -> list[dict[str, Any]]:
        """Doc lich su duoi dang dict (dinh dang tang tren dang dung)."""
        return [
            entry.to_dict()
            for entry in self.load_entries(
                user_id,
                limit=limit,
            )
        ]

    def load_formatted_rows(
        self,
        user_id: int | None,
        limit: int = HISTORY_PAGE_LIMIT,
    ) -> list[dict[str, Any]]:
        """Doc lich su va format san cho View."""
        return format_history_rows(
            self.load_rows(
                user_id,
                limit=limit,
            )
        )

    def clear(
        self,
        user_id: int | None,
    ) -> bool:
        """Xoa lich su cua mot nguoi dung."""
        with perf_monitor.timer("history_service_clear"):
            self._repository.delete_by_user(user_id)

        return True
