"""Service xac thuc nguoi dung.

Sprint 3 gom luat kiem tra du lieu tu `AuthController` ve day.
Sprint 4 doi tang duoi tu `database.auth` (ham thu tuc chua ca SQL, ca bcrypt,
ca business rule) sang `UserRepository` + `utils.password`.

Phan chia trach nhiem sau Sprint 4:

| Viec | Nam o dau |
|---|---|
| Cau SQL | `database.repositories.user_repository` |
| Bam / kiem tra mat khau | `utils.password` |
| Luat validate, luat nang cap hash | File nay |
| Trang thai phien dang nhap | `ui.viewmodels.auth_viewmodel` |
| Binding QML | `ui.auth_controller` |

Schema, thuat toan bam va cau SQL KHONG doi.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from database.entities import User
from database.exceptions import (
    IntegrityError,
    NotFoundError,
    RepositoryError,
)
from config.schema import UIConfig
from core import messages
from database.repositories.user_repository import UserRepository
from utils.password import (
    hash_password,
    needs_rehash,
    verify_password,
)


logger = logging.getLogger(__name__)


MIN_PASSWORD_LENGTH = UIConfig.min_password_length

# Sprint 7: noi dung thong diep nam trong `core/messages.py`.
# Cac ten duoi day duoc giu de code va test hien co khong bi vo.
MSG_MISSING_CREDENTIALS = messages.MSG_MISSING_CREDENTIALS
MSG_WRONG_CREDENTIALS = messages.MSG_WRONG_CREDENTIALS
MSG_LOGIN_OK = messages.MSG_LOGIN_OK
MSG_EMPTY_FULLNAME = messages.MSG_EMPTY_FULLNAME
MSG_EMPTY_USERNAME = messages.MSG_EMPTY_USERNAME
MSG_SHORT_PASSWORD = messages.short_password_message(
    MIN_PASSWORD_LENGTH
)
MSG_SHORT_NEW_PASSWORD = messages.short_new_password_message(
    MIN_PASSWORD_LENGTH
)
MSG_CONFIRM_MISMATCH = messages.MSG_CONFIRM_MISMATCH
MSG_USERNAME_TAKEN = messages.MSG_USERNAME_TAKEN
MSG_REGISTER_OK = messages.MSG_REGISTER_OK
MSG_NEED_LOGIN = messages.MSG_NEED_LOGIN
MSG_MISSING_OLD_PASSWORD = messages.MSG_MISSING_OLD_PASSWORD
MSG_SAME_PASSWORD = messages.MSG_SAME_PASSWORD
MSG_WRONG_OLD_PASSWORD = messages.MSG_WRONG_OLD_PASSWORD
MSG_PASSWORD_CHANGED = messages.MSG_PASSWORD_CHANGED


@dataclass(frozen=True)
class AuthResult:
    """Ket qua mot thao tac xac thuc."""

    success: bool
    message: str
    user: dict[str, Any] | None = None
    error_code: str | None = None


def normalize_user(
    user: User | dict[str, Any] | None,
) -> dict[str, Any]:
    """Chuan hoa thong tin nguoi dung cho View - KHONG kem mat khau."""
    if not user:
        return {}

    if isinstance(user, User):
        return user.to_public_dict()

    return {
        "id": int(user.get("id", 0)),
        "username": str(user.get("username", "")),
        "fullname": str(user.get("fullname", "")),
    }


class AuthService:
    """Diem truy cap duy nhat cua GUI toi xac thuc."""

    def __init__(
        self,
        repository: UserRepository | None = None,
    ) -> None:
        self._repository = (
            repository
            if repository is not None
            else UserRepository()
        )

    @property
    def repository(self) -> UserRepository:
        return self._repository

    @staticmethod
    def _failure_from(
        error: RepositoryError,
        prefix: str,
    ) -> AuthResult:
        """Doi loi ky thuat thanh thong diep nguoi dung, khong lo chi tiet DB."""
        logger.error(
            "%s [%s]: %s",
            prefix,
            error.error_code,
            error,
        )

        return AuthResult(
            success=False,
            message=f"{prefix}: {error.user_message}",
            error_code=error.error_code,
        )

    # ------------------------------------------------------------------
    # Dang nhap
    # ------------------------------------------------------------------

    def login(
        self,
        username: str,
        password: str,
    ) -> AuthResult:
        normalized_username = username.strip()

        if not normalized_username or not password:
            return AuthResult(
                success=False,
                message=MSG_MISSING_CREDENTIALS,
            )

        try:
            user = self._repository.find_by_username(
                normalized_username
            )

        except RepositoryError as error:
            return self._failure_from(
                error,
                messages.PREFIX_LOGIN_FAILED,
            )

        if user is None:
            return AuthResult(
                success=False,
                message=MSG_WRONG_CREDENTIALS,
            )

        if not verify_password(
            password,
            user.password_hash,
        ):
            return AuthResult(
                success=False,
                message=MSG_WRONG_CREDENTIALS,
            )

        self._upgrade_password_if_needed(user, password)

        return AuthResult(
            success=True,
            message=MSG_LOGIN_OK,
            user=user.to_public_dict(),
        )

    def _upgrade_password_if_needed(
        self,
        user: User,
        password: str,
    ) -> None:
        """Nang cap mat khau dang tho len bcrypt sau khi dang nhap dung.

        Day la business rule, truoc Sprint 4 no nam trong `database/auth.py`.
        Loi o buoc nay KHONG duoc lam hong viec dang nhap.
        """
        if not needs_rehash(user.password_hash):
            return

        try:
            self._repository.update_password_hash(
                user.id,
                hash_password(password),
            )
            logger.info(
                "Da nang cap mat khau len bcrypt cho user id=%s",
                user.id,
            )

        except RepositoryError as error:
            logger.warning(
                "Khong nang cap duoc mat khau [%s]: %s",
                error.error_code,
                error,
            )

    # ------------------------------------------------------------------
    # Dang ky
    # ------------------------------------------------------------------

    def register(
        self,
        fullname: str,
        username: str,
        password: str,
        confirm_password: str,
    ) -> AuthResult:
        normalized_fullname = fullname.strip()
        normalized_username = username.strip()

        if not normalized_fullname:
            return AuthResult(False, MSG_EMPTY_FULLNAME)

        if not normalized_username:
            return AuthResult(False, MSG_EMPTY_USERNAME)

        if len(password) < MIN_PASSWORD_LENGTH:
            return AuthResult(False, MSG_SHORT_PASSWORD)

        if password != confirm_password:
            return AuthResult(False, MSG_CONFIRM_MISMATCH)

        try:
            if self._repository.exists(normalized_username):
                return AuthResult(False, MSG_USERNAME_TAKEN)

            self._repository.create(
                normalized_fullname,
                normalized_username,
                hash_password(password),
            )

        except IntegrityError:
            return AuthResult(False, MSG_USERNAME_TAKEN)

        except RepositoryError as error:
            return self._failure_from(
                error,
                messages.PREFIX_REGISTER_FAILED,
            )

        return AuthResult(True, MSG_REGISTER_OK)

    # ------------------------------------------------------------------
    # Doi mat khau
    # ------------------------------------------------------------------

    def change_password(
        self,
        user_id: int | None,
        old_password: str,
        new_password: str,
        confirm_password: str,
    ) -> AuthResult:
        if user_id is None:
            return AuthResult(False, MSG_NEED_LOGIN)

        if not old_password:
            return AuthResult(False, MSG_MISSING_OLD_PASSWORD)

        if len(new_password) < MIN_PASSWORD_LENGTH:
            return AuthResult(False, MSG_SHORT_NEW_PASSWORD)

        if new_password != confirm_password:
            return AuthResult(False, MSG_CONFIRM_MISMATCH)

        if old_password == new_password:
            return AuthResult(False, MSG_SAME_PASSWORD)

        try:
            stored_password = self._repository.get_password_hash(
                int(user_id)
            )

        except NotFoundError:
            return AuthResult(False, MSG_WRONG_OLD_PASSWORD)

        except RepositoryError as error:
            return self._failure_from(
                error,
                messages.PREFIX_CHANGE_PASSWORD_FAILED,
            )

        if not verify_password(
            old_password,
            stored_password,
        ):
            return AuthResult(False, MSG_WRONG_OLD_PASSWORD)

        if verify_password(
            new_password,
            stored_password,
        ):
            return AuthResult(False, MSG_SAME_PASSWORD)

        try:
            self._repository.update_password_hash(
                int(user_id),
                hash_password(new_password),
            )

        except RepositoryError as error:
            return self._failure_from(
                error,
                messages.PREFIX_CHANGE_PASSWORD_FAILED,
            )

        return AuthResult(True, MSG_PASSWORD_CHANGED)
