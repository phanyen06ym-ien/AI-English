import sys

from ml.knn import get_related_words


if hasattr(sys.stdout, "reconfigure"):
    # Giúp terminal Windows in được tiếng Việt.
    sys.stdout.reconfigure(encoding="utf-8")


def print_related_words(word):
    """In danh sách từ liên quan theo dạng dễ đọc."""
    print(f"Từ liên quan với {word}:")
    related_words = get_related_words(word, n=3)

    if not related_words:
        print("[]")
        return

    for item in related_words:
        print(
            f"- {item['english']} | {item['vietnamese']} | "
            f"{item['category']} | {item['level']}"
        )


if __name__ == "__main__":
    print_related_words("laptop")
    print_related_words("book")
    print_related_words("bottle")
