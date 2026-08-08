from __future__ import annotations

import sys
import warnings
from pathlib import Path
from typing import Any

import joblib
import matplotlib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.exceptions import InconsistentVersionWarning
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PATH = PROJECT_ROOT / "dataset" / "vocabulary.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "kmeans.pkl"
RESULT_DIR = PROJECT_ROOT / "docs" / "experiment_results"

ELBOW_PATH = RESULT_DIR / "elbow_curve.png"
SILHOUETTE_PATH = RESULT_DIR / "silhouette_curve.png"
CLUSTER_PATH = RESULT_DIR / "cluster_visualization.png"

REQUIRED_COLUMNS = ["english", "vietnamese", "category", "level"]
K_VALUES = list(range(2, 9))
SELECTED_K = 5

LEVEL_MAPPING = {"Easy": 0, "Medium": 1, "Hard": 2}
CATEGORY_WEIGHT = 5.0
LEVEL_WEIGHT = 2.0
WORD_LENGTH_WEIGHT = 0.5


if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def read_vocabulary() -> pd.DataFrame:
    """Read and normalize the real vocabulary dataset."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Không tìm thấy vocabulary.csv: {DATA_PATH}")

    dataframe = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in dataframe.columns
    ]
    if missing_columns:
        raise ValueError(
            "vocabulary.csv thiếu các cột bắt buộc: "
            + ", ".join(missing_columns)
        )

    dataframe = dataframe[REQUIRED_COLUMNS].copy()
    dataframe["english"] = dataframe["english"].astype(str).str.strip().str.lower()
    dataframe["vietnamese"] = dataframe["vietnamese"].astype(str).str.strip()
    dataframe["category"] = dataframe["category"].astype(str).str.strip()
    dataframe["level"] = dataframe["level"].astype(str).str.strip()
    dataframe = dataframe[dataframe["english"] != ""]
    dataframe = dataframe.drop_duplicates(subset=["english"])
    return dataframe.reset_index(drop=True)


def build_features(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Build the same feature set used by the existing K-Means training code."""
    features = pd.DataFrame(index=dataframe.index)
    features["word_length"] = dataframe["english"].str.len().astype(float)
    features["level_encoded"] = (
        dataframe["level"].map(LEVEL_MAPPING).fillna(0).astype(float)
    )
    category_features = pd.get_dummies(
        dataframe["category"],
        prefix="category",
        dtype=float,
    )
    features = pd.concat([features, category_features], axis=1).astype(float)
    return features, list(features.columns)


def apply_feature_weights(
    scaled_features: np.ndarray,
    feature_columns: list[str],
) -> np.ndarray:
    """Apply the feature weights used by ml/kmeans.py."""
    weighted_features = scaled_features.copy()
    for index, column in enumerate(feature_columns):
        if column.startswith("category_"):
            weighted_features[:, index] *= CATEGORY_WEIGHT
        elif column == "level_encoded":
            weighted_features[:, index] *= LEVEL_WEIGHT
        elif column == "word_length":
            weighted_features[:, index] *= WORD_LENGTH_WEIGHT
    return weighted_features


def prepare_features(dataframe: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """Scale and weight vocabulary features for K-Means."""
    features, feature_columns = build_features(dataframe)
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)
    weighted_features = apply_feature_weights(scaled_features, feature_columns)
    return weighted_features, feature_columns


def load_kmeans_model() -> dict[str, Any]:
    """Load the saved K-Means model directly from models/kmeans.pkl."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Không tìm thấy mô hình KMeans: {MODEL_PATH}")

    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always", InconsistentVersionWarning)
        model_data = joblib.load(MODEL_PATH)
        for warning in caught_warnings:
            print(f"Cảnh báo khi load model: {warning.message}")

    if not isinstance(model_data, dict) or "models" not in model_data:
        raise ValueError("models/kmeans.pkl không có cấu trúc model_data hợp lệ.")

    return model_data


def evaluate_k(weighted_features: np.ndarray) -> tuple[list[int], list[float], list[float]]:
    """Train KMeans for K=2..8 and return SSE and Silhouette values."""
    valid_k_values: list[int] = []
    sse_values: list[float] = []
    silhouette_scores: list[float] = []

    for k in K_VALUES:
        if k >= len(weighted_features):
            print(f"Bỏ qua K={k} vì K >= số lượng mẫu.")
            continue

        model = KMeans(n_clusters=k, random_state=42, n_init=20)
        labels = model.fit_predict(weighted_features)

        valid_k_values.append(k)
        sse_values.append(float(model.inertia_))
        silhouette_scores.append(float(silhouette_score(weighted_features, labels)))

        print(
            f"K={k}: SSE={model.inertia_:.4f}, "
            f"Silhouette={silhouette_scores[-1]:.4f}"
        )

    return valid_k_values, sse_values, silhouette_scores


def plot_elbow_curve(
    k_values: list[int],
    sse_values: list[float],
    output_path: Path,
) -> None:
    """Create the Elbow Curve figure."""
    plt.figure(figsize=(8, 5), dpi=300, facecolor="white")
    plt.plot(
        k_values,
        sse_values,
        marker="o",
        color="blue",
        linewidth=2,
        markersize=6,
    )

    if SELECTED_K in k_values:
        selected_index = k_values.index(SELECTED_K)
        selected_sse = sse_values[selected_index]
        plt.scatter(
            [SELECTED_K],
            [selected_sse],
            color="red",
            s=80,
            zorder=5,
        )
        plt.annotate(
            "Selected K = 5",
            xy=(SELECTED_K, selected_sse),
            xytext=(SELECTED_K + 0.25, selected_sse),
            arrowprops={"arrowstyle": "->", "color": "red"},
            fontsize=10,
            color="red",
        )

    plt.title("Elbow Method for Optimal Number of Clusters", fontsize=13)
    plt.xlabel("Number of Clusters (K)", fontsize=11)
    plt.ylabel("SSE (Inertia)", fontsize=11)
    plt.xticks(k_values)
    plt.grid(True, linestyle="--", alpha=0.45)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor="white")
    plt.close()


def plot_silhouette_curve(
    k_values: list[int],
    silhouette_scores: list[float],
    output_path: Path,
) -> None:
    """Create the Silhouette Curve figure."""
    best_index = int(np.argmax(silhouette_scores))
    best_k = k_values[best_index]
    best_score = silhouette_scores[best_index]

    plt.figure(figsize=(8, 5), dpi=300, facecolor="white")
    plt.plot(
        k_values,
        silhouette_scores,
        marker="o",
        color="blue",
        linewidth=2,
        markersize=6,
    )
    plt.scatter([best_k], [best_score], color="red", s=80, zorder=5)
    plt.annotate(
        f"Best K = {best_k}\nScore = {best_score:.4f}",
        xy=(best_k, best_score),
        xytext=(best_k + 0.25, best_score - 0.04),
        arrowprops={"arrowstyle": "->", "color": "red"},
        fontsize=10,
        color="red",
    )

    plt.title("Silhouette Score by Number of Clusters", fontsize=13)
    plt.xlabel("Number of Clusters (K)", fontsize=11)
    plt.ylabel("Silhouette Score", fontsize=11)
    plt.xticks(k_values)
    plt.grid(True, linestyle="--", alpha=0.45)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor="white")
    plt.close()


def get_model_features_for_pca(
    model_data: dict[str, Any],
    fallback_features: np.ndarray,
) -> np.ndarray:
    """Return the feature matrix in the same space as the saved model."""
    try:
        features = model_data["features"]
        scaler = model_data["scaler"]
        feature_columns = model_data["feature_columns"]
        scaled_features = scaler.transform(features)
        return apply_feature_weights(scaled_features, feature_columns)
    except Exception as error:
        print(f"Không lấy được feature từ model_data, dùng feature đọc từ CSV: {error}")
        return fallback_features


def get_model_labels(
    model_data: dict[str, Any],
    weighted_features: np.ndarray,
) -> np.ndarray:
    """Predict labels with the saved K-Means model."""
    model = model_data["models"]
    try:
        return model.predict(weighted_features).astype(int)
    except Exception as error:
        print(f"Không predict được từ model, dùng labels_ đã lưu: {error}")
        return np.asarray(model.labels_).astype(int)


def plot_cluster_pca(
    dataframe: pd.DataFrame,
    weighted_features: np.ndarray,
    labels: np.ndarray,
    model_data: dict[str, Any],
    output_path: Path,
) -> None:
    """Create PCA scatter plot for vocabulary clusters."""
    pca = PCA(n_components=2)
    points = pca.fit_transform(weighted_features)
    model = model_data["models"]
    unique_clusters = sorted(set(labels.tolist()))
    color_map = plt.get_cmap("tab10")

    plt.figure(figsize=(8, 5), dpi=300, facecolor="white")

    for color_index, cluster_id in enumerate(unique_clusters):
        mask = labels == cluster_id
        plt.scatter(
            points[mask, 0],
            points[mask, 1],
            s=55,
            color=color_map(color_index % 10),
            edgecolors="black",
            linewidths=0.4,
            label=f"Cluster {cluster_id}",
        )

    for index, row in dataframe.iterrows():
        plt.annotate(
            row["english"],
            (points[index, 0], points[index, 1]),
            textcoords="offset points",
            xytext=(5, 4),
            fontsize=9,
        )

    if hasattr(model, "cluster_centers_"):
        centers_pca = pca.transform(model.cluster_centers_)
        plt.scatter(
            centers_pca[:, 0],
            centers_pca[:, 1],
            marker="X",
            s=160,
            color="black",
            label="Centroids",
            zorder=6,
        )
        for cluster_index, center in enumerate(centers_pca):
            plt.annotate(
                f"C{cluster_index}",
                (center[0], center[1]),
                textcoords="offset points",
                xytext=(7, 7),
                fontsize=10,
                fontweight="bold",
                color="black",
            )

    plt.title("K-Means Vocabulary Clusters (PCA)", fontsize=13)
    plt.xlabel("Principal Component 1", fontsize=11)
    plt.ylabel("Principal Component 2", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.45)
    plt.legend(fontsize=9, frameon=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor="white")
    plt.close()


def main() -> None:
    """Generate all K-Means report figures."""
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    vocabulary = read_vocabulary()
    weighted_features, _feature_columns = prepare_features(vocabulary)
    model_data = load_kmeans_model()
    model_features = get_model_features_for_pca(model_data, weighted_features)
    labels = get_model_labels(model_data, model_features)

    print("=" * 60)
    print("TẠO BIỂU ĐỒ K-MEANS CHO BÁO CÁO")
    print("=" * 60)

    k_values, sse_values, silhouette_scores = evaluate_k(weighted_features)

    plot_elbow_curve(k_values, sse_values, ELBOW_PATH)
    plot_silhouette_curve(k_values, silhouette_scores, SILHOUETTE_PATH)
    plot_cluster_pca(vocabulary, model_features, labels, model_data, CLUSTER_PATH)

    print()
    print("Đã tạo:")
    print(f"elbow_curve.png: {ELBOW_PATH}")
    print(f"silhouette_curve.png: {SILHOUETTE_PATH}")
    print(f"cluster_visualization.png: {CLUSTER_PATH}")


if __name__ == "__main__":
    main()
