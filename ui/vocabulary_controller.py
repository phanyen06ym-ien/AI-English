"""Thin Controller cho man hinh tu vung.

`VocabularyModel` da chuyen sang `ui.viewmodels.vocabulary_viewmodel`; import cu
van chay nho re-export o cuoi file.
"""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QObject,
    Signal,
    Slot,
)

from ui.ui_logger import get_ui_logger, log_button_click
from ui.viewmodels.vocabulary_viewmodel import (
    VocabularyModel,
    VocabularyViewModel,
)
from ui.workers.speech_worker import SpeakTask
from ui.workers.task_pool import submit


logger = get_ui_logger("vocabulary_controller")


class VocabularyController(QObject):
    """Adapter giua QML va `VocabularyViewModel`."""

    relatedWordsChanged = Signal(list)
    clusterWordsChanged = Signal(list)

    def __init__(
        self,
        view_model: VocabularyViewModel,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._view_model = view_model

        self._view_model.RelatedWordsUpdated.connect(
            self.relatedWordsChanged
        )
        self._view_model.ClusterWordsUpdated.connect(
            self.clusterWordsChanged
        )

    @property
    def view_model(self) -> VocabularyViewModel:
        return self._view_model

    @Property(QObject, constant=True)
    def model(self):
        return self._view_model.model

    @Slot(str)
    def speak(
        self,
        word: str,
    ) -> None:
        log_button_click(logger, "speak_word")

        submit(
            SpeakTask(word)
        )

    @Slot(str)
    def loadRelatedWords(
        self,
        word: str,
    ) -> None:
        self._view_model.loadRelatedWords(word)

    @Slot(str)
    def loadClusterWords(
        self,
        word: str,
    ) -> None:
        self._view_model.loadClusterWords(word)


__all__ = [
    "VocabularyController",
    "VocabularyModel",
]
