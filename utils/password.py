"""Bam va kiem tra mat khau.

Truoc Sprint 4, cac ham nay nam trong `database/auth.py` - tuc la tang truy van
SQL cung chiu trach nhiem ve mat ma hoc. Sprint 4 tach ra thanh tien ich dung
chung, khong phu thuoc database.

Thuat toan KHONG doi: van la bcrypt voi `gensalt()` mac dinh, va van chap nhan
mat khau dang tho de tuong thich du lieu cu.
"""

from __future__ import annotations


BCRYPT_PREFIXES = (
    "$2a$",
    "$2b$",
    "$2y$",
)


def _load_bcrypt():
    try:
        import bcrypt

        return bcrypt

    except ImportError as error:
        raise RuntimeError(
            "bcrypt is required for authentication. "
            "Install dependencies with: pip install -r requirements.txt"
        ) from error


def hash_password(
    password: str,
) -> str:
    """Bam mat khau bang bcrypt."""
    bcrypt = _load_bcrypt()

    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def is_bcrypt_hash(
    value: str,
) -> bool:
    """True neu chuoi da la hash bcrypt."""
    return bool(value) and value.startswith(BCRYPT_PREFIXES)


def verify_password(
    password: str,
    stored_password: str,
) -> bool:
    """Kiem tra mat khau voi gia tri dang luu.

    Ho tro ca hash bcrypt va mat khau dang tho (du lieu cu).
    """
    if not stored_password:
        return False

    if is_bcrypt_hash(stored_password):
        bcrypt = _load_bcrypt()

        return bcrypt.checkpw(
            password.encode("utf-8"),
            stored_password.encode("utf-8"),
        )

    return password == stored_password


def needs_rehash(
    stored_password: str,
) -> bool:
    """True neu gia tri dang luu chua duoc bam - can nang cap len bcrypt."""
    return not is_bcrypt_hash(stored_password)


__all__ = [
    "hash_password",
    "is_bcrypt_hash",
    "verify_password",
    "needs_rehash",
]
