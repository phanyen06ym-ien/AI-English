"""UI state machine shared by every ViewModel.

State chuan hoa cho toan bo GUI layer:

    Idle -> Loading -> Detecting -> Completed
                            |
                            +-> Error -> Idle

Controller chi doi State, khong tu tinh toan business logic.
"""

from __future__ import annotations

from enum import Enum


class UiState(str, Enum):
    """Trang thai chuan cua mot man hinh GUI."""

    IDLE = "idle"
    LOADING = "loading"
    DETECTING = "detecting"
    COMPLETED = "completed"
    ERROR = "error"

    def is_busy(self) -> bool:
        """True khi man hinh dang ban va khong nhan input moi."""
        return self in _BUSY_STATES

    def is_terminal(self) -> bool:
        """True khi mot chu ky xu ly da ket thuc."""
        return self in _TERMINAL_STATES


_BUSY_STATES = frozenset(
    {
        UiState.LOADING,
        UiState.DETECTING,
    }
)

_TERMINAL_STATES = frozenset(
    {
        UiState.COMPLETED,
        UiState.ERROR,
    }
)


#: Cac chuyen trang thai duoc phep.
ALLOWED_TRANSITIONS: dict[UiState, frozenset[UiState]] = {
    UiState.IDLE: frozenset(
        {
            UiState.IDLE,
            UiState.LOADING,
            UiState.DETECTING,
            UiState.ERROR,
        }
    ),
    UiState.LOADING: frozenset(
        {
            UiState.LOADING,
            UiState.DETECTING,
            UiState.COMPLETED,
            UiState.ERROR,
            UiState.IDLE,
        }
    ),
    UiState.DETECTING: frozenset(
        {
            UiState.DETECTING,
            UiState.COMPLETED,
            UiState.ERROR,
            UiState.IDLE,
        }
    ),
    UiState.COMPLETED: frozenset(
        {
            UiState.IDLE,
            UiState.LOADING,
            UiState.DETECTING,
            UiState.COMPLETED,
            UiState.ERROR,
        }
    ),
    UiState.ERROR: frozenset(
        {
            UiState.IDLE,
            UiState.LOADING,
            UiState.DETECTING,
            UiState.ERROR,
        }
    ),
}


def can_transition(
    current: UiState,
    target: UiState,
) -> bool:
    """Kiem tra mot chuyen trang thai co hop le hay khong."""
    return target in ALLOWED_TRANSITIONS.get(
        current,
        frozenset(),
    )
