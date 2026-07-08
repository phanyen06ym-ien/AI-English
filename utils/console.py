import sys


def use_utf8_console():
    """Force stdout/stderr to UTF-8 so Vietnamese text prints correctly,
    regardless of the system's default codepage (e.g. cp1258 on Windows)."""
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
