"""Cau hinh co dinh kieu cho toan bo ung dung.

Truoc Sprint 6, cau hinh nam rai rac o **ba noi khac nhau**:

1. `utils/config.py`        - hang so module
2. Bien moi truong `.env`   - doc truc tiep bang `os.getenv()` trong `database/`
3. Hang so trong tung file  - `0.25`, `5.0`, `200`, `500`, `3000`, `2`, ...

Khong ai nhin duoc toan canh, khong the doi tham so khi chay, khong the chay hai
cau hinh khac nhau trong cung mot tien trinh (vi du: test va production).

Sprint 6 gom tat ca ve mot cay `AppConfig` co dinh kieu, co gia tri mac dinh, co
kiem tra hop le.

**Moi gia tri mac dinh o day BANG DUNG gia tri dang chay truoc Sprint 6.**
Sprint 6 khong doi hanh vi, chi doi cho cat giu tham so.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path

from config.environment import Environment
from config.errors import ConfigValidationError


PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ----------------------------------------------------------------------
# Duong dan
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class PathConfig:
    """Duong dan trong project. Giu dung cau truc cua `utils/config.py`."""

    project_root: Path = PROJECT_ROOT

    @property
    def assets_dir(self) -> Path:
        return self.project_root / "assets"

    @property
    def models_dir(self) -> Path:
        return self.project_root / "models"

    @property
    def dataset_dir(self) -> Path:
        return self.project_root / "dataset"

    @property
    def font_path(self) -> Path:
        return self.assets_dir / "fonts" / "NotoSans-Regular.ttf"

    @property
    def audio_dir(self) -> Path:
        return self.assets_dir / "audio"

    @property
    def audio_file(self) -> Path:
        return self.audio_dir / "speech.mp3"

    @property
    def test_image_path(self) -> Path:
        return self.dataset_dir / "test_images" / "test1.jpg"

    @property
    def qml_dir(self) -> Path:
        return self.project_root / "ui" / "qml"

    def validate(self) -> None:
        if not isinstance(self.project_root, Path):
            raise ConfigValidationError(
                "paths.project_root",
                self.project_root,
                "phải là một Path",
            )


# ----------------------------------------------------------------------
# AI
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class AIConfig:
    """Tham so cua tang AI.

    CANH BAO: doi cac gia tri nay se doi ket qua nhan dien. Sprint 6 chi di
    chuyen cho cat giu, KHONG doi gia tri.
    """

    #: Nguong confidence toi thieu cua YOLO.
    confidence: float = 0.5

    #: Kich thuoc anh dau vao YOLO.
    image_size: int = 640

    #: Ten file model YOLO trong `models/`.
    model_file_name: str = "best.pt"

    #: So tu lien quan lay tu k-NN.
    related_words_count: int = 3

    def model_path(
        self,
        paths: PathConfig,
    ) -> Path:
        return paths.models_dir / self.model_file_name

    def validate(self) -> None:
        if not 0.0 < self.confidence <= 1.0:
            raise ConfigValidationError(
                "ai.confidence",
                self.confidence,
                "phải nằm trong khoảng (0, 1]",
            )

        if self.image_size <= 0 or self.image_size % 32 != 0:
            raise ConfigValidationError(
                "ai.image_size",
                self.image_size,
                "phải là bội số dương của 32",
            )

        if self.related_words_count < 1:
            raise ConfigValidationError(
                "ai.related_words_count",
                self.related_words_count,
                "phải lớn hơn hoặc bằng 1",
            )


# ----------------------------------------------------------------------
# Camera
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class CameraConfig:
    """Tham so webcam."""

    #: Chi so thiet bi camera.
    camera_id: int = 0

    #: Nhip chay AI tren luong webcam (giay).
    inference_interval_seconds: float = 0.25

    #: So frame toi da duoc phep "dang bay" giua worker va GUI (backpressure).
    max_frames_in_flight: int = 2

    def validate(self) -> None:
        if self.camera_id < 0:
            raise ConfigValidationError(
                "camera.camera_id",
                self.camera_id,
                "không được âm",
            )

        if self.inference_interval_seconds <= 0:
            raise ConfigValidationError(
                "camera.inference_interval_seconds",
                self.inference_interval_seconds,
                "phải lớn hơn 0",
            )

        if self.max_frames_in_flight < 1:
            raise ConfigValidationError(
                "camera.max_frames_in_flight",
                self.max_frames_in_flight,
                "phải lớn hơn hoặc bằng 1",
            )


# ----------------------------------------------------------------------
# Database
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class DatabaseConfig:
    """Tham so ket noi PostgreSQL / Supabase."""

    host: str = ""
    port: str = "5432"
    name: str = "postgres"
    user: str = "postgres"
    password: str = ""

    #: Kich thuoc connection pool (Sprint 4).
    pool_min_connections: int = 1
    pool_max_connections: int = 8

    def connection_parameters(self) -> dict[str, str]:
        """Tham so truyen cho `psycopg2.connect()`."""
        return {
            "host": self.host,
            "database": self.name,
            "user": self.user,
            "password": self.password,
            "port": self.port,
        }

    @property
    def is_configured(self) -> bool:
        """True neu du thong tin de thu ket noi."""
        return bool(self.host and self.user)

    def missing_variables(self) -> list[str]:
        """Danh sach bien moi truong con thieu."""
        missing = []

        if not self.host:
            missing.append("DB_HOST")
        if not self.name:
            missing.append("DB_NAME")
        if not self.user:
            missing.append("DB_USER")
        if not self.password:
            missing.append("DB_PASSWORD")

        return missing

    def masked(self) -> dict[str, str]:
        """Ban an mat khau - dung khi ghi log hoac in cau hinh."""
        return {
            "host": self.host,
            "port": self.port,
            "name": self.name,
            "user": self.user,
            "password": "***" if self.password else "",
        }

    def validate(self) -> None:
        if self.pool_min_connections < 1:
            raise ConfigValidationError(
                "database.pool_min_connections",
                self.pool_min_connections,
                "phải lớn hơn hoặc bằng 1",
            )

        if self.pool_max_connections < self.pool_min_connections:
            raise ConfigValidationError(
                "database.pool_max_connections",
                self.pool_max_connections,
                "không được nhỏ hơn pool_min_connections",
            )

        if self.port and not str(self.port).isdigit():
            raise ConfigValidationError(
                "database.port",
                self.port,
                "phải là số",
            )


# ----------------------------------------------------------------------
# Lich su & thong ke
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class HistoryConfig:
    """Tham so ghi va doc lich su nhan dien."""

    #: Khoang cach toi thieu giua 2 lan luu cung mot tu (giay).
    cooldown_seconds: float = 5.0

    #: So ban ghi hien tren man hinh lich su.
    page_limit: int = 200

    #: So ban ghi dung de tinh thong ke.
    stats_limit: int = 500

    #: Gioi han an toan cua cau SELECT.
    min_query_limit: int = 1
    max_query_limit: int = 500

    #: Kich thuoc hang doi ghi lich su cua webcam.
    write_queue_size: int = 20

    def validate(self) -> None:
        if self.cooldown_seconds < 0:
            raise ConfigValidationError(
                "history.cooldown_seconds",
                self.cooldown_seconds,
                "không được âm",
            )

        if self.page_limit < 1:
            raise ConfigValidationError(
                "history.page_limit",
                self.page_limit,
                "phải lớn hơn hoặc bằng 1",
            )

        if self.max_query_limit < self.min_query_limit:
            raise ConfigValidationError(
                "history.max_query_limit",
                self.max_query_limit,
                "không được nhỏ hơn min_query_limit",
            )

        if self.page_limit > self.max_query_limit:
            raise ConfigValidationError(
                "history.page_limit",
                self.page_limit,
                f"không được vượt max_query_limit ({self.max_query_limit})",
            )

        if self.stats_limit > self.max_query_limit:
            raise ConfigValidationError(
                "history.stats_limit",
                self.stats_limit,
                f"không được vượt max_query_limit ({self.max_query_limit})",
            )

        if self.write_queue_size < 1:
            raise ConfigValidationError(
                "history.write_queue_size",
                self.write_queue_size,
                "phải lớn hơn hoặc bằng 1",
            )


# ----------------------------------------------------------------------
# Thread
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class ThreadConfig:
    """Tham so vong doi worker (Sprint 5)."""

    #: Thoi gian cho toi da khi dung mot worker (ms).
    dispose_timeout_ms: int = 3000

    #: Chu ky kiem tra co huy khi hang doi trong (giay).
    poll_interval_seconds: float = 0.1

    def validate(self) -> None:
        if self.dispose_timeout_ms < 100:
            raise ConfigValidationError(
                "threads.dispose_timeout_ms",
                self.dispose_timeout_ms,
                "phải lớn hơn hoặc bằng 100 ms",
            )

        if not 0 < self.poll_interval_seconds <= 5:
            raise ConfigValidationError(
                "threads.poll_interval_seconds",
                self.poll_interval_seconds,
                "phải nằm trong khoảng (0, 5]",
            )


# ----------------------------------------------------------------------
# Giao dien
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class UIConfig:
    """Tham so trinh bay va xac thuc phia giao dien."""

    application_name: str = "AI-English"
    qt_quick_style: str = "Basic"

    #: Do dai mat khau toi thieu.
    min_password_length: int = 6

    #: Mau va co chu khi ve nhan len anh tinh.
    image_box_color: tuple[int, int, int] = (0, 255, 0)
    image_label_size: int = 28

    #: Mau va co chu khi ve nhan len frame webcam.
    webcam_box_color: tuple[int, int, int] = (0, 180, 0)
    webcam_label_size: int = 24

    def validate(self) -> None:
        if self.min_password_length < 1:
            raise ConfigValidationError(
                "ui.min_password_length",
                self.min_password_length,
                "phải lớn hơn hoặc bằng 1",
            )

        for name, color in (
            ("ui.image_box_color", self.image_box_color),
            ("ui.webcam_box_color", self.webcam_box_color),
        ):
            if len(color) != 3 or not all(
                0 <= channel <= 255 for channel in color
            ):
                raise ConfigValidationError(
                    name,
                    color,
                    "phải là bộ 3 số trong khoảng 0..255",
                )


# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class LoggingConfig:
    """Tham so ghi log. Sprint 7 se mo rong phan nay."""

    level: str = "INFO"
    performance_enabled: bool = False

    def validate(self) -> None:
        allowed = {
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        }

        if self.level.upper() not in allowed:
            raise ConfigValidationError(
                "logging.level",
                self.level,
                f"phải là một trong {sorted(allowed)}",
            )


# ----------------------------------------------------------------------
# Goc
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class AppConfig:
    """Toan bo cau hinh cua ung dung trong mot doi tuong."""

    environment: Environment = Environment.DEVELOPMENT
    paths: PathConfig = field(default_factory=PathConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    history: HistoryConfig = field(default_factory=HistoryConfig)
    threads: ThreadConfig = field(default_factory=ThreadConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    def validate(self) -> "AppConfig":
        """Kiem tra moi nhom. Nem `ConfigValidationError` neu co truong sai."""
        self.paths.validate()
        self.ai.validate()
        self.camera.validate()
        self.database.validate()
        self.history.validate()
        self.threads.validate()
        self.ui.validate()
        self.logging.validate()

        return self

    def with_overrides(self, **changes) -> "AppConfig":
        """Ban sao co doi mot vai nhom - dung trong test."""
        return replace(self, **changes)

    def summary(self) -> dict[str, object]:
        """Ban tom tat de ghi log. Mat khau LUON bi an."""
        return {
            "environment": self.environment.value,
            "database": self.database.masked(),
            "ai": {
                "confidence": self.ai.confidence,
                "image_size": self.ai.image_size,
                "model": self.ai.model_file_name,
            },
            "camera": {
                "camera_id": self.camera.camera_id,
                "inference_interval_seconds": (
                    self.camera.inference_interval_seconds
                ),
                "max_frames_in_flight": self.camera.max_frames_in_flight,
            },
            "history": {
                "cooldown_seconds": self.history.cooldown_seconds,
                "page_limit": self.history.page_limit,
                "stats_limit": self.history.stats_limit,
            },
            "threads": {
                "dispose_timeout_ms": self.threads.dispose_timeout_ms,
            },
            "logging": {
                "level": self.logging.level,
            },
        }


__all__ = [
    "AIConfig",
    "AppConfig",
    "CameraConfig",
    "DatabaseConfig",
    "HistoryConfig",
    "LoggingConfig",
    "PathConfig",
    "PROJECT_ROOT",
    "ThreadConfig",
    "UIConfig",
]
