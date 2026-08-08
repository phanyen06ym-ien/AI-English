"""Nap AI theo kieu tre (lazy) de cua so hien ra ngay.

Van de do duoc o Sprint 8
-------------------------

    import torch                      2.386 ms
    import ai.vocabulary (sklearn,
              pandas di kem)          4.848 ms
    nap model k-NN (.pkl)             1.888 ms
    nap YOLO (ObjectDetector)           431 ms
    ------------------------------------------
    TONG truoc khi cua so hien ra    ~10.000 ms

Toan bo 10 giay do la **chi phi import thu vien**, khong phai tinh toan:
`all_words()` chay xong trong 0 ms sau khi module da nap.

Nguoi dung bam chay va nhin man hinh trong khoang 10 giay ma khong thay gi.

Giai phap
---------

`AIEngine` (Sprint 2) nhan ca 5 phu thuoc qua constructor. Nho vay co the truyen
vao nhung **ham nap tre**: chi import that su o lan goi dau tien.

    AppContext.build()  ->  build_lazy_ai_engine()   (~0 ms)
    cua so hien ra
    context.warmup()    ->  nap AI o thread nen

Ket qua: cua so hien ra gan nhu tuc thi, AI nap xong trong luc nguoi dung con
dang nhin man hinh dang nhap.

**Khong mot dong nao trong `ai/`, `ml/`, `detection/` bi sua.** Ky thuat o day
chi la doi THOI DIEM nap, khong doi thu duoc nap hay ket qua tra ve.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

# Sprint 8: KHONG import `ai.*` o cap module.
# `ai/__init__.py` nap san `ObjectDetector` nen bat ky import nao tu `ai.*`
# cung keo theo torch + ultralytics + sklearn (~6,6 giay). Chi can kieu de
# chu thich thi dung TYPE_CHECKING; cho nao dung that su thi import trong ham.
from core.logging_config import get_logger

if TYPE_CHECKING:  # pragma: no cover
    from ai.pipeline import AIEngine


logger = get_logger("ui.ai_bootstrap")


class LazyObjectDetector:
    """Bao ngoai `ObjectDetector`, chi tao that su o lan `detect()` dau tien.

    An toan da luong: webcam worker va image worker co the cung goi mot luc.
    """

    def __init__(self) -> None:
        self._detector = None
        self._lock = threading.Lock()

    @property
    def is_loaded(self) -> bool:
        return self._detector is not None

    def load(self):
        """Nap detector that. Goi nhieu lan chi nap mot lan."""
        if self._detector is not None:
            return self._detector

        with self._lock:
            if self._detector is not None:
                return self._detector

            logger.info("Bat dau nap YOLO detector")

            from ai.detector import ObjectDetector

            self._detector = ObjectDetector()

            logger.info("Da nap xong YOLO detector")

        return self._detector

    def detect(
        self,
        frame: Any,
    ) -> list[dict[str, Any]]:
        """Giao dien ma `AIEngine` yeu cau."""
        return self.load().detect(frame)


class _LazyCallable:
    """Goi mot ham trong module nang, chi import o lan goi dau tien."""

    def __init__(
        self,
        module_name: str,
        attribute: str,
    ) -> None:
        self._module_name = module_name
        self._attribute = attribute
        self._function = None
        self._lock = threading.Lock()

    @property
    def is_loaded(self) -> bool:
        return self._function is not None

    def load(self):
        if self._function is not None:
            return self._function

        with self._lock:
            if self._function is not None:
                return self._function

            import importlib

            logger.info(
                "Nap %s.%s",
                self._module_name,
                self._attribute,
            )

            module = importlib.import_module(self._module_name)
            self._function = getattr(module, self._attribute)

        return self._function

    def __call__(self, *arguments, **keywords):
        return self.load()(*arguments, **keywords)


class LazyAIEngineParts:
    """Giu tham chieu toi tung phan de `warmup()` nap duoc tat ca."""

    def __init__(self) -> None:
        self.detector = LazyObjectDetector()
        self.classifier = _LazyCallable(
            "ai.vocabulary",
            "classify_word",
        )
        self.related_words_provider = _LazyCallable(
            "ai.knn",
            "get_related_words",
        )
        self.cluster_words_provider = _LazyCallable(
            "ai.kmeans",
            "get_words_in_same_cluster",
        )
        self.vocabulary_provider = _LazyCallable(
            "ai.vocabulary",
            "all_words",
        )

    @property
    def is_loaded(self) -> bool:
        """True khi moi phan da san sang."""
        return all(
            part.is_loaded
            for part in (
                self.detector,
                self.classifier,
                self.related_words_provider,
                self.cluster_words_provider,
                self.vocabulary_provider,
            )
        )

    def warmup(self) -> None:
        """Nap truoc toan bo AI. Goi tren thread nen sau khi cua so hien ra.

        Thu tu nap theo do "nguoi dung can som den dau":
        tu vung -> k-NN/K-Means -> YOLO.
        """
        self.vocabulary_provider.load()
        self.classifier.load()
        self.related_words_provider.load()
        self.cluster_words_provider.load()
        self.detector.load()


def build_lazy_ai_engine() -> "tuple[AIEngine, LazyAIEngineParts]":
    """Tao `AIEngine` khong nap gi ngay - tra ve ca engine va cac phan de warmup.

    `ai.pipeline` duoc import ngay TRONG ham: `AIEngine` la lop dieu phoi nhe,
    nhung `ai/__init__.py` lai keo theo ca torch va sklearn.
    """
    from ai.pipeline import AIEngine

    parts = LazyAIEngineParts()

    engine = AIEngine(
        detector=parts.detector,
        classifier=parts.classifier,
        related_words_provider=parts.related_words_provider,
        cluster_words_provider=parts.cluster_words_provider,
        vocabulary_provider=parts.vocabulary_provider,
    )

    return engine, parts


__all__ = [
    "LazyAIEngineParts",
    "LazyObjectDetector",
    "build_lazy_ai_engine",
]
