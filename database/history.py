from database.db import get_connection


def save_history(english_word, vietnamese_meaning, category, confidence, user_id=None):
    try:
        conn = get_connection()
    except Exception as e:
        print("Không lưu được lịch sử (chưa kết nối được database):", e)
        return

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO history (user_id, english_word, vietnamese_meaning, category, confidence, detected_time) "
        "VALUES (%s, %s, %s, %s, %s, now());",
        (user_id, english_word, vietnamese_meaning, category, confidence),
    )
    conn.commit()
    cur.close()
    conn.close()
