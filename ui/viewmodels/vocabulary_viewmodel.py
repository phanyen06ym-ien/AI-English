"""ViewModel cho man hinh tu vung."""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QModelIndex,
    QObject,
    Qt,
    Signal,
    Slot,
)

from ai.pipeline import AIEngine
from config.schema import AIConfig
from ui.state import UiState
from ui.ui_logger import log_ui_event
from ui.viewmodels.base_viewmodel import BaseViewModel


RELATED_WORDS_COUNT = AIConfig.related_words_count


class VocabularyModel(QAbstractListModel):
    """List model cho danh sach tu vung, kem loc theo tu khoa."""

    EnglishRole = Qt.UserRole + 1
    VietnameseRole = Qt.UserRole + 2
    CategoryRole = Qt.UserRole + 3
    LevelRole = Qt.UserRole + 4

    def __init__(
        self,
        words: list[dict],
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._all_words = words
        self._filtered_words = list(words)

    def roleNames(self):
        return {
            self.EnglishRole: b"english",
            self.VietnameseRole: b"vietnamese",
            self.CategoryRole: b"category",
            self.LevelRole: b"level",
        }

    def rowCount(
        self,
        parent=QModelIndex(),
    ) -> int:
        return len(self._filtered_words)

    def data(
        self,
        index,
        role=Qt.DisplayRole,
    ):
        if not index.isValid():
            return None

        row = self._filtered_words[index.row()]

        if role == self.EnglishRole:
            return row["english"]

        if role == self.VietnameseRole:
            return row["vietnamese"]

        if role == self.CategoryRole:
            return row["category"]

        if role == self.LevelRole:
            return row["level"]

        return None

    @Slot(str)
    def setFilter(
        self,
        query: str,
    ) -> None:
        normalized_query = query.strip().lower()

        self.beginResetModel()

        if not normalized_query:
            self._filtered_words = list(
                self._all_words
            )

        else:
            self._filtered_words = [
                row
                for row in self._all_words
                if (
                    normalized_query
                    in row["english"].lower()
                    or normalized_query
                    in row["vietnamese"].lower()
                )
            ]

        self.endResetModel()


class VocabularyViewModel(BaseViewModel):
    """Cung cap tu vung, tu lien quan (k-NN) va tu cung cum (K-Means)."""

    VocabularyChanged = Signal(list)
    RelatedWordsUpdated = Signal(list)
    ClusterWordsUpdated = Signal(list)

    def __init__(
        self,
        ai_engine: AIEngine,
        config: AIConfig | None = None,
        parent=None,
    ) -> None:
        super().__init__("vocabulary_viewmodel", parent)

        self._ai_engine = ai_engine
        self._config = (
            config
            if config is not None
            else AIConfig()
        )

        vocabulary = self._ai_engine.get_vocabulary_entries()

        self._model = VocabularyModel(vocabulary)
        self.set_state(UiState.IDLE)

    @Property(QObject, constant=True)
    def model(self):
        return self._model

    @Slot(str)
    def loadRelatedWords(
        self,
        word: str,
    ) -> None:
        """Lay tu lien quan qua AIEngine."""
        log_ui_event(self.logger, "load_related_words")

        words = self._ai_engine.get_related_word_dicts(
            word,
            n=self._config.related_words_count,
        )

        self.RelatedWordsUpdated.emit(words)

    @Slot(str)
    def loadClusterWords(
        self,
        word: str,
    ) -> None:
        """Lay tu cung cum qua AIEngine."""
        log_ui_event(self.logger, "load_cluster_words")

        words = self._ai_engine.get_cluster_word_dicts(
            word
        )

        self.ClusterWordsUpdated.emit(words)
