from __future__ import annotations

from typing import Optional

from database.db import database_cursor


def _load_bcrypt():
    try:
        import bcrypt

        return bcrypt

    except ImportError as error:
        raise RuntimeError(
            "bcrypt is required for authentication. "
            "Install dependencies with: pip install -r requirements.txt"
        ) from error


def _hash_password(password: str) -> str:
    bcrypt = _load_bcrypt()
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def _is_bcrypt_hash(value: str) -> bool:
    return (
        value.startswith("$2a$")
        or value.startswith("$2b$")
        or value.startswith("$2y$")
    )


def _verify_password(
    password: str,
    stored_password: str,
) -> bool:
    if not stored_password:
        return False

    if _is_bcrypt_hash(stored_password):
        bcrypt = _load_bcrypt()
        return bcrypt.checkpw(
            password.encode("utf-8"),
            stored_password.encode("utf-8"),
        )

    return password == stored_password


def find_user_by_username(
    username: str,
) -> Optional[dict]:
    normalized_username = username.strip()

    if not normalized_username:
        return None

    query = """
        SELECT
            id,
            username,
            fullname,
            password
        FROM users
        WHERE username = %s
        LIMIT 1;
    """

    try:
        with database_cursor() as cursor:
            cursor.execute(
                query,
                (normalized_username,),
            )
            row = cursor.fetchone()

    except Exception as error:
        print(
            f"Database error while finding user: {error}"
        )
        raise

    if row is None:
        return None

    return {
        "id": row[0],
        "username": row[1],
        "fullname": row[2],
        "password": row[3],
    }


def username_exists(
    username: str,
) -> bool:
    return find_user_by_username(username) is not None


def create_user(
    fullname: str,
    username: str,
    password_hash: str,
) -> dict:
    query = """
        INSERT INTO users (
            fullname,
            username,
            password
        )
        VALUES (%s, %s, %s)
        RETURNING id, username, fullname;
    """

    with database_cursor(commit=True) as cursor:
        cursor.execute(
            query,
            (
                fullname.strip(),
                username.strip(),
                password_hash,
            ),
        )
        row = cursor.fetchone()

    return {
        "id": row[0],
        "username": row[1],
        "fullname": row[2],
    }


def _update_password_hash(
    user_id: int,
    password_hash: str,
) -> None:
    query = """
        UPDATE users
        SET password = %s
        WHERE id = %s;
    """

    with database_cursor(commit=True) as cursor:
        cursor.execute(
            query,
            (
                password_hash,
                user_id,
            ),
        )


def verify_login(
    username: str,
    password: str,
) -> Optional[dict]:
    user = find_user_by_username(username)

    if user is None:
        return None

    stored_password = user.get("password") or ""

    if not _verify_password(
        password,
        stored_password,
    ):
        return None

    if not _is_bcrypt_hash(stored_password):
        _update_password_hash(
            int(user["id"]),
            _hash_password(password),
        )

    return {
        "id": user["id"],
        "username": user["username"],
        "fullname": user["fullname"],
    }


def register_user(
    fullname: str,
    username: str,
    password: str,
) -> dict:
    return create_user(
        fullname,
        username,
        _hash_password(password),
    )


def change_password(
    user_id: int,
    old_password: str,
    new_password: str,
) -> bool:
    query = """
        SELECT password
        FROM users
        WHERE id = %s
        LIMIT 1;
    """

    with database_cursor() as cursor:
        cursor.execute(
            query,
            (user_id,),
        )
        row = cursor.fetchone()

    if row is None:
        return False

    stored_password = row[0] or ""

    if not _verify_password(
        old_password,
        stored_password,
    ):
        return False

    if _verify_password(
        new_password,
        stored_password,
    ):
        return False

    _update_password_hash(
        user_id,
        _hash_password(new_password),
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
