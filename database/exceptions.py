"""Cay exception cua tang du lieu.

Truoc Sprint 4, tang database nuot loi va tra ve gia tri rong:

    get_history()  loi ket noi -> tra ve []
    save_history() loi ket noi -> tra ve False

GUI khong the phan biet "khong co du lieu" voi "database hong".

Sprint 4 dinh nghia exception rieng cho tung loai su co. Tang tren bat dung loai
loi minh quan tam, khong con phai doan tu gia tri tra ve.

    RepositoryError
      ├── ConnectionFailedError   khong ket noi duoc database
      ├── QueryFailedError        cau lenh SQL that bai
      ├── NotFoundError           khong tim thay ban ghi
      └── IntegrityError          vi pham rang buoc du lieu
"""

from __future__ import annotations

from core import messages
from core.errors import AppError


class RepositoryError(AppError):
    """Loi goc cua tang Repository.

    Sprint 7: ke thua `AppError` de bat duoc chung voi moi loi khac cua he thong.
    API (`error_code`, `user_message`, `message`, `cause`) giu nguyen.
    """

    error_code = "REPOSITORY_ERROR"
    user_message = messages.MSG_DATA_UNAVAILABLE


class ConnectionFailedError(RepositoryError):
    """Khong mo duoc ket noi toi database."""

    error_code = "DB_CONNECTION_FAILED"
    user_message = messages.MSG_DATABASE_UNREACHABLE


class QueryFailedError(RepositoryError):
    """Cau lenh SQL that bai."""

    error_code = "DB_QUERY_FAILED"
    user_message = messages.MSG_DATA_OPERATION_FAILED


class NotFoundError(RepositoryError):
    """Khong tim thay ban ghi can tim."""

    error_code = "DB_NOT_FOUND"
    user_message = messages.MSG_DATA_NOT_FOUND


class IntegrityError(RepositoryError):
    """Vi pham rang buoc du lieu, vi du trung username."""

    error_code = "DB_INTEGRITY_ERROR"
    user_message = messages.MSG_DATA_INVALID


__all__ = [
    "RepositoryError",
    "ConnectionFailedError",
    "QueryFailedError",
    "NotFoundError",
    "IntegrityError",
]
