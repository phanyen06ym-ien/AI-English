from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QModelIndex,
    QObject,
    Qt,
    QThreadPool,
    Slot,
)

from dataset.vocabulary import all_words
from app_qt.speech_worker import SpeakTask


class VocabularyModel(QAbstractListModel):
    EnglishRole = Qt.UserRole + 1
    VietnameseRole = Qt.UserRole + 2
    CategoryRole = Qt.UserRole + 3
    LevelRole = Qt.UserRole + 4
    LearnedRole = Qt.UserRole + 5

    def __init__(self, words, parent=None):
        super().__init__(parent)
        self._all = words
        self._filtered = list(words)
        self._learned = set()

    def roleNames(self):
        return {
            self.EnglishRole: b"english",
            self.VietnameseRole: b"vietnamese",
            self.CategoryRole: b"category",
            self.LevelRole: b"level",
            self.LearnedRole: b"learned",
        }

    def rowCount(self, parent=QModelIndex()):
        return len(self._filtered)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = self._filtered[index.row()]
        if role == self.EnglishRole:
            return row["english"]
        if role == self.VietnameseRole:
            return row["vietnamese"]
        if role == self.CategoryRole:
            return row["category"]
        if role == self.LevelRole:
            return row["level"]
        if role == self.LearnedRole:
            return row["english"] in self._learned
        return None

    @Slot(list)
    def setLearnedWords(self, words):
        self.beginResetModel()
        self._learned = set(words)
        self.endResetModel()

    @Slot(str)
    def setFilter(self, query):
        query = query.strip().lower()
        self.beginResetModel()
        if not query:
            self._filtered = list(self._all)
        else:
            self._filtered = [
                row
                for row in self._all
                if query in row["english"].lower() or query in row["vietnamese"].lower()
            ]
        self.endResetModel()


class VocabularyController(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = VocabularyModel(list(all_words().values()))

    @Property(QObject, constant=True)
    def model(self):
        return self._model

    @Slot(str)
    def speak(self, word):
        QThreadPool.globalInstance().start(SpeakTask(word))
