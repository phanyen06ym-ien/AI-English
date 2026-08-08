"""Chan ro ri du lieu nhay cam ra log.

Van de truoc Sprint 7
---------------------

Khong co gi ngan mat khau lot vao log:

    ui/auth_controller.py (da go o Sprint 3)
        in thang ten dang nhap ra stdout bang print()

    ui/services/auth_service.py (Sprint 3, da sua o Sprint 4)
        f"Không thể đăng nhập: {error}"
        -> `error` cua psycopg2 co the kem CA chuoi ket noi day du,
           tuc la host + user + password.

Giai phap
---------

Mot `SensitiveDataFilter` gan vao MOI handler. Bo loc lam hai viec:

1. **Theo mau**: tim `password=...`, `token=...`, `postgresql://user:pass@host`,
   `Bearer ...` roi thay phan bi mat bang `***`.
2. **Theo gia tri**: `register_secret(value)` dang ky mot chuoi bi mat cu the
   (vi du mat khau database doc tu `.env`). Chuoi do bi thay o BAT KY dau no
   xuat hien - ke ca khi lot vao mot thong bao loi khong ngo toi.

Cach 2 la quan trong nhat: khong the doan truoc moi dinh dang ma thu vien ben
thu ba dung khi in loi.
"""

from __future__ import annotations

import logging
import re
import threading


REDACTED = "***"

#: Toi thieu bao nhieu ky tu thi mot bi mat moi duoc dang ky.
#: Chuoi qua ngan (vi du "1") se thay the nham khap noi.
MIN_SECRET_LENGTH = 4


#: Mau nhan dien du lieu nhay cam trong chuoi log.
SENSITIVE_PATTERNS: tuple[tuple[str, re.Pattern, str], ...] = (
    (
        "connection_string",
        re.compile(
            r"(?P<scheme>postgres(?:ql)?|mysql|mongodb)"
            r"://(?P<user>[^:/\s]+):(?P<secret>[^@\s]+)@",
            re.IGNORECASE,
        ),
        r"\g<scheme>://\g<user>:" + REDACTED + "@",
    ),
    (
        # PHAI chay TRUOC `keyword_assignment`: neu khong, mau kia se coi
        # "Authorization: Bearer" la mot cap key=value va che nham chu
        # "Bearer", lam token that lot ra ngoai.
        "bearer_token",
        re.compile(
            r"(?P<prefix>Bearer\s+)(?P<secret>[A-Za-z0-9._\-]+)",
            re.IGNORECASE,
        ),
        r"\g<prefix>" + REDACTED,
    ),
    (
        "keyword_assignment",
        re.compile(
            r"(?P<key>password|passwd|pwd|secret|token|api[_-]?key"
            r"|access[_-]?key|authorization)"
            r"(?P<sep>\s*[=:]\s*)"
            r"(?P<quote>['\"]?)"
            r"(?P<secret>[^\s,;'\"}\)]+)"
            r"(?P=quote)",
            re.IGNORECASE,
        ),
        r"\g<key>\g<sep>\g<quote>" + REDACTED + r"\g<quote>",
    ),
)


_secrets: set[str] = set()
_secrets_lock = threading.Lock()


def register_secret(
    value: str | None,
) -> bool:
    """Dang ky mot chuoi bi mat cu the de luon bi che trong log.

    Tra ve False neu gia tri rong hoac qua ngan de thay the an toan.
    """
    if not value:
        return False

    text = str(value)

    if len(text) < MIN_SECRET_LENGTH:
        return False

    with _secrets_lock:
        _secrets.add(text)

    return True


def clear_secrets() -> None:
    """Xoa danh sach bi mat da dang ky. Chi dung trong test."""
    with _secrets_lock:
        _secrets.clear()


def registered_secret_count() -> int:
    """So bi mat dang duoc theo doi. KHONG tra ve noi dung."""
    with _secrets_lock:
        return len(_secrets)


def redact(
    text: str,
) -> str:
    """Che moi du lieu nhay cam trong mot chuoi."""
    if not text:
        return text

    result = str(text)

    # 1. Che theo gia tri da dang ky - dai truoc de tranh thay the mot phan.
    with _secrets_lock:
        known = sorted(_secrets, key=len, reverse=True)

    for secret in known:
        if secret in result:
            result = result.replace(secret, REDACTED)

    # 2. Che theo mau.
    for _, pattern, replacement in SENSITIVE_PATTERNS:
        result = pattern.sub(replacement, result)

    return result


class SensitiveDataFilter(logging.Filter):
    """Bo loc gan vao handler: che du lieu nhay cam truoc khi ghi.

    Loc o **handler** chu khong o logger, de moi ban ghi deu di qua - ke ca ban
    ghi do thu vien ben thu ba tao ra.

    Quan trong: phai **dinh dang xong roi moi che**. Che trang thai tho
    (`record.msg` con nguyen `%s`) se lam hong chinh placeholder do:

        logger.error("connect: postgresql://u:%s@host", password)

    Mau `connection_string` se coi `%s` la mat khau va thay bang `***`, sau do
    `logging` khong con cho de dat tham so nua va nem
    "not all arguments converted during string formatting".
    """

    def filter(
        self,
        record: logging.LogRecord,
    ) -> bool:
        try:
            # Dinh dang truoc (ap tham so), che sau.
            rendered = record.getMessage()

            record.msg = redact(rendered)
            record.args = ()

            if record.exc_text:
                record.exc_text = redact(record.exc_text)

        except Exception:
            # Bo loc hong KHONG duoc lam mat ban ghi log.
            # Nhung cung khong duoc de lot du lieu nhay cam -> bo noi dung.
            record.msg = "<log bi loi khi che du lieu nhay cam>"
            record.args = ()

        return True


class RedactingFormatter(logging.Formatter):
    """Formatter che lai lan cuoi, ke ca phan stack trace.

    `SensitiveDataFilter` khong voi toi duoc stack trace vi noi dung do chi
    duoc sinh ra luc dinh dang. Formatter nay la lop chan cuoi cung.
    """

    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
        return redact(
            super().format(record)
        )


__all__ = [
    "MIN_SECRET_LENGTH",
    "REDACTED",
    "SENSITIVE_PATTERNS",
    "RedactingFormatter",
    "SensitiveDataFilter",
    "clear_secrets",
    "redact",
    "register_secret",
    "registered_secret_count",
]
