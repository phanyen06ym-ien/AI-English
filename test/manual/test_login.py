import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.auth import login_user  # noqa: E402


def print_user(username, password):
    """In kết quả test đăng nhập ra terminal."""
    try:
        user = login_user(username, password)
    except Exception as exc:
        print(f"{username}: lỗi database - {exc}")
        return

    print(f"{username}: {user}")


if __name__ == "__main__":
    print_user("admin", "123456")
    print_user("student1", "123456")
    print_user("admin", "sai")
