"""Ve bounding box va nhan len frame.

Truoc Sprint 3 logic nay nam truc tiep trong `ImageDetectThread.run()` va
`WebcamThread._draw_results()`. Sprint 3 tach ra service de Worker chi con
dieu phoi thread.

Luu y: format nhan duoc giu NGUYEN VAN so voi Sprint 2 de khong lam vo GUI.

- Anh tinh : "<english> - <vietnamese> [<category>] (<conf:.2f>)"
- Webcam   : `DetectionResult.text`, tuc "[<category> - <level>]"
"""

from __future__ import annotations

from typing import Any, Iterable

import cv2

from utils import perf_monitor
from utils.helper import draw_vietnamese_text


IMAGE_BOX_COLOR = (0, 255, 0)
IMAGE_LABEL_SIZE = 28

WEBCAM_BOX_COLOR = (0, 180, 0)
WEBCAM_LABEL_SIZE = 24

LABEL_Y_OFFSET = 35
LABEL_Y_MIN = 5


def build_image_label(
    detection: Any,
) -> str:
    """Nhan cho anh tinh (khong kem level) - giu dung format Sprint 2."""
    return (
        f"{detection.english} - {detection.vietnamese} "
        f"[{detection.category}] "
        f"({detection.confidence:.2f})"
    )


def build_webcam_label(
    detection: dict[str, Any],
) -> str:
    """Nhan cho webcam - dung san truong `text` cua DetectionResult."""
    return str(
        detection.get("text", "")
    )


class AnnotationService:
    """Ve ket qua nhan dien len anh BGR."""

    def __init__(
        self,
        box_color: tuple[int, int, int] = IMAGE_BOX_COLOR,
        label_size: int = IMAGE_LABEL_SIZE,
    ) -> None:
        self.box_color = box_color
        self.label_size = label_size

    def draw_one(
        self,
        frame,
        box: tuple[int, int, int, int],
        label: str,
    ):
        """Ve mot box + nhan, tra ve frame moi."""
        x1, y1, x2, y2 = box

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            self.box_color,
            2,
        )

        return draw_vietnamese_text(
            frame,
            label,
            (
                x1,
                max(
                    y1 - LABEL_Y_OFFSET,
                    LABEL_Y_MIN,
                ),
            ),
            color=self.box_color,
            size=self.label_size,
        )

    def draw_detections(
        self,
        frame,
        items: Iterable[tuple[tuple[int, int, int, int], str]],
    ):
        """Ve nhieu box + nhan tu cap (box, label)."""
        with perf_monitor.timer("draw_bounding_boxes"):
            for box, label in items:
                frame = self.draw_one(
                    frame,
                    box,
                    label,
                )

        return frame

    @classmethod
    def for_image(cls) -> "AnnotationService":
        """Cau hinh mau/size dung cho anh tinh."""
        return cls(
            box_color=IMAGE_BOX_COLOR,
            label_size=IMAGE_LABEL_SIZE,
        )

    @classmethod
    def for_webcam(cls) -> "AnnotationService":
        """Cau hinh mau/size dung cho webcam."""
        return cls(
            box_color=WEBCAM_BOX_COLOR,
            label_size=WEBCAM_LABEL_SIZE,
        )
