"""Logging danh rieng cho GUI layer.

Quy uoc Sprint 3:

- GUI chi log UI Event, Navigation, Button Click va State Change.
- GUI KHONG log AI (YOLO, KNN, KMeans, vocabulary). Phan do thuoc `ai.pipeline`.
- Moi log deu di qua logger co ten `ui.<component>` de loc de dang.
"""

from __future__ import annotations

import logging
from typing import Any


UI_LOGGER_PREFIX = "ui"

#: Tu khoa thuoc AI layer, GUI khong duoc log.
FORBIDDEN_AI_KEYWORDS = frozenset(
    {
        "yolo",
        "knn",
        "kmeans",
        "vocabulary",
        "detector",
        "cluster",
        "model",
        "inference",
        "confidence",
    }
)


def get_ui_logger(
    component: str,
) -> logging.Logger:
    """Tra ve logger chuan cho mot component GUI."""
    return logging.getLogger(
        f"{UI_LOGGER_PREFIX}.{component}"
    )


def is_ui_event_name(
    event: str,
) -> bool:
    """False neu ten event mang ngu nghia AI (khong duoc log o GUI)."""
    normalized = str(event).strip().lower()

    return not any(
        keyword in normalized
        for keyword in FORBIDDEN_AI_KEYWORDS
    )


def _format_fields(
    fields: dict[str, Any],
) -> str:
    if not fields:
        return ""

    return " " + " ".join(
        f"{key}={value}"
        for key, value in fields.items()
    )


def log_ui_event(
    logger: logging.Logger,
    event: str,
    **fields: Any,
) -> None:
    """Log mot UI event chung."""
    logger.info(
        "ui_event=%s%s",
        event,
        _format_fields(fields),
    )


def log_button_click(
    logger: logging.Logger,
    button: str,
    **fields: Any,
) -> None:
    """Log su kien bam nut tu QML."""
    logger.info(
        "button_click=%s%s",
        button,
        _format_fields(fields),
    )


def log_navigation(
    logger: logging.Logger,
    destination: str,
    **fields: Any,
) -> None:
    """Log dieu huong giua cac trang."""
    logger.info(
        "navigation=%s%s",
        destination,
        _format_fields(fields),
    )


def log_state_change(
    logger: logging.Logger,
    previous: Any,
    current: Any,
) -> None:
    """Log chuyen trang thai cua ViewModel."""
    logger.info(
        "state_change %s -> %s",
        getattr(previous, "value", previous),
        getattr(current, "value", current),
    )
