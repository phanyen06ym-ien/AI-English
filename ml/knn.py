from pathlib import Path
import warnings

import joblib
import pandas as pd
import sklearn
from sklearn.exceptions import InconsistentVersionWarning
from sklearn.neighbors import KNeighborsClassifier, NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.features import build_vectorizer


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "dataset" / "vocabulary.csv"
MODEL_PATH = BASE_DIR / "model" / "knn.pkl"
REQUIRED_COLUMNS = ["english", "vietnamese", "category", "level"]
MODEL_VERSION = 2
CATEGORY_WEIGHT = 5
LEVEL_WEIGHT = 2


def build_pipeline(n_neighbors=3):
    """Giữ pipeline cũ để file khác import không lỗi."""
    return Pipeline([
        ("tfidf", build_vectorizer()),
        ("clf", KNeighborsClassifier(n_neighbors=n_neighbors)),
    ])


def read_vocabulary():
    """Đọc vocabulary.csv 4 cột: english, vietnamese, category, level."""
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing:
        raise ValueError(
            "Thiếu cột dữ liệu: "
            + ", ".join(missing)
            + ". CSV cần có: english,vietnamese,category,level"
        )

    df = df[REQUIRED_COLUMNS].copy()
    df["english"] = df["english"].astype(str).str.strip().str.lower()
    df["vietnamese"] = df["vietnamese"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip()
    df["level"] = df["level"].astype(str).str.strip()
    return df.drop_duplicates(subset=["english"]).reset_index(drop=True)


def _encode_column(df, column):
    """Mã hóa category/level thành số."""
    values = sorted(df[column].unique())
    mapping = {value: index for index, value in enumerate(values)}
    return df[column].map(mapping), mapping


def build_features(df):
    """Feature cho k-NN: category_encoded, level_encoded, length."""
    features = pd.DataFrame()
    features["category_encoded"], category_mapping = _encode_column(df, "category")
    features["level_encoded"], level_mapping = _encode_column(df, "level")
    features["length"] = df["english"].str.len()
    return features, category_mapping, level_mapping


def _dataset_mtime():
    return DATA_PATH.stat().st_mtime


def _apply_feature_weights(scaled_features):
    """Tăng trọng số category/level để ưu tiên từ cùng chủ đề."""
    scaled_features = scaled_features.copy()
    scaled_features[:, 0] *= CATEGORY_WEIGHT
    scaled_features[:, 1] *= LEVEL_WEIGHT
    return scaled_features


def train_knn_model():
    """Train NearestNeighbors và lưu model vào model/knn.pkl."""
    df = read_vocabulary()
    features, category_mapping, level_mapping = build_features(df)

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)
    weighted_features = _apply_feature_weights(scaled_features)

    model = NearestNeighbors(n_neighbors=len(df), metric="euclidean")
    model.fit(weighted_features)

    data = {
        "model": model,
        "scaler": scaler,
        "features": features,
        "vocabulary": df,
        "category_mapping": category_mapping,
        "level_mapping": level_mapping,
        "dataset_mtime": _dataset_mtime(),
        "model_version": MODEL_VERSION,
        "sklearn_version": sklearn.__version__,
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(data, MODEL_PATH)
    return data


def load_knn_model():
    """Load model nếu CSV chưa đổi; file rỗng/lỗi thì train lại."""
    if MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 0:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", InconsistentVersionWarning)
                data = joblib.load(MODEL_PATH)
            if (
                data.get("dataset_mtime") == _dataset_mtime()
                and data.get("model_version") == MODEL_VERSION
                and data.get("sklearn_version") == sklearn.__version__
            ):
                return data
        except Exception:
            pass

    return train_knn_model()


def get_related_words(word, n=3):
    """Trả về danh sách n từ liên quan; không có từ thì trả []."""
    data = load_knn_model()
    df = data["vocabulary"]
    word = str(word).strip().lower()
    matched = df[df["english"] == word]

    if matched.empty:
        return []

    word_index = matched.index[0]
    feature = data["features"].iloc[[word_index]]
    scaled_feature = data["scaler"].transform(feature)
    weighted_feature = _apply_feature_weights(scaled_feature)
    distances, indices = data["model"].kneighbors(weighted_feature)

    related_words = []
    for index in indices[0]:
        if index == word_index:
            continue

        row = df.iloc[index]
        related_words.append({
            "english": row["english"],
            "vietnamese": row["vietnamese"],
            "category": row["category"],
            "level": row["level"],
        })

        if len(related_words) == n:
            break

    return related_words
