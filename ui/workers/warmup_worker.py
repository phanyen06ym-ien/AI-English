"""Worker nap truoc AI va tu vung sau khi cua so da hien ra.

Sprint 8: `AppContext` tao `AIEngine` nap tre (~0 ms) de cua so hien ngay. Worker
nay chay ngay sau do, nap AI o thread nen trong luc nguoi dung con dang nhin man
hinh dang nhap.

Ket qua: nguoi dung khong phai cho ~10 giay man hinh trang, va den luc ho bam
"Nhan dien" thi AI thuong da san sang.
"""

from __future__ import annotations

from PySide6.QtCore import Signal

from ui.workers.cancellation import CancellationToken
from ui.workers.lifecycle import ManagedWorker


class WarmupWorker(ManagedWorker):
    """Nap truoc tu vung, k-NN, K-Means va YOLO."""

    #: Phat khi tu vung san sang - man hinh tu vung dung de dien danh sach.
    vocabularyReady = Signal(list)

    #: Phat khi toan bo AI da san sang.
    warmupCompleted = Signal()

    def __init__(
        self,
        parts,
        token: CancellationToken | None = None,
        parent=None,
    ) -> None:
        super().__init__(
            "warmup_worker",
            token=token,
            parent=parent,
        )

        self._parts = parts

    def execute(self) -> None:
        self.token.raise_if_cancelled()

        # 1. Tu vung truoc: man hinh tu vung can no som nhat.
        vocabulary_provider = self._parts.vocabulary_provider.load()

        self.token.raise_if_cancelled()

        entries = list(
            vocabulary_provider().values()
        )
        self.vocabularyReady.emit(entries)

        self.token.raise_if_cancelled()

        # 2. Phan con lai: phan loai, k-NN, K-Means, YOLO.
        self._parts.classifier.load()
        self.token.raise_if_cancelled()

        self._parts.related_words_provider.load()
        self.token.raise_if_cancelled()

        self._parts.cluster_words_provider.load()
        self.token.raise_if_cancelled()

        self._parts.detector.load()

        self.warmupCompleted.emit()


__all__ = ["WarmupWorker"]
