"""Sprint 4 - Unit test cho Service layer tren Repository.

Kiem tra:

1. `HistoryService` va `AuthService` KHONG con chua cau SQL.
2. Chinh sach loi: ghi = best effort, doc/xoa = nem loi len GUI.
3. Luat nghiep vu (validate, nang cap hash) nam o Service.
4. Khong ro ri mat khau hay chi tiet database ra thong diep nguoi dung.

Toan bo test chay KHONG can PostgreSQL that.
"""

from __future__ import annotations

import datetime
import inspect
import unittest

from test.db_fakes import (
    FakeCursorFactory,
    failing_factory,
    integrity_factory,
)

from database.exceptions import (
    ConnectionFailedError,
    RepositoryError,
)
from database.repositories.history_repository import HistoryRepository
from database.repositories.user_repository import UserRepository
from ui.services.auth_service import (
    MSG_CONFIRM_MISMATCH,
    MSG_EMPTY_FULLNAME,
    MSG_LOGIN_OK,
    MSG_MISSING_CREDENTIALS,
    MSG_PASSWORD_CHANGED,
    MSG_REGISTER_OK,
    MSG_SAME_PASSWORD,
    MSG_SHORT_PASSWORD,
    MSG_USERNAME_TAKEN,
    MSG_WRONG_CREDENTIALS,
    MSG_WRONG_OLD_PASSWORD,
    AuthService,
)
from ui.services.history_service import (
    HistoryService,
    format_history_rows,
)
from ui.services.stats_service import StatsService
from utils.password import hash_password


HISTORY_ROW = (
    1,
    7,
    "laptop",
    "May tinh xach tay",
    "Technology",
    0.93,
    datetime.datetime(2026, 1, 2, 3, 4),
)


def history_service_with(
    factory: FakeCursorFactory,
) -> HistoryService:
    return HistoryService(
        repository=HistoryRepository(cursor_factory=factory)
    )


def auth_service_with(
    factory: FakeCursorFactory,
) -> AuthService:
    return AuthService(
        repository=UserRepository(cursor_factory=factory)
    )


class ServiceHasNoSqlTest(unittest.TestCase):
    """NHIEM VU 8 - Service khong duoc biet SQL."""

    SERVICE_MODULES = (
        "ui.services.history_service",
        "ui.services.auth_service",
        "ui.services.stats_service",
        "ui.services.detection_service",
    )

    SQL_KEYWORDS = (
        "SELECT ",
        "INSERT INTO",
        "UPDATE ",
        "DELETE FROM",
    )

    def test_services_contain_no_sql(self):
        import importlib

        for module_name in self.SERVICE_MODULES:
            module = importlib.import_module(module_name)
            source = inspect.getsource(module)

            for keyword in self.SQL_KEYWORDS:
                self.assertNotIn(
                    keyword,
                    source,
                    f"{module_name} van con cau SQL `{keyword}`",
                )

    def test_services_do_not_import_connection_layer(self):
        import importlib

        for module_name in self.SERVICE_MODULES:
            module = importlib.import_module(module_name)
            source = inspect.getsource(module)

            for forbidden in (
                "database.connection",
                "database.db",
                "psycopg2",
            ):
                self.assertNotIn(
                    forbidden,
                    source,
                    f"{module_name} phai di qua Repository",
                )


class HistoryServiceReadTest(unittest.TestCase):
    """Doc lich su: loi phai bao len GUI."""

    def test_load_entries_returns_typed_entities(self):
        service = history_service_with(
            FakeCursorFactory(results=[[HISTORY_ROW]])
        )

        entries = service.load_entries(user_id=7)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].english_word, "laptop")

    def test_load_rows_keeps_legacy_dict_shape(self):
        service = history_service_with(
            FakeCursorFactory(results=[[HISTORY_ROW]])
        )

        rows = service.load_rows(user_id=7)

        self.assertEqual(rows[0]["english_word"], "laptop")
        self.assertEqual(
            rows[0]["vietnamese_meaning"],
            "May tinh xach tay",
        )

    def test_load_formatted_rows_matches_view_contract(self):
        service = history_service_with(
            FakeCursorFactory(results=[[HISTORY_ROW]])
        )

        rows = service.load_formatted_rows(user_id=7)

        self.assertEqual(rows[0]["english"], "laptop")
        self.assertEqual(
            rows[0]["detected_time"],
            "02/01/2026 03:04",
        )

    def test_read_error_is_raised_to_caller(self):
        service = history_service_with(failing_factory())

        with self.assertRaises(RepositoryError):
            service.load_rows(user_id=7)

    def test_clear_error_is_raised_to_caller(self):
        service = history_service_with(failing_factory())

        with self.assertRaises(RepositoryError):
            service.clear(user_id=7)

    def test_empty_result_is_not_an_error(self):
        service = history_service_with(
            FakeCursorFactory(results=[[]])
        )

        self.assertEqual(
            service.load_rows(user_id=7),
            [],
        )


class HistoryServiceWriteTest(unittest.TestCase):
    """Ghi lich su: best effort, khong duoc lam hong luong nhan dien."""

    class FakeDetection:
        def __init__(self, english="laptop"):
            self.english = english
            self.vietnamese = "May tinh"
            self.category = "Technology"
            self.confidence = 0.93

    def test_save_detection_succeeds(self):
        factory = FakeCursorFactory(rowcount=1)
        service = history_service_with(factory)

        self.assertTrue(
            service.save_detection(
                "laptop",
                "May tinh",
                "Technology",
                0.93,
                user_id=7,
            )
        )
        self.assertTrue(factory.committed())

    def test_save_error_returns_false_instead_of_raising(self):
        service = history_service_with(failing_factory())

        self.assertFalse(
            service.save_detection(
                "laptop",
                "May tinh",
                "Technology",
                0.93,
            )
        )

    def test_save_detections_counts_only_successes(self):
        service = history_service_with(failing_factory())

        saved = service.save_detections(
            [
                self.FakeDetection(),
                self.FakeDetection("mouse"),
            ],
            user_id=7,
        )

        self.assertEqual(saved, 0)

    def test_detection_flow_survives_database_outage(self):
        """Database hong khong duoc lam hong ket qua nhan dien."""
        service = history_service_with(failing_factory())

        try:
            service.save_detections(
                [self.FakeDetection()],
                user_id=7,
            )
        except Exception as error:
            self.fail(
                f"Ghi lich su that bai khong duoc nem loi: {error}"
            )


class StatsServiceTest(unittest.TestCase):
    def test_statistics_are_computed_from_repository(self):
        rows = [
            HISTORY_ROW,
            (
                2,
                7,
                "laptop",
                "May tinh",
                "Technology",
                0.7,
                None,
            ),
        ]
        service = StatsService(
            history_service_with(
                FakeCursorFactory(results=[rows])
            )
        )

        stats = service.compute_for_user(user_id=7)

        self.assertEqual(stats["totalDetections"], 2)
        self.assertEqual(stats["uniqueWords"], 1)
        self.assertEqual(stats["mostCommonWord"], "laptop")
        self.assertAlmostEqual(
            stats["averageConfidence"],
            0.815,
        )

    def test_database_error_propagates_to_worker(self):
        service = StatsService(
            history_service_with(failing_factory())
        )

        with self.assertRaises(RepositoryError):
            service.compute_for_user(user_id=7)


class AuthServiceLoginTest(unittest.TestCase):
    HASHED = hash_password("matkhau123")

    def _row(self, password_value: str):
        return (7, "thiet", "Thach Thiet", password_value)

    def test_successful_login(self):
        service = auth_service_with(
            FakeCursorFactory(
                results=[[self._row(self.HASHED)]]
            )
        )

        result = service.login("  thiet  ", "matkhau123")

        self.assertTrue(result.success)
        self.assertEqual(result.message, MSG_LOGIN_OK)
        self.assertEqual(result.user["username"], "thiet")

    def test_user_dict_never_contains_password(self):
        service = auth_service_with(
            FakeCursorFactory(
                results=[[self._row(self.HASHED)]]
            )
        )

        result = service.login("thiet", "matkhau123")

        self.assertNotIn("password", result.user)
        self.assertNotIn("password_hash", result.user)

    def test_missing_credentials_do_not_touch_database(self):
        factory = FakeCursorFactory()
        service = auth_service_with(factory)

        result = service.login("", "")

        self.assertFalse(result.success)
        self.assertEqual(result.message, MSG_MISSING_CREDENTIALS)
        self.assertEqual(factory.executed, [])

    def test_wrong_password(self):
        service = auth_service_with(
            FakeCursorFactory(
                results=[[self._row(self.HASHED)]]
            )
        )

        result = service.login("thiet", "sai")

        self.assertFalse(result.success)
        self.assertEqual(result.message, MSG_WRONG_CREDENTIALS)

    def test_unknown_user(self):
        service = auth_service_with(
            FakeCursorFactory(results=[[]])
        )

        result = service.login("khong-co", "matkhau123")

        self.assertFalse(result.success)
        self.assertEqual(result.message, MSG_WRONG_CREDENTIALS)

    def test_plaintext_password_is_upgraded_after_login(self):
        """NHIEM VU 7 - luat nang cap hash nam o Service."""
        factory = FakeCursorFactory(
            results=[
                [self._row("matkhau123")],
                [],
            ]
        )
        service = auth_service_with(factory)

        result = service.login("thiet", "matkhau123")

        self.assertTrue(result.success)

        update_queries = [
            query
            for query, _ in factory.executed
            if "UPDATE users" in query
        ]
        self.assertEqual(len(update_queries), 1)

    def test_hashed_password_is_not_rewritten(self):
        factory = FakeCursorFactory(
            results=[[self._row(self.HASHED)]]
        )
        service = auth_service_with(factory)

        service.login("thiet", "matkhau123")

        update_queries = [
            query
            for query, _ in factory.executed
            if "UPDATE users" in query
        ]
        self.assertEqual(update_queries, [])

    def test_database_error_gives_safe_user_message(self):
        service = auth_service_with(failing_factory())

        result = service.login("thiet", "matkhau123")

        self.assertFalse(result.success)
        self.assertEqual(
            result.error_code,
            ConnectionFailedError.error_code,
        )
        self.assertIn("Không thể đăng nhập", result.message)
        self.assertNotIn("psycopg2", result.message)
        self.assertNotIn("matkhau123", result.message)


class AuthServiceRegisterTest(unittest.TestCase):
    def test_validation_rules_run_before_database(self):
        factory = FakeCursorFactory()
        service = auth_service_with(factory)

        cases = [
            (("", "u", "matkhau", "matkhau"), MSG_EMPTY_FULLNAME),
            (("Ten", "u", "123", "123"), MSG_SHORT_PASSWORD),
            (
                ("Ten", "u", "matkhau", "khac"),
                MSG_CONFIRM_MISMATCH,
            ),
        ]

        for arguments, expected in cases:
            result = service.register(*arguments)

            self.assertFalse(result.success)
            self.assertEqual(result.message, expected)

        self.assertEqual(
            factory.executed,
            [],
            "Validate that bai thi khong duoc goi database",
        )

    def test_existing_username_is_rejected(self):
        service = auth_service_with(
            FakeCursorFactory(
                results=[
                    [(7, "thiet", "Thach Thiet", "$2b$x")]
                ]
            )
        )

        result = service.register(
            "Thach Thiet",
            "thiet",
            "matkhau123",
            "matkhau123",
        )

        self.assertFalse(result.success)
        self.assertEqual(result.message, MSG_USERNAME_TAKEN)

    def test_successful_register_stores_hash_not_plaintext(self):
        factory = FakeCursorFactory(
            results=[
                [],
                [(9, "moi", "Nguoi Moi")],
            ]
        )
        service = auth_service_with(factory)

        result = service.register(
            "Nguoi Moi",
            "moi",
            "matkhau123",
            "matkhau123",
        )

        self.assertTrue(result.success)
        self.assertEqual(result.message, MSG_REGISTER_OK)

        insert_parameters = [
            parameters
            for query, parameters in factory.executed
            if "INSERT INTO users" in query
        ][0]

        self.assertNotIn("matkhau123", insert_parameters)
        self.assertTrue(
            insert_parameters[2].startswith("$2")
        )

    def test_integrity_error_becomes_username_taken(self):
        service = auth_service_with(integrity_factory())

        result = service.register(
            "Nguoi Moi",
            "moi",
            "matkhau123",
            "matkhau123",
        )

        self.assertFalse(result.success)
        self.assertEqual(result.message, MSG_USERNAME_TAKEN)


class AuthServiceChangePasswordTest(unittest.TestCase):
    HASHED = hash_password("cu123456")

    def test_requires_login(self):
        service = auth_service_with(FakeCursorFactory())

        result = service.change_password(
            None,
            "cu123456",
            "moi123456",
            "moi123456",
        )

        self.assertFalse(result.success)

    def test_wrong_old_password(self):
        service = auth_service_with(
            FakeCursorFactory(results=[[(self.HASHED,)]])
        )

        result = service.change_password(
            7,
            "sai",
            "moi123456",
            "moi123456",
        )

        self.assertFalse(result.success)
        self.assertEqual(result.message, MSG_WRONG_OLD_PASSWORD)

    def test_same_password_is_rejected(self):
        service = auth_service_with(
            FakeCursorFactory(results=[[(self.HASHED,)]])
        )

        result = service.change_password(
            7,
            "cu123456",
            "cu123456",
            "cu123456",
        )

        self.assertFalse(result.success)
        self.assertEqual(result.message, MSG_SAME_PASSWORD)

    def test_successful_change_stores_hash(self):
        factory = FakeCursorFactory(
            results=[
                [(self.HASHED,)],
                [],
            ]
        )
        service = auth_service_with(factory)

        result = service.change_password(
            7,
            "cu123456",
            "moi123456",
            "moi123456",
        )

        self.assertTrue(result.success)
        self.assertEqual(result.message, MSG_PASSWORD_CHANGED)

        update_parameters = [
            parameters
            for query, parameters in factory.executed
            if "UPDATE users" in query
        ][0]

        self.assertNotIn("moi123456", update_parameters)
        self.assertTrue(
            update_parameters[0].startswith("$2")
        )

    def test_unknown_user_is_reported_as_wrong_password(self):
        service = auth_service_with(
            FakeCursorFactory(results=[[]])
        )

        result = service.change_password(
            999,
            "cu123456",
            "moi123456",
            "moi123456",
        )

        self.assertFalse(result.success)
        self.assertEqual(result.message, MSG_WRONG_OLD_PASSWORD)


class FormatContractTest(unittest.TestCase):
    """Dinh dang gui sang View khong duoc doi sau Sprint 4."""

    def test_format_history_rows_unchanged(self):
        rows = [
            {
                "english_word": "laptop",
                "vietnamese_meaning": None,
                "category": None,
                "confidence": 0.9,
                "detected_time": datetime.datetime(
                    2026, 1, 2, 3, 4
                ),
            }
        ]

        formatted = format_history_rows(rows)[0]

        self.assertEqual(formatted["english"], "laptop")
        self.assertEqual(formatted["vietnamese"], "laptop")
        self.assertEqual(formatted["category"], "Unknown")
        self.assertEqual(
            formatted["detected_time"],
            "02/01/2026 03:04",
        )


if __name__ == "__main__":
    unittest.main()
