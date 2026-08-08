from __future__ import annotations

import logging

from ai.feature_engineering import read_vocabulary
from ai.kmeans import (
    cluster_vocabulary,
    get_kmeans_metrics,
    get_words_in_same_cluster,
)
from ai.knn import get_related_words

logger = logging.getLogger("ml.evaluate")



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

    logger.info("=" * 60)
    logger.info("ĐÁNH GIÁ CÁC THUẬT TOÁN MACHINE LEARNING")
    logger.info("=" * 60)

    logger.info(
        f"Số lượng từ vựng: {len(vocabulary)}"
    )

    logger.info("\n1. K-MEANS - PHÂN CỤM TỪ VỰNG")

    clusters = evaluate_kmeans()

    for cluster_id, words in sorted(
        clusters.items()
    ):
        logger.info(
            f"Cụm {cluster_id}: "
            f"{', '.join(words)}"
        )

    metrics = get_kmeans_metrics()

    logger.info("\nChỉ số K-Means:")

    logger.info(
        f"- Số cụm: "
        f"{metrics['n_clusters']}"
    )

    logger.info(
        f"- Inertia/SSE: "
        f"{metrics['inertia']:.4f}"
    )

    silhouette = metrics[
        "silhouette_score"
    ]

    if silhouette is not None:
        logger.info(
            f"- Silhouette Score: "
            f"{silhouette:.4f}"
        )

    logger.info("\n2. k-NN - GỢI Ý TỪ LIÊN QUAN")

    knn_results = evaluate_knn()

    for word, related_words in (
        knn_results.items()
    ):
        logger.info(
            f"{word}: "
            f"{', '.join(related_words)}"
        )

    logger.info("\n3. CÁC TỪ CÙNG CỤM VỚI LAPTOP")

    same_cluster = get_words_in_same_cluster(
        "laptop"
    )

    if same_cluster:
        logger.info(
            ", ".join(
                item["english"]
                for item in same_cluster
            )
        )
    else:
        logger.info("Không có từ cùng cụm.")


if __name__ == "__main__":
    # Script chay doc lap: tu lap dat logging de bao cao van hien ra console.
    from core.logging_config import setup_logging

    setup_logging(level="INFO")
    from utils.console import use_utf8_console

    use_utf8_console()
    run()
