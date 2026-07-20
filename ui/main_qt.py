from __future__ import annotations

import os
import sys
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

from detection.detector import ObjectDetector
from ui.auth_controller import AuthController
from ui.history_controller import HistoryController
from ui.image_controller import ImageController
from ui.stats_controller import StatsController
from ui.video_item import VideoItem
from ui.vocabulary_controller import VocabularyController
from ui.webcam_controller import WebcamController


QML_DIR = (
    Path(__file__)
    .resolve()
    .parent
    / "qml"
)


def run() -> None:
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
        detector = ObjectDetector()

    except Exception as error:
        print(
            f"Không thể tải mô hình YOLO: {error}"
        )
        raise

    vocabulary_controller = (
        VocabularyController()
    )

    image_controller = (
        ImageController(detector)
    )

    webcam_controller = (
        WebcamController(detector)
    )

    history_controller = (
        HistoryController()
    )

    stats_controller = (
        StatsController()
    )

    auth_controller = (
        AuthController()
    )

    def apply_current_user(
        user: dict,
    ) -> None:
        user_id = (
            int(user.get("id"))
            if user and user.get("id")
            else None
        )
        image_controller.set_user_id(user_id)
        webcam_controller.set_user_id(user_id)
        history_controller.set_user_id(user_id)
        stats_controller.set_user_id(user_id)

        if user_id is not None:
            history_controller.refresh()
            stats_controller.refresh()
        else:
            webcam_controller.stop()
            stats_controller.clear()

    auth_controller.userChanged.connect(
        apply_current_user
    )

    engine = QQmlApplicationEngine()

    context = engine.rootContext()

    context.setContextProperty(
        "vocabController",
        vocabulary_controller,
    )

    context.setContextProperty(
        "imageController",
        image_controller,
    )

    context.setContextProperty(
        "webcamController",
        webcam_controller,
    )

    context.setContextProperty(
        "historyController",
        history_controller,
    )

    context.setContextProperty(
        "statsController",
        stats_controller,
    )

    context.setContextProperty(
        "authController",
        auth_controller,
    )

    app.aboutToQuit.connect(
        webcam_controller.stop
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
