"""Sprint 7 - Unit test cho cay exception va error boundary.

Kiem tra:

1. Moi loi cua ung dung deu ke thua `AppError`.
2. Ma loi duy nhat, khong trung lap.
3. Thong diep ky thuat va thong diep nguoi dung tach bach.
4. Thong diep gui cho nguoi dung KHONG lo chi tiet ky thuat.
5. Error boundary: cho nao bat, cho nao nem tiep, cho nao doi sang thong bao.
"""

from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent),
)

from config.errors import (  # noqa: E402
    ConfigError,
    ConfigValidationError,
    MissingConfigError,
)
from core import messages  # noqa: E402
from core.errors import (  # noqa: E402
    AIError,
    AppError,
    ExternalServiceError,
    InferenceError,
    MediaError,
    ModelLoadError,
    OperationCancelled,
    SpeechError,
    TranslationError,
    UIError,
    all_error_codes,
    error_code_for,
    user_message_for,
)
from database.exceptions import (  # noqa: E402
    ConnectionFailedError,
    IntegrityError,
    NotFoundError,
    QueryFailedError,
    RepositoryError,
)


ALL_ERROR_CLASSES = (
    AppError,
    ConfigError,
    ConfigValidationError,
    MissingConfigError,
    RepositoryError,
    ConnectionFailedError,
    QueryFailedError,
    NotFoundError,
    IntegrityError,
    AIError,
    ModelLoadError,
    InferenceError,
    UIError,
    MediaError,
    OperationCancelled,
    ExternalServiceError,
    SpeechError,
    TranslationError,
)


class HierarchyTest(unittest.TestCase):
    """NHIEM VU 3 - Cay exception co mot goc duy nhat."""

    def test_every_error_derives_from_app_error(self):
        for error_class in ALL_ERROR_CLASSES:
            self.assertTrue(
                issubclass(error_class, AppError),
                f"{error_class.__name__} phai ke thua AppError",
            )

    def test_config_and_repository_share_the_same_root(self):
        """Truoc Sprint 7 hai cay nay khong lien quan gi nhau."""
        self.assertTrue(issubclass(ConfigError, AppError))
        self.assertTrue(issubclass(RepositoryError, AppError))

    def test_catching_app_error_catches_everything(self):
        for error_class in ALL_ERROR_CLASSES:
            if error_class is ConfigValidationError:
                error = error_class("truong", 1, "ly do")
            elif error_class is MissingConfigError:
                error = error_class(["DB_HOST"])
            else:
                error = error_class("loi thu nghiem")

            try:
                raise error
            except AppError:
                pass
            else:  # pragma: no cover
                self.fail(
                    f"{error_class.__name__} khong bat duoc bang AppError"
                )

    def test_subtree_membership(self):
        self.assertTrue(issubclass(ModelLoadError, AIError))
        self.assertTrue(issubclass(InferenceError, AIError))
        self.assertTrue(issubclass(MediaError, UIError))
        self.assertTrue(issubclass(OperationCancelled, UIError))
        self.assertTrue(issubclass(SpeechError, ExternalServiceError))
        self.assertTrue(
            issubclass(TranslationError, ExternalServiceError)
        )
        self.assertTrue(
            issubclass(ConnectionFailedError, RepositoryError)
        )


class ErrorCodeTest(unittest.TestCase):
    def test_every_class_has_a_code(self):
        for error_class in ALL_ERROR_CLASSES:
            self.assertTrue(
                error_class.error_code,
                f"{error_class.__name__} thieu error_code",
            )

    def test_codes_are_unique(self):
        codes = [
            error_class.error_code
            for error_class in ALL_ERROR_CLASSES
        ]

        duplicates = {
            code
            for code in codes
            if codes.count(code) > 1
        }

        self.assertEqual(
            duplicates,
            set(),
            "Ma loi bi trung - tang tren khong phan biet duoc",
        )

    def test_registry_finds_every_subclass(self):
        registry = all_error_codes()

        for error_class in ALL_ERROR_CLASSES:
            self.assertIn(error_class.error_code, registry)

    def test_error_code_for_helper(self):
        self.assertEqual(
            error_code_for(ConnectionFailedError()),
            "DB_CONNECTION_FAILED",
        )
        self.assertEqual(
            error_code_for(ValueError("khong phai AppError")),
            "UNEXPECTED_ERROR",
        )


class TwoMessagesTest(unittest.TestCase):
    """NHIEM VU 5 - thong diep ky thuat tach khoi thong diep nguoi dung."""

    def test_technical_and_display_are_separate(self):
        error = QueryFailedError(
            "INSERT INTO history that bai o cot confidence",
        )

        self.assertIn("INSERT INTO", error.technical_message)
        self.assertNotIn("INSERT INTO", error.display_message)
        self.assertEqual(
            error.display_message,
            messages.MSG_DATA_OPERATION_FAILED,
        )

    def test_display_message_can_be_overridden(self):
        error = AppError(
            "chi tiet ky thuat",
            user_message="Vui lòng thử lại sau.",
        )

        self.assertEqual(
            error.display_message,
            "Vui lòng thử lại sau.",
        )

    def test_legacy_message_property_still_works(self):
        """Code Sprint 4 dung `.message` - khong duoc pha."""
        error = ConnectionFailedError("mat ket noi")

        self.assertEqual(error.message, "mat ket noi")

    def test_cause_is_kept_and_shown_in_technical_text(self):
        cause = ValueError("nguyen nhan goc")
        error = QueryFailedError("that bai", cause=cause)

        self.assertIs(error.cause, cause)
        self.assertIn("nguyen nhan goc", str(error))

    def test_to_dict_has_no_sensitive_payload(self):
        error = ConnectionFailedError(
            "khong ket noi duoc",
            cause=ValueError("password=bimat"),
        )
        data = error.to_dict()

        self.assertEqual(data["error_code"], "DB_CONNECTION_FAILED")
        self.assertEqual(data["cause_type"], "ValueError")
        self.assertNotIn("bimat", str(data))

    def test_user_message_for_hides_unknown_errors(self):
        """Loi ngoai du kien KHONG duoc hien noi dung goc cho nguoi dung."""
        leaky = RuntimeError(
            "postgresql://admin:bimat@db.example.com/postgres"
        )

        shown = user_message_for(leaky)

        self.assertNotIn("bimat", shown)
        self.assertNotIn("postgresql", shown)
        self.assertEqual(shown, AppError.user_message)

    def test_user_message_for_uses_app_error_message(self):
        self.assertEqual(
            user_message_for(NotFoundError()),
            messages.MSG_DATA_NOT_FOUND,
        )


class UserMessageCatalogTest(unittest.TestCase):
    """NHIEM VU 5 - catalog thong diep khong duoc lo chi tiet ky thuat."""

    def test_catalog_is_not_empty(self):
        self.assertGreater(
            len(messages.all_user_messages()),
            25,
        )

    def test_no_message_leaks_technical_detail(self):
        offenders = [
            name
            for name, text in messages.all_user_messages().items()
            if messages.contains_technical_detail(text)
        ]

        self.assertEqual(
            offenders,
            [],
            "Thong diep nguoi dung khong duoc chua chi tiet ky thuat",
        )

    def test_every_error_class_user_message_is_clean(self):
        for error_class in ALL_ERROR_CLASSES:
            self.assertFalse(
                messages.contains_technical_detail(
                    error_class.user_message
                ),
                f"{error_class.__name__}.user_message lo chi tiet ky thuat",
            )

    def test_detector_helper_catches_technical_text(self):
        self.assertTrue(
            messages.contains_technical_detail(
                "Loi psycopg2: SELECT * FROM users"
            )
        )
        self.assertFalse(
            messages.contains_technical_detail(
                "Vui lòng đăng nhập để xem lịch sử."
            )
        )

    def test_modules_reuse_the_catalog(self):
        """Thong diep phai lay tu catalog, khong viet lai o tung file."""
        from ui.services import auth_service
        from ui.viewmodels import image_viewmodel
        from ui.workers import webcam_worker

        self.assertEqual(
            auth_service.MSG_WRONG_CREDENTIALS,
            messages.MSG_WRONG_CREDENTIALS,
        )
        self.assertEqual(
            image_viewmodel.STATUS_NO_OBJECT,
            messages.MSG_NO_OBJECT_FOUND,
        )
        self.assertEqual(
            webcam_worker.STATUS_CAMERA_STOPPED,
            messages.MSG_CAMERA_STOPPED,
        )


class ErrorBoundaryTest(unittest.TestCase):
    """NHIEM VU 4 - ranh gioi bat loi ro rang."""

    def test_repository_raises_instead_of_returning_empty(self):
        """Tang Repository NEM loi, khong nuot roi tra ve rong."""
        from test.db_fakes import failing_factory
        from database.repositories.history_repository import (
            HistoryRepository,
        )

        repository = HistoryRepository(
            cursor_factory=failing_factory()
        )

        with self.assertRaises(AppError):
            repository.list_by_user(user_id=1)

    def test_read_path_propagates_to_caller(self):
        """Doc lich su: loi phai len toi Worker de GUI bao cho nguoi dung."""
        from test.db_fakes import failing_factory
        from database.repositories.history_repository import (
            HistoryRepository,
        )
        from ui.services.history_service import HistoryService

        service = HistoryService(
            repository=HistoryRepository(
                cursor_factory=failing_factory()
            )
        )

        with self.assertRaises(RepositoryError):
            service.load_rows(user_id=1)

    def test_write_path_is_contained(self):
        """Ghi lich su: loi KHONG duoc lam hong ket qua nhan dien."""
        from test.db_fakes import failing_factory
        from database.repositories.history_repository import (
            HistoryRepository,
        )
        from ui.services.history_service import HistoryService

        service = HistoryService(
            repository=HistoryRepository(
                cursor_factory=failing_factory()
            )
        )

        self.assertFalse(
            service.save_detection(
                "laptop",
                "May tinh",
                "Technology",
                0.9,
            )
        )

    def test_auth_service_never_shows_raw_error(self):
        """Thong diep dang nhap that bai KHONG duoc chua chi tiet database."""
        from test.db_fakes import FakeCursorFactory
        from database.repositories.user_repository import UserRepository
        from ui.services.auth_service import AuthService

        leaky = ConnectionFailedError(
            "postgresql://admin:bimat@db.example.com/postgres khong phan hoi"
        )
        service = AuthService(
            repository=UserRepository(
                cursor_factory=FakeCursorFactory(raise_error=leaky)
            )
        )

        result = service.login("thiet", "matkhau123")

        self.assertFalse(result.success)
        self.assertNotIn("bimat", result.message)
        self.assertNotIn("postgresql", result.message)
        self.assertEqual(
            result.error_code,
            "DB_CONNECTION_FAILED",
        )

    def test_dialog_service_publishes_errors_safely(self):
        from test.ui_fakes import ensure_app
        from ui.services.dialog_service import DialogService

        ensure_app()
        service = DialogService()

        shown = []
        service.errorShown.connect(
            lambda title, message: shown.append(message)
        )

        service.publishError(
            RuntimeError("postgresql://admin:bimat@host/db")
        )

        self.assertEqual(len(shown), 1)
        self.assertNotIn("bimat", shown[0])
        self.assertEqual(shown[0], AppError.user_message)

    def test_worker_turns_unexpected_error_into_failed_signal(self):
        """Loi ngoai du kien trong worker -> signal `failed`, khong lam sap app."""
        from test.ui_fakes import ensure_app, process_events, wait_for
        from ui.workers.lifecycle import ManagedWorker, WorkerState

        ensure_app()

        class Boom(ManagedWorker):
            def __init__(self):
                super().__init__("boom_worker")

            def execute(self):
                raise RuntimeError("no tung")

        worker = Boom()
        failures = []
        worker.failed.connect(failures.append)

        worker.start()

        self.assertTrue(
            wait_for(
                lambda: worker.state is WorkerState.FAILED
            )
        )
        worker.dispose(3000)
        process_events(5)

        self.assertEqual(failures, ["no tung"])

    def test_cancellation_is_not_reported_as_failure(self):
        """Nguoi dung huy KHONG duoc hien hop thoai bao loi."""
        from test.ui_fakes import ensure_app, process_events, wait_for
        from ui.workers.cancellation import OperationCancelledError
        from ui.workers.lifecycle import ManagedWorker, WorkerState

        ensure_app()

        class Cancelling(ManagedWorker):
            def __init__(self):
                super().__init__("cancelling_worker")

            def execute(self):
                raise OperationCancelledError()

        worker = Cancelling()
        failures = []
        cancels = []

        worker.failed.connect(failures.append)
        worker.cancelled.connect(lambda: cancels.append(1))

        worker.start()

        self.assertTrue(
            wait_for(
                lambda: worker.state is WorkerState.CANCELLED
            )
        )
        worker.dispose(3000)
        process_events(5)

        self.assertEqual(failures, [])
        self.assertEqual(cancels, [1])


class NoRawErrorInUserTextTest(unittest.TestCase):
    """Khong module nao duoc ghep `str(error)` vao thong diep nguoi dung."""

    MODULES = (
        "ui.services.auth_service",
        "ui.services.history_service",
        "ui.services.detection_service",
        "ui.viewmodels.auth_viewmodel",
        "ui.viewmodels.image_viewmodel",
        "ui.viewmodels.history_viewmodel",
    )

    #: Dinh dang nguy hiem: nhet thang exception vao chuoi hien thi.
    FORBIDDEN = (
        "{error}",
        "{e}",
        "str(error)",
    )

    def test_no_module_formats_raw_exception_into_user_text(self):
        import importlib

        offenders = []

        for module_name in self.MODULES:
            module = importlib.import_module(module_name)
            source = inspect.getsource(module)

            for line in source.splitlines():
                stripped = line.strip()

                if stripped.startswith("#"):
                    continue

                # Chi soi cac dong tao chuoi hien thi (f-string tieng Viet).
                if 'f"' not in stripped:
                    continue

                for pattern in self.FORBIDDEN:
                    if pattern in stripped:
                        offenders.append(
                            f"{module_name}: {stripped}"
                        )

        self.assertEqual(
            offenders,
            [],
            "Thong diep nguoi dung khong duoc ghep thang noi dung exception",
        )


if __name__ == "__main__":
    unittest.main()
