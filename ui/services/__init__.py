"""Service layer cho GUI.

Service chua business logic da duoc bo ra khoi Controller va Worker:

- `annotation_service`: ve bounding box / nhan len frame (OpenCV thuan).
- `history_service`: doc, ghi, xoa va format lich su nhan dien.
- `stats_service`: tinh thong ke tu lich su.
- `detection_service`: dieu phoi AIEngine + annotation + history cho 1 anh/frame.
- `dialog_service`: chuan hoa Loading / Error / Success / Warning dialog.

Chi `dialog_service` phu thuoc Qt. Cac service con lai import duoc trong test
khong can QApplication.
"""

from __future__ import annotations

from ui.services.annotation_service import (
    AnnotationService,
    build_image_label,
    build_webcam_label,
)
from ui.services.detection_service import (
    DetectionService,
    ImageDetectionOutcome,
)
from ui.services.history_service import (
    HistoryRecordPolicy,
    HistoryService,
    format_history_rows,
)
from ui.services.stats_service import (
    EMPTY_STATS,
    compute_statistics,
)


__all__ = [
    "AnnotationService",
    "build_image_label",
    "build_webcam_label",
    "DetectionService",
    "ImageDetectionOutcome",
    "HistoryRecordPolicy",
    "HistoryService",
    "format_history_rows",
    "EMPTY_STATS",
    "compute_statistics",
]
