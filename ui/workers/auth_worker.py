"""Worker xac thuc.

Van de truoc Sprint 5
---------------------

`AuthService` goi database **dong bo tren GUI thread**. Voi Supabase qua Internet,
mot lan `SELECT` mat ~400 ms (do o Sprint 4), con `bcrypt.checkpw()` co y thiet ke
cham. Nguoi dung bam "Đăng nhập" la ca cua so **dung im** trong khoang thoi gian do.

Giai phap
---------

Dua toan bo thao tac xac thuc sang `ManagedWorker`. GUI chi doi trang thai
`loading` roi cho signal `completed`.

Worker KHONG chua luat nghiep vu - moi thu van nam trong `AuthService` (Sprint 4).
"""

from __future__ import annotations

from enum import Enum

from PySide6.QtCore import Signal

from ui.services.auth_service import AuthResult, AuthService
from ui.workers.cancellation import CancellationToken
from ui.workers.lifecycle import ManagedWorker


class AuthOperation(str, Enum):
    """Thao tac xac thuc ma worker co the chay."""

    LOGIN = "login"
    REGISTER = "register"
    CHANGE_PASSWORD = "change_password"


class AuthWorker(ManagedWorker):
    """Chay mot thao tac xac thuc tren thread nen."""

    #: Phat `AuthResult` khi thao tac hoan tat (ke ca khi that bai nghiep vu).
    completed = Signal(object)

    def __init__(
        self,
        auth_service: AuthService,
        operation: AuthOperation,
        arguments: tuple,
        token: CancellationToken | None = None,
        parent=None,
    ) -> None:
        super().__init__(
            "auth_worker",
            token=token,
            parent=parent,
        )

        self._auth_service = auth_service
        self.operation = operation
        self.arguments = tuple(arguments)

    def _call_service(self) -> AuthResult:
        if self.operation is AuthOperation.LOGIN:
            return self._auth_service.login(*self.arguments)

        if self.operation is AuthOperation.REGISTER:
            return self._auth_service.register(*self.arguments)

        if self.operation is AuthOperation.CHANGE_PASSWORD:
            return self._auth_service.change_password(
                *self.arguments
            )

        raise ValueError(
            f"Thao tac xac thuc khong hop le: {self.operation}"
        )

    def execute(self) -> None:
        self.token.raise_if_cancelled()

        result = self._call_service()

        # Nguoi dung da doi y (vi du dang xuat/dong cua so) thi khong ap ket qua.
        self.token.raise_if_cancelled()

        self.completed.emit(result)


__all__ = [
    "AuthOperation",
    "AuthWorker",
]
