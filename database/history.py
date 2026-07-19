from database.db import get_connection


def save_history(english_word, vietnamese_meaning, category, confidence):
    """Lưu một lượt nhận diện. Không raise khi lỗi DB để app vẫn chạy tiếp."""
    try:
        conn = get_connection()
    except Exception as e:
        print("Không lưu được lịch sử (chưa kết nối được database):", e)
        return

    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO history (english_word, vietnamese_meaning, category, confidence, detected_time) "
            "VALUES (%s, %s, %s, %s, now());",
            (english_word, vietnamese_meaning, category, confidence),
        )
        conn.commit()
        cur.close()
    except Exception as e:
        print("Không lưu được lịch sử (lỗi khi ghi dữ liệu):", e)
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        conn.close()


def get_history(limit=200):
    """Trả về danh sách lịch sử nhận diện, mới nhất trước. Trả về [] khi lỗi DB."""
    try:
        conn = get_connection()
    except Exception as e:
        print("Không đọc được lịch sử (chưa kết nối được database):", e)
        return []

    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT english_word, vietnamese_meaning, category, confidence, detected_time "
            "FROM history "
            "ORDER BY detected_time DESC LIMIT %s;",
            (limit,),
        )
        rows = cur.fetchall()
        cur.close()
        return [
            {
                "english": row[0],
                "vietnamese": row[1],
                "category": row[2],
                "confidence": row[3],
                "detected_time": row[4],
            }
            for row in rows
        ]
    except Exception as e:
        print("Không đọc được lịch sử (lỗi khi truy vấn):", e)
        return []
    finally:
        conn.close()


def get_stats():
    """Trả về thống kê nhận diện. Trả về cấu trúc rỗng-an-toàn khi lỗi DB."""
    empty = {"total": 0, "distinct_words": 0, "by_category": {}, "words_detected": []}

    try:
        conn = get_connection()
    except Exception as e:
        print("Không đọc được thống kê (chưa kết nối được database):", e)
        return empty

    try:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*), COUNT(DISTINCT english_word) FROM history;")
        total, distinct_words = cur.fetchone()

        cur.execute(
            "SELECT category, COUNT(*) FROM history "
            "GROUP BY category ORDER BY COUNT(*) DESC;"
        )
        by_category = {row[0]: row[1] for row in cur.fetchall()}

        cur.execute("SELECT DISTINCT english_word FROM history;")
        words_detected = [row[0] for row in cur.fetchall()]

        cur.close()
        return {
            "total": total or 0,
            "distinct_words": distinct_words or 0,
            "by_category": by_category,
            "words_detected": words_detected,
        }
    except Exception as e:
        print("Không đọc được thống kê (lỗi khi truy vấn):", e)
        return empty
    finally:
        conn.close()


def clear_history():
    """Xóa toàn bộ lịch sử nhận diện. Không raise khi lỗi DB."""
    try:
        conn = get_connection()
    except Exception as e:
        print("Không xóa được lịch sử (chưa kết nối được database):", e)
        return

    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM history;")
        conn.commit()
        cur.close()
    except Exception as e:
        print("Không xóa được lịch sử (lỗi khi ghi dữ liệu):", e)
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        conn.close()
