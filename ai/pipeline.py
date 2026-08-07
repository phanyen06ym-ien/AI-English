"""End-to-end AI pipeline orchestration."""

from __future__ import annotations

import logging
from time import perf_counter
from typing import Any, Callable, Protocol

from ai.models import (
    ClusterResult,
    DetectedObject,
    DetectionResult,
    ImageAnalysisResult,
    RelatedWord,
    TimingInfo,
    VocabularyEntry,
)


logger = logging.getLogger(__name__)


class DetectorProtocol(Protocol):
    """Detector contract required by AIEngine."""

    def detect(self, frame: Any) -> list[dict[str, Any]]:
        """Return raw detected objects."""


class AIEngine:
    """Coordinate YOLO, vocabulary, k-NN and K-Means pipeline."""

    def __init__(
        self,
        detector: DetectorProtocol,
        classifier: Callable[[str], dict[str, Any]],
        related_words_provider: Callable[[str, int], list[dict[str, Any]]],
        cluster_words_provider: Callable[[str], list[dict[str, Any]]],
        vocabulary_provider: Callable[[], dict[str, dict[str, Any]]],
    ) -> None:
        self.detector = detector
        self.classifier = classifier
        self.related_words_provider = related_words_provider
        self.cluster_words_provider = cluster_words_provider
        self.vocabulary_provider = vocabulary_provider
        self._related_cache: dict[tuple[str, int], list[RelatedWord]] = {}
        self._cluster_cache: dict[str, list[ClusterResult]] = {}

    @classmethod
    def create_default(cls) -> "AIEngine":
        """Create the runtime engine with the existing project components."""
        from ai.detector import ObjectDetector

        logger.info("Loading default AIEngine dependencies")
        return cls.from_detector(
            ObjectDetector()
        )

    @classmethod
    def from_detector(
        cls,
        detector: DetectorProtocol,
    ) -> "AIEngine":
        """Create an engine around an externally provided detector."""
        from ai.kmeans import get_words_in_same_cluster
        from ai.knn import get_related_words
        from ai.vocabulary import all_words, classify_word

        return cls(
            detector=detector,
            classifier=classify_word,
            related_words_provider=get_related_words,
            cluster_words_provider=get_words_in_same_cluster,
            vocabulary_provider=all_words,
        )

    @staticmethod
    def _elapsed_ms(started_at: float) -> float:
        return (perf_counter() - started_at) * 1000

    def detect_objects(self, frame: Any) -> tuple[list[DetectedObject], float]:
        """Run YOLO detection and return typed detected objects with timing."""
        started_at = perf_counter()
        raw_objects = self.detector.detect(frame)
        elapsed_ms = self._elapsed_ms(started_at)
        logger.info("Detected %s object(s)", len(raw_objects))
        return [
            DetectedObject.from_dict(raw_object)
            for raw_object in raw_objects
        ], elapsed_ms

    def classify_object(
        self,
        detected_object: DetectedObject,
    ) -> tuple[VocabularyEntry, float]:
        """Classify a detected object against the vocabulary."""
        started_at = perf_counter()
        word_info = self.classifier(detected_object.class_name)
        elapsed_ms = self._elapsed_ms(started_at)
        if not word_info.get("vietnamese"):
            logger.error("Vocabulary missing for %s", detected_object.class_name)
        return (
            VocabularyEntry.from_dict(
                detected_object.class_name,
                word_info,
            ),
            elapsed_ms,
        )

    def format_detection(
        self,
        detected_object: DetectedObject,
        vocabulary_entry: VocabularyEntry,
    ) -> DetectionResult:
        """Attach vocabulary metadata to one detected object."""
        return DetectionResult(
            english=detected_object.class_name,
            vietnamese=(
                vocabulary_entry.vietnamese
                or detected_object.class_name
            ),
            category=vocabulary_entry.category or "Unknown",
            level=vocabulary_entry.level or "Unknown",
            confidence=detected_object.confidence,
            box=detected_object.box,
            source=vocabulary_entry.source,
        )

    def detect_and_format(self, frame) -> list[dict]:
        """Compatibility helper returning legacy dictionaries."""
        return self.analyze_frame(
            frame
        ).detections_as_dicts()

    def get_vocabulary_entries(self) -> list[dict[str, Any]]:
        """Return all vocabulary rows for presentation models."""
        started_at = perf_counter()
        words = list(
            self.vocabulary_provider().values()
        )
        logger.info(
            "Loaded %s vocabulary entries in %.3f ms",
            len(words),
            self._elapsed_ms(started_at),
        )
        return words

    def get_related_words(
        self,
        word: str,
        n: int = 3,
    ) -> list[RelatedWord]:
        """Return k-NN related words."""
        cache_key = (str(word).strip().lower(), int(n))
        if cache_key not in self._related_cache:
            logger.info("Run KNN for word=%s n=%s", word, n)
            try:
                related_words = self.related_words_provider(word, n)
                self._related_cache[cache_key] = [
                    RelatedWord.from_dict(item)
                    for item in related_words
                ]
            except Exception:
                logger.exception("KNN failed for word=%s", word)
                self._related_cache[cache_key] = []
        return self._related_cache[cache_key]

    def get_cluster_words(
        self,
        word: str,
    ) -> list[ClusterResult]:
        """Return words in the same K-Means cluster."""
        cache_key = str(word).strip().lower()
        if cache_key not in self._cluster_cache:
            logger.info("Run KMeans cluster lookup for word=%s", word)
            try:
                cluster_words = self.cluster_words_provider(word)
                self._cluster_cache[cache_key] = [
                    ClusterResult.from_dict(item)
                    for item in cluster_words
                ]
            except Exception:
                logger.exception("KMeans failed for word=%s", word)
                self._cluster_cache[cache_key] = []
        return self._cluster_cache[cache_key]

    def get_related_word_dicts(
        self,
        word: str,
        n: int = 3,
    ) -> list[dict[str, Any]]:
        """Return k-NN related words as legacy dictionaries."""
        return [
            item.to_dict()
            for item in self.get_related_words(word, n=n)
        ]

    def get_cluster_word_dicts(
        self,
        word: str,
    ) -> list[dict[str, Any]]:
        """Return K-Means cluster words as legacy dictionaries."""
        return [
            item.to_dict()
            for item in self.get_cluster_words(word)
        ]

    def analyze_frame(
        self,
        frame: Any,
        include_learning: bool = True,
    ) -> ImageAnalysisResult:
        """Run the full AI pipeline for one image/frame."""
        pipeline_started_at = perf_counter()
        yolo_ms = 0.0
        vocabulary_ms = 0.0
        knn_ms = 0.0
        kmeans_ms = 0.0

        try:
            logger.info("AI pipeline started")
            detected_objects, yolo_ms = self.detect_objects(frame)

            detections: list[DetectionResult] = []
            for detected_object in detected_objects:
                vocabulary_entry, elapsed_ms = self.classify_object(
                    detected_object
                )
                vocabulary_ms += elapsed_ms
                detections.append(
                    self.format_detection(
                        detected_object,
                        vocabulary_entry,
                    )
                )

            detections.sort(
                key=lambda item: item.confidence,
                reverse=True,
            )

            related_words: list[RelatedWord] = []
            cluster_words: list[ClusterResult] = []

            if detections and include_learning:
                primary_word = detections[0].english

                started_at = perf_counter()
                related_words = self.get_related_words(
                    primary_word,
                    n=3,
                )
                knn_ms = self._elapsed_ms(started_at)

                started_at = perf_counter()
                cluster_words = self.get_cluster_words(
                    primary_word
                )
                kmeans_ms = self._elapsed_ms(started_at)

            timing = TimingInfo(
                yolo_ms=yolo_ms,
                vocabulary_ms=vocabulary_ms,
                knn_ms=knn_ms,
                kmeans_ms=kmeans_ms,
                pipeline_ms=self._elapsed_ms(pipeline_started_at),
            )
            logger.info(
                "AI pipeline finished in %.3f ms",
                timing.pipeline_ms,
            )
            return ImageAnalysisResult(
                success=True,
                detections=detections,
                related_words=related_words,
                cluster_words=cluster_words,
                timing=timing,
                message="OK",
            )

        except Exception as error:
            logger.exception("AI pipeline failed")
            timing = TimingInfo(
                yolo_ms=yolo_ms,
                vocabulary_ms=vocabulary_ms,
                knn_ms=knn_ms,
                kmeans_ms=kmeans_ms,
                pipeline_ms=self._elapsed_ms(pipeline_started_at),
            )
            return ImageAnalysisResult(
                success=False,
                timing=timing,
                message=str(error),
                error_code="AI_PIPELINE_ERROR",
                exception=error,
            )
