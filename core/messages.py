"""Catalog thong diep hien thi cho nguoi dung.

Van de truoc Sprint 7
---------------------

Thong diep tieng Viet nam rai rac o **7 file**:

    ui/services/auth_service.py       15 thong diep
    ui/services/detection_service.py   1
    ui/viewmodels/image_viewmodel.py   6
    ui/viewmodels/history_viewmodel.py 2
    ui/workers/webcam_worker.py        4
    ui/services/dialog_service.py      4 tieu de
    database/exceptions.py             5

Hau qua: sua mot cach dien dat phai di tim khap noi; hai man hinh noi hai kieu
khac nhau cho cung mot tinh huong; khong ai ra soat duoc lieu co thong diep nao
lo chi tiet ky thuat hay khong.

Giai phap
---------

Gom het ve day. Cac module cu import lai tu day nen **noi dung khong doi mot ky
tu nao** - moi test hien co van xanh.

Nguyen tac viet thong diep cho nguoi dung:

1. Tieng Viet, co dau, du dau cau.
2. Noi nguoi dung can lam gi, khong noi he thong hong o dau.
3. TUYET DOI khong kem: ten bang, cau SQL, chuoi ket noi, ten lop Python,
   stack trace, ten dang nhap.
"""

from __future__ import annotations


# ----------------------------------------------------------------------
# Xac thuc
# ----------------------------------------------------------------------

MSG_MISSING_CREDENTIALS = "Vui lòng nhập tên đăng nhập và mật khẩu."
MSG_WRONG_CREDENTIALS = "Sai tên đăng nhập hoặc mật khẩu."
MSG_LOGIN_OK = "Đăng nhập thành công."
MSG_EMPTY_FULLNAME = "Họ và tên không được để trống."
MSG_EMPTY_USERNAME = "Tên đăng nhập không được để trống."
MSG_CONFIRM_MISMATCH = "Mật khẩu xác nhận không khớp."
MSG_USERNAME_TAKEN = "Tên đăng nhập đã tồn tại."
MSG_REGISTER_OK = "Tạo tài khoản thành công. Vui lòng đăng nhập."
MSG_NEED_LOGIN = "Bạn cần đăng nhập để đổi mật khẩu."
MSG_MISSING_OLD_PASSWORD = "Vui lòng nhập mật khẩu hiện tại."
MSG_SAME_PASSWORD = "Mật khẩu mới không được trùng mật khẩu cũ."
MSG_WRONG_OLD_PASSWORD = "Mật khẩu hiện tại không đúng."
MSG_PASSWORD_CHANGED = "Đổi mật khẩu thành công."

#: Tien to khi mot thao tac xac thuc that bai vi loi he thong.
PREFIX_LOGIN_FAILED = "Không thể đăng nhập"
PREFIX_REGISTER_FAILED = "Không thể tạo tài khoản"
PREFIX_CHANGE_PASSWORD_FAILED = "Không thể đổi mật khẩu"


def short_password_message(
    minimum: int,
) -> str:
    return f"Mật khẩu phải có ít nhất {minimum} ký tự."


def short_new_password_message(
    minimum: int,
) -> str:
    return f"Mật khẩu mới phải có ít nhất {minimum} ký tự."


# ----------------------------------------------------------------------
# Nhan dien anh
# ----------------------------------------------------------------------

MSG_IMAGE_UNREADABLE = "Không đọc được ảnh."
MSG_SELECT_IMAGE_FIRST = "Vui lòng chọn ảnh trước."
MSG_IMAGE_LOADING = "Đang tải ảnh..."
MSG_IMAGE_SELECTED = "Đã chọn ảnh. Bấm Nhận diện để chạy YOLO."
MSG_DETECTING = "Đang nhận diện..."
MSG_NO_OBJECT_FOUND = "Không phát hiện vật thể nào."
MSG_DETECTION_CANCELLED = "Đã hủy nhận diện."


def detected_count_message(
    count: int,
) -> str:
    return f"Phát hiện {count} vật thể."


# ----------------------------------------------------------------------
# Webcam
# ----------------------------------------------------------------------

MSG_CAMERA_OPEN_FAILED = "Không mở được webcam."
MSG_CAMERA_RUNNING = "Webcam đang hoạt động."
MSG_CAMERA_STOPPED = "Webcam đã tắt."
MSG_CAMERA_NO_OBJECT = "Chưa phát hiện vật thể."


# ----------------------------------------------------------------------
# Lich su
# ----------------------------------------------------------------------

MSG_LOGIN_TO_VIEW_HISTORY = "Vui lòng đăng nhập để xem lịch sử."
MSG_LOGIN_TO_CLEAR_HISTORY = "Vui lòng đăng nhập để xóa lịch sử."


def history_loaded_message(
    count: int,
) -> str:
    return f"Đã tải {count} bản ghi."


# ----------------------------------------------------------------------
# Du lieu
# ----------------------------------------------------------------------

MSG_DATA_UNAVAILABLE = "Không truy cập được dữ liệu."
MSG_DATABASE_UNREACHABLE = "Không kết nối được cơ sở dữ liệu."
MSG_DATA_OPERATION_FAILED = "Không thực hiện được thao tác dữ liệu."
MSG_DATA_NOT_FOUND = "Không tìm thấy dữ liệu."
MSG_DATA_INVALID = "Dữ liệu không hợp lệ hoặc đã tồn tại."


# ----------------------------------------------------------------------
# Chung
# ----------------------------------------------------------------------

MSG_UNEXPECTED = "Đã xảy ra lỗi. Vui lòng thử lại."
MSG_OPERATION_FAILED = "Thao tác không thực hiện được. Vui lòng thử lại."
MSG_CANCELLED = "Đã hủy thao tác."

#: Tieu de hop thoai theo muc do (Sprint 3).
TITLE_LOADING = "Đang xử lý"
TITLE_SUCCESS = "Thành công"
TITLE_WARNING = "Cảnh báo"
TITLE_ERROR = "Lỗi"


#: Tu khoa KHONG duoc xuat hien trong thong diep gui cho nguoi dung.
#: Dung cho test tu dong ra soat catalog nay.
FORBIDDEN_IN_USER_MESSAGES = (
    "psycopg2",
    "traceback",
    "select ",
    "insert into",
    "update ",
    "delete from",
    "postgresql://",
    "password=",
    "exception",
    "stack",
)


def contains_technical_detail(
    message: str,
) -> bool:
    """True neu thong diep lo chi tiet ky thuat - khong duoc dua cho nguoi dung."""
    normalized = str(message).lower()

    return any(
        keyword in normalized
        for keyword in FORBIDDEN_IN_USER_MESSAGES
    )


def all_user_messages() -> dict[str, str]:
    """Moi thong diep hang so trong catalog - dung de ra soat tu dong."""
    return {
        name: value
        for name, value in globals().items()
        if name.startswith(("MSG_", "TITLE_", "PREFIX_"))
        and isinstance(value, str)
    }
