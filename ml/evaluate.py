from __future__ import annotations

from ml.features import read_vocabulary
from ml.kmeans import (
    cluster_vocabulary,
    get_kmeans_metrics,
    get_words_in_same_cluster,
)
from ml.knn import get_related_words


def evaluate_kmeans() -> dict:
    """
    Chạy K-Means và nhóm các từ theo cụm.
    """
    clusters: dict[int, list[str]] = {}

    for item in cluster_vocabulary():
        cluster_id = item["cluster"]

        clusters.setdefault(
            cluster_id,
            [],
        ).append(
            item["english"]
        )

    return clusters


def evaluate_knn() -> dict:
    """
    Chạy thử k-NN với một số từ.
    """
    test_words = [
        "laptop",
        "book",
        "bottle",
    ]

    results = {}

    for word in test_words:
        suggestions = get_related_words(
            word,
            n=3,
        )

        results[word] = [
            item["english"]
            for item in suggestions
        ]

    return results


def run() -> None:
    """
    In kết quả đánh giá k-NN và K-Means.
    """
    vocabulary = read_vocabulary()

    print("=" * 60)
    print("ĐÁNH GIÁ CÁC THUẬT TOÁN MACHINE LEARNING")
    print("=" * 60)

    print(
        f"Số lượng từ vựng: {len(vocabulary)}"
    )

    print("\n1. K-MEANS - PHÂN CỤM TỪ VỰNG")

    clusters = evaluate_kmeans()

    for cluster_id, words in sorted(
        clusters.items()
    ):
        print(
            f"Cụm {cluster_id}: "
            f"{', '.join(words)}"
        )

    metrics = get_kmeans_metrics()

    print("\nChỉ số K-Means:")

    print(
        f"- Số cụm: "
        f"{metrics['n_clusters']}"
    )

    print(
        f"- Inertia/SSE: "
        f"{metrics['inertia']:.4f}"
    )

    silhouette = metrics[
        "silhouette_score"
    ]

    if silhouette is not None:
        print(
            f"- Silhouette Score: "
            f"{silhouette:.4f}"
        )

    print("\n2. k-NN - GỢI Ý TỪ LIÊN QUAN")

    knn_results = evaluate_knn()

    for word, related_words in (
        knn_results.items()
    ):
        print(
            f"{word}: "
            f"{', '.join(related_words)}"
        )

    print("\n3. CÁC TỪ CÙNG CỤM VỚI LAPTOP")

    same_cluster = get_words_in_same_cluster(
        "laptop"
    )

    if same_cluster:
        print(
            ", ".join(
                item["english"]
                for item in same_cluster
            )
        )
    else:
        print("Không có từ cùng cụm.")


if __name__ == "__main__":
    from utils.console import use_utf8_console

    use_utf8_console()
    run()
