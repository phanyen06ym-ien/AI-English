from __future__ import annotations

import os
from contextlib import contextmanager

import psycopg2
from dotenv import load_dotenv

from utils import perf_monitor

load_dotenv()


def get_connection():
    """
    Tạo kết nối PostgreSQL/Supabase.
    """
    with perf_monitor.timer("db_open_connection"):
        return psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT"),
        )


@contextmanager
def database_cursor(commit: bool = False):
    """
    Context Manager để làm việc với database.

    Ví dụ:

    with database_cursor() as cursor:
        cursor.execute(...)

    hoặc

    with database_cursor(commit=True) as cursor:
        cursor.execute(...)
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:
        yield cursor

        if commit:
            with perf_monitor.timer("db_commit"):
                connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()
