from PySide6.QtCore import Property, QObject, QThread, Signal, Slot

from database.history import get_stats
from dataset.vocabulary import all_words


class StatsLoadWorker(QThread):
    """Đọc thống kê ở luồng nền để không đơ UI khi DB chậm."""

    loaded = Signal(dict)

    def run(self):
        self.loaded.emit(get_stats())


class StatsController(QObject):
    statsChanged = Signal()
    loadingChanged = Signal(bool)
    detectedWordsChanged = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._total = 0
        self._distinct_words = 0
        self._vocab_learned = 0
        self._vocab_total = len(all_words())
        self._category_breakdown = []
        self._worker = None

    @Property(int, notify=statsChanged)
    def total(self):
        return self._total

    @Property(int, notify=statsChanged)
    def distinctWords(self):
        return self._distinct_words

    @Property(int, notify=statsChanged)
    def vocabLearned(self):
        return self._vocab_learned

    @Property(int, constant=True)
    def vocabTotal(self):
        return self._vocab_total

    @Property(list, notify=statsChanged)
    def categoryBreakdown(self):
        return self._category_breakdown

    def _get_loading(self):
        return self._worker is not None

    loading = Property(bool, _get_loading, notify=loadingChanged)

    @Slot()
    def refresh(self):
        if self._worker is not None:
            return

        self._worker = StatsLoadWorker()
        self._worker.loaded.connect(self._on_loaded)
        self._worker.finished.connect(self._on_finished)
        self.loadingChanged.emit(True)
        self._worker.start()

    def _on_loaded(self, stats):
        detected_words = stats["words_detected"]
        vocab_words = set(all_words().keys())

        self._total = stats["total"]
        self._distinct_words = stats["distinct_words"]
        self._vocab_learned = len(vocab_words & set(detected_words))
        self._category_breakdown = [
            {"category": category, "count": count}
            for category, count in stats["by_category"].items()
        ]

        self.statsChanged.emit()
        self.detectedWordsChanged.emit(detected_words)

    def _on_finished(self):
        self._worker = None
        self.loadingChanged.emit(False)
