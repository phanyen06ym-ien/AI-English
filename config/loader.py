"""Doc cau hinh tu bien moi truong.

Thu tu uu tien:

    gia tri mac dinh trong `config/schema.py`
        <- bi ghi de boi `.env`
            <- bi ghi de boi bien moi truong that su cua he thong
                <- bi ghi de boi tham so truyen thang vao `load_config()`

Gia tri sai kieu (vi du `AI_CONFIDENCE=abc`) khong lam sap ung dung: he thong ghi
canh bao va dung gia tri mac dinh. Gia tri **dung kieu nhung vo ly** (vi du
`AI_CONFIDENCE=5.0`) thi bi `validate()` chan lai ngay khi khoi dong.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from config.environment import Environment
from config.schema import (
    AIConfig,
    AppConfig,
    CameraConfig,
    DatabaseConfig,
    HistoryConfig,
    LoggingConfig,
    PathConfig,
    ThreadConfig,
    UIConfig,
)


logger = logging.getLogger(__name__)


_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


def _read_str(
    name: str,
    default: str,
) -> str:
    value = os.getenv(name)

    if value is None or value.strip() == "":
        return default

    return value.strip()


def _read_int(
    name: str,
    default: int,
) -> int:
    raw = os.getenv(name)

    if raw is None or raw.strip() == "":
        return default

    try:
        return int(raw.strip())

    except ValueError:
        logger.warning(
            "Bien moi truong %s=%r khong phai so nguyen, dung mac dinh %s",
            name,
            raw,
            default,
        )
        return default


def _read_float(
    name: str,
    default: float,
) -> float:
    raw = os.getenv(name)

    if raw is None or raw.strip() == "":
        return default

    try:
        return float(raw.strip())

    except ValueError:
        logger.warning(
            "Bien moi truong %s=%r khong phai so thuc, dung mac dinh %s",
            name,
            raw,
            default,
        )
        return default


def _read_bool(
    name: str,
    default: bool,
) -> bool:
    raw = os.getenv(name)

    if raw is None or raw.strip() == "":
        return default

    return raw.strip().lower() in _TRUE_VALUES


def load_dotenv_file(
    project_root: Path | None = None,
) -> None:
    """Nap `.env` neu co. Khong ghi de bien moi truong da ton tai."""
    load_dotenv()


def build_database_config(
    defaults: DatabaseConfig | None = None,
) -> DatabaseConfig:
    base = defaults if defaults is not None else DatabaseConfig()

    return DatabaseConfig(
        host=_read_str("DB_HOST", base.host),
        port=_read_str("DB_PORT", base.port),
        name=_read_str("DB_NAME", base.name),
        user=_read_str("DB_USER", base.user),
        password=_read_str("DB_PASSWORD", base.password),
        pool_min_connections=_read_int(
            "DB_POOL_MIN",
            base.pool_min_connections,
        ),
        pool_max_connections=_read_int(
            "DB_POOL_MAX",
            base.pool_max_connections,
        ),
    )


def build_ai_config(
    defaults: AIConfig | None = None,
) -> AIConfig:
    base = defaults if defaults is not None else AIConfig()

    return AIConfig(
        confidence=_read_float("AI_CONFIDENCE", base.confidence),
        image_size=_read_int("AI_IMAGE_SIZE", base.image_size),
        model_file_name=_read_str(
            "AI_MODEL_FILE",
            base.model_file_name,
        ),
        related_words_count=_read_int(
            "AI_RELATED_WORDS",
            base.related_words_count,
        ),
    )


def build_camera_config(
    defaults: CameraConfig | None = None,
) -> CameraConfig:
    base = defaults if defaults is not None else CameraConfig()

    return CameraConfig(
        camera_id=_read_int("CAMERA_ID", base.camera_id),
        inference_interval_seconds=_read_float(
            "CAMERA_INFERENCE_INTERVAL",
            base.inference_interval_seconds,
        ),
        max_frames_in_flight=_read_int(
            "CAMERA_MAX_FRAMES_IN_FLIGHT",
            base.max_frames_in_flight,
        ),
    )


def build_history_config(
    defaults: HistoryConfig | None = None,
) -> HistoryConfig:
    base = defaults if defaults is not None else HistoryConfig()

    return HistoryConfig(
        cooldown_seconds=_read_float(
            "HISTORY_COOLDOWN_SECONDS",
            base.cooldown_seconds,
        ),
        page_limit=_read_int(
            "HISTORY_PAGE_LIMIT",
            base.page_limit,
        ),
        stats_limit=_read_int(
            "HISTORY_STATS_LIMIT",
            base.stats_limit,
        ),
        min_query_limit=base.min_query_limit,
        max_query_limit=base.max_query_limit,
        write_queue_size=_read_int(
            "HISTORY_WRITE_QUEUE_SIZE",
            base.write_queue_size,
        ),
    )


def build_thread_config(
    defaults: ThreadConfig | None = None,
) -> ThreadConfig:
    base = defaults if defaults is not None else ThreadConfig()

    return ThreadConfig(
        dispose_timeout_ms=_read_int(
            "THREAD_DISPOSE_TIMEOUT_MS",
            base.dispose_timeout_ms,
        ),
        poll_interval_seconds=_read_float(
            "THREAD_POLL_INTERVAL",
            base.poll_interval_seconds,
        ),
    )


def build_logging_config(
    environment: Environment,
    defaults: LoggingConfig | None = None,
) -> LoggingConfig:
    base = (
        defaults
        if defaults is not None
        else LoggingConfig(level=environment.default_log_level)
    )

    return LoggingConfig(
        level=_read_str("LOG_LEVEL", base.level).upper(),
        performance_enabled=_read_bool(
            "AI_ENGLISH_PERF",
            base.performance_enabled,
        ),
    )


def load_config(
    environment: Environment | None = None,
    read_dotenv: bool = True,
    validate: bool = True,
) -> AppConfig:
    """Doc toan bo cau hinh.

    `environment=None` -> doc tu bien moi truong `AI_ENGLISH_ENV`.
    """
    if read_dotenv:
        load_dotenv_file()

    resolved_environment = (
        environment
        if environment is not None
        else Environment.current()
    )

    config = AppConfig(
        environment=resolved_environment,
        paths=PathConfig(),
        ai=build_ai_config(),
        camera=build_camera_config(),
        database=build_database_config(),
        history=build_history_config(),
        threads=build_thread_config(),
        ui=UIConfig(),
        logging=build_logging_config(resolved_environment),
    )

    if validate:
        config.validate()

    return config


def load_test_config() -> AppConfig:
    """Cau hinh cho unit test: khong doc `.env`, khong cham database that."""
    return AppConfig(
        environment=Environment.TESTING,
        logging=LoggingConfig(level="ERROR"),
    ).validate()


__all__ = [
    "build_ai_config",
    "build_camera_config",
    "build_database_config",
    "build_history_config",
    "build_logging_config",
    "build_thread_config",
    "load_config",
    "load_dotenv_file",
    "load_test_config",
]
