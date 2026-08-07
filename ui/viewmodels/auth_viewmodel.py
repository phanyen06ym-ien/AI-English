"""ViewModel cho dang nhap / dang ky / doi mat khau.

Sprint 3: tach luat kiem tra ra `AuthService`.
Sprint 4: `AuthService` goi `UserRepository` thay vi `database.auth`.
Sprint 5: **thao tac xac thuc chuyen sang thread nen** (`AuthWorker`).

Truoc Sprint 5, bam "Đăng nhập" lam ca cua so dung im trong khoang thoi gian
`SELECT` (~400 ms) cong `bcrypt.checkpw()` (co y thiet ke cham). Gio GUI chi doi
`loading = True` roi cho signal.

Hop dong voi QML KHONG doi: van la `loading`, `statusMessage`, `isLoggedIn`,
`currentUser` va cac signal thanh cong.
"""

from __future__ import annotations

from PySide6.QtCore import Property, Signal, Slot

from ui.services.auth_service import AuthResult, AuthService
from ui.state import UiState
from ui.ui_logger import log_ui_event
from ui.viewmodels.base_viewmodel import BaseViewModel
from ui.workers.auth_worker import AuthOperation, AuthWorker


class AuthViewModel(BaseViewModel):
    """Giu phien dang nhap. Luat kiem tra nam trong `AuthService`."""

    UserChanged = Signal(dict)
    LoggedInChanged = Signal(bool)
    LoadingChanged = Signal(bool)
    LoginSucceeded = Signal()
    RegisterSucceeded = Signal()
    PasswordChanged = Signal()

    def __init__(
        self,
        auth_service: AuthService,
        parent=None,
    ) -> None:
        super().__init__("auth_viewmodel", parent)

        self._auth_service = auth_service
        self._current_user: dict = {}
        self._is_logged_in = False
        self._loading = False
        self._worker: AuthWorker | None = None

    # ------------------------------------------------------------------
    # Trang thai
    # ------------------------------------------------------------------

    @Property(bool, notify=LoggedInChanged)
    def isLoggedIn(self) -> bool:
        return self._is_logged_in

    @Property("QVariantMap", notify=UserChanged)
    def currentUser(self) -> dict:
        return self._current_user

    @Property(bool, notify=LoadingChanged)
    def loading(self) -> bool:
        return self._loading

    def _set_loading(
        self,
        value: bool,
    ) -> None:
        if self._loading == value:
            return

        self._loading = value
        self.set_state(
            UiState.LOADING
            if value
            else UiState.IDLE
        )
        self.LoadingChanged.emit(value)

    def _set_status_once(
        self,
        message: str,
    ) -> None:
        """Chi emit khi noi dung thay doi - giu dung hanh vi Sprint 2."""
        if self.statusMessage == message:
            return

        self.set_status(message)

    def _set_user(
        self,
        user: dict,
    ) -> None:
        was_logged_in = self._is_logged_in

        self._current_user = dict(user) if user else {}
        self._is_logged_in = bool(self._current_user)

        self.UserChanged.emit(self._current_user)

        if was_logged_in != self._is_logged_in:
            self.LoggedInChanged.emit(self._is_logged_in)

    # ------------------------------------------------------------------
    # Dieu phoi worker
    # ------------------------------------------------------------------

    def _start_operation(
        self,
        operation: AuthOperation,
        arguments: tuple,
    ) -> None:
        """Chay mot thao tac xac thuc tren thread nen.

        Chan bam hai lan: dang co worker chay thi bo qua yeu cau moi.
        """
        if self._worker is not None:
            self.logger.info(
                "auth_operation_skipped_busy operation=%s",
                operation.value,
            )
            return

        self._set_loading(True)

        self._worker = AuthWorker(
            self._auth_service,
            operation,
            arguments,
        )
        self._worker.completed.connect(
            lambda result, op=operation: self._on_completed(
                op,
                result,
            )
        )
        self._worker.failed.connect(
            self._on_worker_failed
        )
        self._worker.finished.connect(
            self._on_worker_finished
        )
        self._worker.start()

    def _on_completed(
        self,
        operation: AuthOperation,
        result: AuthResult,
    ) -> None:
        """Chay tren GUI thread nho queued connection."""
        self._set_status_once(result.message)

        if not result.success:
            return

        if operation is AuthOperation.LOGIN:
            self._set_user(result.user or {})
            self.LoginSucceeded.emit()

        elif operation is AuthOperation.REGISTER:
            self.RegisterSucceeded.emit()

        elif operation is AuthOperation.CHANGE_PASSWORD:
            self.PasswordChanged.emit()

    def _on_worker_failed(
        self,
        message: str,
    ) -> None:
        self.logger.error(
            "auth_worker_failed error=%s",
            message,
        )
        self._set_status_once(
            "Không thể thực hiện thao tác. Vui lòng thử lại."
        )

    def _on_worker_finished(self) -> None:
        self._worker = None
        self._set_loading(False)

    # ------------------------------------------------------------------
    # Hanh dong tu QML
    # ------------------------------------------------------------------

    @Slot(str, str)
    def login(
        self,
        username: str,
        password: str,
    ) -> None:
        log_ui_event(self.logger, "login_submitted")

        self._start_operation(
            AuthOperation.LOGIN,
            (username, password),
        )

    @Slot(str, str, str, str)
    def register(
        self,
        fullname: str,
        username: str,
        password: str,
        confirm_password: str,
    ) -> None:
        log_ui_event(self.logger, "register_submitted")

        self._start_operation(
            AuthOperation.REGISTER,
            (
                fullname,
                username,
                password,
                confirm_password,
            ),
        )

    @Slot()
    def logout(self) -> None:
        """Dang xuat chay ngay tren GUI thread - khong cham database."""
        log_ui_event(self.logger, "logout")

        # Ket qua cua thao tac dang chay khong con y nghia sau khi dang xuat.
        if self._worker is not None:
            self._worker.cancel()

        self._set_user({})
        self._set_status_once("")

    @Slot(str, str, str)
    def changePassword(
        self,
        old_password: str,
        new_password: str,
        confirm_password: str,
    ) -> None:
        log_ui_event(self.logger, "change_password_submitted")

        user_id = (
            self._current_user.get("id")
            if self._is_logged_in
            else None
        )

        self._start_operation(
            AuthOperation.CHANGE_PASSWORD,
            (
                user_id,
                old_password,
                new_password,
                confirm_password,
            ),
        )

    # ------------------------------------------------------------------
    # Vong doi
    # ------------------------------------------------------------------

    def shutdown(
        self,
        timeout_ms: int = 3000,
    ) -> None:
        self._await_workers(
            (self._worker,),
            timeout_ms,
        )
