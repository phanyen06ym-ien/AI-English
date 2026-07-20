from __future__ import annotations

import cv2
import numpy as np
from PySide6.QtGui import QImage

from utils import perf_monitor


def to_qimage(
    bgr_frame: np.ndarray,
) -> QImage:
    """
    Chuyển ảnh OpenCV BGR sang QImage RGB.
    """
    if bgr_frame is None:
        return QImage()

    with perf_monitor.timer("convert_bgr_to_rgb"):
        rgb_frame = cv2.cvtColor(
            bgr_frame,
            cv2.COLOR_BGR2RGB,
        )

    with perf_monitor.timer("qimage_make_contiguous"):
        rgb_frame = np.ascontiguousarray(
            rgb_frame
        )

    height, width, channels = rgb_frame.shape

    bytes_per_line = channels * width

    with perf_monitor.timer("qimage_create"):
        image = QImage(
            rgb_frame.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_RGB888,
        )

    with perf_monitor.timer("qimage_copy"):
        return image.copy()
