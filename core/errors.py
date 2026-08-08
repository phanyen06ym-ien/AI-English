"""Cay exception thong nhat cua toan he thong.

Van de truoc Sprint 7
---------------------

Moi tang tu nghi ra cach bao loi cua rieng minh:

    config/errors.py       ConfigError(Exception)      co error_code
    database/exceptions.py RepositoryError(Exception)  co error_code + user_message
    ai/models.py           ImageAnalysisResult         chi co chuoi error_code
    ui/                    khong co gi                 nem Exception tho

Khong the viet mot cho bat loi chung, vi khong co lop cha chung. Muon bat "moi
loi cua ung dung" thi phai liet ke tung lop mot, va se quen mot vai lop.

Giai phap
---------

Mot goc duy nhat:

    AppError                            APP_ERROR
      ├── ConfigError                   CONFIG_ERROR       (config/errors.py)
      │     ├── ConfigValidationError   CONFIG_VALIDATION_ERROR
      │     └── MissingConfigError      CONFIG_MISSING
      ├── RepositoryError               REPOSITORY_ERROR   (database/exceptions.py)
      │     ├── ConnectionFailedError   DB_CONNECTION_FAILED
      │     ├── QueryFailedError        DB_QUERY_FAILED
      │     ├── NotFoundError           DB_NOT_FOUND
      │     └── IntegrityError          DB_INTEGRITY_ERROR
      ├── AIError                       AI_ERROR
      │     ├── ModelLoadError          AI_MODEL_LOAD_FAILED
      │     └── InferenceError          AI_INFERENCE_FAILED
      ├── UIError                       UI_ERROR
      │     ├── MediaError              UI_MEDIA_ERROR
      │     └── OperationCancelled      UI_OPERATION_CANCELLED
      └── ExternalServiceError          EXTERNAL_SERVICE_ERROR
            ├── SpeechError             EXTERNAL_SPEECH_ERROR
            └── TranslationError        EXTERNAL_TRANSLATION_ERROR

Moi loi mang HAI thong diep, tach bach ro rang:

- `technical_message` : cho lap trinh vien, ghi vao log, co the kem chi tiet ky thuat.
- `user_message`      : cho nguoi dung cuoi, tieng Viet, KHONG bao gio lo chi tiet
                        ky thuat hay du lieu nhay cam.

Day la diem mau chot: truoc Sprint 7, thong diep gui cho nguoi dung duoc ghep
bang `f"Không thể đăng nhập: {error}"` — tuc la noi dung loi psycopg2 (co the kem
chuoi ket noi) hien thang len man hinh.
"""

from __future__ import annotations


class AppError(Exception):
    """Goc cua moi loi do ung dung tu dinh nghia.

    Bat `AppError` la bat duoc moi loi da biet cua he thong. Loi KHONG phai
    `AppError` la loi ngoai du kien - phai ghi log kem stack trace.
    """

    #: Ma loi on dinh, dung de tang tren nhan dien ma khong phai doc chuoi.
    error_code: str = "APP_ERROR"

    #: Thong diep mac dinh cho nguoi dung cuoi.
    user_message: str = "Đã xảy ra lỗi. Vui lòng thử lại."

    def __init__(
        self,
        message: str = "",
        cause: Exception | None = None,
        user_message: str | None = None,
    ) -> None:
        resolved_technical = message or self.user_message

        super().__init__(resolved_technical)

        #: Thong diep ky thuat - CHI ghi vao log.
        self.technical_message = resolved_technical

        #: Thong diep hien thi - CHI dua cho nguoi dung.
        self.display_message = (
            user_message
            if user_message
            else self.user_message
        )

        self.cause = cause

    # Giu ten cu de code Sprint 4 khong bi vo.
    @property
    def message(self) -> str:
        return self.technical_message

    def to_dict(self) -> dict[str, str]:
        """Ban ghi cho log co cau truc. KHONG chua du lieu nhay cam."""
        return {
            "error_code": self.error_code,
            "error_type": type(self).__name__,
            "technical_message": self.technical_message,
            "user_message": self.display_message,
            "cause_type": (
                type(self.cause).__name__
                if self.cause is not None
                else ""
            ),
        }

    def __str__(self) -> str:
        if self.cause is None:
            return self.technical_message

        return f"{self.technical_message} ({self.cause})"


# ----------------------------------------------------------------------
# AI
# ----------------------------------------------------------------------


class AIError(AppError):
    """Loi cua tang AI."""

    error_code = "AI_ERROR"
    user_message = "Không xử lý được nhận diện. Vui lòng thử lại."


class ModelLoadError(AIError):
    """Khong nap duoc mo hinh YOLO hoac model .pkl."""

    error_code = "AI_MODEL_LOAD_FAILED"
    user_message = "Không tải được mô hình nhận diện."


class InferenceError(AIError):
    """Pipeline nhan dien that bai giua chung."""

    error_code = "AI_INFERENCE_FAILED"
    user_message = "Nhận diện thất bại. Vui lòng thử lại."


# ----------------------------------------------------------------------
# Giao dien
# ----------------------------------------------------------------------


class UIError(AppError):
    """Loi cua tang giao dien."""

    error_code = "UI_ERROR"
    user_message = "Thao tác không thực hiện được."


class MediaError(UIError):
    """Khong doc duoc anh hoac khong mo duoc camera."""

    error_code = "UI_MEDIA_ERROR"
    user_message = "Không đọc được tệp phương tiện."


class OperationCancelled(UIError):
    """Nguoi dung huy thao tac. KHONG phai loi that su."""

    error_code = "UI_OPERATION_CANCELLED"
    user_message = "Đã hủy thao tác."


# ----------------------------------------------------------------------
# Dich vu ben ngoai
# ----------------------------------------------------------------------


class ExternalServiceError(AppError):
    """Loi khi goi dich vu ben ngoai (mang, API)."""

    error_code = "EXTERNAL_SERVICE_ERROR"
    user_message = "Dịch vụ bên ngoài không phản hồi."


class SpeechError(ExternalServiceError):
    """Khong tao hoac khong phat duoc am thanh."""

    error_code = "EXTERNAL_SPEECH_ERROR"
    user_message = "Không phát được âm thanh."


class TranslationError(ExternalServiceError):
    """Khong dich duoc tu."""

    error_code = "EXTERNAL_TRANSLATION_ERROR"
    user_message = "Không dịch được từ này."


# ----------------------------------------------------------------------
# Tien ich
# ----------------------------------------------------------------------


def user_message_for(
    error: BaseException,
    fallback: str = AppError.user_message,
) -> str:
    """Thong diep an toan de hien cho nguoi dung.

    Loi khong phai `AppError` KHONG duoc hien noi dung goc: noi dung do co the
    chua chuoi ket noi database, duong dan he thong hoac ten dang nhap.
    """
    if isinstance(error, AppError):
        return error.display_message

    return fallback


def error_code_for(
    error: BaseException,
    fallback: str = "UNEXPECTED_ERROR",
) -> str:
    """Ma loi cua mot exception bat ky."""
    if isinstance(error, AppError):
        return error.error_code

    return fallback


def all_error_codes() -> dict[str, type[AppError]]:
    """Toan bo ma loi da dang ky - dung de kiem tra trung lap."""
    codes: dict[str, type[AppError]] = {}

    def walk(cls: type[AppError]) -> None:
        codes[cls.error_code] = cls

        for subclass in cls.__subclasses__():
            walk(subclass)

    walk(AppError)

    return codes


__all__ = [
    "AIError",
    "AppError",
    "ExternalServiceError",
    "InferenceError",
    "MediaError",
    "ModelLoadError",
    "OperationCancelled",
    "SpeechError",
    "TranslationError",
    "UIError",
    "all_error_codes",
    "error_code_for",
    "user_message_for",
]
