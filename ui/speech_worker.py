"""Compatibility shim.

`SpeakTask` da chuyen sang `ui.workers.speech_worker` trong Sprint 3.
Module nay duoc giu de import cu khong bi vo.
"""

from __future__ import annotations

from ui.workers.speech_worker import SpeakTask


__all__ = ["SpeakTask"]
