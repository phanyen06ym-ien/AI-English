"""Chuan hoa dialog / thong bao cho GUI.

Truoc Sprint 3 moi Controller tu emit mot chuoi `statusChanged` roi QML tu doan
mau chu bang cach do chuoi (`indexOf("thành công")`). Sprint 3 gom lai thanh
mot dich vu duy nhat, phan loai ro 4 muc:

    Loading  - dang xu ly, co the kem % tien do
    Success  - thao tac thanh cong
    Warning  - canh bao, nguoi dung can lam them buoc
    Error    - that bai

Vi Sprint 3 khong duoc sua QML, `DialogService` duoc dang ky them nhu mot
context property moi (`dialogService`). QML hien tai van chay binh thuong voi
`statusChanged`; QML tuong lai co the bind truc tiep vao day ma khong can sua
Python.
"""

from __future__ import annotations

from enum import Enum

from PySide6.QtCore import (
    Property,
    QObject,
    Signal,
    Slot,
)

from ui.ui_logger import get_ui_logger, log_ui_event


logger = get_ui_logger("dialog")


class DialogLevel(str, Enum):
    """Muc do cua mot thong bao GUI."""

    LOADING = "loading"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


DEFAULT_TITLES: dict[DialogLevel, str] = {
    DialogLevel.LOADING: "Đang xử lý",
    DialogLevel.SUCCESS: "Thành công",
    DialogLevel.WARNING: "Cảnh báo",
    DialogLevel.ERROR: "Lỗi",
}

#: Tu khoa dung de suy ra muc do tu cac message tieng Viet dang co.
SUCCESS_KEYWORDS = (
    "thành công",
    "đã tải",
    "phát hiện",
    "đang hoạt động",
)

WARNING_KEYWORDS = (
    "vui lòng",
    "chưa phát hiện",
    "không phát hiện",
    "đã tắt",
)

LOADING_KEYWORDS = (
    "đang tải",
    "đang nhận diện",
    "đang lưu",
    "đang đăng nhập",
)


def classify_message(
    message: str,
) -> DialogLevel:
    """Suy ra muc do dialog tu mot status message co san."""
    normalized = str(message).strip().lower()

    if not normalized:
        return DialogLevel.SUCCESS

    for keyword in LOADING_KEYWORDS:
        if keyword in normalized:
            return DialogLevel.LOADING

    for keyword in SUCCESS_KEYWORDS:
        if keyword in normalized:
            return DialogLevel.SUCCESS

    for keyword in WARNING_KEYWORDS:
        if keyword in normalized:
            return DialogLevel.WARNING

    return DialogLevel.ERROR


class DialogService(QObject):
    """Bus thong bao dung chung cho moi Controller."""

    #: level, title, message
    notified = Signal(str, str, str)

    loadingShown = Signal(str)
    loadingProgressChanged = Signal(int)
    loadingHidden = Signal()

    successShown = Signal(str, str)
    warningShown = Signal(str, str)
    errorShown = Signal(str, str)

    visibleChanged = Signal(bool)

    def __init__(
        self,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._visible = False
        self._level = DialogLevel.SUCCESS.value
        self._message = ""

    @Property(bool, notify=visibleChanged)
    def loadingVisible(self) -> bool:
        return self._visible

    @Property(str, notify=notified)
    def level(self) -> str:
        return self._level

    @Property(str, notify=notified)
    def message(self) -> str:
        return self._message

    def _emit(
        self,
        level: DialogLevel,
        message: str,
        title: str | None = None,
    ) -> None:
        resolved_title = (
            title
            if title
            else DEFAULT_TITLES[level]
        )

        self._level = level.value
        self._message = message

        log_ui_event(
            logger,
            "dialog",
            level=level.value,
        )

        self.notified.emit(
            level.value,
            resolved_title,
            message,
        )

    @Slot(str)
    def showLoading(
        self,
        message: str = "",
    ) -> None:
        """Bat dialog loading."""
        if not self._visible:
            self._visible = True
            self.visibleChanged.emit(True)

        self._emit(
            DialogLevel.LOADING,
            message,
        )
        self.loadingShown.emit(message)

    @Slot(int)
    def updateProgress(
        self,
        percent: int,
    ) -> None:
        """Cap nhat % tien do cho dialog loading."""
        self.loadingProgressChanged.emit(
            max(0, min(100, int(percent)))
        )

    @Slot()
    def hideLoading(self) -> None:
        """Tat dialog loading."""
        if not self._visible:
            return

        self._visible = False
        self.visibleChanged.emit(False)
        self.loadingHidden.emit()

    @Slot(str)
    def showSuccess(
        self,
        message: str,
        title: str = "",
    ) -> None:
        self.hideLoading()
        self._emit(
            DialogLevel.SUCCESS,
            message,
            title,
        )
        self.successShown.emit(
            title or DEFAULT_TITLES[DialogLevel.SUCCESS],
            message,
        )

    @Slot(str)
    def showWarning(
        self,
        message: str,
        title: str = "",
    ) -> None:
        self.hideLoading()
        self._emit(
            DialogLevel.WARNING,
            message,
            title,
        )
        self.warningShown.emit(
            title or DEFAULT_TITLES[DialogLevel.WARNING],
            message,
        )

    @Slot(str)
    def showError(
        self,
        message: str,
        title: str = "",
    ) -> None:
        self.hideLoading()
        self._emit(
            DialogLevel.ERROR,
            message,
            title,
        )
        self.errorShown.emit(
            title or DEFAULT_TITLES[DialogLevel.ERROR],
            message,
        )

    @Slot(str)
    def publish(
        self,
        message: str,
    ) -> None:
        """Dinh tuyen mot status message co san sang dung loai dialog."""
        level = classify_message(message)

        if level is DialogLevel.LOADING:
            self.showLoading(message)
        elif level is DialogLevel.SUCCESS:
            self.showSuccess(message)
        elif level is DialogLevel.WARNING:
            self.showWarning(message)
        else:
            self.showError(message)
