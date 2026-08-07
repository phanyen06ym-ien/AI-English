"""Vocabulary lookup facade used by the AI layer."""

from dataset.vocabulary import all_words, get_word_info
from detection.classify import classify_word
from ml.category_predictor import predict_category

__all__ = [
    "all_words",
    "classify_word",
    "get_word_info",
    "predict_category",
]
