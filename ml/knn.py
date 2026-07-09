from pathlib import Path
import warnings
import joblib
import pandas as pd
import sklearn
from sklearn.exceptions import InconsistentVersionWarning
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from ml.features import build_vectorizer   # nếu cần, có thể import

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "dataset" / "vocabulary.csv"
MODEL_PATH = BASE_DIR / "model" / "knn.pkl"
REQUIRED_COLUMNS = ["english", "vietnamese", "category", "level"]
MODEL_VERSION = 2
CATEGORY_WEIGHT = 5
LEVEL_WEIGHT = 2

def read_vocabulary():
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError("Thiếu cột: " + ", ".join(missing))
    df = df[REQUIRED_COLUMNS].copy()
    df["english"] = df["english"].astype(str).str.strip().str.lower()
    df["vietnamese"] = df["vietnamese"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip()
    df["level"] = df["level"].astype(str).str.strip()
    return df.drop_duplicates(subset=["english"]).reset_index(drop=True)

def _encode_column(df, column):
    values = sorted(df[column].unique())
    mapping = {v: i for i, v in enumerate(values)}
    return df[column].map(mapping), mapping

def build_features(df):
    features = pd.DataFrame()
    features["category_encoded"], _ = _encode_column(df, "category")
    features["level_encoded"], _ = _encode_column(df, "level")
    features["length"] = df["english"].str.len()
    return features

def _dataset_mtime():
    return DATA_PATH.stat().st_mtime

def _apply_feature_weights(scaled_features):
    scaled = scaled_features.copy()
    scaled[:, 0] *= CATEGORY_WEIGHT
    scaled[:, 1] *= LEVEL_WEIGHT
    return scaled

def train_knn_model():
    df = read_vocabulary()
    features = build_features(df)
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
        "dataset_mtime": _dataset_mtime(),
        "model_version": MODEL_VERSION,
        "sklearn_version": sklearn.__version__,
    }
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(data, MODEL_PATH)
    return data

def load_knn_model():
    if MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 0:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", InconsistentVersionWarning)
                data = joblib.load(MODEL_PATH)
            if (data.get("dataset_mtime") == _dataset_mtime() and
                data.get("model_version") == MODEL_VERSION and
                data.get("sklearn_version") == sklearn.__version__):
                return data
        except Exception:
            pass
    return train_knn_model()

def get_related_words(word, n=3):
    data = load_knn_model()
    df = data["vocabulary"]
    word = str(word).strip().lower()
    matched = df[df["english"] == word]
    if matched.empty:
        return []
    idx = matched.index[0]
    feature = data["features"].iloc[[idx]]
    scaled = data["scaler"].transform(feature)
    weighted = _apply_feature_weights(scaled)
    distances, indices = data["model"].kneighbors(weighted)

    related = []
    for i in indices[0]:
        if i == idx:
            continue
        row = df.iloc[i]
        related.append({
            "english": row["english"],
            "vietnamese": row["vietnamese"],
            "category": row["category"],
            "level": row["level"],
        })
        if len(related) == n:
            break
    return related