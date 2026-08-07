"""k-NN facade for related-word retrieval."""

from ml.knn import (
    CATEGORY_WEIGHT,
    LEVEL_MAPPING,
    LEVEL_WEIGHT,
    MODEL_PATH,
    MODEL_VERSION,
    REQUIRED_COLUMNS,
    WORD_LENGTH_WEIGHT,
    apply_feature_weights,
    build_features,
    get_dataset_modified_time,
    get_related_words,
    load_knn_model,
    read_vocabulary,
    train_knn_model,
)

__all__ = [
    "CATEGORY_WEIGHT",
    "LEVEL_MAPPING",
    "LEVEL_WEIGHT",
    "MODEL_PATH",
    "MODEL_VERSION",
    "REQUIRED_COLUMNS",
    "WORD_LENGTH_WEIGHT",
    "apply_feature_weights",
    "build_features",
    "get_dataset_modified_time",
    "get_related_words",
    "load_knn_model",
    "read_vocabulary",
    "train_knn_model",
]
