from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QModelIndex,
    QObject,
    Qt,
    QThreadPool,
    Signal,
    Slot,
)

from dataset.vocabulary import all_words
from ml.kmeans import get_words_in_same_cluster
from ml.knn import get_related_words
from ui.speech_worker import SpeakTask


class VocabularyModel(QAbstractListModel):
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

        row = self._filtered_words[
            index.row()
        ]

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
        normalized_query = (
            query.strip().lower()
        )

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


class VocabularyController(QObject):
    relatedWordsChanged = Signal(list)
    clusterWordsChanged = Signal(list)

    def __init__(
        self,
        parent=None,
    ) -> None:
        super().__init__(parent)

        vocabulary = list(
            all_words().values()
        )

        self._model = VocabularyModel(
            vocabulary
        )

    @Property(QObject, constant=True)
    def model(self):
        return self._model

    @Slot(str)
    def speak(
        self,
        word: str,
    ) -> None:
        QThreadPool.globalInstance().start(
            SpeakTask(word)
        )

    @Slot(str)
    def loadRelatedWords(
        self,
        word: str,
    ) -> None:
        words = get_related_words(
            word,
            n=3,
        )

        self.relatedWordsChanged.emit(
            words
        )

    @Slot(str)
    def loadClusterWords(
        self,
        word: str,
    ) -> None:
        words = get_words_in_same_cluster(
            word
        )

        self.clusterWordsChanged.emit(
            words
        )