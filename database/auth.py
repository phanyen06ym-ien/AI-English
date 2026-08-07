"""Compatibility shim cho tang xac thuc.

Sprint 4 tach 3 trach nhiem tung bi tron trong file nay:

| Trach nhiem | Truoc Sprint 4 | Sau Sprint 4 |
|---|---|---|
| Cau SQL | `database/auth.py` | `database.repositories.user_repository` |
| Bam / kiem tra mat khau | `database/auth.py` | `utils.password` |
| Luat nghiep vu (validate, nang cap hash) | `database/auth.py` | `ui.services.auth_service` |

Module nay chi con la lop tuong thich cho script cu. API va hanh vi giu nguyen,
ke ca viec tu dong nang cap mat khau dang tho len bcrypt khi dang nhap thanh cong.

Code moi goi thang `UserRepository` + `AuthService`.
"""

from __future__ import annotations

from typing import Optional

from database.entities import User
from database.exceptions import NotFoundError
from database.repositories.user_repository import UserRepository
from utils.password import (
    hash_password,
    is_bcrypt_hash,
    needs_rehash,
    verify_password,
)


_repository = UserRepository()


# ----------------------------------------------------------------------
# Giu lai ten private cu de script cu import duoc
# ----------------------------------------------------------------------

_hash_password = hash_password
_is_bcrypt_hash = is_bcrypt_hash
_verify_password = verify_password


def _user_to_legacy_dict(
    user: User,
    include_password: bool = True,
) -> dict:
    data = user.to_public_dict()

    if include_password:
        data["password"] = user.password_hash

    return data


def find_user_by_username(
    username: str,
) -> Optional[dict]:
    """Tim nguoi dung theo ten dang nhap."""
    user = _repository.find_by_username(username)

    if user is None:
        return None

    return _user_to_legacy_dict(user)


def username_exists(
    username: str,
) -> bool:
    return _repository.exists(username)


def create_user(
    fullname: str,
    username: str,
    password_hash: str,
) -> dict:
    user = _repository.create(
        fullname,
        username,
        password_hash,
    )

    return user.to_public_dict()


def _update_password_hash(
    user_id: int,
    password_hash: str,
) -> None:
    _repository.update_password_hash(
        user_id,
        password_hash,
    )


def verify_login(
    username: str,
    password: str,
) -> Optional[dict]:
    """Kiem tra dang nhap.

    Giu nguyen hanh vi cu: neu mat khau dang luu chua duoc bam, tu dong nang cap
    len bcrypt sau khi dang nhap thanh cong.
    """
    user = _repository.find_by_username(username)

    if user is None:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    if needs_rehash(user.password_hash):
        _repository.update_password_hash(
            user.id,
            hash_password(password),
        )

    return user.to_public_dict()


def register_user(
    fullname: str,
    username: str,
    password: str,
) -> dict:
    return create_user(
        fullname,
        username,
        hash_password(password),
    )


def change_password(
    user_id: int,
    old_password: str,
    new_password: str,
) -> bool:
    """Doi mat khau. False neu mat khau cu sai hoac trung mat khau moi."""
    try:
        stored_password = _repository.get_password_hash(user_id)

    except NotFoundError:
        return False

    if not verify_password(
        old_password,
        stored_password,
    ):
        return False

    if verify_password(
        new_password,
        stored_password,
    ):
        return False

    _repository.update_password_hash(
        user_id,
        hash_password(new_password),
    )

    return True


def login_user(
    username: str,
    password: str,
) -> Optional[dict]:
    return verify_login(
        username,
        password,
    )


__all__ = [
    "find_user_by_username",
    "username_exists",
    "create_user",
    "verify_login",
    "register_user",
    "change_password",
    "login_user",
]
