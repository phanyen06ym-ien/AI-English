import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db import get_connection  # noqa: E402
from utils.console import use_utf8_console  # noqa: E402

use_utf8_console()

try:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT version();")
    version = cur.fetchone()

    print(" Kết nối thành công!")
    print(version)

    cur.close()
    conn.close()

except Exception as e:
    print("Lỗi kết nối:")
    print(e)