"""AI facade package for detection and vocabulary learning modules."""

from ai.detector import ObjectDetector
from ai.kmeans import (
    cluster_vocabulary,
    get_cluster_by_word,
    get_kmeans_metrics,
    get_topic_clusters,
    get_words_in_same_cluster,
)
from ai.knn import get_related_words
from ai.models import (
    ClusterResult,
    DetectedObject,
    DetectionResult,
    ImageAnalysisResult,
    RelatedWord,
    TimingInfo,
    VocabularyEntry,
)
from ai.pipeline import AIEngine
from ai.vocabulary import all_words, classify_word, get_word_info

__all__ = [
    "AIEngine",
    "ClusterResult",
    "DetectedObject",
    "DetectionResult",
    "ImageAnalysisResult",
    "ObjectDetector",
    "RelatedWord",
    "TimingInfo",
    "VocabularyEntry",
    "all_words",
    "classify_word",
    "cluster_vocabulary",
    "get_cluster_by_word",
    "get_kmeans_metrics",
    "get_related_words",
    "get_topic_clusters",
    "get_word_info",
    "get_words_in_same_cluster",
]
