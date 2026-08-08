"""AI facade package for detection and vocabulary learning modules.

Sprint 8 - nap tre (PEP 562)
----------------------------

Truoc Sprint 8, file nay import san MOI thu ngay khi ai do cham vao `ai.*`:

    from ai.models import ImageAnalysisResult     # chi can 1 dataclass...
      -> chay ai/__init__.py
        -> from ai.detector import ObjectDetector -> ultralytics + torch
        -> from ai.kmeans  import ...             -> scikit-learn + pandas
        -> from ai.knn     import ...             -> scikit-learn
      => 6.662 ms

Vi vay `AppContext.build()` — vốn chỉ cần lớp điều phối `AIEngine` — phải chờ
gần 7 giây trước khi cửa sổ kịp hiện ra.

Gio dung `__getattr__` cap module: ten chi duoc phan giai khi that su duoc dung.

    import ai                    # ~0 ms
    ai.ObjectDetector            # luc nay moi nap ultralytics

**API cong khai KHONG doi.** `from ai import ObjectDetector`,
`from ai.pipeline import AIEngine`, `ai.all_words()` deu chay y het truoc.
Day chi la doi THOI DIEM nap, khong doi mot phep tinh nao.

`ml/`, `detection/`, `dataset/` va toan bo thuat toan van nguyen ven.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any


#: Ten cong khai -> module chua no.
_EXPORTS: dict[str, str] = {
    "ObjectDetector": "ai.detector",
    "cluster_vocabulary": "ai.kmeans",
    "get_cluster_by_word": "ai.kmeans",
    "get_kmeans_metrics": "ai.kmeans",
    "get_topic_clusters": "ai.kmeans",
    "get_words_in_same_cluster": "ai.kmeans",
    "get_related_words": "ai.knn",
    "ClusterResult": "ai.models",
    "DetectedObject": "ai.models",
    "DetectionResult": "ai.models",
    "ImageAnalysisResult": "ai.models",
    "RelatedWord": "ai.models",
    "TimingInfo": "ai.models",
    "VocabularyEntry": "ai.models",
    "AIEngine": "ai.pipeline",
    "all_words": "ai.vocabulary",
    "classify_word": "ai.vocabulary",
    "get_word_info": "ai.vocabulary",
}


def __getattr__(name: str) -> Any:
    """Nap module chua `name` o lan truy cap dau tien (PEP 562)."""
    module_name = _EXPORTS.get(name)

    if module_name is None:
        raise AttributeError(
            f"module 'ai' has no attribute {name!r}"
        )

    value = getattr(
        importlib.import_module(module_name),
        name,
    )

    # Ghi lai vao module de lan sau khong phai tra bang nua.
    globals()[name] = value

    return value


def __dir__() -> list[str]:
    return sorted(__all__)


if TYPE_CHECKING:  # pragma: no cover
    # Chi de cong cu kiem tra kieu nhin thay, khong chay luc runtime.
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
