import logging
import sys


logger = logging.getLogger(__name__)


def use_utf8_console() -> None:
    """
    Thiết lập stdout và stderr sử dụng UTF-8.

    Giúp Terminal Windows hiển thị tiếng Việt chính xác.
    """
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(
                encoding="utf-8"
            )

        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(
                encoding="utf-8"
            )

    except Exception as error:
        logger.warning(
            "Khong thiet lap duoc UTF-8 cho console: %s",
            error,
        )