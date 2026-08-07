"""ViewModel layer (MVVM).

    QML  ->  Controller (thin adapter)  ->  ViewModel  ->  Worker  ->  Service
                                                             |
                                                             v
                                                          AIEngine / Repository

ViewModel giu trang thai trinh bay va State machine (`ui.state.UiState`).
Controller khong con giu business logic, chi chuyen tiep Property/Signal/Slot
sang dung ten ma QML hien tai dang bind.
"""

from __future__ import annotations

from ui.viewmodels.base_viewmodel import BaseViewModel
from ui.viewmodels.history_viewmodel import (
    HistoryModel,
    HistoryViewModel,
)
from ui.viewmodels.image_viewmodel import ImageViewModel
from ui.viewmodels.statistics_viewmodel import StatisticsViewModel
from ui.viewmodels.vocabulary_viewmodel import (
    VocabularyModel,
    VocabularyViewModel,
)
from ui.viewmodels.webcam_viewmodel import WebcamViewModel


__all__ = [
    "BaseViewModel",
    "HistoryModel",
    "HistoryViewModel",
    "ImageViewModel",
    "StatisticsViewModel",
    "VocabularyModel",
    "VocabularyViewModel",
    "WebcamViewModel",
]
