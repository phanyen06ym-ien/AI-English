# ĐỀ BÀI CÁC SPRINT CÒN LẠI — AI-ENGLISH

Tài liệu này chứa prompt đầy đủ cho Sprint 4 → 8, viết theo đúng định dạng đã dùng
ở Sprint 1, 2, 3.

## Lưu ý về thứ tự

Kế hoạch gốc đặt *Database* ở Sprint 3 và *GUI* ở Sprint 4. Thực tế đã làm **GUI
trước**, nên thứ tự được điều chỉnh:

| Sprint | Kế hoạch gốc | Thực tế |
|---|---|---|
| 3 | Database & Repository | ✅ GUI Layer Refactor (MVVM) |
| 4 | GUI Controller | ⏭️ Database & Repository Refactor |
| 5 | Worker & Thread | Worker & Thread (còn ~40%) |
| 6 | Config & DI | Config & DI (còn ~50%) |
| 7 | Logging & Error Handling | Logging & Error Handling (còn ~60%) |
| 8 | Testing & Performance | Testing & Performance (còn ~50%) |

Sprint 3 đã hoàn thành trước một phần nội dung của Sprint 5, 6, 7 (worker tầng GUI,
`AppContext` dependency injection, `ui_logger`). Các prompt dưới đây **đã trừ đi**
phần đã làm để không lặp việc.

---

# ==========================================================
# SPRINT 4
# DATABASE & REPOSITORY REFACTOR
# ==========================================================

## Vai trò

Bạn là

- Senior Database Engineer

- Senior Python Engineer

- Tech Lead

- Software Architect

Sprint 1

AI Facade

✓

Sprint 2

AI Engine

✓

Sprint 3

GUI Layer MVVM

✓

Bây giờ

KHÔNG được sửa thuật toán AI.

KHÔNG được sửa YOLO.

KHÔNG được sửa KNN.

KHÔNG được sửa KMeans.

KHÔNG được sửa QML.

KHÔNG được đổi schema database.

KHÔNG được đổi câu SQL đang chạy đúng.

Mục tiêu:

Refactor Database Layer thành Repository Pattern.

==========================================================
MỤC TIÊU
==========================================================

Biến `database/` thành

Repository Layer.

Service không được biết SQL.

Service chỉ gọi Repository.

==========================================================
NHIỆM VỤ 1

ĐÁNH GIÁ DATABASE HIỆN TẠI
==========================================================

Đọc toàn bộ:

database/db.py

database/auth.py

database/history.py

Đánh giá:

Hàm nào mở connection mới cho mỗi query.

Hàm nào nuốt exception.

Hàm nào trộn business logic vào SQL.

Hàm nào không test được nếu thiếu database.

==========================================================
NHIỆM VỤ 2

CONNECTION MANAGEMENT
==========================================================

Hiện tại

get_connection() mở connection mới cho MỖI câu lệnh.

Thiết kế

Connection Pool.

Hoặc

Connection Manager tái sử dụng.

Đo lại thời gian mở connection trước và sau.

==========================================================
NHIỆM VỤ 3

REPOSITORY
==========================================================

Thiết kế Repository.

Ví dụ

UserRepository

HistoryRepository

Mỗi Repository

- có interface rõ ràng

- trả về Entity, không trả về tuple thô

- không chứa business rule

Service

↓

Repository

↓

Database

==========================================================
NHIỆM VỤ 4

ENTITY / MODEL
==========================================================

Thiết kế dataclass.

Ví dụ

User

HistoryEntry

Không để tầng trên nhận `row[0]`, `row[1]`.

==========================================================
NHIỆM VỤ 5

ERROR HANDLING
==========================================================

Hiện tại

get_history() lỗi database → trả về [].

save_history() lỗi database → trả về False.

GUI không phân biệt được

"không có dữ liệu"

và

"database hỏng".

Thiết kế Exception riêng.

Ví dụ

RepositoryError

ConnectionError

NotFoundError

==========================================================
NHIỆM VỤ 6

TRANSACTION
==========================================================

Chuẩn hóa transaction boundary.

Rõ ràng

- khi nào commit

- khi nào rollback

- khi nào retry

==========================================================
NHIỆM VỤ 7

MIGRATION LOGIC
==========================================================

Hiện tại

verify_login() tự động băm lại mật khẩu dạng thô.

Đây là business logic nằm trong tầng truy vấn.

Tách ra đúng tầng.

==========================================================
NHIỆM VỤ 8

SERVICE ADAPTER
==========================================================

Cập nhật

HistoryService

AuthService

để gọi Repository thay vì gọi `database.*`.

GUI KHÔNG được thay đổi.

==========================================================
NHIỆM VỤ 9

BACKWARD COMPATIBILITY
==========================================================

Giữ nguyên

database/auth.py

database/history.py

như shim re-export.

Script cũ vẫn phải chạy được.

==========================================================
NHIỆM VỤ 10

UNIT TEST
==========================================================

Thêm

test_repository.py

test_database_service.py

Test phải chạy được KHÔNG cần database thật.

Dùng Fake Repository / In-memory Repository.

==========================================================
NHIỆM VỤ 11

PERFORMANCE
==========================================================

Đo

- thời gian mở connection

- thời gian 1 lần save_history

- thời gian 1 lần get_history

Trước và sau.

==========================================================
NHIỆM VỤ 12

ARCHITECTURE
==========================================================

Sau Sprint

Kiến trúc phải là

QML

↓

Controller

↓

ViewModel

↓

Worker

↓

Service

↓

Repository

↓

Database

==========================================================
NHIỆM VỤ 13

OUTPUT
==========================================================

Sinh

SPRINT_4_REPORT.md

Bao gồm

1. Kiến trúc trước

2. Kiến trúc sau

3. Database Review

4. Repository

5. Entity

6. Error Handling

7. Transaction

8. Connection Pool

9. Regression Test

10. Performance

11. Risk

12. Changelog

==========================================================
YÊU CẦU
==========================================================

Được phép sửa source.

Không thay đổi AI.

Không thay đổi QML.

Không thay đổi schema.

Regression Test phải PASS.

==========================================================
KẾT THÚC
==========================================================

Kết thúc bằng

"Sprint 4 hoàn thành.

Database Layer đã được chuẩn hóa.

Service không còn biết SQL.

Sẵn sàng chuyển sang Sprint 5: Worker & Thread Refactor."

---

# ==========================================================
# SPRINT 5
# WORKER & THREAD REFACTOR
# ==========================================================

## Vai trò

Bạn là

- Senior Qt Developer

- Concurrency Engineer

- Tech Lead

Sprint 3 đã làm

- ImageWorker

- WebcamWorker

- HistoryWorker

- StatsWorker

- HistoryWriterWorker

Bây giờ

KHÔNG được sửa AI.

KHÔNG được sửa Database.

KHÔNG được sửa QML.

Mục tiêu:

Chuẩn hóa toàn bộ mô hình đa luồng.

==========================================================
NHIỆM VỤ 1

ĐÁNH GIÁ THREAD HIỆN TẠI
==========================================================

Liệt kê mọi thread trong hệ thống.

Đánh giá:

Thread nào còn chạy đồng bộ trên GUI thread.

Thread nào không có timeout.

Thread nào không hủy được.

Thread nào có thể rò rỉ.

==========================================================
NHIỆM VỤ 2

AUTH KHÔNG CÒN CHẶN GUI
==========================================================

Hiện tại

AuthService gọi database đồng bộ trên GUI thread.

Chuyển sang Worker.

Giữ nguyên

- thứ tự signal

- nội dung thông báo

- hành vi QML

==========================================================
NHIỆM VỤ 3

THREAD POOL
==========================================================

Đánh giá

QThread và QThreadPool đang dùng lẫn lộn.

Chuẩn hóa

- tác vụ ngắn → QThreadPool / QRunnable

- tác vụ dài, có vòng lặp → QThread

==========================================================
NHIỆM VỤ 4

CANCELLATION
==========================================================

Mọi worker phải

- hủy được

- có timeout

- không rò rỉ

Thiết kế `CancellationToken` dùng chung.

==========================================================
NHIỆM VỤ 5

WORKER LIFECYCLE
==========================================================

Chuẩn hóa

Created → Running → Finished → Disposed

Không worker nào được hủy khi đang chạy.

==========================================================
NHIỆM VỤ 6

BACKPRESSURE
==========================================================

Webcam emit frame nhanh hơn GUI vẽ.

Thiết kế cơ chế

- bỏ frame cũ

- hoặc giới hạn hàng đợi

Đo số frame bị bỏ.

==========================================================
NHIỆM VỤ 7

DEADLOCK / RACE
==========================================================

Rà soát

- shared state giữa các thread

- biến không có lock

- signal emit từ thread không phải QThread

==========================================================
NHIỆM VỤ 8

UNIT TEST
==========================================================

Thêm

test_thread_safety.py

test_cancellation.py

==========================================================
NHIỆM VỤ 9

OUTPUT
==========================================================

Sinh

SPRINT_5_REPORT.md

Bao gồm

1. Bản đồ thread trước

2. Bản đồ thread sau

3. Thread Review

4. Cancellation

5. Lifecycle

6. Backpressure

7. Race / Deadlock

8. Regression Test

9. Performance

10. Risk

11. Changelog

==========================================================
KẾT THÚC
==========================================================

"Sprint 5 hoàn thành.

Thread Model đã được chuẩn hóa.

Không còn tác vụ chặn GUI.

Sẵn sàng chuyển sang Sprint 6: Config & Dependency Injection."

---

# ==========================================================
# SPRINT 6
# CONFIG & DEPENDENCY INJECTION
# ==========================================================

## Vai trò

Bạn là

- Software Architect

- Senior Python Engineer

- DevOps Engineer

Sprint 3 đã làm

AppContext (composition root).

Bây giờ

KHÔNG được sửa AI.

KHÔNG được sửa QML.

Mục tiêu:

Gom toàn bộ cấu hình về một nơi.

==========================================================
NHIỆM VỤ 1

ĐÁNH GIÁ CONFIG
==========================================================

Liệt kê mọi nguồn cấu hình.

utils/config.py

biến môi trường (.env)

hằng số rải rác trong code

Đánh giá:

Hằng số nào đang hardcode trong module.

Cấu hình nào trùng lặp.

Cấu hình nào không đổi được khi chạy.

==========================================================
NHIỆM VỤ 2

CONFIG SCHEMA
==========================================================

Thiết kế cấu hình có định kiểu.

Ví dụ

AppConfig

DatabaseConfig

AIConfig

UIConfig

CameraConfig

Có giá trị mặc định.

Có validate.

==========================================================
NHIỆM VỤ 3

ENVIRONMENT
==========================================================

Chuẩn hóa

development

testing

production

Cập nhật `.env.example` đầy đủ.

==========================================================
NHIỆM VỤ 4

DEPENDENCY INJECTION
==========================================================

Mở rộng AppContext.

Mọi thành phần

- nhận phụ thuộc qua constructor

- không tự tạo phụ thuộc bên trong

Không dùng biến toàn cục.

==========================================================
NHIỆM VỤ 5

HẰNG SỐ MA
==========================================================

Gom mọi magic number.

Ví dụ

0.25 (nhịp suy luận webcam)

5.0 (cooldown lịch sử)

200 / 500 (giới hạn truy vấn)

3000 (timeout thread)

==========================================================
NHIỆM VỤ 6

DEPENDENCY VERSION
==========================================================

Ghim phiên bản trong requirements.txt.

Tách

requirements.txt

requirements-dev.txt

==========================================================
NHIỆM VỤ 7

UNIT TEST
==========================================================

Thêm

test_config.py

test_di.py

==========================================================
NHIỆM VỤ 8

OUTPUT
==========================================================

Sinh

SPRINT_6_REPORT.md

Bao gồm

1. Config trước

2. Config sau

3. Config Review

4. Schema

5. Environment

6. Dependency Injection

7. Magic Number

8. Regression Test

9. Risk

10. Changelog

==========================================================
KẾT THÚC
==========================================================

"Sprint 6 hoàn thành.

Config đã được chuẩn hóa.

Dependency Injection đã hoàn chỉnh.

Sẵn sàng chuyển sang Sprint 7: Logging & Error Handling."

---

# ==========================================================
# SPRINT 7
# LOGGING & ERROR HANDLING
# ==========================================================

## Vai trò

Bạn là

- Senior Python Engineer

- Site Reliability Engineer

- Tech Lead

Sprint 3 đã làm

ui/ui_logger.py cho tầng GUI.

Bây giờ

KHÔNG được sửa AI.

KHÔNG được sửa QML.

Mục tiêu:

Chuẩn hóa logging và xử lý lỗi toàn hệ thống.

==========================================================
NHIỆM VỤ 1

ĐÁNH GIÁ
==========================================================

Hiện còn 73 lệnh print() trong code.

Liệt kê từng nơi.

Đánh giá:

print() nào là log.

print() nào là output người dùng.

print() nào làm lộ dữ liệu nhạy cảm.

==========================================================
NHIỆM VỤ 2

LOGGING ARCHITECTURE
==========================================================

Thiết kế

Logger phân cấp

ai.*

ui.*

database.*

ml.*

Có

- level chuẩn

- format chuẩn

- file handler + console handler

- xoay vòng file log

==========================================================
NHIỆM VỤ 3

EXCEPTION HIERARCHY
==========================================================

Thiết kế cây exception.

Ví dụ

AppError

├── AIError

├── RepositoryError

├── UIError

└── ConfigError

Mỗi lỗi có

- mã lỗi

- thông điệp cho người dùng

- thông điệp cho lập trình viên

==========================================================
NHIỆM VỤ 4

ERROR BOUNDARY
==========================================================

Xác định rõ

- nơi nào bắt lỗi

- nơi nào ném tiếp

- nơi nào chuyển thành thông báo người dùng

Không được nuốt lỗi im lặng.

==========================================================
NHIỆM VỤ 5

USER-FACING MESSAGE
==========================================================

Tách

thông điệp kỹ thuật (log)

khỏi

thông điệp người dùng (tiếng Việt).

Gom về một nơi.

==========================================================
NHIỆM VỤ 6

SENSITIVE DATA
==========================================================

Rà soát log.

Không được ghi

- mật khẩu

- tên đăng nhập

- chuỗi kết nối database

==========================================================
NHIỆM VỤ 7

UNIT TEST
==========================================================

Thêm

test_logging.py

test_error_handling.py

==========================================================
NHIỆM VỤ 8

OUTPUT
==========================================================

Sinh

SPRINT_7_REPORT.md

Bao gồm

1. Logging trước

2. Logging sau

3. print() Review

4. Exception Hierarchy

5. Error Boundary

6. User Message

7. Sensitive Data

8. Regression Test

9. Risk

10. Changelog

==========================================================
KẾT THÚC
==========================================================

"Sprint 7 hoàn thành.

Logging và Error Handling đã được chuẩn hóa.

Không còn print() và không còn lỗi bị nuốt.

Sẵn sàng chuyển sang Sprint 8: Testing & Performance."

---

# ==========================================================
# SPRINT 8
# TESTING & PERFORMANCE
# ==========================================================

## Vai trò

Bạn là

- QA Automation Engineer

- Performance Engineer

- Tech Lead

Sprint 3 đã làm

104 unit test.

Bây giờ

KHÔNG được sửa AI.

KHÔNG được sửa QML.

Mục tiêu:

Hoàn thiện kiểm thử và tối ưu hiệu năng.

==========================================================
NHIỆM VỤ 1

TEST INVENTORY
==========================================================

Liệt kê toàn bộ test hiện có.

Đánh giá:

Test nào là unit test thật.

Test nào là script thủ công.

Module nào chưa có test.

==========================================================
NHIỆM VỤ 2

TEST PYRAMID
==========================================================

Chuẩn hóa

Unit Test

Integration Test

End-to-End Test

Tách rõ 3 mức.

==========================================================
NHIỆM VỤ 3

COVERAGE
==========================================================

Đo độ phủ.

Đặt ngưỡng tối thiểu.

Báo cáo module nào dưới ngưỡng.

==========================================================
NHIỆM VỤ 4

TEST RUNNER
==========================================================

Chuẩn hóa lệnh chạy test.

Một lệnh chạy tất cả.

Không được sửa artifact mô hình khi chạy test.

==========================================================
NHIỆM VỤ 5

PERFORMANCE BASELINE
==========================================================

Đo và ghi lại

- thời gian khởi động ứng dụng

- thời gian tải YOLO

- thời gian 1 lần nhận diện ảnh

- FPS webcam

- thời gian truy vấn database

- mức dùng RAM

==========================================================
NHIỆM VỤ 6

TỐI ƯU
==========================================================

Tối ưu điểm nghẽn.

KHÔNG được đổi kết quả AI.

Đo lại sau khi tối ưu.

==========================================================
NHIỆM VỤ 7

REGRESSION SUITE
==========================================================

Xây bộ test hồi quy chạy được mọi lúc.

Không cần YOLO.

Không cần database.

Không cần webcam.

==========================================================
NHIỆM VỤ 8

OUTPUT
==========================================================

Sinh

SPRINT_8_REPORT.md

Bao gồm

1. Test Inventory

2. Test Pyramid

3. Coverage

4. Performance Baseline

5. Tối ưu

6. So sánh trước / sau

7. Regression Suite

8. Risk

9. Changelog

10. Tổng kết 8 Sprint

==========================================================
KẾT THÚC
==========================================================

"Sprint 8 hoàn thành.

Kiểm thử và hiệu năng đã được chuẩn hóa.

Toàn bộ 8 Sprint đã hoàn thành.

Dự án AI-English đã sẵn sàng bàn giao."
