from __future__ import annotations

from dataset.object_mapping import OBJECT_MAPPING
from dataset.vocabulary import get_word_info


def dich_tu(
    word: str,
) -> str:
    """
    Dịch từ tiếng Anh sang tiếng Việt.

    Thứ tự ưu tiên:
    1. vocabulary.csv
    2. object_mapping.py
    3. Google Translate
    """
    normalized_word = word.strip().lower()

    if not normalized_word:
        return "Không có dữ liệu"

    word_info = get_word_info(
        normalized_word
    )

    if word_info:
        vietnamese = word_info.get(
            "vietnamese"
        )

        if vietnamese:
            return vietnamese

    mapped_value = OBJECT_MAPPING.get(
        normalized_word
    )

    if mapped_value:
        return mapped_value

    try:
        from googletrans import Translator

        translator = Translator()

        translated_result = translator.translate(
            normalized_word,
            src="en",
            dest="vi",
        )

        return translated_result.text

    except Exception as error:
        print(
            f"Không thể dịch từ "
            f"'{normalized_word}': {error}"
        )

        return "Chưa có nghĩa tiếng Việt"