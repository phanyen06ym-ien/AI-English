"""Sprint 3 - Unit test cho ViewModel layer va State machine.

Kiem tra:

1. State machine Idle -> Loading -> Detecting -> Completed -> Error.
2. ViewModel dieu phoi Worker/Service va giu trang thai trinh bay.
3. Signal chuan hoa duoc emit dung thu tu.
4. ViewModel khong goi truc tiep YOLO / KNN / KMeans / database.
"""

from __future__ import annotations

import inspect
import unittest

from test.ui_fakes import (
    FakeAIEngine,
    FakeCamera,
    FakeHistoryService,
    ensure_app,
    make_analysis,
    make_frame,
    process_events,
    wait_for,
)

from ui.services.detection_service import DetectionService
from ui.services.stats_service import StatsService
from ui.state import ALLOWED_TRANSITIONS, UiState, can_transition
from ui.viewmodels.auth_viewmodel import AuthViewModel
from ui.viewmodels.base_viewmodel import BaseViewModel
from ui.viewmodels.history_viewmodel import HistoryViewModel
from ui.viewmodels.image_viewmodel import ImageViewModel
from ui.viewmodels.statistics_viewmodel import StatisticsViewModel
from ui.viewmodels.vocabulary_viewmodel import VocabularyViewModel
from ui.viewmodels.webcam_viewmodel import WebcamViewModel


def build_detection_service(
    engine=None,
    history_service=None,
    image_reader=None,
) -> DetectionService:
    return DetectionService(
        engine if engine is not None else FakeAIEngine(),
        history_service=(
            history_service
            if history_service is not None
            else FakeHistoryService()
        ),
        image_reader=(
            image_reader
            if image_reader is not None
            else (lambda path: make_frame())
        ),
    )


class UiStateTest(unittest.TestCase):
    """NHIEM VU 7 - State Management."""

    def test_busy_states(self):
        self.assertTrue(UiState.LOADING.is_busy())
        self.assertTrue(UiState.DETECTING.is_busy())
        self.assertFalse(UiState.IDLE.is_busy())
        self.assertFalse(UiState.COMPLETED.is_busy())
        self.assertFalse(UiState.ERROR.is_busy())

    def test_terminal_states(self):
        self.assertTrue(UiState.COMPLETED.is_terminal())
        self.assertTrue(UiState.ERROR.is_terminal())
        self.assertFalse(UiState.IDLE.is_terminal())

    def test_happy_path_transitions(self):
        self.assertTrue(
            can_transition(UiState.IDLE, UiState.LOADING)
        )
        self.assertTrue(
            can_transition(UiState.LOADING, UiState.DETECTING)
        )
        self.assertTrue(
            can_transition(UiState.DETECTING, UiState.COMPLETED)
        )
        self.assertTrue(
            can_transition(UiState.COMPLETED, UiState.IDLE)
        )

    def test_error_path_transitions(self):
        self.assertTrue(
            can_transition(UiState.DETECTING, UiState.ERROR)
        )
        self.assertTrue(
            can_transition(UiState.ERROR, UiState.IDLE)
        )

    def test_invalid_transition_is_rejected(self):
        self.assertFalse(
            can_transition(UiState.IDLE, UiState.COMPLETED)
        )
        self.assertFalse(
            can_transition(UiState.ERROR, UiState.COMPLETED)
        )

    def test_every_state_has_a_transition_table(self):
        for state in UiState:
            self.assertIn(state, ALLOWED_TRANSITIONS)


class BaseViewModelTest(unittest.TestCase):
    def setUp(self):
        ensure_app()
        self.vm = BaseViewModel("test_vm")

    def test_initial_state_is_idle(self):
        self.assertEqual(self.vm.state, UiState.IDLE.value)
        self.assertFalse(self.vm.busy)

    def test_state_change_emits_signal(self):
        states = []
        busy_values = []

        self.vm.StateChanged.connect(states.append)
        self.vm.BusyChanged.connect(busy_values.append)

        self.vm.set_state(UiState.DETECTING)

        self.assertEqual(states, ["detecting"])
        self.assertEqual(busy_values, [True])
        self.assertTrue(self.vm.busy)

    def test_invalid_transition_keeps_state(self):
        changed = self.vm.set_state(UiState.COMPLETED)

        self.assertFalse(changed)
        self.assertEqual(self.vm.state, UiState.IDLE.value)

    def test_fail_moves_to_error_and_raises_signal(self):
        errors = []
        self.vm.ErrorRaised.connect(errors.append)

        self.vm.fail("hong roi")

        self.assertEqual(self.vm.state, UiState.ERROR.value)
        self.assertEqual(errors, ["hong roi"])
        self.assertEqual(self.vm.statusMessage, "hong roi")


class ImageViewModelTest(unittest.TestCase):
    def setUp(self):
        ensure_app()
        self.engine = FakeAIEngine()
        self.history_service = FakeHistoryService()
        self.service = build_detection_service(
            self.engine,
            self.history_service,
        )
        self.vm = ImageViewModel(self.service)

    def tearDown(self):
        self.vm.shutdown()
        process_events(10)

    def test_select_image_loads_preview_off_thread(self):
        previews = []
        paths = []
        states = []

        self.vm.PreviewUpdated.connect(previews.append)
        self.vm.SelectedImageChanged.connect(paths.append)
        self.vm.StateChanged.connect(states.append)

        self.vm.selectImage("photo.jpg")

        self.assertTrue(
            wait_for(lambda: len(previews) >= 1)
        )
        self.assertTrue(
            wait_for(lambda: self.vm.state == UiState.IDLE.value)
        )

        self.assertEqual(paths, ["photo.jpg"])
        self.assertEqual(self.vm.selectedImagePath, "photo.jpg")
        self.assertIn("loading", states)

    def test_select_image_failure_moves_to_error(self):
        vm = ImageViewModel(
            build_detection_service(
                image_reader=lambda path: None,
            )
        )
        self.addCleanup(vm.shutdown)

        errors = []
        vm.ErrorRaised.connect(errors.append)

        vm.selectImage("missing.jpg")

        self.assertTrue(
            wait_for(lambda: len(errors) >= 1)
        )
        self.assertEqual(vm.selectedImagePath, "")

    def test_detect_without_selection_warns(self):
        statuses = []
        self.vm.StatusMessageChanged.connect(statuses.append)

        self.vm.detectSelectedImage()

        self.assertEqual(
            statuses,
            ["Vui lòng chọn ảnh trước."],
        )
        self.assertEqual(self.engine.analyze_calls, 0)

    def test_full_detection_flow(self):
        self.vm.set_user_id(42)
        self.vm.selectImage("photo.jpg")
        self.assertTrue(
            wait_for(
                lambda: self.vm.selectedImagePath == "photo.jpg"
            )
        )
        wait_for(lambda: self.vm.state == UiState.IDLE.value)

        started = []
        results = []
        related = []
        cluster = []
        finished = []
        progress = []

        self.vm.DetectionStarted.connect(
            lambda: started.append(1)
        )
        self.vm.DetectionCompleted.connect(results.append)
        self.vm.RelatedWordsUpdated.connect(related.append)
        self.vm.ClusterWordsUpdated.connect(cluster.append)
        self.vm.DetectionFinished.connect(
            lambda: finished.append(1)
        )
        self.vm.ProgressChanged.connect(progress.append)

        self.vm.detectSelectedImage()

        self.assertTrue(
            wait_for(lambda: len(finished) >= 1)
        )

        self.assertEqual(started, [1])
        self.assertEqual(self.vm.state, UiState.IDLE.value)
        self.assertFalse(self.vm.busy)

        self.assertTrue(results)
        detections = results[-1]
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0]["english"], "laptop")

        self.assertNotIn(
            "box",
            detections[0],
            "GUI khong can toa do box",
        )
        self.assertEqual(
            detections[0]["text"],
            "laptop - May tinh xach tay [Technology - Medium] (0.93)",
        )

        self.assertEqual(related[-1][0]["english"], "mouse")
        self.assertEqual(cluster[-1][0]["english"], "keyboard")
        self.assertEqual(progress[-1], 100)

        self.assertEqual(
            self.vm.statusMessage,
            "Phát hiện 1 vật thể.",
        )
        self.assertEqual(
            self.history_service.saved[0][4],
            42,
        )

    def test_detection_failure_emits_detection_failed(self):
        engine = FakeAIEngine(
            analysis=make_analysis(
                success=False,
                message="AI loi",
            )
        )
        vm = ImageViewModel(
            build_detection_service(engine)
        )
        self.addCleanup(vm.shutdown)

        vm.selectImage("photo.jpg")
        self.assertTrue(
            wait_for(
                lambda: vm.selectedImagePath == "photo.jpg"
            )
        )
        wait_for(lambda: vm.state == UiState.IDLE.value)

        failures = []
        errors = []
        finished = []

        vm.DetectionFailed.connect(failures.append)
        vm.ErrorRaised.connect(errors.append)
        vm.DetectionFinished.connect(
            lambda: finished.append(1)
        )

        vm.detectSelectedImage()

        self.assertTrue(
            wait_for(lambda: len(finished) >= 1)
        )
        self.assertEqual(failures, ["AI loi"])
        self.assertEqual(errors, ["AI loi"])

    def test_no_detection_reports_empty_status(self):
        engine = FakeAIEngine(
            analysis=make_analysis(detections=[])
        )
        vm = ImageViewModel(
            build_detection_service(engine)
        )
        self.addCleanup(vm.shutdown)

        vm.selectImage("photo.jpg")
        self.assertTrue(
            wait_for(
                lambda: vm.selectedImagePath == "photo.jpg"
            )
        )
        wait_for(lambda: vm.state == UiState.IDLE.value)

        finished = []
        vm.DetectionFinished.connect(
            lambda: finished.append(1)
        )

        vm.detectSelectedImage()
        self.assertTrue(
            wait_for(lambda: len(finished) >= 1)
        )

        self.assertEqual(
            vm.statusMessage,
            "Không phát hiện vật thể nào.",
        )


class WebcamViewModelTest(unittest.TestCase):
    def setUp(self):
        ensure_app()
        self.camera = FakeCamera(frames=1000)
        self.service = build_detection_service()
        self.vm = WebcamViewModel(
            self.service,
            camera_id=0,
            capture_factory=lambda camera_id: self.camera,
        )

    def tearDown(self):
        self.vm.shutdown()
        process_events(20)

    def test_start_then_stop(self):
        running_values = []
        frames = []

        self.vm.RunningChanged.connect(running_values.append)
        self.vm.FrameUpdated.connect(frames.append)

        self.vm.start()

        self.assertTrue(self.vm.running)
        self.assertEqual(running_values, [True])
        self.assertTrue(
            wait_for(lambda: len(frames) >= 1)
        )

        self.vm.stop()

        self.assertTrue(
            wait_for(lambda: not self.vm.running)
        )
        self.assertEqual(running_values, [True, False])
        self.assertEqual(self.vm.state, UiState.IDLE.value)
        self.assertTrue(self.camera.released)

    def test_stop_without_worker_reports_status(self):
        statuses = []
        self.vm.StatusMessageChanged.connect(statuses.append)

        self.vm.stop()

        self.assertEqual(statuses, ["Webcam đã tắt."])

    def test_start_twice_keeps_one_worker(self):
        self.vm.start()
        running_values = []
        self.vm.RunningChanged.connect(running_values.append)

        self.vm.start()

        self.assertEqual(running_values, [])

    def test_detections_are_exposed(self):
        self.vm.start()

        self.assertTrue(
            wait_for(lambda: len(self.vm.detections) >= 1)
        )
        self.assertEqual(
            self.vm.detections[0]["english"],
            "laptop",
        )


class HistoryViewModelTest(unittest.TestCase):
    ROWS = [
        {
            "english_word": "laptop",
            "vietnamese_meaning": "May tinh",
            "category": "Technology",
            "confidence": 0.9,
            "detected_time": None,
        }
    ]

    def setUp(self):
        ensure_app()
        self.service = FakeHistoryService(
            rows=list(self.ROWS)
        )
        self.vm = HistoryViewModel(self.service)

    def tearDown(self):
        self.vm.shutdown()
        process_events(10)

    def test_refresh_without_user_warns(self):
        statuses = []
        self.vm.StatusMessageChanged.connect(statuses.append)

        self.vm.refresh()

        self.assertEqual(
            statuses,
            ["Vui lòng đăng nhập để xem lịch sử."],
        )

    def test_clear_without_user_warns(self):
        statuses = []
        self.vm.StatusMessageChanged.connect(statuses.append)

        self.vm.clearHistory()

        self.assertEqual(
            statuses,
            ["Vui lòng đăng nhập để xóa lịch sử."],
        )
        self.assertEqual(self.service.cleared, [])

    def test_refresh_fills_model(self):
        self.vm.set_user_id(1)

        updates = []
        loading_values = []

        self.vm.HistoryUpdated.connect(updates.append)
        self.vm.LoadingChanged.connect(loading_values.append)

        self.vm.refresh()

        self.assertTrue(
            wait_for(lambda: len(updates) >= 1)
        )
        wait_for(lambda: loading_values[-1] is False)

        self.assertEqual(self.vm.model.rowCount(), 1)
        self.assertEqual(loading_values, [True, False])
        self.assertEqual(
            self.vm.statusMessage,
            "Đã tải 1 bản ghi.",
        )

    def test_clear_history_calls_service(self):
        self.vm.set_user_id(9)

        updates = []
        self.vm.HistoryUpdated.connect(updates.append)

        self.vm.clearHistory()

        self.assertTrue(
            wait_for(lambda: len(updates) >= 1)
        )
        self.assertEqual(self.service.cleared, [9])
        self.assertEqual(self.vm.model.rowCount(), 0)

    def test_set_user_id_resets_model(self):
        self.vm.set_user_id(1)
        self.vm.refresh()
        wait_for(lambda: self.vm.model.rowCount() == 1)

        self.vm.set_user_id(2)

        self.assertEqual(self.vm.model.rowCount(), 0)

    def test_failure_is_reported(self):
        vm = HistoryViewModel(
            FakeHistoryService(fail=True)
        )
        self.addCleanup(vm.shutdown)
        vm.set_user_id(1)

        failures = []
        vm.HistoryFailed.connect(failures.append)

        vm.refresh()

        self.assertTrue(
            wait_for(lambda: len(failures) >= 1)
        )


class StatisticsViewModelTest(unittest.TestCase):
    ROWS = [
        {
            "english_word": "laptop",
            "category": "Technology",
            "confidence": 0.9,
        },
        {
            "english_word": "mouse",
            "category": "Technology",
            "confidence": 0.7,
        },
    ]

    def setUp(self):
        ensure_app()
        self.history_service = FakeHistoryService(
            rows=list(self.ROWS)
        )
        self.vm = StatisticsViewModel(
            StatsService(self.history_service)
        )

    def tearDown(self):
        self.vm.shutdown()
        process_events(10)

    def test_refresh_without_user_clears(self):
        updates = []
        self.vm.StatisticsUpdated.connect(updates.append)

        self.vm.refresh()

        self.assertEqual(updates[-1]["totalDetections"], 0)

    def test_refresh_computes_statistics(self):
        self.vm.set_user_id(1)

        updates = []
        self.vm.StatisticsUpdated.connect(updates.append)

        self.vm.refresh()

        self.assertTrue(
            wait_for(lambda: len(updates) >= 1)
        )

        stats = updates[-1]
        self.assertEqual(stats["totalDetections"], 2)
        self.assertEqual(stats["uniqueWords"], 2)
        self.assertEqual(
            stats["categories"],
            {"Technology": 2},
        )
        self.assertAlmostEqual(
            stats["averageConfidence"],
            0.8,
        )

    def test_set_user_none_clears(self):
        self.vm.set_user_id(1)

        updates = []
        self.vm.StatisticsUpdated.connect(updates.append)

        self.vm.set_user_id(None)

        self.assertEqual(updates[-1]["totalDetections"], 0)

    def test_failure_clears_and_reports(self):
        vm = StatisticsViewModel(
            StatsService(
                FakeHistoryService(fail=True)
            )
        )
        self.addCleanup(vm.shutdown)
        vm.set_user_id(1)

        failures = []
        vm.StatisticsFailed.connect(failures.append)

        vm.refresh()

        self.assertTrue(
            wait_for(lambda: len(failures) >= 1)
        )
        self.assertEqual(
            vm.statistics["totalDetections"],
            0,
        )


class VocabularyViewModelTest(unittest.TestCase):
    def setUp(self):
        ensure_app()
        self.engine = FakeAIEngine()
        self.vm = VocabularyViewModel(self.engine)

    def test_model_is_filled_from_engine(self):
        self.assertEqual(self.vm.model.rowCount(), 2)

    def test_filter_reduces_rows(self):
        self.vm.model.setFilter("key")

        self.assertEqual(self.vm.model.rowCount(), 1)

        self.vm.model.setFilter("")

        self.assertEqual(self.vm.model.rowCount(), 2)

    def test_related_words_go_through_engine(self):
        emitted = []
        self.vm.RelatedWordsUpdated.connect(emitted.append)

        self.vm.loadRelatedWords("laptop")

        self.assertEqual(
            self.engine.related_calls,
            [("laptop", 3)],
        )
        self.assertEqual(
            emitted[-1][0]["english"],
            "mouse",
        )

    def test_cluster_words_go_through_engine(self):
        emitted = []
        self.vm.ClusterWordsUpdated.connect(emitted.append)

        self.vm.loadClusterWords("laptop")

        self.assertEqual(
            self.engine.cluster_calls,
            ["laptop"],
        )
        self.assertEqual(
            emitted[-1][0]["english"],
            "keyboard",
        )


class FakeAuthService:
    def __init__(self):
        from ui.services.auth_service import AuthResult

        self.AuthResult = AuthResult
        self.calls = []

    def login(self, username, password):
        self.calls.append(("login", username))

        if username == "thiet" and password == "secret":
            return self.AuthResult(
                True,
                "Đăng nhập thành công.",
                {
                    "id": 1,
                    "username": "thiet",
                    "fullname": "Thiet",
                },
            )

        return self.AuthResult(
            False,
            "Sai tên đăng nhập hoặc mật khẩu.",
        )

    def register(self, fullname, username, password, confirm):
        self.calls.append(("register", username))
        return self.AuthResult(True, "Tạo tài khoản thành công. Vui lòng đăng nhập.")

    def change_password(self, user_id, old, new, confirm):
        self.calls.append(("change_password", user_id))
        return self.AuthResult(True, "Đổi mật khẩu thành công.")


class AuthViewModelTest(unittest.TestCase):
    """Sprint 5: xac thuc chay tren thread nen, GUI khong bi chan."""

    def setUp(self):
        ensure_app()
        self.service = FakeAuthService()
        self.vm = AuthViewModel(self.service)

    def tearDown(self):
        self.vm.shutdown()
        process_events(10)

    def _login_and_wait(
        self,
        username="thiet",
        password="secret",
    ) -> None:
        self.vm.login(username, password)
        self.assertTrue(
            wait_for(lambda: not self.vm.loading),
            "Thao tac xac thuc phai ket thuc",
        )

    def test_login_does_not_block_gui_thread(self):
        """NHIEM VU 2 - bam Dang nhap khong duoc lam dung GUI."""
        import time

        started_at = time.perf_counter()
        self.vm.login("thiet", "secret")
        elapsed = time.perf_counter() - started_at

        self.assertLess(
            elapsed,
            0.05,
            "login() phai tra ve ngay, khong cho database",
        )
        self.assertTrue(self.vm.loading)

        wait_for(lambda: not self.vm.loading)

    def test_successful_login_sets_user(self):
        users = []
        logged_in = []
        succeeded = []
        loading_values = []

        self.vm.UserChanged.connect(users.append)
        self.vm.LoggedInChanged.connect(logged_in.append)
        self.vm.LoadingChanged.connect(loading_values.append)
        self.vm.LoginSucceeded.connect(
            lambda: succeeded.append(1)
        )

        self._login_and_wait()

        self.assertTrue(self.vm.isLoggedIn)
        self.assertEqual(logged_in, [True])
        self.assertEqual(succeeded, [1])
        self.assertEqual(users[-1]["username"], "thiet")
        self.assertEqual(loading_values, [True, False])

    def test_failed_login_keeps_logged_out(self):
        self._login_and_wait(password="wrong")

        self.assertFalse(self.vm.isLoggedIn)
        self.assertEqual(
            self.vm.statusMessage,
            "Sai tên đăng nhập hoặc mật khẩu.",
        )

    def test_second_submit_is_ignored_while_busy(self):
        self.vm.login("thiet", "secret")
        self.vm.login("thiet", "secret")

        wait_for(lambda: not self.vm.loading)

        login_calls = [
            call
            for call in self.service.calls
            if call[0] == "login"
        ]
        self.assertEqual(
            len(login_calls),
            1,
            "Bam hai lan chi duoc chay mot lan",
        )

    def test_logout_clears_user(self):
        self._login_and_wait()

        logged_in = []
        self.vm.LoggedInChanged.connect(logged_in.append)

        self.vm.logout()

        self.assertFalse(self.vm.isLoggedIn)
        self.assertEqual(self.vm.currentUser, {})
        self.assertEqual(logged_in, [False])

    def test_change_password_uses_current_user_id(self):
        self._login_and_wait()

        changed = []
        self.vm.PasswordChanged.connect(
            lambda: changed.append(1)
        )

        self.vm.changePassword("old", "newpass", "newpass")
        self.assertTrue(
            wait_for(lambda: len(changed) >= 1)
        )

        self.assertIn(
            ("change_password", 1),
            self.service.calls,
        )


class ViewModelIsolationTest(unittest.TestCase):
    """ViewModel khong duoc goi thang AI hoac database."""

    VIEWMODEL_MODULES = (
        "ui.viewmodels.image_viewmodel",
        "ui.viewmodels.webcam_viewmodel",
        "ui.viewmodels.history_viewmodel",
        "ui.viewmodels.statistics_viewmodel",
        "ui.viewmodels.auth_viewmodel",
    )

    def test_viewmodels_do_not_import_database_or_ai_internals(self):
        import importlib

        for module_name in self.VIEWMODEL_MODULES:
            module = importlib.import_module(module_name)
            source = inspect.getsource(module)

            self.assertNotIn(
                "from database",
                source,
                f"{module_name} phai di qua Service",
            )
            for forbidden in (
                "from ml.",
                "from detection.",
                "ObjectDetector",
            ):
                self.assertNotIn(
                    forbidden,
                    source,
                    f"{module_name} khong duoc goi AI truc tiep",
                )

    def test_viewmodels_do_not_import_qtwidgets(self):
        import importlib

        for module_name in self.VIEWMODEL_MODULES:
            module = importlib.import_module(module_name)
            source = inspect.getsource(module)

            self.assertNotIn(
                "QtWidgets",
                source,
                f"{module_name} khong duoc tao widget",
            )


if __name__ == "__main__":
    unittest.main()
