from database.db import get_connection

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