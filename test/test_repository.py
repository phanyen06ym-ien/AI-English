"""Sprint 4 - Unit test cho Repository layer.

Kiem tra:

1. Repository tra ve Entity, khong tra ve tuple tho.
2. Cau SQL va tham so dung nhu truoc Sprint 4.
3. Transaction boundary: chi INSERT/UPDATE/DELETE moi commit.
4. Loi database duoc nem ra ngoai, khong bi nuot.
5. Repository khong chua business rule.

Toan bo test chay KHONG can PostgreSQL that.
"""

from __future__ import annotations

import datetime
import inspect
import unittest

from test.db_fakes import (
    FakeCursorFactory,
    failing_factory,
)

from database.entities import HistoryEntry, User
from database.exceptions import (
    ConnectionFailedError,
    IntegrityError,
    NotFoundError,
    QueryFailedError,
    RepositoryError,
)
from database.repositories.history_repository import (
    MAX_LIMIT,
    MIN_LIMIT,
    HistoryRepository,
    clamp_limit,
)
from database.repositories.user_repository import UserRepository


USER_ROW = (7, "thiet", "Thach Thiet", "$2b$12$abcdefghijklmnopqrstuv")

HISTORY_ROW = (
    1,
    7,
    "laptop",
    "May tinh xach tay",
    "Technology",
    0.93,
    datetime.datetime(2026, 1, 2, 3, 4),
)


class EntityTest(unittest.TestCase):
    """NHIEM VU 4 - Entity thay cho tuple tho."""

    def test_user_from_row(self):
        user = User.from_row(USER_ROW)

        self.assertEqual(user.id, 7)
        self.assertEqual(user.username, "thiet")
        self.assertEqual(user.fullname, "Thach Thiet")
        self.assertTrue(user.password_hash.startswith("$2b$"))

    def test_user_public_dict_hides_password(self):
        user = User.from_row(USER_ROW)
        data = user.to_public_dict()

        self.assertNotIn("password", data)
        self.assertNotIn("password_hash", data)
        self.assertEqual(
            set(data),
            {"id", "username", "fullname"},
        )

    def test_user_from_row_without_password_column(self):
        user = User.from_row(
            (7, "thiet", "Thach Thiet"),
            include_password=False,
        )

        self.assertEqual(user.password_hash, "")

    def test_history_entry_from_row(self):
        entry = HistoryEntry.from_row(HISTORY_ROW)

        self.assertEqual(entry.english_word, "laptop")
        self.assertEqual(entry.category, "Technology")
        self.assertAlmostEqual(entry.confidence, 0.93)
        self.assertEqual(entry.user_id, 7)

    def test_history_entry_null_fallbacks(self):
        entry = HistoryEntry.from_row(
            (1, None, "laptop", None, None, None, None)
        )

        self.assertEqual(entry.vietnamese_meaning, "")
        self.assertEqual(entry.category, "Unknown")
        self.assertEqual(entry.confidence, 0.0)
        self.assertIsNone(entry.detected_time)

    def test_history_entry_dict_keys_match_service_contract(self):
        entry = HistoryEntry.from_row(HISTORY_ROW)
        data = entry.to_dict()

        for key in (
            "id",
            "user_id",
            "english_word",
            "vietnamese_meaning",
            "category",
            "confidence",
            "detected_time",
        ):
            self.assertIn(key, data)


class ExceptionHierarchyTest(unittest.TestCase):
    """NHIEM VU 5 - Exception rieng cho tang du lieu."""

    def test_all_errors_derive_from_repository_error(self):
        for error_class in (
            ConnectionFailedError,
            QueryFailedError,
            NotFoundError,
            IntegrityError,
        ):
            self.assertTrue(
                issubclass(error_class, RepositoryError)
            )

    def test_each_error_has_code_and_user_message(self):
        for error_class in (
            RepositoryError,
            ConnectionFailedError,
            QueryFailedError,
            NotFoundError,
            IntegrityError,
        ):
            error = error_class()

            self.assertTrue(error.error_code)
            self.assertTrue(error.user_message)

    def test_error_codes_are_unique(self):
        codes = [
            error_class.error_code
            for error_class in (
                RepositoryError,
                ConnectionFailedError,
                QueryFailedError,
                NotFoundError,
                IntegrityError,
            )
        ]

        self.assertEqual(len(codes), len(set(codes)))

    def test_cause_is_kept(self):
        cause = ValueError("goc")
        error = QueryFailedError("that bai", cause=cause)

        self.assertIs(error.cause, cause)
        self.assertIn("goc", str(error))


class UserRepositoryTest(unittest.TestCase):
    def test_find_by_username_returns_entity(self):
        factory = FakeCursorFactory(results=[[USER_ROW]])
        repository = UserRepository(cursor_factory=factory)

        user = repository.find_by_username("  thiet  ")

        self.assertIsInstance(user, User)
        self.assertEqual(user.username, "thiet")
        self.assertEqual(
            factory.last_parameters(),
            ("thiet",),
        )

    def test_find_by_username_returns_none_when_missing(self):
        factory = FakeCursorFactory(results=[[]])
        repository = UserRepository(cursor_factory=factory)

        self.assertIsNone(
            repository.find_by_username("khong-co")
        )

    def test_empty_username_does_not_touch_database(self):
        factory = FakeCursorFactory()
        repository = UserRepository(cursor_factory=factory)

        self.assertIsNone(
            repository.find_by_username("   ")
        )
        self.assertEqual(factory.executed, [])

    def test_select_does_not_commit(self):
        factory = FakeCursorFactory(results=[[USER_ROW]])
        repository = UserRepository(cursor_factory=factory)

        repository.find_by_username("thiet")

        self.assertFalse(factory.committed())

    def test_create_commits_and_returns_entity(self):
        factory = FakeCursorFactory(
            results=[[(9, "moi", "Nguoi Moi")]]
        )
        repository = UserRepository(cursor_factory=factory)

        user = repository.create(
            "  Nguoi Moi  ",
            "  moi  ",
            "$2b$hash",
        )

        self.assertTrue(factory.committed())
        self.assertEqual(user.id, 9)
        self.assertEqual(user.password_hash, "")
        self.assertEqual(
            factory.last_parameters(),
            ("Nguoi Moi", "moi", "$2b$hash"),
        )

    def test_update_password_commits(self):
        factory = FakeCursorFactory(rowcount=1)
        repository = UserRepository(cursor_factory=factory)

        changed = repository.update_password_hash(7, "$2b$new")

        self.assertTrue(changed)
        self.assertTrue(factory.committed())

    def test_update_password_reports_no_row(self):
        factory = FakeCursorFactory(rowcount=0)
        repository = UserRepository(cursor_factory=factory)

        self.assertFalse(
            repository.update_password_hash(999, "$2b$new")
        )

    def test_get_password_hash_raises_when_user_missing(self):
        factory = FakeCursorFactory(results=[[]])
        repository = UserRepository(cursor_factory=factory)

        with self.assertRaises(NotFoundError):
            repository.get_password_hash(999)

    def test_database_error_is_raised_not_swallowed(self):
        repository = UserRepository(
            cursor_factory=failing_factory()
        )

        with self.assertRaises(ConnectionFailedError):
            repository.find_by_username("thiet")

    def test_repository_has_no_password_logic(self):
        source = inspect.getsource(
            inspect.getmodule(UserRepository)
        )

        for forbidden in ("bcrypt", "hashpw", "checkpw"):
            self.assertNotIn(
                forbidden,
                source,
                "Repository khong duoc chua logic mat ma hoc",
            )


class HistoryRepositoryTest(unittest.TestCase):
    def test_list_by_user_returns_entities(self):
        factory = FakeCursorFactory(
            results=[[HISTORY_ROW, HISTORY_ROW]]
        )
        repository = HistoryRepository(cursor_factory=factory)

        entries = repository.list_by_user(user_id=7, limit=200)

        self.assertEqual(len(entries), 2)
        self.assertIsInstance(entries[0], HistoryEntry)
        self.assertEqual(
            factory.last_parameters(),
            (7, 200),
        )

    def test_list_all_when_user_id_is_none(self):
        factory = FakeCursorFactory(results=[[HISTORY_ROW]])
        repository = HistoryRepository(cursor_factory=factory)

        repository.list_by_user(user_id=None, limit=50)

        self.assertNotIn(
            "WHERE user_id",
            factory.last_query(),
        )
        self.assertEqual(
            factory.last_parameters(),
            (50,),
        )

    def test_limit_is_clamped(self):
        self.assertEqual(clamp_limit(0), MIN_LIMIT)
        self.assertEqual(clamp_limit(-5), MIN_LIMIT)
        self.assertEqual(clamp_limit(9999), MAX_LIMIT)
        self.assertEqual(clamp_limit(200), 200)

    def test_add_normalizes_and_commits(self):
        factory = FakeCursorFactory(rowcount=1)
        repository = HistoryRepository(cursor_factory=factory)

        saved = repository.add(
            "  laptop  ",
            "  May tinh  ",
            None,
            0.93,
            user_id=7,
        )

        self.assertTrue(saved)
        self.assertTrue(factory.committed())
        self.assertEqual(
            factory.last_parameters(),
            (7, "laptop", "May tinh", "Unknown", 0.93),
        )

    def test_add_rejects_empty_word_without_touching_database(self):
        factory = FakeCursorFactory()
        repository = HistoryRepository(cursor_factory=factory)

        self.assertFalse(
            repository.add("   ", "x", "y", 0.9)
        )
        self.assertEqual(factory.executed, [])

    def test_delete_by_user_commits(self):
        factory = FakeCursorFactory(rowcount=3)
        repository = HistoryRepository(cursor_factory=factory)

        deleted = repository.delete_by_user(7)

        self.assertEqual(deleted, 3)
        self.assertTrue(factory.committed())
        self.assertEqual(
            factory.last_parameters(),
            (7,),
        )

    def test_delete_all_when_user_id_is_none(self):
        factory = FakeCursorFactory(rowcount=10)
        repository = HistoryRepository(cursor_factory=factory)

        repository.delete_by_user(None)

        self.assertNotIn(
            "WHERE",
            factory.last_query(),
        )

    def test_database_error_is_raised_not_swallowed(self):
        repository = HistoryRepository(
            cursor_factory=failing_factory()
        )

        with self.assertRaises(ConnectionFailedError):
            repository.list_by_user(user_id=7)

        with self.assertRaises(ConnectionFailedError):
            repository.add("laptop", "x", "y", 0.9)

    def test_rollback_happens_on_error(self):
        factory = failing_factory()
        repository = HistoryRepository(cursor_factory=factory)

        with self.assertRaises(RepositoryError):
            repository.add("laptop", "x", "y", 0.9)

        self.assertEqual(factory.rollbacks, 1)
        self.assertFalse(factory.committed())


class RepositoryIsolationTest(unittest.TestCase):
    """Repository khong duoc chua business rule hoac cham vao GUI."""

    REPOSITORY_MODULES = (
        "database.repositories.base",
        "database.repositories.user_repository",
        "database.repositories.history_repository",
    )

    def test_repositories_do_not_import_ui_or_ai(self):
        import importlib

        for module_name in self.REPOSITORY_MODULES:
            module = importlib.import_module(module_name)
            source = inspect.getsource(module)

            for forbidden in (
                "from ui",
                "from ai",
                "PySide6",
                "import cv2",
            ):
                self.assertNotIn(
                    forbidden,
                    source,
                    f"{module_name} phai doc lap voi GUI/AI",
                )

    def test_repositories_do_not_print(self):
        import importlib

        for module_name in self.REPOSITORY_MODULES:
            module = importlib.import_module(module_name)
            source = inspect.getsource(module)

            self.assertNotIn(
                "print(",
                source,
                f"{module_name} khong duoc dung print()",
            )


class LegacyShimTest(unittest.TestCase):
    """NHIEM VU 9 - Script cu van chay duoc."""

    def test_database_history_module_keeps_old_api(self):
        from database import history

        for name in (
            "save_history",
            "get_history",
            "clear_history",
            "delete_history_by_user",
        ):
            self.assertTrue(
                callable(getattr(history, name)),
                f"database.history.{name} phai con ton tai",
            )

    def test_database_auth_module_keeps_old_api(self):
        from database import auth

        for name in (
            "find_user_by_username",
            "username_exists",
            "create_user",
            "verify_login",
            "register_user",
            "change_password",
            "login_user",
        ):
            self.assertTrue(
                callable(getattr(auth, name)),
                f"database.auth.{name} phai con ton tai",
            )

    def test_database_db_module_keeps_old_api(self):
        from database import db

        self.assertTrue(callable(db.get_connection))
        self.assertTrue(callable(db.database_cursor))

    def test_legacy_history_swallows_error_like_before(self):
        from database import history

        original = history._repository
        history._repository = HistoryRepository(
            cursor_factory=failing_factory()
        )

        try:
            self.assertEqual(
                history.get_history(user_id=1),
                [],
            )
            self.assertFalse(
                history.save_history("laptop", "x", "y", 0.9)
            )
            self.assertFalse(
                history.clear_history(1)
            )
        finally:
            history._repository = original

    def test_legacy_auth_still_rehashes_plaintext(self):
        from database import auth

        plaintext_row = (7, "thiet", "Thach Thiet", "matkhau123")
        factory = FakeCursorFactory(
            results=[[plaintext_row], []]
        )

        original = auth._repository
        auth._repository = UserRepository(cursor_factory=factory)

        try:
            user = auth.verify_login("thiet", "matkhau123")
        finally:
            auth._repository = original

        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "thiet")
        self.assertNotIn("password", user)

        update_queries = [
            query
            for query, _ in factory.executed
            if "UPDATE users" in query
        ]
        self.assertEqual(
            len(update_queries),
            1,
            "Phai tu nang cap mat khau tho len bcrypt nhu truoc",
        )


class PasswordUtilTest(unittest.TestCase):
    """NHIEM VU 7 - Logic mat ma hoc da roi khoi tang truy van."""

    def test_hash_and_verify(self):
        from utils.password import hash_password, verify_password

        hashed = hash_password("matkhau123")

        self.assertTrue(verify_password("matkhau123", hashed))
        self.assertFalse(verify_password("sai", hashed))

    def test_plaintext_is_still_accepted(self):
        from utils.password import verify_password

        self.assertTrue(
            verify_password("matkhau123", "matkhau123")
        )

    def test_needs_rehash(self):
        from utils.password import (
            hash_password,
            needs_rehash,
        )

        self.assertTrue(needs_rehash("matkhau123"))
        self.assertFalse(
            needs_rehash(hash_password("matkhau123"))
        )

    def test_empty_stored_password_is_rejected(self):
        from utils.password import verify_password

        self.assertFalse(verify_password("bat ky", ""))


if __name__ == "__main__":
    unittest.main()
