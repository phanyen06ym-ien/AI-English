from pathlib import Path
import warnings

import joblib
import pandas as pd
import sklearn
from sklearn.exceptions import InconsistentVersionWarning
from sklearn.naive_bayes import GaussianNB, MultinomialNB
from sklearn.pipeline import Pipeline

from ml.features import build_vectorizer


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "dataset" / "vocabulary.csv"
MODEL_PATH = BASE_DIR / "model" / "bayes.pkl"
REQUIRED_COLUMNS = ["english", "vietnamese", "category", "level", "frequency"]
MODEL_VERSION = 1


def build_pipeline():
    """Giữ pipeline cũ để file khác import không bị lỗi."""
    return Pipeline([
        ("tfidf", build_vectorizer()),
        ("clf", MultinomialNB()),
    ])


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
    """Mã hóa cột chữ thành số theo thứ tự ổn định."""
    values = sorted(df[column].unique())
    mapping = {value: index for index, value in enumerate(values)}
    return df[column].map(mapping), mapping


def build_features(df):
    """Feature cho Bayes: length, frequency, category_encoded."""
    features = pd.DataFrame()
    features["length"] = df["english"].str.len()
    features["frequency"] = df["frequency"]
    features["category_encoded"], category_mapping = _encode_column(df, "category")
    return features, category_mapping


def _dataset_mtime():
    """Lấy thời gian sửa CSV để biết model còn mới hay không."""
    return DATA_PATH.stat().st_mtime


def train_bayes_model():
    """Train GaussianNB để phân loại độ khó từ vựng: Easy, Medium, Hard."""
    df = read_vocabulary()
    features, category_mapping = build_features(df)

    model = GaussianNB()
    model.fit(features, df["level"])

    data = {
        "model": model,
        "vocabulary": df,
        "category_mapping": category_mapping,
        "dataset_mtime": _dataset_mtime(),
        "model_version": MODEL_VERSION,
        "sklearn_version": sklearn.__version__,
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(data, MODEL_PATH)
    return data


def load_bayes_model():
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

    return train_bayes_model()


def predict_word_level(word):
    """Dự đoán độ khó của từ; nếu từ không có trong CSV thì trả Unknown."""
    data = load_bayes_model()
    df = data["vocabulary"]
    word = str(word).strip().lower()
    matched = df[df["english"] == word]

    if matched.empty:
        return "Unknown"

    row = matched.iloc[0]
    features = pd.DataFrame([
        {
            "length": len(row["english"]),
            "frequency": row["frequency"],
            "category_encoded": data["category_mapping"].get(row["category"], -1),
        }
    ])
    return str(data["model"].predict(features)[0])
