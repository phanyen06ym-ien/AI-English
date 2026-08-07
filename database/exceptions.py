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


class RepositoryError(Exception):
    """Loi goc cua tang Repository."""

    #: Ma loi de tang tren nhan dien ma khong can doc chuoi.
    error_code = "REPOSITORY_ERROR"

    #: Thong diep hien thi cho nguoi dung cuoi.
    user_message = "Không truy cập được dữ liệu."

    def __init__(
        self,
        message: str = "",
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message or self.user_message)

        self.message = message or self.user_message
        self.cause = cause

    def __str__(self) -> str:
        if self.cause is None:
            return self.message

        return f"{self.message} ({self.cause})"


class ConnectionFailedError(RepositoryError):
    """Khong mo duoc ket noi toi database."""

    error_code = "DB_CONNECTION_FAILED"
    user_message = "Không kết nối được cơ sở dữ liệu."


class QueryFailedError(RepositoryError):
    """Cau lenh SQL that bai."""

    error_code = "DB_QUERY_FAILED"
    user_message = "Không thực hiện được thao tác dữ liệu."


class NotFoundError(RepositoryError):
    """Khong tim thay ban ghi can tim."""

    error_code = "DB_NOT_FOUND"
    user_message = "Không tìm thấy dữ liệu."


class IntegrityError(RepositoryError):
    """Vi pham rang buoc du lieu, vi du trung username."""

    error_code = "DB_INTEGRITY_ERROR"
    user_message = "Dữ liệu không hợp lệ hoặc đã tồn tại."


__all__ = [
    "RepositoryError",
    "ConnectionFailedError",
    "QueryFailedError",
    "NotFoundError",
    "IntegrityError",
]
