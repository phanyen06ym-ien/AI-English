"""Quan ly ket noi database.

Van de truoc Sprint 4
---------------------

`get_connection()` mo mot ket noi TCP + TLS moi cho MOI cau lenh:

    save_history()  -> connect -> INSERT -> close
    get_history()   -> connect -> SELECT -> close

Voi Supabase (PostgreSQL qua Internet), moi lan bat tay ton hang tram mili giay.
Webcam ghi lich su lien tuc nen chi phi nay lap lai rat nhieu lan.

Giai phap Sprint 4
------------------

Dung `psycopg2.pool.ThreadedConnectionPool`:

- Tai su dung ket noi da mo.
- An toan da luong (worker cua Sprint 3 chay tren nhieu thread).
- Tu dong mo lai neu ket noi trong pool bi hong.

Cau hinh, schema va cau SQL KHONG doi.
"""

from __future__ import annotations

import logging
import os
import threading
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool as psycopg2_pool
from dotenv import load_dotenv

from config.schema import DatabaseConfig
from database.exceptions import (
    ConnectionFailedError,
    IntegrityError,
    QueryFailedError,
)
from utils import perf_monitor


load_dotenv()


logger = logging.getLogger(__name__)


#: So ket noi toi thieu giu san trong pool (gia tri mac dinh).
POOL_MIN_CONNECTIONS = DatabaseConfig.pool_min_connections

#: So ket noi toi da. Du cho GUI thread + cac worker cua Sprint 3.
POOL_MAX_CONNECTIONS = DatabaseConfig.pool_max_connections


_pool: psycopg2_pool.ThreadedConnectionPool | None = None
_pool_lock = threading.Lock()
_pool_disabled = False

#: Cau hinh dang dung. Sprint 6: `AppContext` tiem vao luc khoi dong.
_config: DatabaseConfig | None = None


def configure(
    config: DatabaseConfig,
) -> None:
    """Dat cau hinh database. Goi mot lan tu `AppContext.build()`.

    Doi cau hinh se dong pool cu de lan sau mo lai voi tham so moi.
    """
    global _config

    if _config == config:
        return

    close_pool()
    _config = config


def current_config() -> DatabaseConfig:
    """Cau hinh dang dung. Chua tiem thi doc thang tu bien moi truong."""
    if _config is not None:
        return _config

    return DatabaseConfig(
        host=os.getenv("DB_HOST") or "",
        port=os.getenv("DB_PORT") or "5432",
        name=os.getenv("DB_NAME") or "postgres",
        user=os.getenv("DB_USER") or "postgres",
        password=os.getenv("DB_PASSWORD") or "",
    )


def connection_parameters() -> dict[str, str | None]:
    """Tham so ket noi. Khong doi so voi Sprint 4."""
    return current_config().connection_parameters()


def _create_pool() -> psycopg2_pool.ThreadedConnectionPool:
    config = current_config()

    with perf_monitor.timer("db_create_pool"):
        return psycopg2_pool.ThreadedConnectionPool(
            config.pool_min_connections,
            config.pool_max_connections,
            **config.connection_parameters(),
        )


def get_pool() -> psycopg2_pool.ThreadedConnectionPool | None:
    """Tra ve pool dung chung, tao lan dau khi can.

    Tra ve None neu khong tao duoc pool - luc do he thong tu dong quay ve che do
    mo ket noi truc tiep (hanh vi cu cua Sprint 3).
    """
    global _pool, _pool_disabled

    if _pool_disabled:
        return None

    if _pool is not None:
        return _pool

    with _pool_lock:
        if _pool is not None:
            return _pool

        try:
            _pool = _create_pool()
        except Exception:
            # Khong dung duoc pool thi van phai chay duoc bang ket noi truc tiep.
            _pool_disabled = True
            return None

    return _pool


def close_pool() -> None:
    """Dong toan bo ket noi. Goi khi thoat ung dung."""
    global _pool, _pool_disabled

    with _pool_lock:
        if _pool is None:
            return

        try:
            _pool.closeall()
        finally:
            _pool = None
            _pool_disabled = False


def get_connection():
    """Tao ket noi PostgreSQL/Supabase truc tiep (khong qua pool)."""
    with perf_monitor.timer("db_open_connection"):
        try:
            return psycopg2.connect(
                **connection_parameters()
            )
        except Exception as error:
            raise ConnectionFailedError(
                "Không mở được kết nối cơ sở dữ liệu.",
                cause=error,
            ) from error


@contextmanager
def _leased_connection():
    """Muon mot ket noi tu pool, hoac mo truc tiep neu khong co pool."""
    connection_pool = get_pool()

    if connection_pool is None:
        connection = get_connection()

        try:
            yield connection
        finally:
            connection.close()

        return

    try:
        with perf_monitor.timer("db_lease_connection"):
            connection = connection_pool.getconn()
    except Exception as error:
        raise ConnectionFailedError(
            "Không lấy được kết nối từ pool.",
            cause=error,
        ) from error

    broken = False

    try:
        yield connection

    except Exception:
        broken = True
        raise

    finally:
        try:
            connection_pool.putconn(
                connection,
                close=broken,
            )
        except Exception as release_error:
            # Khong tra duoc ket noi ve pool khong duoc che loi GOC,
            # nhung cung khong duoc im lang (NHIEM VU 4 - Sprint 7).
            logger.warning(
                "Khong tra duoc ket noi ve pool: %s",
                release_error,
            )


def _translate(error: Exception) -> Exception:
    """Doi loi cua psycopg2 sang exception cua tang Repository."""
    if isinstance(error, psycopg2.IntegrityError):
        return IntegrityError(
            "Dữ liệu vi phạm ràng buộc.",
            cause=error,
        )

    if isinstance(error, psycopg2.OperationalError):
        return ConnectionFailedError(
            "Mất kết nối cơ sở dữ liệu.",
            cause=error,
        )

    if isinstance(error, psycopg2.Error):
        return QueryFailedError(
            "Câu lệnh cơ sở dữ liệu thất bại.",
            cause=error,
        )

    return error


@contextmanager
def database_cursor(commit: bool = False):
    """Context Manager de lam viec voi database.

    Ranh gioi transaction ro rang:

    - Ra khoi khoi `with` binh thuong + `commit=True`  -> COMMIT.
    - Ra khoi khoi `with` binh thuong + `commit=False` -> ROLLBACK (chi doc).
    - Co exception                                     -> ROLLBACK roi nem tiep.

    Vi du:

        with database_cursor() as cursor:
            cursor.execute(...)

        with database_cursor(commit=True) as cursor:
            cursor.execute(...)
    """
    with _leased_connection() as connection:
        cursor = connection.cursor()

        try:
            yield cursor

            if commit:
                with perf_monitor.timer("db_commit"):
                    connection.commit()
            else:
                # Ket thuc transaction chi doc de ket noi tra ve pool sach se.
                connection.rollback()

        except Exception as error:
            try:
                connection.rollback()
            except Exception as rollback_error:
                logger.warning(
                    "Rollback that bai sau loi %s: %s",
                    type(error).__name__,
                    rollback_error,
                )

            raise _translate(error) from error

        finally:
            cursor.close()


__all__ = [
    "POOL_MIN_CONNECTIONS",
    "POOL_MAX_CONNECTIONS",
    "close_pool",
    "configure",
    "current_config",
    "connection_parameters",
    "database_cursor",
    "get_connection",
    "get_pool",
]
