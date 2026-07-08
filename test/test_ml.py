import sys

from ml.bayes import predict_word_level
from ml.kmeans import get_cluster_by_word, get_words_in_same_cluster
from ml.knn import get_related_words


if hasattr(sys.stdout, "reconfigure"):
    # Giúp terminal Windows in được tiếng Việt.
    sys.stdout.reconfigure(encoding="utf-8")


def print_words(words):
    """In danh sách từ vựng theo dạng dễ đọc."""
    if not words:
        print("[]")
        return

    for word in words:
        print(
            f"- {word['english']} | {word['vietnamese']} | "
            f"{word['category']} | {word['level']}"
        )


def test_kmeans():
    print("=== K-Means: phân cụm từ vựng ===")
    for word in ["book", "laptop", "bottle"]:
        print(f"Cụm của {word}: {get_cluster_by_word(word)}")

    print("Các từ cùng cụm với laptop:")
    print_words(get_words_in_same_cluster("laptop"))


def test_bayes():
    print("\n=== Naive Bayes: phân loại độ khó ===")
    for word in ["book", "keyboard", "backpack", "unknown_word"]:
        print(f"Level của {word}: {predict_word_level(word)}")


def test_knn():
    print("\n=== k-NN: gợi ý từ liên quan ===")
    for word in ["laptop", "book", "bottle"]:
        print(f"Từ liên quan với {word}:")
        print_words(get_related_words(word, n=3))


if __name__ == "__main__":
    test_kmeans()
    test_bayes()
    test_knn()
