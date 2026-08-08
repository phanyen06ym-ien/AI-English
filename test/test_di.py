"""Sprint 6 - Unit test cho Dependency Injection.

Kiem tra:

1. `AppContext.build(config=...)` day cau hinh xuong MOI tang.
2. Doi cau hinh la doi hanh vi that su, khong phai chi doi mot con so vo dung.
3. Hai `AppContext` voi hai cau hinh khac nhau song song duoc trong cung tien trinh.
4. Thanh phan nhan phu thuoc qua constructor, khong doc bien toan cuc.
5. Khong con module nao doc `os.getenv()` truc tiep ngoai tang config.
"""

from __future__ import annotations

import inspect
import re
import unittest

from test.ui_fakes import (
    FakeAIEngine,
    FakeCamera,
    FakeHistoryService,
    ensure_app,
    process_events,
)

from config import AppConfig, Environment, load_test_config
from config.schema import (
    AIConfig,
    CameraConfig,
    DatabaseConfig,
    HistoryConfig,
    ThreadConfig,
    UIConfig,
)
from ui.app_context import AppContext


def build_context(
    config: AppConfig | None = None,
) -> AppContext:
    """Cay phu thuoc day du, khong cham YOLO / camera / database that."""
    return AppContext.build(
        config=config if config is not None else load_test_config(),
        ai_engine=FakeAIEngine(),
        file_picker=lambda: "",
        history_service=FakeHistoryService(),
        capture_factory=lambda camera_id: FakeCamera(),
    )


class ConfigPropagationTest(unittest.TestCase):
    """Cau hinh phai di het xuong tung tang."""

    def setUp(self):
        ensure_app()
        self.contexts: list[AppContext] = []

    def tearDown(self):
        for context in self.contexts:
            context.shutdown()
        process_events(10)

    def _build(self, config=None) -> AppContext:
        context = build_context(config)
        self.contexts.append(context)
        return context

    def test_context_keeps_the_config(self):
        config = load_test_config()
        context = self._build(config)

        self.assertIs(context.config, config)
        self.assertIs(
            context.config.environment,
            Environment.TESTING,
        )

    def test_camera_config_reaches_view_model(self):
        config = load_test_config().with_overrides(
            camera=CameraConfig(
                camera_id=7,
                inference_interval_seconds=0.5,
                max_frames_in_flight=5,
            )
        )
        context = self._build(config)

        self.assertEqual(
            context.webcam_view_model._camera_id,
            7,
        )

    def test_camera_config_reaches_worker(self):
        config = load_test_config().with_overrides(
            camera=CameraConfig(
                camera_id=3,
                inference_interval_seconds=0.75,
                max_frames_in_flight=6,
            )
        )
        context = self._build(config)

        context.webcam_view_model.start()

        try:
            worker = context.webcam_view_model._worker

            self.assertIsNotNone(worker)
            self.assertEqual(
                worker._inference_interval_seconds,
                0.75,
            )
            self.assertEqual(
                worker.frame_gate.max_in_flight,
                6,
            )
        finally:
            context.webcam_view_model.shutdown()
            process_events(10)

    def test_history_config_reaches_service(self):
        """Dung `HistoryService` that (repository gia) de doc duoc `.config`."""
        from test.db_fakes import FakeCursorFactory
        from database.repositories.history_repository import (
            HistoryRepository,
        )
        from ui.services.history_service import HistoryService

        history_config = HistoryConfig(
            cooldown_seconds=12.0,
            page_limit=25,
            stats_limit=99,
        )
        config = load_test_config().with_overrides(
            history=history_config
        )

        context = AppContext.build(
            config=config,
            ai_engine=FakeAIEngine(),
            file_picker=lambda: "",
            history_repository=HistoryRepository(
                cursor_factory=FakeCursorFactory(results=[[]]),
                config=history_config,
            ),
            capture_factory=lambda camera_id: FakeCamera(),
        )
        self.contexts.append(context)

        self.assertEqual(
            context.history_service.config.cooldown_seconds,
            12.0,
        )
        self.assertEqual(
            context.history_service.page_limit,
            25,
        )
        self.assertEqual(
            context.stats_service.stats_limit,
            99,
        )

    def test_ai_config_reaches_vocabulary_view_model(self):
        config = load_test_config().with_overrides(
            ai=AIConfig(related_words_count=8)
        )
        context = self._build(config)

        context.vocabulary_view_model.loadRelatedWords("laptop")

        self.assertEqual(
            context.ai_engine.related_calls,
            [("laptop", 8)],
        )

    def test_ui_config_reaches_annotation_service(self):
        config = load_test_config().with_overrides(
            ui=UIConfig(
                image_box_color=(1, 2, 3),
                image_label_size=99,
            )
        )
        context = self._build(config)

        annotator = context.detection_service._image_annotator

        self.assertEqual(annotator.box_color, (1, 2, 3))
        self.assertEqual(annotator.label_size, 99)

    def test_thread_config_used_at_shutdown(self):
        config = load_test_config().with_overrides(
            threads=ThreadConfig(dispose_timeout_ms=1500)
        )
        context = self._build(config)

        self.assertEqual(
            context.config.threads.dispose_timeout_ms,
            1500,
        )

        context.shutdown()

    def test_database_config_is_applied_to_connection_layer(self):
        from database import connection

        config = load_test_config().with_overrides(
            database=DatabaseConfig(
                host="db.test.local",
                user="tester",
                password="secret",
                pool_max_connections=4,
            )
        )
        self._build(config)

        try:
            current = connection.current_config()

            self.assertEqual(current.host, "db.test.local")
            self.assertEqual(current.pool_max_connections, 4)
        finally:
            connection.configure(DatabaseConfig())
            connection.close_pool()


class ConfigChangesBehaviourTest(unittest.TestCase):
    """Doi cau hinh phai doi HANH VI, khong chi doi con so."""

    def test_cooldown_changes_history_policy(self):
        from ui.services.history_service import HistoryRecordPolicy

        strict = HistoryRecordPolicy.from_config(
            AIConfig(confidence=0.5),
            HistoryConfig(cooldown_seconds=10.0),
        )
        loose = HistoryRecordPolicy.from_config(
            AIConfig(confidence=0.5),
            HistoryConfig(cooldown_seconds=1.0),
        )

        for policy in (strict, loose):
            self.assertTrue(
                policy.should_record("laptop", 0.9, 100.0)
            )
            policy.mark_recorded("laptop", 100.0)

        self.assertFalse(
            strict.should_record("laptop", 0.9, 105.0)
        )
        self.assertTrue(
            loose.should_record("laptop", 0.9, 105.0)
        )

    def test_confidence_changes_history_policy(self):
        from ui.services.history_service import HistoryRecordPolicy

        permissive = HistoryRecordPolicy.from_config(
            AIConfig(confidence=0.3),
            HistoryConfig(),
        )
        strict = HistoryRecordPolicy.from_config(
            AIConfig(confidence=0.9),
            HistoryConfig(),
        )

        self.assertTrue(
            permissive.should_record("laptop", 0.5, 100.0)
        )
        self.assertFalse(
            strict.should_record("laptop", 0.5, 100.0)
        )

    def test_query_limit_changes_repository_clamp(self):
        from test.db_fakes import FakeCursorFactory
        from database.repositories.history_repository import (
            HistoryRepository,
        )

        factory = FakeCursorFactory(results=[[]])
        repository = HistoryRepository(
            cursor_factory=factory,
            config=HistoryConfig(
                min_query_limit=1,
                max_query_limit=10,
            ),
        )

        repository.list_by_user(user_id=1, limit=9999)

        self.assertEqual(
            factory.last_parameters(),
            (1, 10),
            "Gioi han phai bi ep ve max_query_limit cua config",
        )

    def test_page_limit_is_used_when_caller_omits_it(self):
        from test.db_fakes import FakeCursorFactory
        from database.repositories.history_repository import (
            HistoryRepository,
        )
        from ui.services.history_service import HistoryService

        factory = FakeCursorFactory(results=[[]])
        config = HistoryConfig(page_limit=42)
        service = HistoryService(
            repository=HistoryRepository(
                cursor_factory=factory,
                config=config,
            ),
            config=config,
        )

        service.load_rows(user_id=1)

        self.assertEqual(
            factory.last_parameters(),
            (1, 42),
        )

    def test_annotation_colors_change_output_config(self):
        from ui.services.annotation_service import AnnotationService

        service = AnnotationService.for_webcam(
            UIConfig(
                webcam_box_color=(10, 20, 30),
                webcam_label_size=11,
            )
        )

        self.assertEqual(service.box_color, (10, 20, 30))
        self.assertEqual(service.label_size, 11)

    def test_min_password_length_from_config(self):
        from ui.services.auth_service import MIN_PASSWORD_LENGTH

        self.assertEqual(
            MIN_PASSWORD_LENGTH,
            UIConfig.min_password_length,
        )


class IsolatedContextTest(unittest.TestCase):
    """Hai cau hinh khac nhau phai song song duoc."""

    def setUp(self):
        ensure_app()

    def test_two_contexts_do_not_share_config(self):
        first = build_context(
            load_test_config().with_overrides(
                camera=CameraConfig(camera_id=1)
            )
        )
        second = build_context(
            load_test_config().with_overrides(
                camera=CameraConfig(camera_id=2)
            )
        )

        try:
            self.assertEqual(
                first.webcam_view_model._camera_id,
                1,
            )
            self.assertEqual(
                second.webcam_view_model._camera_id,
                2,
            )
            self.assertIsNot(first.config, second.config)
            self.assertIsNot(
                first.history_service,
                second.history_service,
            )
        finally:
            first.shutdown()
            second.shutdown()
            process_events(10)

    def test_contexts_do_not_share_view_models(self):
        first = build_context()
        second = build_context()

        try:
            self.assertIsNot(
                first.image_view_model,
                second.image_view_model,
            )
            self.assertIsNot(
                first.auth_view_model,
                second.auth_view_model,
            )
        finally:
            first.shutdown()
            second.shutdown()
            process_events(10)


class ConstructorInjectionTest(unittest.TestCase):
    """Thanh phan phai nhan phu thuoc qua constructor."""

    COMPONENTS = (
        ("ui.services.history_service", "HistoryService"),
        ("ui.services.stats_service", "StatsService"),
        ("ui.services.auth_service", "AuthService"),
        ("ui.services.detection_service", "DetectionService"),
        ("ui.viewmodels.webcam_viewmodel", "WebcamViewModel"),
        ("ui.viewmodels.vocabulary_viewmodel", "VocabularyViewModel"),
        ("ui.workers.webcam_worker", "WebcamWorker"),
        (
            "database.repositories.history_repository",
            "HistoryRepository",
        ),
    )

    def test_every_component_accepts_config_or_dependencies(self):
        import importlib

        for module_name, class_name in self.COMPONENTS:
            module = importlib.import_module(module_name)
            component = getattr(module, class_name)
            parameters = inspect.signature(
                component.__init__
            ).parameters

            injectable = [
                name
                for name in parameters
                if name != "self"
            ]

            self.assertTrue(
                injectable,
                f"{class_name} phai nhan phu thuoc qua constructor",
            )

    def test_config_bearing_components_accept_a_config(self):
        import importlib

        expected = (
            ("ui.services.history_service", "HistoryService"),
            ("ui.services.stats_service", "StatsService"),
            ("ui.viewmodels.webcam_viewmodel", "WebcamViewModel"),
            (
                "ui.viewmodels.vocabulary_viewmodel",
                "VocabularyViewModel",
            ),
            (
                "database.repositories.history_repository",
                "HistoryRepository",
            ),
        )

        for module_name, class_name in expected:
            module = importlib.import_module(module_name)
            component = getattr(module, class_name)
            parameters = inspect.signature(
                component.__init__
            ).parameters

            self.assertIn(
                "config",
                parameters,
                f"{class_name} phai nhan `config`",
            )


class NoScatteredEnvReadTest(unittest.TestCase):
    """Chi tang `config/` duoc doc bien moi truong."""

    #: Module duoc phep doc `os.getenv()`.
    ALLOWED = {
        "config.loader",
        "config.environment",
        # Doc truc tiep khi chua co config duoc tiem (che do tuong thich).
        "database.connection",
        # Co bat/tat do hieu nang, khong phai cau hinh nghiep vu.
        "utils.perf_monitor",
        # GHI (khong doc) bien QT_QUICK_CONTROLS_STYLE tu gia tri lay o config.
        # Qt chi doc bien nay mot lan luc nap thu vien nen bat buoc phai dat
        # truoc khi import PySide6.
        "ui.main_qt",
    }

    MODULES = (
        "ui.app_context",
        "ui.main_qt",
        "ui.services.history_service",
        "ui.services.stats_service",
        "ui.services.auth_service",
        "ui.services.detection_service",
        "ui.services.annotation_service",
        "ui.workers.webcam_worker",
        "ui.workers.image_worker",
        "ui.workers.lifecycle",
        "ui.viewmodels.webcam_viewmodel",
        "ui.viewmodels.vocabulary_viewmodel",
        "database.repositories.history_repository",
        "database.repositories.user_repository",
        "database.repositories.base",
        "utils.password",
    )

    def test_no_direct_env_read_outside_config_layer(self):
        import importlib

        offenders = []

        for module_name in self.MODULES:
            if module_name in self.ALLOWED:
                continue

            module = importlib.import_module(module_name)
            source = inspect.getsource(module)

            if re.search(r"os\.getenv|os\.environ", source):
                offenders.append(module_name)

        self.assertEqual(
            offenders,
            [],
            "Chi tang config/ duoc doc bien moi truong",
        )

    def test_no_hardcoded_tuning_numbers_left(self):
        """Cac magic number cua NHIEM VU 5 phai lay tu config."""
        import importlib

        checks = (
            ("ui.workers.webcam_worker", "INFERENCE_INTERVAL_SECONDS"),
            ("ui.workers.backpressure", "DEFAULT_MAX_IN_FLIGHT"),
            ("ui.workers.lifecycle", "DEFAULT_DISPOSE_TIMEOUT_MS"),
            ("ui.services.history_service", "HISTORY_COOLDOWN_SECONDS"),
            ("ui.services.history_service", "HISTORY_PAGE_LIMIT"),
            ("ui.services.stats_service", "STATS_HISTORY_LIMIT"),
        )

        for module_name, constant in checks:
            module = importlib.import_module(module_name)
            source = inspect.getsource(module)

            pattern = re.compile(
                rf"^{constant}\s*=\s*(.+)$",
                re.MULTILINE,
            )
            match = pattern.search(source)

            self.assertIsNotNone(
                match,
                f"Khong tim thay {constant} trong {module_name}",
            )
            self.assertIn(
                "Config",
                match.group(1),
                f"{constant} phai lay tu config, dang la {match.group(1)!r}",
            )


class TestEnvironmentSafetyTest(unittest.TestCase):
    """Moi truong `testing` khong duoc cham database that."""

    def test_test_config_forbids_real_database(self):
        config = load_test_config()

        self.assertFalse(
            config.environment.allows_database
        )

    def test_test_config_has_no_credentials(self):
        config = load_test_config()

        self.assertFalse(config.database.is_configured)
        self.assertEqual(config.database.password, "")


if __name__ == "__main__":
    unittest.main()
