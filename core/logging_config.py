"""Kien truc logging cua toan he thong.

Van de truoc Sprint 7
---------------------

    main.py / ui/main_qt.py:  logging.basicConfig(level=logging.INFO)

Chi mot dong. Hau qua:

- Moi thu do ra console, khong luu file -> nguoi dung bao loi thi khong co gi de xem.
- Khong chinh duoc muc log cho tung tang: bat DEBUG cho database la ngap
  log cua `ultralytics` va `matplotlib`.
- Khong co gi chan mat khau lot vao log.
- Thu vien ben thu ba (torch, PIL, matplotlib) do log rac vao chung.

Giai phap
---------

Logger phan cap theo tang, moi tang chinh muc rieng:

    ai.*          INFO      pipeline nhan dien
    ui.*          INFO      su kien giao dien (Sprint 3)
    database.*    INFO      truy van, ket noi
    config.*      INFO      nap cau hinh
    core.*        INFO      loi he thong
    <thu vien>    WARNING   torch, PIL, matplotlib, ultralytics... chi bao dong

Hai duong ra:

    Console  -> muc theo cau hinh, dinh dang ngan gon cho nguoi doc
    File     -> LUON o muc DEBUG, dinh dang day du, xoay vong 5 file x 2 MB

Ca hai duong deu di qua `SensitiveDataFilter`.
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any

from core.redaction import (
    RedactingFormatter,
    SensitiveDataFilter,
    register_secret,
)

# LUU Y: module nay KHONG duoc import `config` o cap module.
# `core/` la tang thap nhat: `config/errors.py` ke thua `core.errors.AppError`,
# nen neu `core` import `config` luc nap module se tao vong lap import.
# Cho nao can `config`, import ben trong ham.


#: Ten cac logger goc cua du an.
APPLICATION_LOGGERS = (
    "ai",
    "ui",
    "database",
    "config",
    "core",
    "utils",
    "ml",
    "detection",
    "dataset",
)

#: Thu vien ben thu ba chi duoc bao tu WARNING tro len.
NOISY_THIRD_PARTY_LOGGERS = (
    "PIL",
    "matplotlib",
    "torch",
    "ultralytics",
    "urllib3",
    "asyncio",
    "gtts",
    "comtypes",
)

THIRD_PARTY_LEVEL = logging.WARNING

CONSOLE_FORMAT = "%(levelname)-8s %(name)-28s %(message)s"
FILE_FORMAT = (
    "%(asctime)s %(levelname)-8s %(name)-28s "
    "[%(threadName)s] %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

DEFAULT_LEVEL = "INFO"

LOG_FILE_NAME = "ai-english.log"
LOG_FILE_MAX_BYTES = 2 * 1024 * 1024
LOG_FILE_BACKUP_COUNT = 5

#: Danh dau de khong gan handler hai lan.
_HANDLER_TAG = "ai_english_handler"

_configured = False


#: Goc project - suy ra tu vi tri file nay, khong can `config`.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def log_directory(
    paths: Any | None = None,
) -> Path:
    """Thu muc chua file log."""
    root = (
        paths.project_root
        if paths is not None
        else PROJECT_ROOT
    )

    return Path(root) / "logs"


def _has_our_handlers(
    logger: logging.Logger,
) -> bool:
    return any(
        getattr(handler, _HANDLER_TAG, False)
        for handler in logger.handlers
    )


def _remove_our_handlers(
    logger: logging.Logger,
) -> None:
    for handler in list(logger.handlers):
        if getattr(handler, _HANDLER_TAG, False):
            logger.removeHandler(handler)

            try:
                handler.close()
            except Exception:
                # Dong handler that bai khong duoc lam sap viec lap dat log.
                # Khong the ghi log o day vi handler dang bi go bo.
                pass


def build_console_handler(
    level: int,
) -> logging.Handler:
    """Handler ghi ra console cho nguoi doc truc tiep."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(
        RedactingFormatter(CONSOLE_FORMAT)
    )
    handler.addFilter(SensitiveDataFilter())
    setattr(handler, _HANDLER_TAG, True)

    return handler


def build_file_handler(
    directory: Path,
    level: int = logging.DEBUG,
) -> logging.Handler | None:
    """Handler ghi ra file, xoay vong. None neu khong tao duoc thu muc.

    Khong ghi duoc file KHONG duoc lam sap ung dung - console van chay.
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)

        handler = logging.handlers.RotatingFileHandler(
            directory / LOG_FILE_NAME,
            maxBytes=LOG_FILE_MAX_BYTES,
            backupCount=LOG_FILE_BACKUP_COUNT,
            encoding="utf-8",
        )

    except Exception:
        return None

    handler.setLevel(level)
    handler.setFormatter(
        RedactingFormatter(FILE_FORMAT, DATE_FORMAT)
    )
    handler.addFilter(SensitiveDataFilter())
    setattr(handler, _HANDLER_TAG, True)

    return handler


def resolve_level(
    level: str | int,
) -> int:
    """Doi ten muc log sang so. Ten la -> INFO."""
    if isinstance(level, int):
        return level

    return getattr(
        logging,
        str(level).upper(),
        logging.INFO,
    )


def setup_logging(
    config: Any | None = None,
    paths: Any | None = None,
    enable_file: bool = True,
    force: bool = False,
    level: str | int | None = None,
) -> logging.Logger:
    """Lap dat logging cho toan he thong. Goi MOT lan luc khoi dong.

    `config` la mot `LoggingConfig` (hoac bat ky doi tuong co thuoc tinh
    `level`). Truyen `level` de chi dinh thang, khong can doi tuong config.

    Goi lai khong nhan doi handler (tru khi `force=True`).
    """
    global _configured

    if level is not None:
        console_level = resolve_level(level)
    elif config is not None:
        console_level = resolve_level(
            getattr(config, "level", DEFAULT_LEVEL)
        )
    else:
        console_level = resolve_level(DEFAULT_LEVEL)

    root = logging.getLogger()

    if _configured and not force:
        return root

    _remove_our_handlers(root)

    # Root o DEBUG de file handler nhan duoc moi thu; console tu loc theo muc.
    root.setLevel(logging.DEBUG)
    root.addHandler(
        build_console_handler(console_level)
    )

    if enable_file:
        file_handler = build_file_handler(
            log_directory(paths)
        )

        if file_handler is not None:
            root.addHandler(file_handler)

    for name in NOISY_THIRD_PARTY_LOGGERS:
        logging.getLogger(name).setLevel(THIRD_PARTY_LEVEL)

    _configured = True

    return root


def setup_from_app_config(
    app_config,
    enable_file: bool = True,
    force: bool = False,
) -> logging.Logger:
    """Lap dat logging tu `AppConfig` va dang ky mat khau can che.

    Day la diem duy nhat noi mat khau database duoc dua vao bo loc.
    """
    register_secret(app_config.database.password)

    return setup_logging(
        config=app_config.logging,
        paths=app_config.paths,
        enable_file=enable_file,
        force=force,
    )


def set_layer_level(
    layer: str,
    level: str | int,
) -> None:
    """Chinh muc log cho mot tang, vi du `set_layer_level("database", "DEBUG")`."""
    logging.getLogger(layer).setLevel(
        resolve_level(level)
    )


def reset_logging() -> None:
    """Go moi handler cua du an. Chi dung trong test."""
    global _configured

    _remove_our_handlers(logging.getLogger())
    _configured = False


def is_configured() -> bool:
    return _configured


def get_logger(
    name: str,
) -> logging.Logger:
    """Logger theo ten phan cap, vi du `get_logger("database.repository")`."""
    return logging.getLogger(name)


__all__ = [
    "APPLICATION_LOGGERS",
    "CONSOLE_FORMAT",
    "FILE_FORMAT",
    "LOG_FILE_BACKUP_COUNT",
    "LOG_FILE_MAX_BYTES",
    "LOG_FILE_NAME",
    "NOISY_THIRD_PARTY_LOGGERS",
    "build_console_handler",
    "build_file_handler",
    "get_logger",
    "is_configured",
    "log_directory",
    "reset_logging",
    "resolve_level",
    "set_layer_level",
    "setup_from_app_config",
    "setup_logging",
]
