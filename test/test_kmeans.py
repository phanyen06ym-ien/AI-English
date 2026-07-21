from __future__ import annotations

import sys
from pathlib import Path

from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.kmeans import apply_feature_weights, load_kmeans_model  # noqa: E402


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    model_data = load_kmeans_model()
    model = model_data["models"]
    vocabulary = model_data["vocabulary"]
    features = model_data["features"]
    scaler = model_data["scaler"]
    feature_columns = model_data["feature_columns"]

    scaled_features = scaler.transform(features)
    weighted_features = apply_feature_weights(
        scaled_features,
        feature_columns,
    )

    labels = model.labels_

    print("=== KMeans labels_ ===")
    print(labels.tolist())

    print("\n=== KMeans cluster centers ===")
    for index, center in enumerate(model.cluster_centers_):
        rounded = [round(float(value), 4) for value in center]
        print(f"cluster {index}: {rounded}")

    print("\n=== Cluster tung tu ===")
    for _, row in vocabulary.iterrows():
        print(
            f"{row['english']}: cluster {int(row['cluster'])}"
        )

    print("\n=== Metrics ===")
    print(f"inertia: {float(model.inertia_):.6f}")

    if len(set(labels)) > 1 and len(labels) > len(set(labels)):
        print(
            "silhouette: "
            f"{silhouette_score(weighted_features, labels):.6f}"
        )
        print(
            "davies: "
            f"{davies_bouldin_score(weighted_features, labels):.6f}"
        )
        print(
            "calinski: "
            f"{calinski_harabasz_score(weighted_features, labels):.6f}"
        )
    else:
        print("silhouette: N/A")
        print("davies: N/A")
        print("calinski: N/A")


if __name__ == "__main__":
    main()
