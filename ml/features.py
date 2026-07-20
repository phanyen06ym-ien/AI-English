from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "dataset" / "vocabulary.csv"

REQUIRED_COLUMNS = [
    "english",
    "vietnamese",
    "category",
    "level",
]

LEVEL_ORDER = {
    "Easy": 0,
    "Medium": 1,
    "Hard": 2,
}


def read_vocabulary() -> pd.DataFrame:
    """
    Đọc và chuẩn hóa dữ liệu từ vocabulary.csv.
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy vocabulary.csv tại: {DATA_PATH}"
        )

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


def build_features(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Chuyển dữ liệu từ vựng thành các đặc trưng số.

    Đặc trưng gồm:
    - Độ dài từ.
    - Độ khó.
    - One-hot category.
    """
    features = pd.DataFrame(
        index=dataframe.index
    )

    features["word_length"] = (
        dataframe["english"].str.len()
    )

    features["level_encoded"] = (
        dataframe["level"]
        .map(LEVEL_ORDER)
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


def get_dataset_modified_time() -> float:
    """
    Lấy thời gian cập nhật cuối của vocabulary.csv.

    Dùng để tự train lại models khi CSV thay đổi.
    """
    return DATA_PATH.stat().st_mtime