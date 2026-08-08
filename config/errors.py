"""Loi cua tang cau hinh.

Cau hinh sai phai bao **ngay khi khoi dong**, kem ten truong va gia tri sai.
Truoc Sprint 6, cau hinh sai chi lo ra khi chay giua chung: `CONFIDENCE = 5.0`
lam YOLO khong bao gio phat hien vat the nao ma khong co mot thong bao nao.
"""

from __future__ import annotations


class ConfigError(Exception):
    """Loi goc cua tang cau hinh."""

    error_code = "CONFIG_ERROR"


class ConfigValidationError(ConfigError):
    """Mot truong cau hinh co gia tri khong hop le."""

    error_code = "CONFIG_VALIDATION_ERROR"

    def __init__(
        self,
        field: str,
        value: object,
        reason: str,
    ) -> None:
        super().__init__(
            f"Cấu hình `{field}` không hợp lệ: {value!r} — {reason}"
        )

        self.field = field
        self.value = value
        self.reason = reason


class MissingConfigError(ConfigError):
    """Thieu mot bien moi truong bat buoc."""

    error_code = "CONFIG_MISSING"

    def __init__(
        self,
        variables: list[str],
    ) -> None:
        joined = ", ".join(variables)

        super().__init__(
            f"Thiếu biến môi trường bắt buộc: {joined}. "
            "Sao chép `.env.example` thành `.env` rồi điền giá trị."
        )

        self.variables = list(variables)


__all__ = [
    "ConfigError",
    "ConfigValidationError",
    "MissingConfigError",
]
