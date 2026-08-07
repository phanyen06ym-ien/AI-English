from __future__ import annotations

import os
import sys
import logging
from pathlib import Path

os.environ.setdefault(
    "QT_QUICK_CONTROLS_STYLE",
    "Basic",
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


QML_DIR = (
    Path(__file__)
    .resolve()
    .parent
    / "qml"
)


def run() -> None:
    logging.basicConfig(level=logging.INFO)

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "AI-English"
    )

    qmlRegisterType(
        VideoItem,
        "AIEnglish",
        1,
        0,
        "VideoItem",
    )

    try:
        context = AppContext.build()

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
                QML_DIR / "Main.qml"
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
