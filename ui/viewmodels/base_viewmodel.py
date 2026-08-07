"""BaseViewModel - lop nen cho moi ViewModel trong GUI layer.

ViewModel giu TRANG THAI trinh bay va dieu phoi Worker/Service. ViewModel
khong biet QML, khong tao widget, khong mo dialog. Controller chi doc lai
trang thai nay va chuyen tiep ra QML.

Signal chuan hoa (NHIEM VU 3) dung PascalCase dung theo dac ta Sprint 3, tach
biet han voi signal legacy camelCase ma QML hien tai dang bind.
"""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QObject,
    Signal,
    Slot,
)

from ui.state import UiState, can_transition
from ui.ui_logger import get_ui_logger, log_state_change


class BaseViewModel(QObject):
    """Trang thai + vong doi chung cho moi ViewModel."""

    #: Signal chuan hoa - dung chung cho toan bo ViewModel.
    StateChanged = Signal(str)
    StatusMessageChanged = Signal(str)
    BusyChanged = Signal(bool)
    ErrorRaised = Signal(str)

    def __init__(
        self,
        component: str,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._component = component
        self._logger = get_ui_logger(component)
        self._state = UiState.IDLE
        self._status_message = ""
        self._user_id: int | None = None

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def logger(self):
        return self._logger

    @Property(str, notify=StateChanged)
    def state(self) -> str:
        return self._state.value

    @property
    def ui_state(self) -> UiState:
        return self._state

    @Property(bool, notify=BusyChanged)
    def busy(self) -> bool:
        return self._state.is_busy()

    @Property(str, notify=StatusMessageChanged)
    def statusMessage(self) -> str:
        return self._status_message

    @property
    def user_id(self) -> int | None:
        return self._user_id

    def set_user_id(
        self,
        user_id: int | None,
    ) -> None:
        """Doi nguoi dung hien tai. Lop con override de reset du lieu."""
        self._user_id = user_id

    def set_state(
        self,
        state: UiState,
    ) -> bool:
        """Doi trang thai. Tra ve False neu chuyen trang thai khong hop le."""
        if state is self._state:
            return True

        if not can_transition(self._state, state):
            self._logger.warning(
                "invalid_state_transition %s -> %s",
                self._state.value,
                state.value,
            )
            return False

        previous = self._state
        was_busy = previous.is_busy()

        self._state = state
        log_state_change(self._logger, previous, state)
        self.StateChanged.emit(state.value)

        if was_busy != state.is_busy():
            self.BusyChanged.emit(state.is_busy())

        return True

    def set_status(
        self,
        message: str,
    ) -> None:
        """Cap nhat status message hien thi tren View."""
        self._status_message = message
        self.StatusMessageChanged.emit(message)

    def fail(
        self,
        message: str,
    ) -> None:
        """Chuyen sang trang thai loi kem thong bao."""
        self.set_state(UiState.ERROR)
        self.set_status(message)
        self.ErrorRaised.emit(message)

    @Slot()
    def reset(self) -> None:
        """Ve trang thai Idle."""
        self.set_state(UiState.IDLE)

    # ------------------------------------------------------------------
    # Vong doi
    # ------------------------------------------------------------------

    def _cancel_workers(
        self,
        workers,
    ) -> None:
        """Yeu cau moi worker dung. KHONG chan GUI thread (Sprint 5)."""
        for worker in workers:
            if worker is None:
                continue

            try:
                worker.cancel()
            except RuntimeError:
                continue

    def _await_workers(
        self,
        workers,
        timeout_ms: int = 3000,
    ) -> None:
        """Huy va cho cac worker nen ket thuc truoc khi bo ViewModel.

        Bo qua buoc nay se lam Qt abort voi loi
        "QThread: Destroyed while thread is still running".

        Sprint 5: moi worker la `ManagedWorker` nen dung `dispose()` - vua huy
        vua cho, va danh dau trang thai `disposed`.
        """
        for worker in workers:
            if worker is None:
                continue

            try:
                disposer = getattr(worker, "dispose", None)

                if disposer is not None:
                    disposer(timeout_ms)
                elif worker.isRunning():
                    worker.wait(timeout_ms)

            except RuntimeError:
                # Worker da bi Qt huy truoc do.
                continue

    def shutdown(
        self,
        timeout_ms: int = 3000,
    ) -> None:
        """Dung moi worker nen. Lop con override khi co worker rieng."""
        return None
