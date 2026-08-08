"""Moi truong chay cua ung dung.

    development  - may cua lap trinh vien, log chi tiet
    testing      - chay unit test, KHONG duoc cham database that
    production   - may nguoi dung cuoi

Chon bang bien moi truong `AI_ENGLISH_ENV`. Khong dat thi mac dinh la
`development`.
"""

from __future__ import annotations

import os
from enum import Enum


ENV_VARIABLE = "AI_ENGLISH_ENV"


class Environment(str, Enum):
    """Moi truong chay."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

    @property
    def is_production(self) -> bool:
        return self is Environment.PRODUCTION

    @property
    def is_testing(self) -> bool:
        return self is Environment.TESTING

    @property
    def allows_database(self) -> bool:
        """False trong moi truong test: test khong duoc cham database that."""
        return self is not Environment.TESTING

    @property
    def default_log_level(self) -> str:
        if self is Environment.PRODUCTION:
            return "WARNING"

        if self is Environment.TESTING:
            return "ERROR"

        return "INFO"

    @classmethod
    def parse(
        cls,
        value: str | None,
    ) -> "Environment":
        """Doc moi truong tu chuoi. Gia tri la khong hop le -> development."""
        if not value:
            return cls.DEVELOPMENT

        normalized = str(value).strip().lower()

        aliases = {
            "dev": cls.DEVELOPMENT,
            "develop": cls.DEVELOPMENT,
            "development": cls.DEVELOPMENT,
            "test": cls.TESTING,
            "testing": cls.TESTING,
            "prod": cls.PRODUCTION,
            "production": cls.PRODUCTION,
        }

        return aliases.get(normalized, cls.DEVELOPMENT)

    @classmethod
    def current(cls) -> "Environment":
        """Doc moi truong hien tai tu bien moi truong."""
        return cls.parse(
            os.getenv(ENV_VARIABLE)
        )


__all__ = [
    "ENV_VARIABLE",
    "Environment",
]
