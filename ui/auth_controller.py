from __future__ import annotations

from PySide6.QtCore import (
    QObject,
    Property,
    Signal,
    Slot,
)

from database.auth import (
    change_password,
    register_user,
    username_exists,
    verify_login,
)


class AuthController(QObject):
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
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._is_logged_in = False
        self._current_user = {}
        self._loading = False
        self._status_message = ""

    @Property(bool, notify=isLoggedInChanged)
    def isLoggedIn(self) -> bool:
        return self._is_logged_in

    @Property("QVariantMap", notify=currentUserChanged)
    def currentUser(self) -> dict:
        return self._current_user

    @Property(bool, notify=loadingChanged)
    def loading(self) -> bool:
        return self._loading

    @Property(str, notify=statusMessageChanged)
    def statusMessage(self) -> str:
        return self._status_message

    def _set_loading(
        self,
        value: bool,
    ) -> None:
        if self._loading == value:
            return
        self._loading = value
        self.loadingChanged.emit(value)

    def _set_status(
        self,
        message: str,
    ) -> None:
        if self._status_message == message:
            return
        self._status_message = message
        self.statusMessageChanged.emit(message)

    def _set_user(
        self,
        user: dict,
    ) -> None:
        normalized_user = {
            "id": int(user.get("id", 0)),
            "username": str(user.get("username", "")),
            "fullname": str(user.get("fullname", "")),
        } if user else {}

        was_logged_in = self._is_logged_in
        self._current_user = normalized_user
        self._is_logged_in = bool(normalized_user)

        self.currentUserChanged.emit(
            self._current_user
        )
        self.userChanged.emit(
            self._current_user
        )

        if was_logged_in != self._is_logged_in:
            self.isLoggedInChanged.emit(
                self._is_logged_in
            )

    @Slot(str, str)
    def login(
        self,
        username: str,
        password: str,
    ) -> None:
        normalized_username = username.strip()
        print(
            f"AuthController.login called for username='{normalized_username}'"
        )

        if not normalized_username or not password:
            self._set_status(
                "Vui lòng nhập tên đăng nhập và mật khẩu."
            )
            return

        self._set_loading(True)

        try:
            user = verify_login(
                normalized_username,
                password,
            )
            print(
                "AuthController.login database result: "
                + ("found" if user else "not found")
            )

            if user is None:
                self._set_status(
                    "Sai tên đăng nhập hoặc mật khẩu."
                )
                return

            self._set_user(user)
            self._set_status(
                "Đăng nhập thành công."
            )
            self.loginSucceeded.emit()

        except Exception as error:
            self._set_status(
                f"Không thể đăng nhập: {error}"
            )

        finally:
            self._set_loading(False)

    @Slot(str, str, str, str)
    def register(
        self,
        fullname: str,
        username: str,
        password: str,
        confirm_password: str,
    ) -> None:
        normalized_fullname = fullname.strip()
        normalized_username = username.strip()

        if not normalized_fullname:
            self._set_status(
                "Họ và tên không được để trống."
            )
            return

        if not normalized_username:
            self._set_status(
                "Tên đăng nhập không được để trống."
            )
            return

        if len(password) < 6:
            self._set_status(
                "Mật khẩu phải có ít nhất 6 ký tự."
            )
            return

        if password != confirm_password:
            self._set_status(
                "Mật khẩu xác nhận không khớp."
            )
            return

        self._set_loading(True)

        try:
            if username_exists(normalized_username):
                self._set_status(
                    "Tên đăng nhập đã tồn tại."
                )
                return

            register_user(
                normalized_fullname,
                normalized_username,
                password,
            )

            self._set_status(
                "Tạo tài khoản thành công. Vui lòng đăng nhập."
            )
            self.registerSucceeded.emit()

        except Exception as error:
            self._set_status(
                f"Không thể tạo tài khoản: {error}"
            )

        finally:
            self._set_loading(False)

    @Slot()
    def logout(self) -> None:
        self._set_user({})
        self._set_status("")

    @Slot(str, str, str)
    def changePassword(
        self,
        old_password: str,
        new_password: str,
        confirm_password: str,
    ) -> None:
        if not self._is_logged_in:
            self._set_status(
                "Bạn cần đăng nhập để đổi mật khẩu."
            )
            return

        if not old_password:
            self._set_status(
                "Vui lòng nhập mật khẩu hiện tại."
            )
            return

        if len(new_password) < 6:
            self._set_status(
                "Mật khẩu mới phải có ít nhất 6 ký tự."
            )
            return

        if new_password != confirm_password:
            self._set_status(
                "Mật khẩu xác nhận không khớp."
            )
            return

        if old_password == new_password:
            self._set_status(
                "Mật khẩu mới không được trùng mật khẩu cũ."
            )
            return

        self._set_loading(True)

        try:
            changed = change_password(
                int(self._current_user["id"]),
                old_password,
                new_password,
            )

            if not changed:
                self._set_status(
                    "Mật khẩu hiện tại không đúng."
                )
                return

            self._set_status(
                "Đổi mật khẩu thành công."
            )
            self.passwordChanged.emit()

        except Exception as error:
            self._set_status(
                f"Không thể đổi mật khẩu: {error}"
            )

        finally:
            self._set_loading(False)
