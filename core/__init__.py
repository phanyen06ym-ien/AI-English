"""Tang loi va logging dung chung cho toan he thong.

    core/errors.py          Cay exception co goc `AppError`
    core/logging_config.py  Logger phan cap, console + file xoay vong
    core/redaction.py       Chan ro ri du lieu nhay cam ra log
    core/messages.py        Catalog thong diep hien thi cho nguoi dung

Quy tac Sprint 7:

1. Moi loi do ung dung dinh nghia deu ke thua `AppError`.
2. Moi loi mang HAI thong diep: `technical_message` (cho log) va
   `display_message` (cho nguoi dung). Khong bao gio dung nham.
3. Khong tang nao duoc goi `print()` - dung logger cua tang minh.
4. Khong nuot loi im lang: hoac xu ly, hoac ghi log, hoac nem tiep.
5. Mat khau va chuoi ket noi khong bao gio lot ra log.
"""

from __future__ import annotations

from core.errors import (
    AIError,
    AppError,
    ExternalServiceError,
    InferenceError,
    MediaError,
    ModelLoadError,
    OperationCancelled,
    SpeechError,
    TranslationError,
    UIError,
    all_error_codes,
    error_code_for,
    user_message_for,
)
from core.logging_config import (
    get_logger,
    reset_logging,
    set_layer_level,
    setup_from_app_config,
    setup_logging,
)
from core.redaction import (
    SensitiveDataFilter,
    redact,
    register_secret,
)


__all__ = [
    "AIError",
    "AppError",
    "ExternalServiceError",
    "InferenceError",
    "MediaError",
    "ModelLoadError",
    "OperationCancelled",
    "SensitiveDataFilter",
    "SpeechError",
    "TranslationError",
    "UIError",
    "all_error_codes",
    "error_code_for",
    "get_logger",
    "redact",
    "register_secret",
    "reset_logging",
    "set_layer_level",
    "setup_from_app_config",
    "setup_logging",
    "user_message_for",
]
