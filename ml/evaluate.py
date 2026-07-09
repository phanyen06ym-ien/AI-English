from ml.bayes import predict_word_level, read_vocabulary as read_bayes_vocabulary
from ml.kmeans import cluster_vocabulary, get_words_in_same_cluster
from ml.knn import get_related_words


def evaluate_bayes():
    """Demo Bayes đúng vai trò: phân loại độ khó từ vựng."""
    words = ["book", "keyboard", "backpack", "unknown_word"]
    return {word: predict_word_level(word) for word in words}


def evaluate_kmeans():
    """Demo K-Means đúng vai trò: phân cụm từ vựng không giám sát."""
    clusters = {}
    for item in cluster_vocabulary():
        clusters.setdefault(item["cluster"], []).append(item["english"])
    return clusters


def evaluate_knn():
    """Demo k-NN đúng vai trò: gợi ý từ liên quan."""
    words = ["laptop", "book", "bottle"]
    return {word: [item["english"] for item in get_related_words(word)] for word in words}


def run():
    """In kết quả demo cho từng thuật toán theo đúng ý nghĩa báo cáo."""
    df = read_bayes_vocabulary()
    print(f"Số lượng từ vựng trong dataset: {len(df)}")

    print("\nNaive Bayes - phân loại độ khó:")
    for word, level in evaluate_bayes().items():
        print(f"  {word}: {level}")

    print("\nK-Means - phân cụm từ vựng:")
    for cluster, words in sorted(evaluate_kmeans().items()):
        print(f"  Cụm {cluster}: {', '.join(words)}")

    print("\nk-NN - gợi ý từ liên quan:")
    for word, related_words in evaluate_knn().items():
        print(f"  {word}: {', '.join(related_words)}")

    print("\nCác từ cùng cụm với laptop:")
    same_cluster = [item["english"] for item in get_words_in_same_cluster("laptop")]
    print(f"  {', '.join(same_cluster)}")


if __name__ == "__main__":
    from utils.console import use_utf8_console

    use_utf8_console()
    run()
