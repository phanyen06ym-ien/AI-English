from pathlib import Path
import warnings

import joblib
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
from sklearn.exceptions import InconsistentVersionWarning
from sklearn.preprocessing import StandardScaler


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "dataset" / "vocabulary.csv"
MODEL_PATH = BASE_DIR / "model" / "kmeans.pkl"
REQUIRED_COLUMNS = ["english", "vietnamese", "category", "level", "frequency"]
MODEL_VERSION = 1


def read_vocabulary():
    """Đọc vocabulary.csv và kiểm tra đủ cột cần dùng."""
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing:
        raise ValueError(
            "Thiếu cột dữ liệu: "
            + ", ".join(missing)
            + ". CSV cần có: english,vietnamese,category,level,frequency"
        )

    df = df[REQUIRED_COLUMNS].copy()
    df["english"] = df["english"].astype(str).str.strip().str.lower()
    df["vietnamese"] = df["vietnamese"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip()
    df["level"] = df["level"].astype(str).str.strip()
    df["frequency"] = pd.to_numeric(df["frequency"], errors="coerce").fillna(0)
    return df.drop_duplicates(subset=["english"]).reset_index(drop=True)


def _encode_column(df, column):
    """Mã hóa category/level thành số để K-Means xử lý được."""
    values = sorted(df[column].unique())
    mapping = {value: index for index, value in enumerate(values)}
    return df[column].map(mapping), mapping


def build_features(df):
    """Feature cho K-Means: length, frequency, category_encoded, level_encoded."""
    features = pd.DataFrame()
    features["length"] = df["english"].str.len()
    features["frequency"] = df["frequency"]
    features["category_encoded"], category_mapping = _encode_column(df, "category")
    features["level_encoded"], level_mapping = _encode_column(df, "level")
    return features, category_mapping, level_mapping


def _dataset_mtime():
    """Lấy thời gian sửa CSV để biết model còn mới hay không."""
    return DATA_PATH.stat().st_mtime


def train_kmeans_model(n_clusters=4):
    """Train K-Means để phân cụm từ vựng, không dùng như classifier."""
    df = read_vocabulary()
    features, category_mapping, level_mapping = build_features(df)

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    cluster_count = min(n_clusters, len(df))
    model = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
    df["cluster"] = model.fit_predict(scaled_features)

    data = {
        "model": model,
        "scaler": scaler,
        "vocabulary": df,
        "category_mapping": category_mapping,
        "level_mapping": level_mapping,
        "dataset_mtime": _dataset_mtime(),
        "n_clusters": cluster_count,
        "model_version": MODEL_VERSION,
        "sklearn_version": sklearn.__version__,
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(data, MODEL_PATH)
    return data


def load_kmeans_model(n_clusters=4):
    """Load model nếu CSV chưa đổi; file rỗng/lỗi thì train lại."""
    if MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 0:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", InconsistentVersionWarning)
                data = joblib.load(MODEL_PATH)
            expected_clusters = min(n_clusters, len(read_vocabulary()))
            if (
                data.get("dataset_mtime") == _dataset_mtime()
                and data.get("n_clusters") == expected_clusters
                and data.get("model_version") == MODEL_VERSION
                and data.get("sklearn_version") == sklearn.__version__
            ):
                return data
        except Exception:
            pass

    return train_kmeans_model(n_clusters)


def cluster_vocabulary(n_clusters=4):
    """Trả về danh sách từ vựng kèm mã cụm."""
    data = load_kmeans_model(n_clusters)
    columns = ["english", "vietnamese", "category", "level", "cluster"]
    return data["vocabulary"][columns].to_dict(orient="records")


def get_cluster_by_word(word):
    """Lấy mã cụm của một từ tiếng Anh."""
    data = load_kmeans_model()
    df = data["vocabulary"]
    word = str(word).strip().lower()
    matched = df[df["english"] == word]

    if matched.empty:
        return None

    return int(matched.iloc[0]["cluster"])


def get_words_in_same_cluster(word):
    """Trả về các từ cùng cụm với từ đầu vào."""
    data = load_kmeans_model()
    df = data["vocabulary"]
    cluster = get_cluster_by_word(word)

    if cluster is None:
        return []

    columns = ["english", "vietnamese", "category", "level", "cluster"]
    return df[df["cluster"] == cluster][columns].to_dict(orient="records")
