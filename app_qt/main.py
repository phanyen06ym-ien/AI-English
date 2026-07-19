import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

import PySide6

# Python 3.8+ trên Windows không còn dùng PATH để tìm DLL phụ thuộc, chỉ
# add_dll_directory() mới có tác dụng. Các plugin QML (vd. qtquickcontrols2plugin.dll
# trong PySide6/qml/QtQuick/Controls/) nằm khác thư mục với Qt6*.dll gốc nên cần
# khai báo tường minh, nếu không sẽ lỗi "The specified module could not be found".
os.add_dll_directory(str(Path(PySide6.__file__).parent))

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PySide6.QtWidgets import QApplication

from detection.detector import ObjectDetector
from app_qt.video_item import VideoItem
from app_qt.vocabulary_controller import VocabularyController
from app_qt.image_controller import ImageController
from app_qt.webcam_controller import WebcamController
from app_qt.history_controller import HistoryController
from app_qt.stats_controller import StatsController

QML_DIR = Path(__file__).parent / "qml"


def run():
    app = QApplication(sys.argv)
    app.setApplicationName("AI-English")

    qmlRegisterType(VideoItem, "AIEnglish", 1, 0, "VideoItem")

    detector = ObjectDetector()

    vocab_controller = VocabularyController()
    image_controller = ImageController(detector)
    webcam_controller = WebcamController(detector)
    history_controller = HistoryController()
    stats_controller = StatsController()

    engine = QQmlApplicationEngine()
    ctx = engine.rootContext()
    ctx.setContextProperty("vocabController", vocab_controller)
    ctx.setContextProperty("imageController", image_controller)
    ctx.setContextProperty("webcamController", webcam_controller)
    ctx.setContextProperty("historyController", history_controller)
    ctx.setContextProperty("statsController", stats_controller)

    app.aboutToQuit.connect(webcam_controller.stop)
    image_controller.detectionFinished.connect(stats_controller.refresh)
    stats_controller.detectedWordsChanged.connect(vocab_controller.model.setLearnedWords)

    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    from utils.console import use_utf8_console

    use_utf8_console()
    run()
