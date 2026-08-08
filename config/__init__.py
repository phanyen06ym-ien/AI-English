"""Tang cau hinh.

    load_config()  ->  AppConfig
                         ├── paths     PathConfig
                         ├── ai        AIConfig
                         ├── camera    CameraConfig
                         ├── database  DatabaseConfig
                         ├── history   HistoryConfig
                         ├── threads   ThreadConfig
                         ├── ui        UIConfig
                         └── logging   LoggingConfig

Quy tac Sprint 6:

1. Moi tham so co the doi duoc deu nam trong `AppConfig`, khong nam rai rac.
2. Thanh phan nhan config **qua constructor**, khong doc bien toan cuc.
3. Cau hinh sai bi chan ngay khi khoi dong, kem ten truong va ly do.
4. Mat khau database khong bao gio xuat hien trong log (`masked()` / `summary()`).

Ngoai le duy nhat: `utils/config.py` van xuat hang so module vi cac module AI
(`detection/`, `ml/`, `dataset/`) doc chung luc import, ma Sprint 6 khong duoc
sua cac module do.
"""

from __future__ import annotations

from config.environment import ENV_VARIABLE, Environment
from config.errors import (
    ConfigError,
    ConfigValidationError,
    MissingConfigError,
)
from config.loader import (
    load_config,
    load_test_config,
)
from config.schema import (
    PROJECT_ROOT,
    AIConfig,
    AppConfig,
    CameraConfig,
    DatabaseConfig,
    HistoryConfig,
    LoggingConfig,
    PathConfig,
    ThreadConfig,
    UIConfig,
)


#: Cau hinh mac dinh dung chung.
#:
#: Chi ton tai de `utils/config.py` xuat duoc hang so module cho cac module AI cu.
#: Code moi KHONG duoc dung bien nay - hay nhan `AppConfig` qua constructor.
_default_config: AppConfig | None = None


def get_default_config() -> AppConfig:
    """Cau hinh mac dinh, tao lan dau khi can.

    Chi danh cho lop tuong thich `utils/config.py`.
    """
    global _default_config

    if _default_config is None:
        _default_config = load_config()

    return _default_config


def set_default_config(
    config: AppConfig,
) -> None:
    """Doi cau hinh mac dinh. Chi dung trong test."""
    global _default_config

    _default_config = config


def reset_default_config() -> None:
    """Xoa cau hinh mac dinh da nap. Chi dung trong test."""
    global _default_config

    _default_config = None


__all__ = [
    "AIConfig",
    "AppConfig",
    "CameraConfig",
    "ConfigError",
    "ConfigValidationError",
    "DatabaseConfig",
    "ENV_VARIABLE",
    "Environment",
    "HistoryConfig",
    "LoggingConfig",
    "MissingConfigError",
    "PROJECT_ROOT",
    "PathConfig",
    "ThreadConfig",
    "UIConfig",
    "get_default_config",
    "load_config",
    "load_test_config",
    "reset_default_config",
    "set_default_config",
]
