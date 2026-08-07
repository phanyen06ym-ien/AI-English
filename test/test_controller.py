"""Sprint 3 - Unit test cho Controller layer (Thin Controller).

Kiem tra:

1. Controller khong con Business Logic / AI / Database.
2. Controller chuyen tiep Signal cua ViewModel sang ten legacy ma QML dang bind.
3. HOP DONG QML: moi member ma file .qml dang dung deu con ton tai.
4. `AppContext` lap rap dung cay phu thuoc.
"""

from __future__ import annotations

import inspect
import re
import unittest
from pathlib import Path

from test.ui_fakes import (
    FakeAIEngine,
    FakeCamera,
    FakeHistoryService,
    ensure_app,
    make_frame,
    process_events,
    wait_for,
)

from ui.app_context import AppContext
from ui.auth_controller import AuthController
from ui.history_controller import HistoryController
from ui.image_controller import ImageController
from ui.services.detection_service import DetectionService
from ui.services.dialog_service import (
    DialogLevel,
    DialogService,
    classify_message,
)
from ui.services.stats_service import StatsService
from ui.stats_controller import StatsController
from ui.viewmodels.auth_viewmodel import AuthViewModel
from ui.viewmodels.history_viewmodel import HistoryViewModel
from ui.viewmodels.image_viewmodel import ImageViewModel
from ui.viewmodels.statistics_viewmodel import StatisticsViewModel
from ui.viewmodels.vocabulary_viewmodel import VocabularyViewModel
from ui.viewmodels.webcam_viewmodel import WebcamViewModel
from ui.vocabulary_controller import VocabularyController
from ui.webcam_controller import WebcamController


QML_DIR = (
    Path(__file__).resolve().parent.parent
    / "ui"
    / "qml"
)


def build_detection_service(
    engine=None,
    history_service=None,
) -> DetectionService:
    return DetectionService(
        engine if engine is not None else FakeAIEngine(),
        history_service=(
            history_service
            if history_service is not None
            else FakeHistoryService()
        ),
        image_reader=lambda path: make_frame(),
    )


class ControllerIsolationTest(unittest.TestCase):
    """NHIEM VU 1 - Controller khong duoc chua Business Logic."""

    CONTROLLER_MODULES = (
        "ui.image_controller",
        "ui.webcam_controller",
        "ui.vocabulary_controller",
        "ui.history_controller",
        "ui.stats_controller",
        "ui.auth_controller",
    )

    #: Dau hieu con sot Business Logic trong Controller.
    FORBIDDEN_CALLS = (
        "save_history(",
        "get_history(",
        "clear_history(",
        "analyze_frame(",
        "cv2.",
        "VideoCapture",
        "draw_vietnamese_text",
        "Counter(",
        "verify_login(",
        "register_user(",
        "change_password(",
    )

    def _source_without_comments(
        self,
        module_name: str,
    ) -> str:
        import importlib

        module = importlib.import_module(module_name)
        source = inspect.getsource(module)

        # Bo docstring dau module de khong dinh phai vi du trong tai lieu.
        without_docstring = re.sub(
            r'^"""[\s\S]*?"""',
            "",
            source,
            count=1,
        )

        return "\n".join(
            line
            for line in without_docstring.splitlines()
            if not line.strip().startswith("#")
        )

    def test_controllers_have_no_business_logic_calls(self):
        for module_name in self.CONTROLLER_MODULES:
            source = self._source_without_comments(module_name)

            for forbidden in self.FORBIDDEN_CALLS:
                self.assertNotIn(
                    forbidden,
                    source,
                    f"{module_name} van con goi `{forbidden}`",
                )

    def test_controllers_do_not_create_threads(self):
        for module_name in self.CONTROLLER_MODULES:
            source = self._source_without_comments(module_name)

            self.assertNotIn(
                "QThread(",
                source,
                f"{module_name} khong duoc tu tao QThread",
            )

    def test_controllers_do_not_import_ai_or_database(self):
        for module_name in self.CONTROLLER_MODULES:
            source = self._source_without_comments(module_name)

            for forbidden in (
                "from database",
                "from ai.",
                "from ml.",
                "from detection.",
            ):
                self.assertNotIn(
                    forbidden,
                    source,
                    f"{module_name} phai di qua ViewModel/Service",
                )


class ImageControllerTest(unittest.TestCase):
    def setUp(self):
        ensure_app()
        self.history_service = FakeHistoryService()
        self.vm = ImageViewModel(
            build_detection_service(
                history_service=self.history_service
            )
        )
        self.dialog_service = DialogService()
        self.picked_path = "photo.jpg"
        self.controller = ImageController(
            self.vm,
            dialog_service=self.dialog_service,
            file_picker=lambda: self.picked_path,
        )

    def tearDown(self):
        process_events(10)

    def test_choose_image_delegates_to_view_model(self):
        images = []
        paths = []

        self.controller.imageChanged.connect(images.append)
        self.controller.selectedImagePathChanged.connect(
            paths.append
        )

        self.controller.chooseImage()

        self.assertTrue(
            wait_for(lambda: len(images) >= 1)
        )
        self.assertEqual(paths, ["photo.jpg"])
        self.assertEqual(
            self.controller.selectedImagePath,
            "photo.jpg",
        )

    def test_cancelled_file_dialog_does_nothing(self):
        self.picked_path = ""

        paths = []
        self.controller.selectedImagePathChanged.connect(
            paths.append
        )

        self.controller.chooseImage()
        process_events(5)

        self.assertEqual(paths, [])

    def test_detection_relays_view_model_signals(self):
        self.controller.chooseImage()
        self.assertTrue(
            wait_for(
                lambda: self.controller.selectedImagePath
                == "photo.jpg"
            )
        )
        wait_for(lambda: not self.controller.busy)

        results = []
        related = []
        cluster = []
        statuses = []
        finished = []
        busy_values = []

        self.controller.resultsChanged.connect(results.append)
        self.controller.relatedWordsChanged.connect(related.append)
        self.controller.clusterWordsChanged.connect(cluster.append)
        self.controller.statusChanged.connect(statuses.append)
        self.controller.busyChanged.connect(busy_values.append)
        self.controller.detectionFinished.connect(
            lambda: finished.append(1)
        )

        self.controller.detectSelectedImage()

        self.assertTrue(
            wait_for(lambda: len(finished) >= 1)
        )

        self.assertEqual(
            self.controller.detections[0]["english"],
            "laptop",
        )
        self.assertTrue(related[-1])
        self.assertTrue(cluster[-1])
        self.assertIn("Đang nhận diện...", statuses)
        self.assertIn("Phát hiện 1 vật thể.", statuses)
        self.assertIn(True, busy_values)
        self.assertIn(False, busy_values)
        self.assertFalse(self.controller.busy)

    def test_set_user_id_is_forwarded(self):
        self.controller.set_user_id(11)

        self.assertEqual(self.vm.user_id, 11)

    def test_status_is_routed_to_dialog_service(self):
        levels = []
        self.dialog_service.notified.connect(
            lambda level, title, message: levels.append(level)
        )

        self.controller.chooseImage()

        self.assertTrue(
            wait_for(lambda: len(levels) >= 1)
        )
        self.assertIn(
            DialogLevel.LOADING.value,
            levels,
        )


class WebcamControllerTest(unittest.TestCase):
    def setUp(self):
        ensure_app()
        self.camera = FakeCamera(frames=1000)
        self.vm = WebcamViewModel(
            build_detection_service(),
            camera_id=0,
            capture_factory=lambda camera_id: self.camera,
        )
        self.controller = WebcamController(self.vm)

    def tearDown(self):
        self.controller.shutdown()
        process_events(20)

    def test_start_and_stop_relay_running(self):
        running_values = []
        frames = []

        self.controller.runningChanged.connect(
            running_values.append
        )
        self.controller.frameChanged.connect(frames.append)

        self.controller.start()

        self.assertTrue(self.controller.running)
        self.assertTrue(
            wait_for(lambda: len(frames) >= 1)
        )

        self.controller.stop()

        self.assertTrue(
            wait_for(lambda: not self.controller.running)
        )
        self.assertEqual(running_values, [True, False])

    def test_results_are_relayed(self):
        results = []
        self.controller.resultsChanged.connect(results.append)

        self.controller.start()

        self.assertTrue(
            wait_for(lambda: len(results) >= 1)
        )
        self.assertEqual(
            self.controller.detections[0]["english"],
            "laptop",
        )

    def test_set_user_id_is_forwarded(self):
        self.controller.set_user_id(5)

        self.assertEqual(self.vm.user_id, 5)


class HistoryControllerTest(unittest.TestCase):
    def setUp(self):
        ensure_app()
        self.service = FakeHistoryService(
            rows=[
                {
                    "english_word": "laptop",
                    "vietnamese_meaning": "May tinh",
                    "category": "Technology",
                    "confidence": 0.9,
                    "detected_time": None,
                }
            ]
        )
        self.vm = HistoryViewModel(self.service)
        self.controller = HistoryController(self.vm)

    def tearDown(self):
        process_events(10)

    def test_model_is_exposed_for_qml(self):
        self.assertIs(
            self.controller.model,
            self.vm.model,
        )

    def test_refresh_relays_loading_and_status(self):
        self.controller.set_user_id(1)

        loading_values = []
        statuses = []

        self.controller.loadingChanged.connect(
            loading_values.append
        )
        self.controller.statusChanged.connect(statuses.append)

        self.controller.refresh()

        self.assertTrue(
            wait_for(
                lambda: loading_values[-1:] == [False]
            )
        )
        self.assertEqual(loading_values, [True, False])
        self.assertIn("Đã tải 1 bản ghi.", statuses)

    def test_clear_history_relays(self):
        self.controller.set_user_id(2)

        statuses = []
        self.controller.statusChanged.connect(statuses.append)

        self.controller.clearHistory()

        self.assertTrue(
            wait_for(lambda: bool(statuses))
        )
        self.assertEqual(self.service.cleared, [2])


class StatsControllerTest(unittest.TestCase):
    def setUp(self):
        ensure_app()
        self.vm = StatisticsViewModel(
            StatsService(
                FakeHistoryService(
                    rows=[
                        {
                            "english_word": "laptop",
                            "category": "Technology",
                            "confidence": 0.9,
                        }
                    ]
                )
            )
        )
        self.controller = StatsController(self.vm)

    def tearDown(self):
        process_events(10)

    def test_refresh_relays_stats(self):
        payloads = []
        self.controller.statsChanged.connect(payloads.append)

        self.controller.set_user_id(1)
        self.controller.refresh()

        self.assertTrue(
            wait_for(
                lambda: any(
                    item["totalDetections"] == 1
                    for item in payloads
                )
            )
        )

    def test_clear_emits_empty_stats(self):
        payloads = []
        self.controller.statsChanged.connect(payloads.append)

        self.controller.clear()

        self.assertEqual(payloads[-1]["totalDetections"], 0)


class VocabularyControllerTest(unittest.TestCase):
    def setUp(self):
        ensure_app()
        self.engine = FakeAIEngine()
        self.vm = VocabularyViewModel(self.engine)
        self.controller = VocabularyController(self.vm)

    def test_model_is_exposed(self):
        self.assertEqual(
            self.controller.model.rowCount(),
            2,
        )

    def test_related_words_are_relayed(self):
        emitted = []
        self.controller.relatedWordsChanged.connect(
            emitted.append
        )

        self.controller.loadRelatedWords("laptop")

        self.assertEqual(
            emitted[-1][0]["english"],
            "mouse",
        )

    def test_cluster_words_are_relayed(self):
        emitted = []
        self.controller.clusterWordsChanged.connect(
            emitted.append
        )

        self.controller.loadClusterWords("laptop")

        self.assertEqual(
            emitted[-1][0]["english"],
            "keyboard",
        )


class AuthControllerTest(unittest.TestCase):
    def setUp(self):
        ensure_app()

        from test.test_viewmodel import FakeAuthService

        self.service = FakeAuthService()
        self.vm = AuthViewModel(self.service)
        self.controller = AuthController(self.vm)

    def tearDown(self):
        self.vm.shutdown()
        process_events(10)

    def test_login_relays_user_signals(self):
        current_users = []
        session_users = []
        logged_in = []

        self.controller.currentUserChanged.connect(
            current_users.append
        )
        self.controller.userChanged.connect(
            session_users.append
        )
        self.controller.isLoggedInChanged.connect(
            logged_in.append
        )

        self.controller.login("thiet", "secret")

        self.assertTrue(
            wait_for(lambda: self.controller.isLoggedIn)
        )
        self.assertEqual(len(current_users), 1)
        self.assertEqual(len(session_users), 1)
        self.assertEqual(logged_in, [True])

    def test_login_relays_loading_state(self):
        """Sprint 5: QML dua vao `loading` de khoa nut trong luc cho."""
        loading_values = []
        self.controller.loadingChanged.connect(
            loading_values.append
        )

        self.controller.login("thiet", "secret")

        self.assertTrue(self.controller.loading)
        self.assertTrue(
            wait_for(lambda: not self.controller.loading)
        )
        self.assertEqual(loading_values, [True, False])

    def test_failed_login_relays_status(self):
        statuses = []
        self.controller.statusMessageChanged.connect(
            statuses.append
        )

        self.controller.login("thiet", "wrong")

        self.assertTrue(
            wait_for(
                lambda: "Sai tên đăng nhập hoặc mật khẩu."
                in statuses
            )
        )
        self.assertFalse(self.controller.isLoggedIn)


class DialogServiceTest(unittest.TestCase):
    """NHIEM VU 8 - Chuan hoa dialog."""

    def setUp(self):
        ensure_app()
        self.service = DialogService()

    def test_message_classification(self):
        self.assertEqual(
            classify_message("Đang nhận diện..."),
            DialogLevel.LOADING,
        )
        self.assertEqual(
            classify_message("Đăng nhập thành công."),
            DialogLevel.SUCCESS,
        )
        self.assertEqual(
            classify_message("Vui lòng chọn ảnh trước."),
            DialogLevel.WARNING,
        )
        self.assertEqual(
            classify_message("Không đọc được ảnh."),
            DialogLevel.ERROR,
        )

    def test_loading_lifecycle(self):
        shown = []
        hidden = []
        progress = []

        self.service.loadingShown.connect(shown.append)
        self.service.loadingHidden.connect(
            lambda: hidden.append(1)
        )
        self.service.loadingProgressChanged.connect(
            progress.append
        )

        self.service.showLoading("Đang nhận diện...")
        self.service.updateProgress(150)
        self.service.showSuccess("Xong.")

        self.assertEqual(shown, ["Đang nhận diện..."])
        self.assertEqual(progress, [100])
        self.assertEqual(hidden, [1])
        self.assertFalse(self.service.loadingVisible)

    def test_each_level_has_its_own_signal(self):
        errors = []
        warnings = []
        successes = []

        self.service.errorShown.connect(
            lambda title, message: errors.append(message)
        )
        self.service.warningShown.connect(
            lambda title, message: warnings.append(message)
        )
        self.service.successShown.connect(
            lambda title, message: successes.append(message)
        )

        self.service.publish("Không đọc được ảnh.")
        self.service.publish("Vui lòng chọn ảnh trước.")
        self.service.publish("Đăng nhập thành công.")

        self.assertEqual(errors, ["Không đọc được ảnh."])
        self.assertEqual(warnings, ["Vui lòng chọn ảnh trước."])
        self.assertEqual(successes, ["Đăng nhập thành công."])


class QmlContractTest(unittest.TestCase):
    """Bao dam GUI (.qml) khong bi vo sau refactor.

    Test quet truc tiep file .qml, lay ra moi member ma QML dang goi tren
    cac context property, roi kiem tra Controller that su co member do.
    """

    CONTEXT_PROPERTY_NAMES = (
        "imageController",
        "webcamController",
        "vocabController",
        "historyController",
        "statsController",
        "authController",
    )

    @classmethod
    def setUpClass(cls):
        ensure_app()

        cls.context = AppContext.build(
            ai_engine=FakeAIEngine(),
            file_picker=lambda: "",
            history_service=FakeHistoryService(),
            capture_factory=lambda camera_id: FakeCamera(),
        )
        cls.objects = cls.context.context_properties()

        cls.sources = {
            path.name: path.read_text(encoding="utf-8")
            for path in QML_DIR.rglob("*.qml")
        }

    @classmethod
    def tearDownClass(cls):
        cls.context.shutdown()
        process_events(10)

    def test_qml_files_are_found(self):
        self.assertGreater(len(self.sources), 5)

    def test_every_member_used_by_qml_exists(self):
        pattern = re.compile(
            r"\b("
            + "|".join(self.CONTEXT_PROPERTY_NAMES)
            + r")\.(\w+)"
        )

        missing = []

        for file_name, source in self.sources.items():
            for controller_name, member in pattern.findall(source):
                controller = self.objects[controller_name]

                if not hasattr(controller, member):
                    missing.append(
                        f"{file_name}: {controller_name}.{member}"
                    )

        self.assertEqual(
            missing,
            [],
            "QML dang goi member khong con ton tai",
        )

    def test_every_signal_handler_used_by_qml_exists(self):
        connections_pattern = re.compile(
            r"Connections\s*\{\s*target:\s*(\w+)([\s\S]*?)\n    \}",
        )
        handler_pattern = re.compile(
            r"function\s+on([A-Z]\w*)\s*\("
        )

        missing = []

        for file_name, source in self.sources.items():
            for target, body in connections_pattern.findall(source):
                if target not in self.objects:
                    continue

                controller = self.objects[target]

                for handler in handler_pattern.findall(body):
                    signal_name = (
                        handler[0].lower() + handler[1:]
                    )

                    if not hasattr(controller, signal_name):
                        missing.append(
                            f"{file_name}: {target}.{signal_name}"
                        )

        self.assertEqual(
            missing,
            [],
            "QML dang lang nghe signal khong con ton tai",
        )

    def test_context_property_names_are_preserved(self):
        for name in self.CONTEXT_PROPERTY_NAMES:
            self.assertIn(
                name,
                self.objects,
                f"Thieu context property `{name}` ma QML dang dung",
            )


class AppContextTest(unittest.TestCase):
    """NHIEM VU 12 - Kien truc sau Sprint."""

    @classmethod
    def setUpClass(cls):
        ensure_app()

    def setUp(self):
        self.context = AppContext.build(
            ai_engine=FakeAIEngine(),
            file_picker=lambda: "",
            history_service=FakeHistoryService(),
            capture_factory=lambda camera_id: FakeCamera(),
        )

    def tearDown(self):
        self.context.shutdown()
        process_events(10)

    def test_controllers_are_wired_to_view_models(self):
        self.assertIs(
            self.context.image_controller.view_model,
            self.context.image_view_model,
        )
        self.assertIs(
            self.context.webcam_controller.view_model,
            self.context.webcam_view_model,
        )
        self.assertIs(
            self.context.history_controller.view_model,
            self.context.history_view_model,
        )
        self.assertIs(
            self.context.stats_controller.view_model,
            self.context.statistics_view_model,
        )

    def test_services_share_one_history_service(self):
        self.assertIs(
            self.context.detection_service.history_service,
            self.context.history_service,
        )

    def test_login_propagates_user_id_to_every_view_model(self):
        self.context.apply_current_user(
            {
                "id": 7,
                "username": "thiet",
                "fullname": "Thiet",
            }
        )

        self.assertEqual(
            self.context.image_view_model.user_id,
            7,
        )
        self.assertEqual(
            self.context.webcam_view_model.user_id,
            7,
        )
        self.assertEqual(
            self.context.history_view_model.user_id,
            7,
        )
        self.assertEqual(
            self.context.statistics_view_model.user_id,
            7,
        )

    def test_logout_clears_user_id(self):
        self.context.apply_current_user({"id": 7})
        self.context.apply_current_user({})

        self.assertIsNone(
            self.context.image_view_model.user_id
        )
        self.assertIsNone(
            self.context.history_view_model.user_id
        )

    def test_extra_view_model_properties_are_registered(self):
        properties = self.context.context_properties()

        for name in (
            "imageViewModel",
            "webcamViewModel",
            "historyViewModel",
            "statsViewModel",
            "dialogService",
        ):
            self.assertIn(name, properties)


if __name__ == "__main__":
    unittest.main()
