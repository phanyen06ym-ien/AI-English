from __future__ import annotations

import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
from sklearn.exceptions import InconsistentVersionWarning
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from utils.console import use_utf8_console
from utils import perf_monitor


use_utf8_console()


# =========================================================
# 1. CẤU HÌNH ĐƯỜNG DẪN
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = (
    PROJECT_ROOT
    / "dataset"
    / "vocabulary.csv"
)

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "kmeans.pkl"
)

_MODEL_CACHE: dict | None = None


# =========================================================
# 2. CẤU HÌNH MODEL
# =========================================================

MODEL_VERSION = 4

REQUIRED_COLUMNS = [
    "english",
    "vietnamese",
    "category",
    "level",
]

LEVEL_MAPPING = {
    "Easy": 0,
    "Medium": 1,
    "Hard": 2,
}

CATEGORY_WEIGHT = 5.0
LEVEL_WEIGHT = 2.0
WORD_LENGTH_WEIGHT = 0.5


# =========================================================
# 3. ĐỌC VÀ CHUẨN HÓA DỮ LIỆU
# =========================================================

def read_vocabulary() -> pd.DataFrame:
    """
    Đọc và chuẩn hóa vocabulary.csv.
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy vocabulary.csv: {DATA_PATH}"
        )

    with perf_monitor.timer("kmeans_read_vocabulary_csv"):
        dataframe = pd.read_csv(
            DATA_PATH,
            encoding="utf-8-sig",
        )

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "vocabulary.csv thiếu các cột: "
            + ", ".join(missing_columns)
        )

    dataframe = dataframe[REQUIRED_COLUMNS].copy()

    dataframe["english"] = (
        dataframe["english"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    dataframe["vietnamese"] = (
        dataframe["vietnamese"]
        .astype(str)
        .str.strip()
    )

    dataframe["category"] = (
        dataframe["category"]
        .astype(str)
        .str.strip()
    )

    dataframe["level"] = (
        dataframe["level"]
        .astype(str)
        .str.strip()
    )

    dataframe = dataframe[
        dataframe["english"] != ""
    ]

    dataframe = dataframe.drop_duplicates(
        subset=["english"]
    )

    return dataframe.reset_index(drop=True)


# =========================================================
# 4. TẠO ĐẶC TRƯNG
# =========================================================

def build_features(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Tạo đặc trưng cho K-Means.

    Đặc trưng gồm:
    - word_length;
    - level_encoded;
    - one-hot category.
    """
    features = pd.DataFrame(
        index=dataframe.index
    )

    features["word_length"] = (
        dataframe["english"]
        .str.len()
        .astype(float)
    )

    features["level_encoded"] = (
        dataframe["level"]
        .map(LEVEL_MAPPING)
        .fillna(0)
        .astype(float)
    )

    category_features = pd.get_dummies(
        dataframe["category"],
        prefix="category",
        dtype=float,
    )

    features = pd.concat(
        [
            features,
            category_features,
        ],
        axis=1,
    )

    return features.astype(float)


def apply_feature_weights(
    features: np.ndarray,
    feature_columns: list[str],
) -> np.ndarray:
    """
    Gán trọng số để chủ đề ảnh hưởng mạnh nhất.
    """
    weighted_features = features.copy()

    for index, column in enumerate(feature_columns):
        if column.startswith("category_"):
            weighted_features[:, index] *= (
                CATEGORY_WEIGHT
            )

        elif column == "level_encoded":
            weighted_features[:, index] *= (
                LEVEL_WEIGHT
            )

        elif column == "word_length":
            weighted_features[:, index] *= (
                WORD_LENGTH_WEIGHT
            )

    return weighted_features


def get_dataset_modified_time() -> float:
    """
    Lấy thời gian cập nhật cuối của vocabulary.csv.
    """
    return DATA_PATH.stat().st_mtime


def get_default_cluster_count(
    dataframe: pd.DataFrame,
) -> int:
    """
    Chọn số cụm dựa trên số chủ đề trong dữ liệu.
    """
    category_count = int(
        dataframe["category"].nunique()
    )

    return max(
        2,
        min(
            category_count,
            len(dataframe) - 1,
        ),
    )


# =========================================================
# 5. HUẤN LUYỆN MODEL
# =========================================================

def train_kmeans_model(
    n_clusters: int | None = None,
) -> dict:
    """
    Huấn luyện K-Means để phân cụm từ vựng.
    """
    dataframe = read_vocabulary()

    if len(dataframe) < 3:
        raise ValueError(
            "Cần ít nhất 3 từ để thực hiện K-Means."
        )

    if n_clusters is None:
        cluster_count = (
            get_default_cluster_count(dataframe)
        )
    else:
        cluster_count = max(
            2,
            min(
                int(n_clusters),
                len(dataframe) - 1,
            ),
        )

    features = build_features(dataframe)
    feature_columns = list(features.columns)

    scaler = StandardScaler()

    scaled_features = scaler.fit_transform(
        features
    )

    weighted_features = apply_feature_weights(
        scaled_features,
        feature_columns,
    )

    model = KMeans(
        n_clusters=cluster_count,
        random_state=42,
        n_init=20,
    )

    cluster_labels = model.fit_predict(
        weighted_features
    )

    dataframe = dataframe.copy()
    dataframe["cluster"] = cluster_labels

    silhouette = None

    if (
        cluster_count > 1
        and cluster_count < len(dataframe)
        and len(set(cluster_labels)) > 1
    ):
        silhouette = float(
            silhouette_score(
                weighted_features,
                cluster_labels,
            )
        )

    model_data = {
        "models": model,
        "scaler": scaler,
        "features": features,
        "feature_columns": feature_columns,
        "vocabulary": dataframe,
        "n_clusters": cluster_count,
        "inertia": float(model.inertia_),
        "silhouette_score": silhouette,
        "dataset_mtime": get_dataset_modified_time(),
        "model_version": MODEL_VERSION,
        "sklearn_version": sklearn.__version__,
    }

    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        model_data,
        MODEL_PATH,
    )

    print(
        f"Đã lưu mô hình K-Means: {MODEL_PATH}"
    )

    return model_data


def load_kmeans_model(
    n_clusters: int | None = None,
) -> dict:
    """
    Tải models K-Means hoặc tự train lại.
    """
    global _MODEL_CACHE

    if _MODEL_CACHE is not None and n_clusters is None:
        is_cached_valid = (
            _MODEL_CACHE.get("dataset_mtime")
            == get_dataset_modified_time()
            and _MODEL_CACHE.get("model_version")
            == MODEL_VERSION
            and _MODEL_CACHE.get("sklearn_version")
            == sklearn.__version__
        )

        if is_cached_valid:
            return _MODEL_CACHE

    dataframe = read_vocabulary()

    if n_clusters is None:
        expected_clusters = (
            get_default_cluster_count(dataframe)
        )
    else:
        expected_clusters = max(
            2,
            min(
                int(n_clusters),
                len(dataframe) - 1,
            ),
        )

    if _MODEL_CACHE is not None:
        is_cached_valid = (
            _MODEL_CACHE.get("dataset_mtime")
            == get_dataset_modified_time()
            and _MODEL_CACHE.get("n_clusters")
            == expected_clusters
            and _MODEL_CACHE.get("model_version")
            == MODEL_VERSION
            and _MODEL_CACHE.get("sklearn_version")
            == sklearn.__version__
        )

        if is_cached_valid:
            return _MODEL_CACHE

    if (
        MODEL_PATH.exists()
        and MODEL_PATH.stat().st_size > 0
    ):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter(
                    "error",
                    InconsistentVersionWarning,
                )

                with perf_monitor.timer("kmeans_joblib_load"):
                    model_data = joblib.load(
                        MODEL_PATH
                    )

            is_valid = (
                model_data.get("dataset_mtime")
                == get_dataset_modified_time()
                and model_data.get("n_clusters")
                == expected_clusters
                and model_data.get("model_version")
                == MODEL_VERSION
                and model_data.get("sklearn_version")
                == sklearn.__version__
            )

            if is_valid:
                _MODEL_CACHE = model_data
                return model_data

        except Exception as error:
            print(
                "Không thể dùng models K-Means cũ, "
                f"đang train lại: {error}"
            )

    _MODEL_CACHE = train_kmeans_model(
        n_clusters=expected_clusters
    )
    return _MODEL_CACHE


# =========================================================
# 6. CÁC HÀM PHÂN CỤM
# =========================================================

def cluster_vocabulary(
    n_clusters: int | None = None,
) -> list[dict]:
    """
    Trả về danh sách toàn bộ từ và cụm tương ứng.
    """
    model_data = load_kmeans_model(
        n_clusters
    )

    dataframe: pd.DataFrame = (
        model_data["vocabulary"]
    )

    columns = [
        "english",
        "vietnamese",
        "category",
        "level",
        "cluster",
    ]

    return dataframe[columns].to_dict(
        orient="records"
    )


def get_cluster_by_word(
    word: str,
) -> int | None:
    """
    Trả về mã cụm của một từ.
    """
    normalized_word = (
        str(word)
        .strip()
        .lower()
    )

    if not normalized_word:
        return None

    model_data = load_kmeans_model()

    dataframe: pd.DataFrame = (
        model_data["vocabulary"]
    )

    matched_rows = dataframe[
        dataframe["english"]
        == normalized_word
    ]

    if matched_rows.empty:
        return None

    return int(
        matched_rows.iloc[0]["cluster"]
    )


def get_words_in_same_cluster(
    word: str,
    include_input_word: bool = False,
) -> list[dict]:
    """
    Lấy các từ nằm cùng cụm với từ đầu vào.
    """
    normalized_word = (
        str(word)
        .strip()
        .lower()
    )

    model_data = load_kmeans_model()

    dataframe: pd.DataFrame = (
        model_data["vocabulary"]
    )

    matched_rows = dataframe[
        dataframe["english"]
        == normalized_word
    ]

    if matched_rows.empty:
        return []

    cluster_id = int(
        matched_rows.iloc[0]["cluster"]
    )

    same_cluster = dataframe[
        dataframe["cluster"]
        == cluster_id
    ]

    if not include_input_word:
        same_cluster = same_cluster[
            same_cluster["english"]
            != normalized_word
        ]

    columns = [
        "english",
        "vietnamese",
        "category",
        "level",
        "cluster",
    ]

    return same_cluster[columns].to_dict(
        orient="records"
    )


def get_topic_clusters() -> dict[int, dict]:
    """
    Nhóm các từ theo cụm và xác định chủ đề chính
    của từng cụm bằng category xuất hiện nhiều nhất.
    """
    model_data = load_kmeans_model()

    dataframe: pd.DataFrame = (
        model_data["vocabulary"]
    )

    topic_clusters = {}

    for cluster_id, group in dataframe.groupby(
        "cluster"
    ):
        dominant_category = (
            group["category"]
            .mode()
            .iloc[0]
        )

        topic_clusters[int(cluster_id)] = {
            "topic": dominant_category,
            "words": group[
                [
                    "english",
                    "vietnamese",
                    "category",
                    "level",
                ]
            ].to_dict(
                orient="records"
            ),
        }

    return topic_clusters


def get_kmeans_metrics() -> dict:
    """
    Lấy chỉ số đánh giá K-Means.
    """
    model_data = load_kmeans_model()

    return {
        "n_clusters": model_data["n_clusters"],
        "inertia": model_data["inertia"],
        "silhouette_score": model_data[
            "silhouette_score"
        ],
    }


# =========================================================
# 7. CHẠY THỬ
# =========================================================

if __name__ == "__main__":
    from utils.console import use_utf8_console

    use_utf8_console()

    print("=" * 60)
    print("KẾT QUẢ PHÂN CỤM CHỦ ĐỀ BẰNG K-MEANS")
    print("=" * 60)

    clusters = get_topic_clusters()

    for cluster_id, cluster_info in sorted(
        clusters.items()
    ):
        print(
            f"\nCụm {cluster_id} "
            f"- Chủ đề chính: "
            f"{cluster_info['topic']}"
        )

        for item in cluster_info["words"]:
            print(
                f"  - {item['english']} "
                f"({item['vietnamese']}) "
                f"| {item['level']}"
            )

    metrics = get_kmeans_metrics()

    print("\n" + "=" * 60)
    print("CHỈ SỐ ĐÁNH GIÁ")
    print("=" * 60)

    print(
        f"Số cụm: {metrics['n_clusters']}"
    )

    print(
        f"Inertia/SSE: "
        f"{metrics['inertia']:.4f}"
    )

    if metrics["silhouette_score"] is not None:
        print(
            f"Silhouette Score: "
            f"{metrics['silhouette_score']:.4f}"
        )
