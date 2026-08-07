"""YOLO detector facade.

This module keeps the public AI import path independent from the legacy
`detection` package while preserving the existing detector implementation.
"""

from detection.detector import ObjectDetector

__all__ = ["ObjectDetector"]
