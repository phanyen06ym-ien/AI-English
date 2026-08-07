"""Thin Controller cho dang nhap / dang ky / doi mat khau.

Luat kiem tra du lieu va goi database da chuyen sang `ui.services.auth_service`;
trang thai phien chuyen sang `ui.viewmodels.auth_viewmodel`.

Property / Signal / Slot public giu nguyen ten de QML khong phai sua.
"""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QObject,
    Signal,
    Slot,
)

from ui.ui_logger import get_ui_logger, log_button_click
from ui.viewmodels.auth_viewmodel import AuthViewModel


logger = get_ui_logger("auth_controller")


class AuthController(QObject):
    """Adapter giua QML va `AuthViewModel`."""

    isLoggedInChanged = Signal(bool)
    currentUserChanged = Signal(dict)
    loadingChanged = Signal(bool)
    statusMessageChanged = Signal(str)
    userChanged = Signal(dict)
    loginSucceeded = Signal()
    registerSucceeded = Signal()
    passwordChanged = Signal()

    def __init__(
        self,
        view_model: AuthViewModel,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._view_model = view_model

        self._view_model.LoggedInChanged.connect(
            self.isLoggedInChanged
        )
        self._view_model.UserChanged.connect(
            self._on_user_changed
        )
        self._view_model.LoadingChanged.connect(
            self.loadingChanged
        )
        self._view_model.StatusMessageChanged.connect(
            self.statusMessageChanged
        )
        self._view_model.LoginSucceeded.connect(
            self.loginSucceeded
        )
        self._view_model.RegisterSucceeded.connect(
            self.registerSucceeded
        )
        self._view_model.PasswordChanged.connect(
            self.passwordChanged
        )

    def _on_user_changed(
        self,
        user: dict,
    ) -> None:
        self.currentUserChanged.emit(user)
        self.userChanged.emit(user)

    @property
    def view_model(self) -> AuthViewModel:
        return self._view_model

    @Property(bool, notify=isLoggedInChanged)
    def isLoggedIn(self) -> bool:
        return self._view_model.isLoggedIn

    @Property("QVariantMap", notify=currentUserChanged)
    def currentUser(self) -> dict:
        return self._view_model.currentUser

    @Property(bool, notify=loadingChanged)
    def loading(self) -> bool:
        return self._view_model.loading

    @Property(str, notify=statusMessageChanged)
    def statusMessage(self) -> str:
        return self._view_model.statusMessage

    @Slot(str, str)
    def login(
        self,
        username: str,
        password: str,
    ) -> None:
        log_button_click(logger, "login")

        self._view_model.login(username, password)

    @Slot(str, str, str, str)
    def register(
        self,
        fullname: str,
        username: str,
        password: str,
        confirm_password: str,
    ) -> None:
        log_button_click(logger, "register")

        self._view_model.register(
            fullname,
            username,
            password,
            confirm_password,
        )

    @Slot()
    def logout(self) -> None:
        log_button_click(logger, "logout")

        self._view_model.logout()

    @Slot(str, str, str)
    def changePassword(
        self,
        old_password: str,
        new_password: str,
        confirm_password: str,
    ) -> None:
        log_button_click(logger, "change_password")

        self._view_model.changePassword(
            old_password,
            new_password,
            confirm_password,
        )
