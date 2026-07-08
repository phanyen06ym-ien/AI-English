from dataset.vocabulary import all_words, get_word_info


def predict_category(english_word):
    """Lấy category từ vocabulary.csv; nếu chưa có thì trả Unknown."""
    word = str(english_word).strip().lower()
    info = get_word_info(word)

    if info:
        return info["category"]

    # Tìm gần đúng theo tên tiếng Anh nếu đầu vào khác hoa/thường hoặc có khoảng trắng.
    for english, row in all_words().items():
        if english.strip().lower() == word:
            return row["category"]

    return "Unknown"
