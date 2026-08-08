"""Sprint 6 - Unit test cho tang cau hinh.

Kiem tra:

1. Gia tri mac dinh BANG DUNG gia tri dang chay truoc Sprint 6 (khong doi hanh vi).
2. Bien moi truong ghi de duoc gia tri mac dinh.
3. Gia tri sai kieu khong lam sap ung dung; gia tri vo ly bi chan khi khoi dong.
4. Mat khau database khong bao gio ro ri ra log.
5. `utils/config.py` (shim) van xuat du hang so cho cac module AI cu.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent),
)

from config import (  # noqa: E402
    AppConfig,
    ConfigValidationError,
    Environment,
    load_config,
    load_test_config,
)
from config.errors import MissingConfigError  # noqa: E402
from config.loader import (  # noqa: E402
    build_ai_config,
    build_camera_config,
    build_database_config,
    build_history_config,
    build_thread_config,
)
from config.schema import (  # noqa: E402
    AIConfig,
    CameraConfig,
    DatabaseConfig,
    HistoryConfig,
    LoggingConfig,
    PathConfig,
    ThreadConfig,
    UIConfig,
)


def clean_env(**overrides):
    """Chay voi mot moi truong sach, chi co bien duoc chi dinh."""
    managed = [
        "AI_ENGLISH_ENV",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "DB_POOL_MIN",
        "DB_POOL_MAX",
        "AI_CONFIDENCE",
        "AI_IMAGE_SIZE",
        "AI_MODEL_FILE",
        "AI_RELATED_WORDS",
        "CAMERA_ID",
        "CAMERA_INFERENCE_INTERVAL",
        "CAMERA_MAX_FRAMES_IN_FLIGHT",
        "HISTORY_COOLDOWN_SECONDS",
        "HISTORY_PAGE_LIMIT",
        "HISTORY_STATS_LIMIT",
        "HISTORY_WRITE_QUEUE_SIZE",
        "THREAD_DISPOSE_TIMEOUT_MS",
        "THREAD_POLL_INTERVAL",
        "LOG_LEVEL",
        "AI_ENGLISH_PERF",
    ]

    environment = {
        name: os.environ[name]
        for name in managed
        if name in os.environ
    }
    for name in environment:
        pass

    patched = dict(os.environ)
    for name in managed:
        patched.pop(name, None)
    patched.update(overrides)

    return mock.patch.dict(
        os.environ,
        patched,
        clear=True,
    )


class DefaultValueTest(unittest.TestCase):
    """Gia tri mac dinh phai giong het truoc Sprint 6."""

    def test_ai_defaults_unchanged(self):
        config = AIConfig()

        self.assertEqual(config.confidence, 0.5)
        self.assertEqual(config.image_size, 640)
        self.assertEqual(config.model_file_name, "best.pt")
        self.assertEqual(config.related_words_count, 3)

    def test_camera_defaults_unchanged(self):
        config = CameraConfig()

        self.assertEqual(config.camera_id, 0)
        self.assertEqual(
            config.inference_interval_seconds,
            0.25,
        )
        self.assertEqual(config.max_frames_in_flight, 2)

    def test_history_defaults_unchanged(self):
        config = HistoryConfig()

        self.assertEqual(config.cooldown_seconds, 5.0)
        self.assertEqual(config.page_limit, 200)
        self.assertEqual(config.stats_limit, 500)
        self.assertEqual(config.min_query_limit, 1)
        self.assertEqual(config.max_query_limit, 500)
        self.assertEqual(config.write_queue_size, 20)

    def test_thread_defaults_unchanged(self):
        config = ThreadConfig()

        self.assertEqual(config.dispose_timeout_ms, 3000)
        self.assertEqual(config.poll_interval_seconds, 0.1)

    def test_database_pool_defaults_unchanged(self):
        config = DatabaseConfig()

        self.assertEqual(config.pool_min_connections, 1)
        self.assertEqual(config.pool_max_connections, 8)

    def test_ui_defaults_unchanged(self):
        config = UIConfig()

        self.assertEqual(config.min_password_length, 6)
        self.assertEqual(config.image_box_color, (0, 255, 0))
        self.assertEqual(config.image_label_size, 28)
        self.assertEqual(config.webcam_box_color, (0, 180, 0))
        self.assertEqual(config.webcam_label_size, 24)
        self.assertEqual(config.application_name, "AI-English")

    def test_paths_match_project_layout(self):
        paths = PathConfig()

        self.assertTrue(paths.project_root.exists())
        self.assertEqual(paths.assets_dir.name, "assets")
        self.assertEqual(paths.models_dir.name, "models")
        self.assertEqual(
            paths.font_path.name,
            "NotoSans-Regular.ttf",
        )
        self.assertEqual(paths.audio_file.name, "speech.mp3")
        self.assertTrue(paths.qml_dir.exists())


class ModuleConstantsMatchConfigTest(unittest.TestCase):
    """Hang so module phai lay tu config - chi mot nguon su that."""

    def test_worker_constants(self):
        from ui.workers.backpressure import DEFAULT_MAX_IN_FLIGHT
        from ui.workers.lifecycle import DEFAULT_DISPOSE_TIMEOUT_MS
        from ui.workers.webcam_worker import (
            HISTORY_POLL_SECONDS,
            HISTORY_QUEUE_MAX_SIZE,
            INFERENCE_INTERVAL_SECONDS,
        )

        self.assertEqual(
            DEFAULT_MAX_IN_FLIGHT,
            CameraConfig.max_frames_in_flight,
        )
        self.assertEqual(
            DEFAULT_DISPOSE_TIMEOUT_MS,
            ThreadConfig.dispose_timeout_ms,
        )
        self.assertEqual(
            INFERENCE_INTERVAL_SECONDS,
            CameraConfig.inference_interval_seconds,
        )
        self.assertEqual(
            HISTORY_QUEUE_MAX_SIZE,
            HistoryConfig.write_queue_size,
        )
        self.assertEqual(
            HISTORY_POLL_SECONDS,
            ThreadConfig.poll_interval_seconds,
        )

    def test_service_constants(self):
        from ui.services.auth_service import MIN_PASSWORD_LENGTH
        from ui.services.history_service import (
            HISTORY_COOLDOWN_SECONDS,
            HISTORY_PAGE_LIMIT,
        )
        from ui.services.stats_service import STATS_HISTORY_LIMIT

        self.assertEqual(
            HISTORY_COOLDOWN_SECONDS,
            HistoryConfig.cooldown_seconds,
        )
        self.assertEqual(
            HISTORY_PAGE_LIMIT,
            HistoryConfig.page_limit,
        )
        self.assertEqual(
            STATS_HISTORY_LIMIT,
            HistoryConfig.stats_limit,
        )
        self.assertEqual(
            MIN_PASSWORD_LENGTH,
            UIConfig.min_password_length,
        )

    def test_repository_limits(self):
        from database.repositories.history_repository import (
            MAX_LIMIT,
            MIN_LIMIT,
        )

        self.assertEqual(MIN_LIMIT, HistoryConfig.min_query_limit)
        self.assertEqual(MAX_LIMIT, HistoryConfig.max_query_limit)

    def test_legacy_utils_config_shim(self):
        """Cac module AI cu doc hang so o day - khong duoc mat."""
        import utils.config as legacy

        for name in (
            "PROJECT_ROOT",
            "ASSETS_DIR",
            "MODELS_DIR",
            "DATASET_DIR",
            "MODEL_PATH",
            "CONFIDENCE",
            "IMAGE_SIZE",
            "CAMERA_ID",
            "LEVELS",
            "DEFAULT_LANGUAGE",
            "FONT_PATH",
            "AUDIO_DIR",
            "AUDIO_FILE",
            "TEST_IMAGE_PATH",
        ):
            self.assertTrue(
                hasattr(legacy, name),
                f"utils.config.{name} phai con ton tai",
            )

        self.assertEqual(legacy.CONFIDENCE, 0.5)
        self.assertEqual(legacy.IMAGE_SIZE, 640)
        self.assertEqual(legacy.MODEL_PATH.name, "best.pt")
        self.assertEqual(
            legacy.LEVELS,
            {
                "Easy": "Cơ bản",
                "Medium": "Trung bình",
                "Hard": "Nâng cao",
            },
        )


class EnvironmentTest(unittest.TestCase):
    def test_parse_aliases(self):
        self.assertIs(
            Environment.parse("dev"),
            Environment.DEVELOPMENT,
        )
        self.assertIs(
            Environment.parse("PRODUCTION"),
            Environment.PRODUCTION,
        )
        self.assertIs(
            Environment.parse("  test  "),
            Environment.TESTING,
        )

    def test_unknown_falls_back_to_development(self):
        self.assertIs(
            Environment.parse("khong-biet"),
            Environment.DEVELOPMENT,
        )
        self.assertIs(
            Environment.parse(None),
            Environment.DEVELOPMENT,
        )

    def test_log_level_per_environment(self):
        self.assertEqual(
            Environment.DEVELOPMENT.default_log_level,
            "INFO",
        )
        self.assertEqual(
            Environment.TESTING.default_log_level,
            "ERROR",
        )
        self.assertEqual(
            Environment.PRODUCTION.default_log_level,
            "WARNING",
        )

    def test_testing_environment_forbids_real_database(self):
        self.assertFalse(
            Environment.TESTING.allows_database
        )
        self.assertTrue(
            Environment.DEVELOPMENT.allows_database
        )
        self.assertTrue(
            Environment.PRODUCTION.allows_database
        )

    def test_current_reads_env_variable(self):
        with clean_env(AI_ENGLISH_ENV="production"):
            self.assertIs(
                Environment.current(),
                Environment.PRODUCTION,
            )


class EnvironmentOverrideTest(unittest.TestCase):
    """Bien moi truong phai ghi de duoc gia tri mac dinh."""

    def test_ai_override(self):
        with clean_env(
            AI_CONFIDENCE="0.75",
            AI_IMAGE_SIZE="320",
            AI_RELATED_WORDS="5",
        ):
            config = build_ai_config()

        self.assertEqual(config.confidence, 0.75)
        self.assertEqual(config.image_size, 320)
        self.assertEqual(config.related_words_count, 5)

    def test_camera_override(self):
        with clean_env(
            CAMERA_ID="2",
            CAMERA_INFERENCE_INTERVAL="0.5",
            CAMERA_MAX_FRAMES_IN_FLIGHT="4",
        ):
            config = build_camera_config()

        self.assertEqual(config.camera_id, 2)
        self.assertEqual(
            config.inference_interval_seconds,
            0.5,
        )
        self.assertEqual(config.max_frames_in_flight, 4)

    def test_history_override(self):
        with clean_env(
            HISTORY_COOLDOWN_SECONDS="10",
            HISTORY_PAGE_LIMIT="50",
        ):
            config = build_history_config()

        self.assertEqual(config.cooldown_seconds, 10.0)
        self.assertEqual(config.page_limit, 50)

    def test_thread_override(self):
        with clean_env(THREAD_DISPOSE_TIMEOUT_MS="5000"):
            config = build_thread_config()

        self.assertEqual(config.dispose_timeout_ms, 5000)

    def test_database_override(self):
        with clean_env(
            DB_HOST="db.example.com",
            DB_PORT="6543",
            DB_POOL_MAX="16",
        ):
            config = build_database_config()

        self.assertEqual(config.host, "db.example.com")
        self.assertEqual(config.port, "6543")
        self.assertEqual(config.pool_max_connections, 16)

    def test_empty_variable_uses_default(self):
        with clean_env(AI_CONFIDENCE=""):
            config = build_ai_config()

        self.assertEqual(config.confidence, 0.5)

    def test_bad_type_falls_back_to_default(self):
        """Gia tri sai kieu KHONG duoc lam sap ung dung."""
        with clean_env(
            AI_CONFIDENCE="rat-cao",
            AI_IMAGE_SIZE="to",
        ):
            config = build_ai_config()

        self.assertEqual(config.confidence, 0.5)
        self.assertEqual(config.image_size, 640)


class ValidationTest(unittest.TestCase):
    """Gia tri vo ly phai bi chan NGAY khi khoi dong."""

    def test_confidence_out_of_range(self):
        with self.assertRaises(ConfigValidationError) as caught:
            AIConfig(confidence=5.0).validate()

        self.assertEqual(caught.exception.field, "ai.confidence")

    def test_confidence_zero_rejected(self):
        with self.assertRaises(ConfigValidationError):
            AIConfig(confidence=0.0).validate()

    def test_image_size_must_be_multiple_of_32(self):
        with self.assertRaises(ConfigValidationError):
            AIConfig(image_size=100).validate()

        AIConfig(image_size=320).validate()

    def test_negative_camera_id(self):
        with self.assertRaises(ConfigValidationError):
            CameraConfig(camera_id=-1).validate()

    def test_zero_inference_interval(self):
        with self.assertRaises(ConfigValidationError):
            CameraConfig(
                inference_interval_seconds=0
            ).validate()

    def test_frames_in_flight_must_be_positive(self):
        with self.assertRaises(ConfigValidationError):
            CameraConfig(max_frames_in_flight=0).validate()

    def test_pool_max_below_min(self):
        with self.assertRaises(ConfigValidationError):
            DatabaseConfig(
                pool_min_connections=5,
                pool_max_connections=2,
            ).validate()

    def test_non_numeric_port(self):
        with self.assertRaises(ConfigValidationError):
            DatabaseConfig(port="abc").validate()

    def test_page_limit_cannot_exceed_max_query_limit(self):
        with self.assertRaises(ConfigValidationError):
            HistoryConfig(page_limit=1000).validate()

    def test_stats_limit_cannot_exceed_max_query_limit(self):
        with self.assertRaises(ConfigValidationError):
            HistoryConfig(stats_limit=1000).validate()

    def test_negative_cooldown(self):
        with self.assertRaises(ConfigValidationError):
            HistoryConfig(cooldown_seconds=-1).validate()

    def test_dispose_timeout_too_small(self):
        with self.assertRaises(ConfigValidationError):
            ThreadConfig(dispose_timeout_ms=10).validate()

    def test_bad_log_level(self):
        with self.assertRaises(ConfigValidationError):
            LoggingConfig(level="VERBOSE").validate()

    def test_bad_color(self):
        with self.assertRaises(ConfigValidationError):
            UIConfig(image_box_color=(0, 999, 0)).validate()

    def test_error_message_names_the_field(self):
        try:
            AIConfig(confidence=9.0).validate()
        except ConfigValidationError as error:
            self.assertIn("ai.confidence", str(error))
            self.assertIn("9.0", str(error))
        else:
            self.fail("Phai nem ConfigValidationError")

    def test_valid_config_passes(self):
        self.assertIsInstance(
            AppConfig().validate(),
            AppConfig,
        )


class SecretHandlingTest(unittest.TestCase):
    """Mat khau database KHONG duoc ro ri ra log."""

    SECRET = "sieu-bi-mat-12345"

    def _config(self) -> AppConfig:
        return AppConfig(
            database=DatabaseConfig(
                host="db.example.com",
                user="admin",
                password=self.SECRET,
            )
        )

    def test_masked_hides_password(self):
        masked = self._config().database.masked()

        self.assertEqual(masked["password"], "***")
        self.assertNotIn(self.SECRET, str(masked))

    def test_summary_hides_password(self):
        summary = self._config().summary()

        self.assertNotIn(self.SECRET, str(summary))

    def test_connection_parameters_still_carry_password(self):
        """Tham so ket noi that su van phai co mat khau."""
        parameters = self._config().database.connection_parameters()

        self.assertEqual(parameters["password"], self.SECRET)

    def test_missing_variables_are_reported(self):
        config = DatabaseConfig()

        missing = config.missing_variables()

        self.assertIn("DB_HOST", missing)
        self.assertIn("DB_PASSWORD", missing)
        self.assertFalse(config.is_configured)

    def test_missing_config_error_lists_variables(self):
        error = MissingConfigError(["DB_HOST", "DB_USER"])

        self.assertIn("DB_HOST", str(error))
        self.assertIn(".env.example", str(error))


class LoadConfigTest(unittest.TestCase):
    def test_load_test_config_is_testing_environment(self):
        config = load_test_config()

        self.assertIs(
            config.environment,
            Environment.TESTING,
        )
        self.assertEqual(config.logging.level, "ERROR")

    def test_load_config_validates(self):
        with clean_env(AI_CONFIDENCE="5.0"):
            with self.assertRaises(ConfigValidationError):
                load_config(read_dotenv=False)

    def test_load_config_can_skip_validation(self):
        with clean_env(AI_CONFIDENCE="5.0"):
            config = load_config(
                read_dotenv=False,
                validate=False,
            )

        self.assertEqual(config.ai.confidence, 5.0)

    def test_explicit_environment_wins(self):
        with clean_env(AI_ENGLISH_ENV="production"):
            config = load_config(
                environment=Environment.TESTING,
                read_dotenv=False,
            )

        self.assertIs(
            config.environment,
            Environment.TESTING,
        )

    def test_with_overrides_creates_a_copy(self):
        original = AppConfig()
        changed = original.with_overrides(
            camera=CameraConfig(camera_id=3)
        )

        self.assertEqual(original.camera.camera_id, 0)
        self.assertEqual(changed.camera.camera_id, 3)
        self.assertIsNot(original, changed)

    def test_config_is_immutable(self):
        config = AppConfig()

        with self.assertRaises(Exception):
            config.camera.camera_id = 5


class DotEnvExampleTest(unittest.TestCase):
    """`.env.example` phai liet ke moi bien ma loader doc."""

    EXPECTED_VARIABLES = (
        "AI_ENGLISH_ENV",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "DB_POOL_MIN",
        "DB_POOL_MAX",
        "AI_CONFIDENCE",
        "AI_IMAGE_SIZE",
        "AI_MODEL_FILE",
        "AI_RELATED_WORDS",
        "CAMERA_ID",
        "CAMERA_INFERENCE_INTERVAL",
        "CAMERA_MAX_FRAMES_IN_FLIGHT",
        "HISTORY_COOLDOWN_SECONDS",
        "HISTORY_PAGE_LIMIT",
        "HISTORY_STATS_LIMIT",
        "HISTORY_WRITE_QUEUE_SIZE",
        "THREAD_DISPOSE_TIMEOUT_MS",
        "THREAD_POLL_INTERVAL",
        "LOG_LEVEL",
        "AI_ENGLISH_PERF",
    )

    def test_every_variable_is_documented(self):
        path = (
            Path(__file__).resolve().parent.parent
            / ".env.example"
        )

        self.assertTrue(path.exists(), ".env.example phai ton tai")

        content = path.read_text(encoding="utf-8")

        missing = [
            name
            for name in self.EXPECTED_VARIABLES
            if name not in content
        ]

        self.assertEqual(
            missing,
            [],
            "Bien chua duoc ghi trong .env.example",
        )

    def test_example_contains_no_real_secret(self):
        path = (
            Path(__file__).resolve().parent.parent
            / ".env.example"
        )
        content = path.read_text(encoding="utf-8").lower()

        self.assertIn("your-password", content)


class RequirementsTest(unittest.TestCase):
    """NHIEM VU 6 - moi thu vien phai duoc ghim phien ban."""

    ROOT = Path(__file__).resolve().parent.parent

    def _requirement_lines(
        self,
        file_name: str,
    ) -> list[str]:
        path = self.ROOT / file_name

        self.assertTrue(path.exists(), f"{file_name} phai ton tai")

        return [
            line.strip()
            for line in path.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
            and not line.strip().startswith("#")
            and not line.strip().startswith("-r ")
        ]

    def test_every_runtime_dependency_is_pinned(self):
        unpinned = [
            line
            for line in self._requirement_lines("requirements.txt")
            if "==" not in line
        ]

        self.assertEqual(
            unpinned,
            [],
            "Moi thu vien trong requirements.txt phai ghim phien ban",
        )

    def test_every_dev_dependency_is_pinned(self):
        unpinned = [
            line
            for line in self._requirement_lines(
                "requirements-dev.txt"
            )
            if "==" not in line
        ]

        self.assertEqual(unpinned, [])

    def test_dev_file_includes_runtime_file(self):
        content = (
            self.ROOT / "requirements-dev.txt"
        ).read_text(encoding="utf-8")

        self.assertIn("-r requirements.txt", content)


if __name__ == "__main__":
    unittest.main()
