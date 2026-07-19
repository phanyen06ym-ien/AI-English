# ml/knn.py

from pathlib import Path
import joblib
import pandas as pd

from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "dataset" / "vocabulary.csv"
MODEL_PATH = BASE_DIR / "model" / "knn.pkl"


REQUIRED_COLUMNS = [
    "english",
    "vietnamese",
    "category",
    "level"
]


CATEGORY_WEIGHT = 5
LEVEL_WEIGHT = 2


def read_vocabulary():
    df = pd.read_csv(
        DATA_PATH,
        encoding="utf-8-sig"
    )

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Dataset thiếu cột: {missing_columns}"
        )

    df = df[REQUIRED_COLUMNS].copy()

    df["english"] = (
        df["english"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    df["vietnamese"] = (
        df["vietnamese"]
        .astype(str)
        .str.strip()
    )

    df["category"] = (
        df["category"]
        .astype(str)
        .str.strip()
    )

    df["level"] = (
        df["level"]
        .astype(str)
        .str.strip()
    )

    df = df.drop_duplicates(
        subset=["english"]
    )

    return df.reset_index(drop=True)


def encode_column(df, column):
    values = sorted(
        df[column].unique()
    )

    mapping = {
        value: index
        for index, value in enumerate(values)
    }

    encoded = df[column].map(mapping)

    return encoded


def build_features(df):

    features = pd.DataFrame()

    features["category"] = encode_column(
        df,
        "category"
    )

    features["level"] = encode_column(
        df,
        "level"
    )

    features["length"] = (
        df["english"].str.len()
    )

    return features


def apply_weights(features):

    features = features.copy()

    features[:, 0] *= CATEGORY_WEIGHT

    features[:, 1] *= LEVEL_WEIGHT

    return features


def train_knn_model():

    df = read_vocabulary()

    features = build_features(df)

    scaler = StandardScaler()

    scaled_features = scaler.fit_transform(
        features
    )

    weighted_features = apply_weights(
        scaled_features
    )

    model = NearestNeighbors(
        n_neighbors=len(df),
        metric="euclidean"
    )

    model.fit(
        weighted_features
    )

    data = {
        "model": model,
        "scaler": scaler,
        "features": features,
        "vocabulary": df
    }

    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    joblib.dump(
        data,
        MODEL_PATH
    )

    print("Đã huấn luyện KNN thành công!")

    return data


def load_knn_model():

    if not MODEL_PATH.exists():
        return train_knn_model()

    return joblib.load(
        MODEL_PATH
    )


def get_related_words(
    word,
    n=3
):

    data = load_knn_model()

    df = data["vocabulary"]

    word = (
        str(word)
        .strip()
        .lower()
    )

    matched = df[
        df["english"] == word
    ]

    if matched.empty:
        return []

    index = matched.index[0]

    feature = (
        data["features"]
        .iloc[[index]]
    )

    scaled = data["scaler"].transform(
        feature
    )

    weighted = apply_weights(
        scaled
    )

    distances, indices = (
        data["model"].kneighbors(
            weighted
        )
    )

    results = []

    for i in indices[0]:

        if i == index:
            continue

        row = df.iloc[i]

        results.append({
            "english": row["english"],
            "vietnamese": row["vietnamese"],
            "category": row["category"],
            "level": row["level"]
        })

        if len(results) >= n:
            break

    return results