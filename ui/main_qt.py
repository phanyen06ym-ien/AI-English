from __future__ import annotations

import os
import sys
import logging
from pathlib import Path

from config import load_config
from core.logging_config import setup_from_app_config

# Cau hinh phai duoc doc TRUOC khi import PySide6: style cua Qt Quick chi doc
# bien moi truong mot lan luc nap thu vien.
APP_CONFIG = load_config()

os.environ.setdefault(
    "QT_QUICK_CONTROLS_STYLE",
    APP_CONFIG.ui.qt_quick_style,
)

import PySide6

if (
    sys.platform.startswith("win")
    and hasattr(
        os,
        "add_dll_directory",
    )
):
    os.add_dll_directory(
        str(
            Path(
                PySide6.__file__
            ).parent
        )
    )

from PySide6.QtCore import QUrl
from PySide6.QtQml import (
    QQmlApplicationEngine,
    qmlRegisterType,
)
from PySide6.QtWidgets import QApplication

from ui.app_context import AppContext
from ui.video_item import VideoItem


QML_DIR = APP_CONFIG.paths.qml_dir


def run(
    config=None,
) -> None:
    app_config = (
        config
        if config is not None
        else APP_CONFIG
    )

    # Sprint 7: logger phan cap + file xoay vong + che du lieu nhay cam.
    setup_from_app_config(app_config)

    logging.getLogger("ui.bootstrap").info(
        "Khoi dong voi cau hinh: %s",
        app_config.summary(),
    )

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        app_config.ui.application_name
    )

    qmlRegisterType(
        VideoItem,
        "AIEnglish",
        1,
        0,
        "VideoItem",
    )

    try:
        context = AppContext.build(config=app_config)

    except Exception as error:
        logging.getLogger(__name__).exception(
            "Khong the khoi tao AppContext: %s",
            error,
        )
        raise

    engine = QQmlApplicationEngine()

    qml_context = engine.rootContext()

    for name, obj in context.context_properties().items():
        qml_context.setContextProperty(
            name,
            obj,
        )

    app.aboutToQuit.connect(
        context.shutdown
    )

    engine.load(
        QUrl.fromLocalFile(
            str(
                app_config.paths.qml_dir / "Main.qml"
            )
        )
    )

    if not engine.rootObjects():
        raise RuntimeError(
            "Không tải được Main.qml."
        )

    sys.exit(
        app.exec()
    )
