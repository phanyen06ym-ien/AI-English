# BÁO CÁO TỔNG QUAN DỰ ÁN AI-ENGLISH

**Bản báo cáo chia sẻ — Quét dự án & Tổng hợp thay đổi**

| Mục | Nội dung |
|---|---|
| Dự án | AI-English — Ứng dụng học từ vựng tiếng Anh qua nhận diện vật thể |
| Ngày báo cáo | 08/08/2026 |
| Phạm vi báo cáo | Quét toàn bộ dự án + tổng hợp thay đổi Sprint 1 → 6 |
| Trạng thái | Sprint 1 → 6 **HOÀN THÀNH** — 303/303 test PASS |

---

## 1. TÓM TẮT ĐIỀU HÀNH

AI-English là ứng dụng desktop cho phép người học chụp ảnh hoặc bật webcam, hệ
thống dùng **YOLO** nhận diện vật thể, tra **từ vựng Anh–Việt**, rồi gợi ý các từ
liên quan bằng **k-NN** và các từ cùng nhóm chủ đề bằng **K-Means**. Toàn bộ kết
quả được lưu vào lịch sử để thống kê tiến độ học.

Dự án đã trải qua **6 sprint tái cấu trúc** với một nguyên tắc xuyên suốt:

> **Không thay đổi thuật toán AI, không thay đổi Database, không thay đổi giao diện.
> Chỉ thay đổi cách các tầng nói chuyện với nhau.**

Kết quả sau 6 sprint:

| Tiêu chí | Trước Sprint 1 | Sau Sprint 6 |
|---|---|---|
| Số tầng kiến trúc rõ ràng | 2 (GUI + logic trộn lẫn) | 7 (View → Controller → ViewModel → Worker → Service → Repository → Data) |
| Business logic trong Controller | Rất nhiều | **0** |
| SQL trong tầng Service | Có | **0** |
| Chạy test không cần YOLO/DB/webcam | Không | **Có** |
| Số unit test tự động | 0 (chỉ script thủ công) | **303 test, PASS 100%** |
| Điểm gọi AI duy nhất | Không có | `AIEngine` |
| Dòng code Controller | 1.800 | 864 (**−52%**) |
| Thời gian 1 truy vấn database | 1.092 ms | **400 ms** (nhanh hơn 2,7×) |
| GUI bị treo khi đăng nhập | ~630 ms | **~1 ms** (ít hơn ~400×) |
| Tác vụ nền hủy được | 3/8 | **8/8** |
| Tham số đổi được không cần sửa code | 0 | **23 biến môi trường** |
| Thư viện ghim phiên bản | 1/18 | **18/18** |
| Lỗi thread/race đã phát hiện & sửa | — | **5** |

---

## 2. QUÉT DỰ ÁN (PROJECT SCAN)

### 2.1 Quy mô

| Chỉ số | Giá trị |
|---|---:|
| File Python | 84 |
| File QML (giao diện) | 15 |
| Tổng dòng code Python | ~12.963 |
| Dòng code test | 4.362 |
| Tỉ lệ code test / tổng | ~34% |

### 2.2 Công nghệ sử dụng

| Tầng | Công nghệ |
|---|---|
| Giao diện | PySide6 (Qt Quick / QML) |
| Thị giác máy tính | Ultralytics YOLO 8.4.72, OpenCV, PyTorch |
| Học máy | scikit-learn (k-NN, K-Means), joblib |
| Cơ sở dữ liệu | PostgreSQL trên Supabase (`psycopg2`) |
| Bảo mật | bcrypt (băm mật khẩu) |
| Phát âm | gTTS, pyttsx3 |
| Xử lý ảnh/chữ | Pillow (font Unicode tiếng Việt) |

### 2.3 Bản đồ package

| Package | Dòng | Vai trò | Trạng thái |
|---|---:|---|---|
| `ai/` | 677 | Facade + AIEngine điều phối AI | ✅ Sprint 1, 2 |
| `ml/` | 1.468 | k-NN, K-Means, feature, đánh giá | Nguyên bản (không đụng) |
| `detection/` | 263 | YOLO detector, nhận diện ảnh/webcam | Nguyên bản (không đụng) |
| `dataset/` | 420 | Từ vựng, ánh xạ lớp COCO | Nguyên bản (không đụng) |
| `database/` | 525 → 1.050 | Repository, Entity, Exception, Pool | ✅ Sprint 4 |
| `ui/` | 1.463 | Controller mỏng + composition root | ✅ Sprint 3 |
| `ui/services/` | 1.196 | Business logic tầng GUI | ✅ Sprint 3 (mới) |
| `ui/viewmodels/` | 1.319 | ViewModel + State machine | ✅ Sprint 3 (mới) |
| `ui/workers/` | 698 → 1.497 | Worker + hủy tác vụ + backpressure | ✅ Sprint 3, 5 |
| `ui/qml/` | 15 file | Giao diện | Không đụng (theo yêu cầu) |
| `utils/` | 559 → 646 | Font, speech, mật khẩu, đo hiệu năng | ✅ Sprint 4, 6 |
| `config/` | 0 → 900 | AppConfig có định kiểu, loader, validate | ✅ Sprint 6 (mới) |
| `test/` | 4.362 | Kiểm thử | ✅ Sprint 3 mở rộng mạnh |

### 2.4 Luồng nghiệp vụ chính

```text
Người dùng đăng nhập
        │
        ├── Chọn ảnh ────┐
        └── Bật webcam ──┤
                         ▼
                  YOLO nhận diện vật thể
                         │
                  Tra từ vựng Anh–Việt
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
      k-NN: từ liên quan    K-Means: từ cùng nhóm
              └──────────┬──────────┘
                         ▼
                 Lưu vào lịch sử
                         │
                    Thống kê học tập
```

---

## 3. NHỮNG GÌ ĐÃ THAY ĐỔI

### 3.1 Sprint 1 — AI Layer Facade

**Vấn đề:** Giao diện gọi thẳng vào `detection.detector`, `ml.knn`, `ml.kmeans`,
`dataset.vocabulary`. Muốn đổi mô hình AI phải sửa cả file giao diện.

**Giải pháp:** Tạo package `ai/` làm mặt tiền (facade) duy nhất.

| Trước | Sau |
|---|---|
| `from ml.knn import get_related_words` | `from ai.knn import get_related_words` |
| `from detection.detector import ObjectDetector` | `from ai.detector import ObjectDetector` |
| 4 điểm nhập AI rải rác trong GUI | 1 package `ai/` |

**Không đổi:** thuật toán, tham số, mô hình, kết quả trả về. Module gốc
`detection/`, `ml/`, `dataset/` giữ nguyên để tương thích ngược.

### 3.2 Sprint 2 — AI Engine Enhancement

**Vấn đề:** Mỗi màn hình tự ghép YOLO → từ vựng → k-NN → K-Means theo cách riêng.
Ba nơi lặp lại cùng một chuỗi xử lý, dễ lệch kết quả.

**Giải pháp:** Nâng `AIEngine` thành trung tâm điều phối.

```text
Ảnh / Frame
    │
    ▼
AIEngine.analyze_frame()
    ├── YOLO detect        → đo yolo_ms
    ├── Tra từ vựng        → đo vocabulary_ms
    ├── k-NN từ liên quan  → đo knn_ms
    └── K-Means cùng nhóm  → đo kmeans_ms
    │
    ▼
ImageAnalysisResult (success, message, error_code, timing, detections, ...)
```

**Thêm mới:**
- 7 kiểu dữ liệu có định kiểu (`DetectedObject`, `DetectionResult`, `TimingInfo`…)
- Dependency Injection cho detector, classifier, k-NN, K-Means, từ vựng
- Đo thời gian từng bước
- Xử lý lỗi thống nhất qua `ImageAnalysisResult`

**Không đổi:** thuật toán, tham số, định dạng nhãn hiển thị.

### 3.3 Sprint 3 — GUI Layer Refactor (MVVM)

**Vấn đề nghiêm trọng nhất:** Controller làm mọi việc — quản lý luồng, gọi AI,
ghi database, vẽ ảnh, tính thống kê, kiểm tra mật khẩu.

**Giải pháp:** Tách thành 6 tầng rõ ràng.

```text
QML (giao diện — không đổi)
  │
  ▼
Controller  ← chỉ nhận sự kiện & đổi tên tín hiệu
  │
  ▼
ViewModel   ← giữ trạng thái (Idle/Loading/Detecting/Completed/Error)
  │
  ▼
Worker      ← chỉ điều phối luồng nền
  │
  ▼
Service     ← toàn bộ business logic
  │
  ▼
AIEngine / Database
```

**Kết quả cụ thể:**

| File Controller | Trước | Sau | Giảm |
|---|---:|---:|---:|
| `webcam_controller.py` | 432 | 136 | −69% |
| `history_controller.py` | 276 | 94 | −66% |
| `stats_controller.py` | 166 | 72 | −57% |
| `auth_controller.py` | 278 | 141 | −49% |
| `vocabulary_controller.py` | 161 | 87 | −46% |
| `main_qt.py` | 185 | 107 | −42% |
| `image_controller.py` | 302 | 227 | −25% |
| **Tổng** | **1.800** | **864** | **−52%** |

**21 file mới** được tạo: 7 service, 6 worker, 8 viewmodel, 1 composition root,
1 state machine, 1 module log giao diện, 4 file test.

### 3.4 Sprint 4 — Database & Repository Refactor

**Vấn đề:** Tầng `database/` mở **một kết nối mới cho mỗi câu lệnh**, nuốt lỗi
(trả về `[]` hoặc `False`), đẩy tuple thô (`row[0]`, `row[1]`…) lên tầng trên, và
trộn lẫn SQL với mã hóa mật khẩu lẫn luật nghiệp vụ trong cùng một file.

**Giải pháp:** Tách thành Repository Pattern.

```text
Service     ← luật nghiệp vụ, KHÔNG có SQL
  │
  ▼
Repository  ← SQL, trả về Entity
  │
  ▼
Connection Pool (1..8 kết nối, an toàn đa luồng)
  │
  ▼
PostgreSQL / Supabase
```

**Kết quả đo được trên database thật (Supabase PostgreSQL 17.6):**

| Chế độ | Trung vị | Tổng 8 câu lệnh |
|---|---:|---:|
| Trước Sprint 4 — mở kết nối mới mỗi lần | 1.092,7 ms | 8.755,4 ms |
| Sau Sprint 4 — connection pool | **400,5 ms** | **4.029,5 ms** |

→ **Nhanh hơn 2,7 lần**, tiết kiệm 4.726 ms trên 8 câu lệnh.

**Thêm mới:**
- `UserRepository`, `HistoryRepository` — trả về Entity `User`, `HistoryEntry`
- Cây exception có mã lỗi: `RepositoryError` → `ConnectionFailedError`,
  `QueryFailedError`, `NotFoundError`, `IntegrityError`
- `utils/password.py` — bcrypt tách khỏi tầng truy vấn
- Ranh giới transaction rõ ràng (COMMIT / ROLLBACK / đóng kết nối hỏng)
- 72 test mới, chạy không cần database thật

**Thay đổi hành vi có chủ ý:** trước đây database hỏng thì giao diện hiện
"Đã tải 0 bản ghi"; giờ hiện thông điệp lỗi thật sự.

**Không đổi:** schema, nội dung câu SQL, thuật toán băm mật khẩu, định dạng dữ
liệu gửi lên giao diện. `database/auth.py`, `database/history.py`, `database/db.py`
giữ nguyên API cũ làm lớp tương thích — script cũ vẫn chạy.

### 3.5 Sprint 5 — Worker & Thread Refactor

**Vấn đề:** Ba thao tác xác thực (đăng nhập, đăng ký, đổi mật khẩu) chạy **đồng bộ
trên luồng giao diện** — bấm "Đăng nhập" là cả cửa sổ đứng im. 5 trong 8 tác vụ
nền **không hủy được**. Mỗi worker tự nghĩ ra cách dừng riêng. Webcam gửi khung
hình không giới hạn nên hàng đợi giao diện phình dần.

**Giải pháp:**

```text
ManagedWorker  ← vòng đời + cơ chế hủy thống nhất cho MỌI luồng nền
   Created → Running → Finished / Cancelled / Failed → Disposed

CancellationToken  ← hủy được từ giao diện, không chặn
FrameGate          ← tối đa 2 khung hình "đang bay" giữa worker và giao diện
AuthWorker         ← xác thực rời khỏi luồng giao diện
```

**Kết quả đo được trên database thật:**

| Phép đo | Trước | Sau |
|---|---:|---:|
| Giao diện bị treo khi đăng nhập | 402,3 ms | **1,0 ms** |
| Giao diện bị treo (có tài khoản, kèm bcrypt) | ~630 ms | **~1 ms** |
| Tổng thời gian đăng nhập | ~409 ms | ~409 ms (không đổi) |

→ Giao diện bị treo **ít hơn ~400 lần**. Công việc vẫn tốn ngần ấy thời gian —
chỉ là không còn làm đứng màn hình.

**Backpressure (webcam, giao diện vẽ 25 ms/khung, chạy 2 giây):**

| Chỉ số | Giá trị |
|---|---:|
| Khung hình worker đọc được | 279 |
| Gửi tới giao diện | 75 |
| Bỏ bớt | 204 (73%) |

Không có `FrameGate`, 204 khung hình đó sẽ nằm xếp hàng trong giao diện — mất
thêm 5,1 giây để vẽ hết, trong khi camera vẫn tiếp tục đọc. Bỏ khung hình cũ là
đúng với video trực tiếp, và **không ảnh hưởng kết quả nhận diện** vì AI chạy
theo nhịp riêng 0,25 giây.

**Thêm mới:** 47 test (`test_cancellation.py`, `test_thread_safety.py`) — trong đó
có test khẳng định mọi tín hiệu từ luồng nền đều được nhận trên luồng giao diện,
và test chạy 8 luồng song song để chứng minh `FrameGate` không bao giờ vượt hạn mức.

**Không đổi:** QML, AI, database, nhịp suy luận webcam, ngưỡng lưu lịch sử.

### 3.6 Sprint 6 — Config & Dependency Injection

**Vấn đề:** Cấu hình nằm rải rác ở **ba nơi không liên quan gì đến nhau** — hằng
số trong `utils/config.py`, biến môi trường đọc thẳng bằng `os.getenv()`, và hằng
số nằm rải trong 12 file khác nhau. Không ai nhìn được toàn cảnh, không đổi được
tham số nếu không sửa mã nguồn, và không có kiểm tra gì: đặt `CONFIDENCE = 5.0`
thì YOLO đơn giản là không phát hiện được gì mà **không một dòng cảnh báo nào**.

**Giải pháp:** Gom về một cây `AppConfig` có định kiểu, bất biến, có validate.

```text
                     load_config()
                          │
                          ▼
                      AppConfig
                          │
    ┌──────┬──────┬───────┼───────┬────────┬────────┬─────────┐
    ▼      ▼      ▼       ▼       ▼        ▼        ▼         ▼
  paths   ai   camera  database history threads    ui      logging
```

**Kết quả cụ thể:**

| Trước | Sau |
|---|---|
| 18 nhóm hằng số nằm rải rác trong 12 file | 1 cây `AppConfig` |
| 0 tham số đổi được khi chạy | **23 biến môi trường** |
| Cấu hình sai chạy im lặng | Bị chặn ngay khi khởi động, kèm tên trường và lý do |
| 1/18 thư viện ghim phiên bản | **18/18** |
| Hai cấu hình không song song được | Chạy song song được trong cùng tiến trình |

Ví dụ kiểm tra hợp lệ:

```
$ AI_CONFIDENCE=5.0 python -c "from config import load_config; load_config()"

ConfigValidationError
Cấu hình `ai.confidence` không hợp lệ: 5.0 — phải nằm trong khoảng (0, 1]
```

Và đổi `.env` giờ đổi được cả tham số mà tầng AI đang dùng — điều trước Sprint 6
không làm được:

```
$ AI_CONFIDENCE=0.75 CAMERA_ID=2 python ...
utils.config.CONFIDENCE : 0.75   (mặc định 0.5)
utils.config.CAMERA_ID  : 2      (mặc định 0)
```

**Thêm mới:** 77 test (`test_config.py`, `test_di.py`), `requirements-dev.txt`,
`.env.example` viết lại đầy đủ 23 biến kèm ghi chú.

**Không đổi:** **mọi giá trị tham số** — chỉ đổi chỗ cất giữ. Có 7 bài test khẳng
định từng con số một bằng đúng giá trị trước Sprint 6. Không một test cũ nào phải sửa.

---

## 4. NĂM LỖI THẬT ĐƯỢC PHÁT HIỆN & SỬA

Đây là các lỗi có sẵn trong code trước đó, được phát hiện trong quá trình tái cấu
trúc:

### Lỗi 1 — Race condition làm treo luồng webcam

`WebcamThread.run()` bật cờ "đang chạy" **sau khi** mở camera. Nếu người dùng bấm
Tắt camera trong khoảng thời gian đó, cờ dừng bị ghi đè → luồng chạy mãi mãi →
Qt buộc dừng ứng dụng với lỗi `QThread: Destroyed while thread is still running`.

**Đã sửa:** dùng cờ một chiều `_stop_requested`, không bao giờ ghi đè trong `run()`.
Có test hồi quy `test_stop_before_run_reaches_loop_still_exits`.

### Lỗi 2 — Luồng nền bị hủy khi đang chạy

Khi đóng ứng dụng, không có ai chờ các luồng nền kết thúc.

**Đã sửa:** `AppContext.shutdown()` gọi `shutdown()` của từng ViewModel, mỗi
ViewModel chờ worker của mình kết thúc.

### Lỗi 3 — Giao diện đứng 3 giây khi tắt camera

`WebcamController.stop()` gọi `wait(3000)` ngay trên luồng giao diện.

**Đã sửa (Sprint 3):** tách `request_stop()` (không chặn) và `stop()` (chặn, chỉ dùng khi
thoát ứng dụng).

### Lỗi 4 — Luồng ghi lịch sử có thể treo vĩnh viễn

`HistoryWriterWorker` chờ vô hạn ở `queue.get()` và được dừng bằng một "stop token"
đẩy vào hàng đợi. Nếu hàng đợi đang đầy, stop token bị bỏ — luồng không bao giờ
nhận được lệnh dừng.

**Đã sửa (Sprint 5):** đổi sang `get(timeout=0,1s)` có kiểm tra cờ hủy, và ghi nốt
hàng đợi trước khi tắt để không mất dữ liệu.

### Lỗi 5 — Hàng đợi khung hình phình không giới hạn

Webcam gửi khung hình nhanh hơn tốc độ giao diện vẽ. Mỗi lần gửi là một sự kiện
xếp vào hàng đợi giao diện — độ trễ tăng dần không giới hạn.

**Đã sửa (Sprint 5):** `FrameGate` giới hạn tối đa 2 khung hình "đang bay", vượt
hạn mức thì bỏ khung hình mới thay vì xếp thêm.

*Ngoài ra:* `AuthController` in tên đăng nhập của người dùng ra màn hình console —
đã gỡ bỏ.

---

## 5. KẾT QUẢ KIỂM THỬ

### 5.1 Bộ test tự động

| Bộ test | Số test | Kết quả |
|---|---:|---|
| `test_ai_engine.py` — AIEngine (Sprint 2) | 7 | ✅ PASS |
| `test_controller.py` — Controller mỏng (Sprint 3) | 34 | ✅ PASS |
| `test_viewmodel.py` — ViewModel & State (Sprint 3) | 42 | ✅ PASS |
| `test_worker.py` — Worker & Thread (Sprint 3) | 24 | ✅ PASS |
| `test_repository.py` — Repository & Entity (Sprint 4) | 40 | ✅ PASS |
| `test_database_service.py` — Service trên Repository (Sprint 4) | 32 | ✅ PASS |
| `test_cancellation.py` — Hủy tác vụ & vòng đời (Sprint 5) | 31 | ✅ PASS |
| `test_thread_safety.py` — An toàn đa luồng (Sprint 5) | 16 | ✅ PASS |
| `test_config.py` — Cấu hình & validate (Sprint 6) | 55 | ✅ PASS |
| `test_di.py` — Dependency Injection (Sprint 6) | 22 | ✅ PASS |
| **Tổng** | **303** | **✅ PASS 100%** |

Bộ test chạy trong **7,06 giây**, **không cần** YOLO, PostgreSQL hay webcam thật.

Lệnh chạy:

```bash
python -m unittest test.test_ai_engine test.test_config test.test_di test.test_repository test.test_database_service test.test_worker test.test_viewmodel test.test_controller test.test_cancellation test.test_thread_safety
```

### 5.2 Test bảo vệ kiến trúc

Ngoài test chức năng, dự án có các test **tự động chặn việc phá vỡ kiến trúc**:

| Test | Bảo vệ điều gì |
|---|---|
| `ControllerIsolationTest` | Controller không được gọi lại database, AI, `cv2`, tự tạo luồng |
| `WorkerIsolationTest` | Worker không được chạm vào giao diện |
| `ViewModelIsolationTest` | ViewModel không được gọi thẳng AI hoặc database |
| `QmlContractTest` | Quét 15 file `.qml`, kiểm tra mọi thuộc tính & tín hiệu giao diện đang dùng vẫn còn tồn tại |
| `ServiceHasNoSqlTest` | Service không được chứa `SELECT`, `INSERT`, `UPDATE`, `DELETE` |
| `RepositoryIsolationTest` | Repository không được import giao diện/AI, không được dùng `print()` |
| `NoScatteredEnvReadTest` | Chỉ tầng `config/` được đọc biến môi trường |
| `DefaultValueTest` | Mọi giá trị mặc định bằng đúng giá trị trước Sprint 6 |
| `RequirementsTest` | Mọi thư viện đều ghim phiên bản |

Nghĩa là: nếu ai đó vô tình đưa business logic ngược vào Controller, **test sẽ đỏ ngay**.

### 5.3 Kiểm chứng ràng buộc

```bash
git status --short ai/ ml/ detection/ dataset/ models/ ui/qml/
# (không có kết quả — không file nào bị sửa)
```

Bốn sprint tái cấu trúc **không thay đổi một dòng nào** trong thuật toán AI,
schema cơ sở dữ liệu hay giao diện. Tầng `database/` được tái cấu trúc ở Sprint 4
nhưng **nội dung câu SQL giữ nguyên văn** và API cũ vẫn chạy.

### 5.4 Hồi quy dữ liệu hiển thị

| Kiểm tra | Kết quả |
|---|---|
| Nhãn trên ảnh tĩnh | `laptop - Máy tính xách tay [Technology] (0.93)` — không đổi |
| Nhãn trên webcam | `laptop - Máy tính xách tay [Technology - Medium] (0.93)` — không đổi |
| Định dạng ngày lịch sử | `%d/%m/%Y %H:%M` — không đổi |
| Công thức thống kê | Không đổi |
| Ngưỡng lưu lịch sử | `CONFIDENCE = 0.5`, cooldown `5.0s` — không đổi |
| Nhịp suy luận webcam | `0.25s` — không đổi |

---

## 6. NỢ KỸ THUẬT CÒN LẠI

Kết quả quét dự án cho thấy các điểm sau **chưa** được xử lý (là mục tiêu của các
sprint tiếp theo):

| # | Vấn đề | Mức độ | Sprint xử lý |
|---|---|---|---|
| 1 | ~~`database/db.py` mở kết nối mới cho mỗi câu lệnh~~ | — | ✅ Sprint 4 |
| 2 | ~~`database/history.py` nuốt lỗi, trả `[]` / `False`~~ | — | ✅ Sprint 4 |
| 3 | ~~Không có tầng Repository — SQL nằm rải rác~~ | — | ✅ Sprint 4 |
| 4 | ~~`verify_login()` trộn logic migration vào tầng truy vấn~~ | — | ✅ Sprint 4 |
| 5 | ~~Đăng nhập gọi database đồng bộ trên luồng giao diện~~ | — | ✅ Sprint 5 |
| 6 | ~~`QThread`/`QThreadPool` dùng lẫn lộn, không có cơ chế hủy thống nhất~~ | — | ✅ Sprint 5 |
| 7 | ~~Cấu hình rải rác giữa `utils/config.py`, biến môi trường và hằng số trong code~~ | — | ✅ Sprint 6 |
| 8 | ~~`requirements.txt` chỉ ghim phiên bản cho `ultralytics`~~ | — | ✅ Sprint 6 |
| 9 | ~~Magic number rải rác chưa vào config~~ | — | ✅ Sprint 6 |
| 10 | Còn **68 lệnh `print()`** trong `ml/`, `detection/`, `dataset/`, `utils/` thay vì logging | 🔴 Cao | Sprint 7 |
| 11 | Chưa có cây exception thống nhất — `ConfigError` và `RepositoryError` còn tách rời | 🟡 Trung bình | Sprint 7 |
| 12 | Chưa đo hiệu năng end-to-end có hệ thống (YOLO, FPS webcam, RAM) | 🟡 Trung bình | Sprint 8 |

---

## 7. LỘ TRÌNH CÒN LẠI

> ⚠️ **Lưu ý về thứ tự sprint:** Kế hoạch ban đầu đặt *Database* ở Sprint 3 và
> *GUI* ở Sprint 4. Trên thực tế đã thực hiện **GUI trước** (Sprint 3), nên
> Database lùi xuống Sprint 4. Ngoài ra, Sprint 3 đã hoàn thành **một phần đáng kể**
> nội dung của Sprint 5 (Worker & Thread), Sprint 6 (Dependency Injection) và
> Sprint 7 (Logging tầng GUI). Lộ trình dưới đây đã được điều chỉnh theo thực tế.

| Sprint | Nội dung | Trạng thái | Ghi chú |
|---|---|---|---|
| 1 | AI Layer Facade | ✅ Xong | |
| 2 | AI Engine Enhancement | ✅ Xong | |
| 3 | GUI Layer Refactor (MVVM) | ✅ Xong | Làm trước Database |
| 4 | Database & Repository Refactor | ✅ Xong | Nhanh hơn 2,7× |
| 5 | Worker & Thread Refactor | ✅ Xong | Giao diện hết treo |
| 6 | Config & Dependency Injection | ✅ Xong | 23 biến đổi được khi chạy |
| **7** | **Logging & Error Handling** | ⏭️ Tiếp theo | Còn ~55% — log tầng GUI đã xong |
| 8 | Testing & Performance | 🔶 Còn ~40% | 303 test đã có |

### Vì sao Sprint 7 sẽ thuận lợi

Năm sprint trước đã chuẩn bị sẵn điểm bám:

1. `LoggingConfig` đã có `level` và `performance_enabled`, đọc được từ `LOG_LEVEL`.
   Sprint 7 chỉ cần thêm file handler và xoay vòng file log.
2. `Environment.default_log_level` đã phân biệt development / testing / production.
3. Cây exception đã có sẵn mẫu ở hai nơi — `ConfigError` (Sprint 6) và
   `RepositoryError` (Sprint 4) — đều có mã lỗi và thông điệp cho người dùng.
   Sprint 7 chỉ cần gom chúng dưới một gốc chung.
4. `DatabaseConfig.masked()` đã chặn rò rỉ mật khẩu — Sprint 7 mở rộng nguyên tắc
   này cho toàn bộ log.

---

## 8. KẾT LUẬN

Sau sáu sprint, dự án AI-English đã chuyển từ một ứng dụng **trộn lẫn giao diện,
nghiệp vụ và truy vấn SQL** sang một kiến trúc **phân tầng rõ ràng, có kiểm thử tự
động bảo vệ**.

Điều quan trọng nhất: **toàn bộ quá trình không làm thay đổi** thuật toán AI,
schema cơ sở dữ liệu hay giao diện — người dùng cuối không thấy khác biệt nào về
chức năng, nhưng đội phát triển giờ có thể:

- Thay mô hình AI mà không đụng vào giao diện
- Thay cơ sở dữ liệu mà không đụng vào giao diện
- Đổi tham số qua `.env` mà không cần chạm vào mã nguồn
- Chạy 303 bài kiểm thử trong 7,06 giây mà không cần cài YOLO hay kết nối database
- Được cảnh báo tự động nếu ai đó phá vỡ kiến trúc

Và người dùng cuối *có* thấy hai khác biệt rõ rệt:

- **Truy vấn dữ liệu nhanh hơn 2,7 lần** (Sprint 4)
- **Giao diện không còn đứng hình khi đăng nhập** — từ ~630 ms xuống ~1 ms (Sprint 5)

---

## PHỤ LỤC — Tài liệu chi tiết

| Tài liệu | Nội dung |
|---|---|
| `SPRINT_1_REPORT.md` | Chi tiết Sprint 1 — AI Layer Facade |
| `SPRINT_2_REPORT.md` | Chi tiết Sprint 2 — AI Engine Enhancement |
| `SPRINT_3_REPORT.md` | Chi tiết Sprint 3 — GUI Layer Refactor (16 mục) |
| `SPRINT_4_REPORT.md` | Chi tiết Sprint 4 — Database & Repository Refactor (13 mục) |
| `SPRINT_5_REPORT.md` | Chi tiết Sprint 5 — Worker & Thread Refactor (14 mục) |
| `SPRINT_6_REPORT.md` | Chi tiết Sprint 6 — Config & Dependency Injection (12 mục) |
| `SPRINT_PROMPTS.md` | Đề bài chi tiết cho Sprint 4 → 8 |
| `PROJECT_ARCHITECTURE_DISCOVERY.md` | Khảo sát kiến trúc ban đầu |
| `AI_ALGORITHM_ANALYSIS.md` | Phân tích thuật toán AI |
| `CODE_REVIEW_REPORT.md` | Rà soát chất lượng mã nguồn |
