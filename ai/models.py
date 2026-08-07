"""Typed data models for the AI pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DetectedObject:
    """Raw object returned by the detector."""

    class_name: str
    confidence: float
    box: tuple[int, int, int, int]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DetectedObject":
        return cls(
            class_name=str(data["class_name"]),
            confidence=float(data["confidence"]),
            box=tuple(data["box"]),
        )


@dataclass(frozen=True)
class VocabularyEntry:
    """Vocabulary metadata for a detected English word."""

    english: str
    vietnamese: str | None
    category: str | None
    level: str | None
    source: str = "lookup"

    @classmethod
    def from_dict(
        cls,
        english: str,
        data: dict[str, Any],
    ) -> "VocabularyEntry":
        return cls(
            english=english,
            vietnamese=data.get("vietnamese"),
            category=data.get("category"),
            level=data.get("level"),
            source=data.get("source", "lookup"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "english": self.english,
            "vietnamese": self.vietnamese,
            "category": self.category,
            "level": self.level,
            "source": self.source,
        }


@dataclass(frozen=True)
class RelatedWord:
    """One related vocabulary item returned by k-NN."""

    english: str
    vietnamese: str
    category: str
    level: str
    distance: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RelatedWord":
        return cls(
            english=str(data["english"]),
            vietnamese=str(data["vietnamese"]),
            category=str(data["category"]),
            level=str(data["level"]),
            distance=float(data["distance"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "english": self.english,
            "vietnamese": self.vietnamese,
            "category": self.category,
            "level": self.level,
            "distance": self.distance,
        }


@dataclass(frozen=True)
class ClusterResult:
    """One vocabulary item from the same K-Means cluster."""

    english: str
    vietnamese: str
    category: str
    level: str
    cluster: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClusterResult":
        return cls(
            english=str(data["english"]),
            vietnamese=str(data["vietnamese"]),
            category=str(data["category"]),
            level=str(data["level"]),
            cluster=int(data["cluster"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "english": self.english,
            "vietnamese": self.vietnamese,
            "category": self.category,
            "level": self.level,
            "cluster": self.cluster,
        }


@dataclass(frozen=True)
class DetectionResult:
    """Formatted detection consumed by GUI and history flows."""

    english: str
    vietnamese: str
    category: str
    level: str
    confidence: float
    box: tuple[int, int, int, int]
    source: str = "lookup"

    @property
    def text(self) -> str:
        return (
            f"{self.english} - {self.vietnamese} "
            f"[{self.category} - {self.level}] "
            f"({self.confidence:.2f})"
        )

    def to_dict(
        self,
        include_box: bool = True,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            "english": self.english,
            "vietnamese": self.vietnamese,
            "category": self.category,
            "level": self.level,
            "confidence": self.confidence,
            "text": self.text,
        }
        if include_box:
            data["box"] = self.box
        return data


@dataclass(frozen=True)
class TimingInfo:
    """Measured duration of each AI pipeline step in milliseconds."""

    yolo_ms: float = 0.0
    vocabulary_ms: float = 0.0
    knn_ms: float = 0.0
    kmeans_ms: float = 0.0
    pipeline_ms: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {
            "yolo_ms": self.yolo_ms,
            "vocabulary_ms": self.vocabulary_ms,
            "knn_ms": self.knn_ms,
            "kmeans_ms": self.kmeans_ms,
            "pipeline_ms": self.pipeline_ms,
        }


@dataclass(frozen=True)
class ImageAnalysisResult:
    """Complete result returned by AIEngine."""

    success: bool
    detections: list[DetectionResult] = field(default_factory=list)
    related_words: list[RelatedWord] = field(default_factory=list)
    cluster_words: list[ClusterResult] = field(default_factory=list)
    timing: TimingInfo = field(default_factory=TimingInfo)
    message: str = ""
    error_code: str | None = None
    exception: Exception | None = None

    def detections_as_dicts(
        self,
        include_box: bool = True,
    ) -> list[dict[str, Any]]:
        return [
            detection.to_dict(include_box=include_box)
            for detection in self.detections
        ]

    def related_words_as_dicts(self) -> list[dict[str, Any]]:
        return [
            word.to_dict()
            for word in self.related_words
        ]

    def cluster_words_as_dicts(self) -> list[dict[str, Any]]:
        return [
            word.to_dict()
            for word in self.cluster_words
        ]
