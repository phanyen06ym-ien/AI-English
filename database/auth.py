from database.db import get_connection


def login_user(username, password):
    """Kiểm tra đăng nhập bằng bảng users trong PostgreSQL/Supabase."""
    username = username.strip()
    password = password.strip()

    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, fullname "
            "FROM users "
            "WHERE username = %s AND password = %s",
            (username, password),
        )
        row = cur.fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "username": row[1],
            "fullname": row[2],
        }
    except Exception as exc:
        # Cho UI biết đây là lỗi database, không phải sai mật khẩu.
        print("Lỗi database khi đăng nhập:", exc)
        raise
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()
