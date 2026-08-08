"""Sprint 7 - Unit test cho kien truc logging va chong ro ri du lieu.

Kiem tra:

1. Logger phan cap theo tang, chinh muc doc lap duoc.
2. Console + file xoay vong, ca hai deu qua bo loc.
3. Mat khau / chuoi ket noi / token KHONG bao gio lot ra log.
4. Khong con `print()` o cac file da thong nhat trong Sprint 7.
5. Log hong khong duoc lam sap ung dung.
"""

from __future__ import annotations

import logging
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent),
)

from config.schema import (  # noqa: E402
    AppConfig,
    DatabaseConfig,
    LoggingConfig,
)
from core import logging_config  # noqa: E402
from core.logging_config import (  # noqa: E402
    CONSOLE_FORMAT,
    FILE_FORMAT,
    LOG_FILE_BACKUP_COUNT,
    LOG_FILE_MAX_BYTES,
    LOG_FILE_NAME,
    NOISY_THIRD_PARTY_LOGGERS,
    THIRD_PARTY_LEVEL,
    build_file_handler,
    get_logger,
    log_directory,
    reset_logging,
    resolve_level,
    set_layer_level,
    setup_from_app_config,
    setup_logging,
)
from core.redaction import (  # noqa: E402
    REDACTED,
    SensitiveDataFilter,
    clear_secrets,
    redact,
    register_secret,
    registered_secret_count,
)


class CapturingHandler(logging.Handler):
    """Handler thu ban ghi da qua bo loc, de kiem tra noi dung."""

    def __init__(self) -> None:
        super().__init__()
        self.messages: list[str] = []
        self.addFilter(SensitiveDataFilter())

    def emit(self, record):
        self.messages.append(record.getMessage())

    def text(self) -> str:
        return "\n".join(self.messages)


class RedactionTest(unittest.TestCase):
    """NHIEM VU 6 - Du lieu nhay cam."""

    def setUp(self):
        clear_secrets()

    def tearDown(self):
        clear_secrets()

    def test_connection_string_password_is_masked(self):
        text = redact(
            "connect postgresql://admin:sieumatkhau@db.example.com:5432/postgres"
        )

        self.assertNotIn("sieumatkhau", text)
        self.assertIn(REDACTED, text)
        self.assertIn("admin", text)
        self.assertIn("db.example.com", text)

    def test_keyword_assignment_is_masked(self):
        for raw in (
            "password=bimat123",
            "PASSWORD: bimat123",
            "token = bimat123",
            "api_key='bimat123'",
            'secret="bimat123"',
        ):
            self.assertNotIn(
                "bimat123",
                redact(raw),
                f"Khong che duoc: {raw}",
            )

    def test_bearer_token_is_masked(self):
        text = redact("Authorization: Bearer abc.def.ghi")

        self.assertNotIn("abc.def.ghi", text)

    def test_registered_secret_is_masked_anywhere(self):
        """Gia tri da dang ky bi che o BAT KY dinh dang nao."""
        register_secret("MatKhauSieuBiMat2026")

        for raw in (
            "loi la MatKhauSieuBiMat2026",
            "{'pwd': 'MatKhauSieuBiMat2026'}",
            "FATAL: MatKhauSieuBiMat2026 khong dung",
        ):
            self.assertNotIn(
                "MatKhauSieuBiMat2026",
                redact(raw),
            )

    def test_short_secret_is_rejected(self):
        """Chuoi qua ngan se thay the nham khap noi - phai tu choi."""
        self.assertFalse(register_secret("ab"))
        self.assertFalse(register_secret(""))
        self.assertFalse(register_secret(None))
        self.assertEqual(registered_secret_count(), 0)

    def test_longer_secret_is_replaced_first(self):
        register_secret("matkhau")
        register_secret("matkhaudai")

        text = redact("gia tri: matkhaudai")

        self.assertNotIn("matkhau", text)

    def test_harmless_text_is_untouched(self):
        text = "Đã tải 12 bản ghi."

        self.assertEqual(redact(text), text)

    def test_empty_input(self):
        self.assertEqual(redact(""), "")

    def test_filter_masks_log_record(self):
        register_secret("MatKhauCuaToi123")

        logger = logging.getLogger("test.redaction.record")
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        handler = CapturingHandler()
        logger.addHandler(handler)

        try:
            logger.error(
                "Khong ket noi duoc: %s",
                "password=MatKhauCuaToi123",
            )
            logger.error(
                "postgresql://user:MatKhauCuaToi123@host/db"
            )
        finally:
            logger.removeHandler(handler)

        self.assertNotIn("MatKhauCuaToi123", handler.text())
        self.assertIn(REDACTED, handler.text())

    def test_filter_masks_dict_args(self):
        register_secret("BiMatTrongDict")

        logger = logging.getLogger("test.redaction.dict")
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        handler = CapturingHandler()
        logger.addHandler(handler)

        try:
            logger.info(
                "ket noi %(host)s voi %(pwd)s",
                {
                    "host": "db.local",
                    "pwd": "BiMatTrongDict",
                },
            )
        finally:
            logger.removeHandler(handler)

        self.assertNotIn("BiMatTrongDict", handler.text())

    def test_broken_filter_does_not_lose_the_record(self):
        """Bo loc hong khong duoc lam mat ban ghi, cung khong duoc lot bi mat."""

        class Exploding:
            def __str__(self):
                raise RuntimeError("khong doi duoc sang chuoi")

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg=Exploding(),
            args=(),
            exc_info=None,
        )

        self.assertTrue(
            SensitiveDataFilter().filter(record)
        )
        self.assertIn("che du lieu nhay cam", str(record.msg))


class DatabasePasswordNeverLeaksTest(unittest.TestCase):
    """Mat khau database that phai bi che o moi duong ra log."""

    PASSWORD = "MatKhauDatabaseThat2026"

    def setUp(self):
        clear_secrets()
        reset_logging()

    def tearDown(self):
        clear_secrets()
        reset_logging()

    def _app_config(self) -> AppConfig:
        return AppConfig(
            database=DatabaseConfig(
                host="db.example.com",
                user="admin",
                password=self.PASSWORD,
            ),
            logging=LoggingConfig(level="DEBUG"),
        )

    def test_setup_registers_database_password(self):
        setup_from_app_config(
            self._app_config(),
            enable_file=False,
            force=True,
        )

        self.assertGreaterEqual(
            registered_secret_count(),
            1,
        )
        self.assertNotIn(
            self.PASSWORD,
            redact(f"loi: {self.PASSWORD}"),
        )

    def test_password_never_reaches_the_log_file(self):
        with tempfile.TemporaryDirectory() as directory:
            register_secret(self.PASSWORD)

            handler = build_file_handler(Path(directory))
            self.assertIsNotNone(handler)

            logger = logging.getLogger("test.leak.file")
            logger.setLevel(logging.DEBUG)
            logger.propagate = False
            logger.addHandler(handler)

            try:
                logger.error(
                    "connect: postgresql://admin:%s@db.example.com/postgres",
                    self.PASSWORD,
                )
                logger.error("password=%s", self.PASSWORD)
                handler.flush()

                content = (
                    Path(directory) / LOG_FILE_NAME
                ).read_text(encoding="utf-8")
            finally:
                logger.removeHandler(handler)
                handler.close()

        self.assertNotIn(self.PASSWORD, content)
        self.assertIn(REDACTED, content)

    def test_config_summary_never_contains_password(self):
        summary = str(self._app_config().summary())

        self.assertNotIn(self.PASSWORD, summary)


class LoggingSetupTest(unittest.TestCase):
    def setUp(self):
        reset_logging()

    def tearDown(self):
        reset_logging()

    def test_setup_attaches_console_handler(self):
        root = setup_logging(
            level="INFO",
            enable_file=False,
            force=True,
        )

        ours = [
            handler
            for handler in root.handlers
            if getattr(handler, "ai_english_handler", False)
        ]

        self.assertEqual(len(ours), 1)

    def test_setup_is_idempotent(self):
        setup_logging(level="INFO", enable_file=False, force=True)
        setup_logging(level="INFO", enable_file=False)
        setup_logging(level="INFO", enable_file=False)

        ours = [
            handler
            for handler in logging.getLogger().handlers
            if getattr(handler, "ai_english_handler", False)
        ]

        self.assertEqual(
            len(ours),
            1,
            "Goi lai setup_logging khong duoc nhan doi handler",
        )

    def test_root_stays_at_debug_so_file_gets_everything(self):
        setup_logging(level="WARNING", enable_file=False, force=True)

        self.assertEqual(
            logging.getLogger().level,
            logging.DEBUG,
        )

    def test_console_level_follows_config(self):
        root = setup_logging(
            config=LoggingConfig(level="ERROR"),
            enable_file=False,
            force=True,
        )

        console = [
            handler
            for handler in root.handlers
            if getattr(handler, "ai_english_handler", False)
        ][0]

        self.assertEqual(console.level, logging.ERROR)

    def test_third_party_loggers_are_quietened(self):
        setup_logging(level="DEBUG", enable_file=False, force=True)

        for name in NOISY_THIRD_PARTY_LOGGERS:
            self.assertEqual(
                logging.getLogger(name).level,
                THIRD_PARTY_LEVEL,
                f"Logger {name} phai bi ha xuong WARNING",
            )

    def test_file_handler_rotates(self):
        with tempfile.TemporaryDirectory() as directory:
            handler = build_file_handler(Path(directory))

            self.assertIsNotNone(handler)
            self.assertEqual(handler.maxBytes, LOG_FILE_MAX_BYTES)
            self.assertEqual(
                handler.backupCount,
                LOG_FILE_BACKUP_COUNT,
            )

            handler.close()

    def test_unwritable_log_directory_does_not_crash(self):
        """Khong ghi duoc file log KHONG duoc lam sap ung dung."""
        handler = build_file_handler(
            Path("Z:/khong-ton-tai/logs")
        )

        self.assertIsNone(handler)

        root = setup_logging(
            level="INFO",
            enable_file=True,
            force=True,
        )

        self.assertTrue(root.handlers)

    def test_resolve_level(self):
        self.assertEqual(resolve_level("debug"), logging.DEBUG)
        self.assertEqual(resolve_level("ERROR"), logging.ERROR)
        self.assertEqual(resolve_level(logging.WARNING), logging.WARNING)
        self.assertEqual(resolve_level("khong-co"), logging.INFO)

    def test_log_directory_is_inside_project(self):
        directory = log_directory()

        self.assertEqual(directory.name, "logs")
        self.assertTrue(
            (directory.parent / "config").exists()
        )


class HierarchicalLoggerTest(unittest.TestCase):
    """Moi tang chinh muc log doc lap."""

    def tearDown(self):
        for name in ("ai", "ui", "database", "core"):
            logging.getLogger(name).setLevel(logging.NOTSET)

    def test_layer_level_is_independent(self):
        set_layer_level("database", "DEBUG")
        set_layer_level("ai", "ERROR")

        self.assertEqual(
            logging.getLogger("database").level,
            logging.DEBUG,
        )
        self.assertEqual(
            logging.getLogger("ai").level,
            logging.ERROR,
        )

    def test_child_inherits_from_layer(self):
        set_layer_level("database", "ERROR")

        child = logging.getLogger("database.repository.history")

        self.assertFalse(
            child.isEnabledFor(logging.INFO)
        )
        self.assertTrue(
            child.isEnabledFor(logging.ERROR)
        )

    def test_project_modules_use_hierarchical_names(self):
        import importlib

        expected = {
            "ui.services.history_service": "ui",
            "database.connection": "database",
            "config.loader": "config",
            "utils.perf_monitor": "utils",
        }

        for module_name, layer in expected.items():
            module = importlib.import_module(module_name)
            logger = getattr(module, "logger", None)

            self.assertIsNotNone(
                logger,
                f"{module_name} phai co logger rieng",
            )
            self.assertTrue(
                logger.name.startswith(layer),
                f"{module_name}: logger `{logger.name}` "
                f"phai thuoc tang `{layer}`",
            )

    def test_ui_logger_prefix(self):
        from ui.ui_logger import get_ui_logger

        self.assertEqual(
            get_ui_logger("image_controller").name,
            "ui.image_controller",
        )

    def test_get_logger_returns_named_logger(self):
        self.assertEqual(
            get_logger("database.repository").name,
            "database.repository",
        )


class NoPrintLeftTest(unittest.TestCase):
    """NHIEM VU 1 - khong con print() o cac file da thong nhat."""

    ROOT = Path(__file__).resolve().parent.parent

    #: File duoc phep con `print()` - quyet dinh co y cua Sprint 7.
    ALLOWED = {
        "ml/knn.py",
        "ml/kmeans.py",
    }

    PACKAGES = (
        "ai",
        "ml",
        "detection",
        "dataset",
        "database",
        "ui",
        "utils",
        "config",
        "core",
    )

    @staticmethod
    def _print_call_lines(source: str) -> list[int]:
        """Dong co goi `print()` THAT SU.

        Dung `ast` thay vi regex: chuoi va docstring co chua chu `print(` KHONG
        phai la loi goi, va khong duoc bao dong nham.
        """
        import ast

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []

        return [
            node.lineno
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
        ]

    def _python_files(self):
        for package in self.PACKAGES:
            directory = self.ROOT / package

            if not directory.exists():
                continue

            for path in directory.rglob("*.py"):
                if "__pycache__" in path.parts:
                    continue
                yield path

    def test_no_print_outside_allowed_files(self):
        offenders = []

        for path in self._python_files():
            relative = path.relative_to(self.ROOT).as_posix()

            if relative in self.ALLOWED:
                continue

            lines = self._print_call_lines(
                path.read_text(encoding="utf-8")
            )

            if lines:
                offenders.append(
                    f"{relative}:{lines[0]}"
                )

        self.assertEqual(
            offenders,
            [],
            "Cac file nay van con print(), phai dung logger",
        )

    def test_allowed_files_are_documented(self):
        """File duoc mien tru phai that su ton tai va that su con print()."""
        for relative in self.ALLOWED:
            path = self.ROOT / relative

            self.assertTrue(path.exists(), f"{relative} khong ton tai")
            self.assertTrue(
                self._print_call_lines(
                    path.read_text(encoding="utf-8")
                ),
                f"{relative} khong con print() - go khoi danh sach mien tru",
            )

    def test_scripts_bootstrap_logging(self):
        """Script chay doc lap phai tu lap dat logging, neu khong se im lang."""
        for relative in (
            "dataset/prepare_dataset.py",
            "ml/evaluate.py",
            "detection/webcam_detect.py",
        ):
            source = (self.ROOT / relative).read_text(
                encoding="utf-8"
            )

            self.assertIn(
                "setup_logging",
                source,
                f"{relative} phai goi setup_logging() khi chay doc lap",
            )


class NoSilentSwallowTest(unittest.TestCase):
    """NHIEM VU 4 - khong duoc nuot loi im lang."""

    ROOT = Path(__file__).resolve().parent.parent

    MODULES = (
        "ui",
        "database",
        "config",
        "core",
    )

    #: `except ...: pass` chi duoc phep khi co giai thich ngay ben tren.
    PATTERN = re.compile(
        r"except[^\n]*:\n(?P<body>(?:[ \t]*(?:#[^\n]*)?\n)*?[ \t]*pass\b)",
    )

    def test_every_swallow_is_explained(self):
        offenders = []

        for package in self.MODULES:
            for path in (self.ROOT / package).rglob("*.py"):
                if "__pycache__" in path.parts:
                    continue

                source = path.read_text(encoding="utf-8")

                for match in self.PATTERN.finditer(source):
                    if "#" not in match.group("body"):
                        line = source[: match.start()].count("\n") + 1
                        offenders.append(
                            f"{path.relative_to(self.ROOT).as_posix()}:{line}"
                        )

        self.assertEqual(
            offenders,
            [],
            "`except: pass` phai co ghi chu giai thich vi sao bo qua",
        )


class FormatTest(unittest.TestCase):
    def test_console_format_has_level_and_name(self):
        self.assertIn("%(levelname)", CONSOLE_FORMAT)
        self.assertIn("%(name)", CONSOLE_FORMAT)
        self.assertIn("%(message)", CONSOLE_FORMAT)

    def test_file_format_has_time_and_thread(self):
        self.assertIn("%(asctime)", FILE_FORMAT)
        self.assertIn("%(threadName)", FILE_FORMAT)
        self.assertIn("%(levelname)", FILE_FORMAT)

    def test_module_exposes_reset_for_tests(self):
        self.assertTrue(
            hasattr(logging_config, "reset_logging")
        )


if __name__ == "__main__":
    unittest.main()
