"""Service dieu phoi mot lan nhan dien cho anh tinh va cho webcam frame.

Day la noi duy nhat cua GUI layer duoc phep goi `AIEngine`. Service khong biet
gi ve Qt, khong biet gi ve QML, nen co the unit test khong can QApplication.

Sprint 3 KHONG doi thuat toan AI: service chi goi lai `AIEngine.analyze_frame()`
da co tu Sprint 2 va khong dung toi YOLO / KNN / KMeans truc tiep.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from typing import Any, Callable

import cv2

from ai.models import ImageAnalysisResult
from ai.pipeline import AIEngine
from config.schema import UIConfig
from ui.services.annotation_service import (
    AnnotationService,
    build_image_label,
    build_webcam_label,
)
from ui.services.history_service import (
    HistoryRecordPolicy,
    HistoryService,
)


ERROR_IMAGE_UNREADABLE = "Không đọc được ảnh."


@dataclass(frozen=True)
class ImageDetectionOutcome:
    """Ket qua mot lan nhan dien anh tinh."""

    success: bool
    message: str = ""
    analysis: ImageAnalysisResult | None = None
    annotated_frame: Any = None
    saved_history_count: int = 0

    @property
    def detections(self) -> list:
        if self.analysis is None:
            return []
        return list(self.analysis.detections)


@dataclass
class FrameDetectionOutcome:
    """Ket qua mot lan nhan dien webcam frame."""

    success: bool
    message: str = ""
    analysis: ImageAnalysisResult | None = None
    results: list[dict[str, Any]] = field(default_factory=list)
    recordable: list[dict[str, Any]] = field(default_factory=list)


class DetectionService:
    """Business logic cua luong nhan dien, dung chung cho Image va Webcam."""

    def __init__(
        self,
        ai_engine: AIEngine,
        history_service: HistoryService | None = None,
        image_reader: Callable[[str], Any] = cv2.imread,
        ui_config: UIConfig | None = None,
    ) -> None:
        self.ai_engine = ai_engine
        self.history_service = (
            history_service
            if history_service is not None
            else HistoryService()
        )
        self._image_reader = image_reader
        self._ui_config = (
            ui_config
            if ui_config is not None
            else UIConfig()
        )
        self._image_annotator = AnnotationService.for_image(
            self._ui_config
        )
        self._webcam_annotator = AnnotationService.for_webcam(
            self._ui_config
        )

    # ------------------------------------------------------------------
    # Anh tinh
    # ------------------------------------------------------------------

    def load_image(
        self,
        image_path: str,
    ):
        """Doc anh tu dia. Tra ve None neu khong doc duoc."""
        if not image_path:
            return None

        return self._image_reader(image_path)

    def analyze_image_file(
        self,
        image_path: str,
        user_id: int | None = None,
        save_history: bool = True,
        progress_callback: Callable[[int], None] | None = None,
    ) -> ImageDetectionOutcome:
        """Doc anh -> AIEngine -> luu lich su -> ve nhan.

        `progress_callback` cho phep Worker phat tien do ma khong can biet
        chi tiet business logic.
        """

        def report(value: int) -> None:
            if progress_callback is not None:
                progress_callback(value)

        report(5)

        image = self.load_image(image_path)

        if image is None:
            return ImageDetectionOutcome(
                success=False,
                message=ERROR_IMAGE_UNREADABLE,
            )

        report(25)

        analysis = self.ai_engine.analyze_frame(image)

        report(70)

        if not analysis.success:
            return ImageDetectionOutcome(
                success=False,
                message=analysis.message,
                analysis=analysis,
            )

        saved_count = 0

        if save_history:
            saved_count = self.history_service.save_detections(
                analysis.detections,
                user_id=user_id,
            )

        report(85)

        annotated = self._image_annotator.draw_detections(
            image,
            (
                (
                    detection.box,
                    build_image_label(detection),
                )
                for detection in analysis.detections
            ),
        )

        report(100)

        return ImageDetectionOutcome(
            success=True,
            message=analysis.message,
            analysis=analysis,
            annotated_frame=annotated,
            saved_history_count=saved_count,
        )

    # ------------------------------------------------------------------
    # Webcam
    # ------------------------------------------------------------------

    def analyze_camera_frame(
        self,
        frame,
        policy: HistoryRecordPolicy,
        now: float | None = None,
    ) -> FrameDetectionOutcome:
        """Chay AI cho mot frame va quyet dinh detection nao duoc ghi lich su."""
        timestamp = (
            monotonic()
            if now is None
            else now
        )

        analysis = self.ai_engine.analyze_frame(frame)

        if not analysis.success:
            return FrameDetectionOutcome(
                success=False,
                message=analysis.message,
                analysis=analysis,
            )

        results = analysis.detections_as_dicts()

        recordable: list[dict[str, Any]] = []

        for result in results:
            class_name = result.get("english", "")
            confidence = float(
                result.get("confidence")
                or 0.0
            )

            if policy.should_record(
                class_name,
                confidence,
                timestamp,
            ):
                policy.mark_recorded(
                    class_name,
                    timestamp,
                )
                recordable.append(result)

        return FrameDetectionOutcome(
            success=True,
            message=analysis.message,
            analysis=analysis,
            results=results,
            recordable=recordable,
        )

    def annotate_camera_frame(
        self,
        frame,
        results: list[dict[str, Any]],
    ):
        """Ve ket qua len frame webcam."""
        return self._webcam_annotator.draw_detections(
            frame,
            (
                (
                    result["box"],
                    build_webcam_label(result),
                )
                for result in results
            ),
        )
