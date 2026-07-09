# detection/classify.py
from ml.knn import get_related_words   # giả sử dùng knn

def classify_word(word: str):
    """
    Trả về thông tin của từ tiếng Anh.
    Nếu không tìm thấy, trả về thông tin mặc định.
    """
    related = get_related_words(word, n=1)   # lấy 1 từ gần nhất
    if related:
        info = related[0]
        # Chuyển level thành frequency (nếu cần)
        level = info.get("level", "A1")
        freq_map = {"A1": "high", "B1": "medium", "B2": "medium", "C1": "low", "C2": "low"}
        frequency = freq_map.get(level, "medium")
        return {
            "vietnamese": info["vietnamese"],
            "category": info["category"],
            "frequency": frequency,
            "level": level
        }
    else:
        # Không tìm thấy → trả về từ gốc, category unknown
        return {
            "vietnamese": word,
            "category": "unknown",
            "frequency": "unknown",
            "level": "unknown"
        }