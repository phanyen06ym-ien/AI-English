from database.db import get_connection

try:
    conn = get_connection()
    print("Kết nối SQL Server thành công!")

    cursor = conn.cursor()
    cursor.execute("SELECT GETDATE()")
    print(cursor.fetchone()[0])

    cursor.close()
    conn.close()

except Exception as e:
    print("Lỗi:", e)