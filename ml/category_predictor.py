from __future__ import annotations

from dataset.vocabulary import (
    all_words,
    get_word_info,
)


def predict_category(
    english_word: str,
) -> str:
    """
    Trả về chủ đề của một từ tiếng Anh.

    Nếu không tìm thấy trong vocabulary.csv,
    trả về Unknown.
    """
    normalized_word = (
        str(english_word)
        .strip()
        .lower()
    )

    if not normalized_word:
        return "Unknown"

    word_info = get_word_info(
        normalized_word
    )

    if word_info:
        return (
            word_info.get("category")
            or "Unknown"
        )

    for word, information in all_words().items():
        if word.strip().lower() == normalized_word:
            return (
                information.get("category")
                or "Unknown"
            )

    return "Unknown"