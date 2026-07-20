from __future__ import annotations

import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.exceptions import InconsistentVersionWarning
from sklearn.neighbors import NearestNeighbors
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
    / "knn.pkl"
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

# Chủ đề quan trọng nhất khi gợi ý từ
CATEGORY_WEIGHT = 5.0

# Độ khó có mức ưu tiên thứ hai
LEVEL_WEIGHT = 2.0

# Độ dài từ chỉ là đặc trưng phụ
WORD_LENGTH_WEIGHT = 0.5


# =========================================================
# 3. ĐỌC VÀ CHUẨN HÓA DỮ LIỆU
# =========================================================

def read_vocabulary() -> pd.DataFrame:
    """
    Đọc vocabulary.csv và chuẩn hóa dữ liệu.
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy vocabulary.csv: {DATA_PATH}"
        )

    with perf_monitor.timer("knn_read_vocabulary_csv"):
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
    Tạo đặc trưng số cho k-NN.

    Gồm:
    - Độ dài từ.
    - Độ khó.
    - One-hot chủ đề.
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
    Gán trọng số cho từng nhóm đặc trưng.
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
    Lấy thời gian cập nhật vocabulary.csv.
    """
    return DATA_PATH.stat().st_mtime


# =========================================================
# 5. HUẤN LUYỆN VÀ LƯU MODEL
# =========================================================

def train_knn_model() -> dict:
    """
    Huấn luyện NearestNeighbors để gợi ý từ liên quan.
    """
    dataframe = read_vocabulary()

    if len(dataframe) < 2:
        raise ValueError(
            "Cần ít nhất 2 từ để xây dựng mô hình k-NN."
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

    model = NearestNeighbors(
        n_neighbors=len(dataframe),
        metric="euclidean",
    )

    model.fit(weighted_features)

    model_data = {
        "models": model,
        "scaler": scaler,
        "features": features,
        "feature_columns": feature_columns,
        "vocabulary": dataframe,
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
        f"Đã lưu mô hình k-NN: {MODEL_PATH}"
    )

    return model_data


def load_knn_model() -> dict:
    """
    Tải mô hình k-NN.

    Tự train lại khi:
    - Chưa có file models.
    - vocabulary.csv thay đổi.
    - Khác phiên bản sklearn.
    - Khác phiên bản cấu trúc models.
    """
    global _MODEL_CACHE

    if _MODEL_CACHE is not None:
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

                with perf_monitor.timer("knn_joblib_load"):
                    model_data = joblib.load(
                        MODEL_PATH
                    )

            is_valid = (
                model_data.get("dataset_mtime")
                == get_dataset_modified_time()
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
                "Không thể dùng models k-NN cũ, "
                f"đang train lại: {error}"
            )

    _MODEL_CACHE = train_knn_model()
    return _MODEL_CACHE


# =========================================================
# 6. GỢI Ý TỪ LIÊN QUAN
# =========================================================

def get_related_words(
    word: str,
    n: int = 3,
) -> list[dict]:
    """
    Gợi ý n từ liên quan với từ đầu vào.

    Ví dụ:
        get_related_words("laptop", 3)
    """
    normalized_word = (
        str(word)
        .strip()
        .lower()
    )

    if not normalized_word:
        return []

    model_data = load_knn_model()

    dataframe: pd.DataFrame = (
        model_data["vocabulary"]
    )

    matched_rows = dataframe[
        dataframe["english"]
        == normalized_word
    ]

    if matched_rows.empty:
        return []

    word_index = int(
        matched_rows.index[0]
    )

    features: pd.DataFrame = (
        model_data["features"]
    )

    query_feature = features.iloc[
        [word_index]
    ]

    scaled_feature = (
        model_data["scaler"]
        .transform(query_feature)
    )

    weighted_feature = apply_feature_weights(
        scaled_feature,
        model_data["feature_columns"],
    )

    distances, indices = (
        model_data["models"]
        .kneighbors(weighted_feature)
    )

    number_of_results = max(
        1,
        min(
            int(n),
            len(dataframe) - 1,
        ),
    )

    related_words = []

    for distance, index in zip(
        distances[0],
        indices[0],
    ):
        index = int(index)

        # Không trả lại chính từ đầu vào
        if index == word_index:
            continue

        row = dataframe.iloc[index]

        related_words.append(
            {
                "english": row["english"],
                "vietnamese": row["vietnamese"],
                "category": row["category"],
                "level": row["level"],
                "distance": float(distance),
            }
        )

        if len(related_words) >= number_of_results:
            break

    return related_words


# =========================================================
# 7. CHẠY THỬ
# =========================================================

if __name__ == "__main__":
    from utils.console import use_utf8_console

    use_utf8_console()

    input_word = "laptop"

    print(
        f"Các từ liên quan đến '{input_word}':"
    )

    suggestions = get_related_words(
        input_word,
        n=3,
    )

    if not suggestions:
        print("Không tìm thấy từ liên quan.")

    for index, item in enumerate(
        suggestions,
        start=1,
    ):
        print(
            f"{index}. "
            f"{item['english']} - "
            f"{item['vietnamese']} | "
            f"{item['category']} | "
            f"{item['level']} | "
            f"Distance = {item['distance']:.4f}"
        )
