# SPRINT 5 REPORT - WORKER & THREAD REFACTOR

Pham vi: chuan hoa toan bo mo hinh da luong. Khong con tac vu nao chan GUI thread.

Rang buoc da tuan thu:

| Rang buoc | Ket qua |
|---|---|
| Khong sua thuat toan AI | Khong file nao trong `ai/`, `ml/`, `detection/`, `dataset/` bi sua |
| Khong sua Database | Khong file nao trong `database/` bi sua o Sprint nay |
| Khong sua QML | Khong file nao trong `ui/qml/` bi sua |
| Regression Test PASS | **226/226 test PASS** |

---

## 1. BAN DO THREAD TRUOC

```text
GUI Thread (QApplication)
 |
 ├── AuthService.login()          ← CHAN GUI ~630 ms (SELECT + bcrypt)
 ├── AuthService.register()       ← CHAN GUI
 ├── AuthService.change_password()← CHAN GUI
 |
 ├── QThreadPool.globalInstance() ← goi THANG tu Controller
 |     └── SpeakTask (QRunnable)  ← khong huy duoc
 |
 ├── ImageWorker (QThread)        ← khong huy duoc
 ├── PreviewLoadWorker (QThread)  ← khong huy duoc
 ├── HistoryWorker (QThread)      ← khong huy duoc
 ├── StatsWorker (QThread)        ← khong huy duoc
 |
 └── WebcamWorker (QThread)       ← co co `_stop_requested` RIENG
       └── HistoryWriterWorker    ← `queue.get()` CHAN VO HAN
                                     dung bang "stop token" day vao hang doi
```

Van de do duoc:

| # | Van de | Hau qua |
|---|---|---|
| 1 | 3 thao tac xac thuc chay dong bo tren GUI thread | Bam "Đăng nhập" -> ca cua so dung im **~630 ms** |
| 2 | 4/6 worker khong huy duoc | Chon nham anh la phai cho YOLO chay xong |
| 3 | Moi worker tu nghi ra cach dung rieng | Khong the viet code chung, moi cho mot kieu bug |
| 4 | Khong co khai niem "trang thai worker" | Khong biet worker dang chay hay da xong |
| 5 | `HistoryWriterWorker` chan vo han o `queue.get()` | Hang doi day -> stop token bi bo -> **worker treo vinh vien** |
| 6 | `WebcamWorker` emit frame khong gioi han | Hang doi GUI phinh khong gioi han, do tre tang dan |
| 7 | Controller goi thang `QThreadPool` | Controller lai biet ve thread, pha vo Sprint 3 |
| 8 | Khong ai cho `QThreadPool` khi thoat app | Tac vu ngan bi cat ngang |

---

## 2. BAN DO THREAD SAU

```text
GUI Thread (QApplication)
 |
 ├── ManagedWorker (QThread) ─ vong doi + CancellationToken thong nhat
 |     ├── AuthWorker            ← MOI: xac thuc khong con chan GUI
 |     ├── ImageWorker           ← huy duoc tai moi moc tien do
 |     ├── PreviewLoadWorker     ← huy duoc
 |     ├── HistoryWorker         ← huy duoc
 |     ├── StatsWorker           ← huy duoc
 |     ├── WebcamWorker          ← huy duoc, co FrameGate
 |     └── HistoryWriterWorker   ← huy duoc, ghi not hang doi truoc khi tat
 |
 └── QThreadPool (qua `task_pool.submit()`)
       └── PooledTask
             └── SpeakTask       ← huy duoc

Backpressure:
    WebcamWorker ──FrameGate(max 2)──> GUI Thread
                   bo frame khi GUI khong theo kip

Shutdown (dung thu tu):
    1. dispose() moi QThread   (cancel + wait)
    2. wait_for_pool()          (cho tac vu ngan)
    3. close_pool()             (dong ket noi database)
```

---

## 3. THREAD REVIEW (NHIEM VU 1)

### 3.1 Kiem ke day du

| Thread | Truoc Sprint 5 | Sau Sprint 5 |
|---|---|---|
| `AuthService.login/register/change_password` | Chay **tren GUI thread** | `AuthWorker` (QThread) |
| `ImageWorker` | QThread, khong huy duoc, khong co timeout | `ManagedWorker`, huy tai moc tien do |
| `PreviewLoadWorker` | QThread, khong huy duoc | `ManagedWorker`, huy truoc/sau khi doc anh |
| `HistoryWorker` | QThread, khong huy duoc | `ManagedWorker`, huy truoc/sau moi buoc |
| `StatsWorker` | QThread, khong huy duoc | `ManagedWorker`, huy truoc/sau moi buoc |
| `WebcamWorker` | QThread, co dung rieng `_stop_requested` | `ManagedWorker`, dung `CancellationToken` |
| `HistoryWriterWorker` | QThread, `queue.get()` chan vo han | `ManagedWorker`, `get(timeout)` + ghi not hang doi |
| `SpeakTask` | `QRunnable` tho, khong huy duoc | `PooledTask`, huy duoc |

### 3.2 Thread co the ro ri

| Rui ro | Truoc | Sau |
|---|---|---|
| `HistoryWriterWorker` treo khi hang doi day | **Co** | Khong: `get(timeout=0.1)` + kiem tra co huy |
| QThread bi huy khi con chay | Co (da sua o Sprint 3 cho webcam, con lai chua) | Khong: `dispose()` bat buoc cancel + wait cho MOI worker |
| `QThreadPool` con tac vu khi thoat app | **Co** | Khong: `wait_for_pool()` trong `AppContext.shutdown()` |
| Connection pool dong truoc khi worker dung | **Co** | Khong: shutdown theo dung thu tu 1-2-3 |

---

## 4. CANCELLATION (NHIEM VU 4)

`ui/workers/cancellation.py`:

```python
token = CancellationToken()

# GUI thread
token.cancel()                   # khong chan

# Worker thread
token.raise_if_cancelled()       # nem OperationCancelledError
if token.is_cancelled: ...       # kiem tra thu cong
token.wait(0.25)                 # ngu, tinh day NGAY khi bi huy
```

Diem quan trong: `token.wait()` dung `threading.Event` thay cho `time.sleep()`.
Worker dang ngu **phan hoi lenh huy ngay lap tuc** thay vi phai cho het gio.
Co test do thoi gian: `test_wait_wakes_up_immediately_on_cancel`.

### Diem kiem tra huy trong tung worker

| Worker | Kiem tra huy o dau |
|---|---|
| `ImageWorker` | Truoc khi chay + tai moc tien do 5 / 25 / 70 / 85 / 100 |
| `PreviewLoadWorker` | Truoc va sau khi doc anh |
| `HistoryWorker` | Truoc khi xoa, truoc khi doc, truoc khi emit |
| `StatsWorker` | Truoc khi tinh, truoc khi emit |
| `WebcamWorker` | Dieu kien vong lap + sau moi lan chay AI |
| `HistoryWriterWorker` | Dieu kien vong lap (co timeout 0,1 s) |
| `AuthWorker` | Truoc khi goi service + truoc khi ap ket qua |
| `SpeakTask` | Truoc khi phat am |

### `OperationCancelledError` KHONG phai loi

`ManagedWorker.run()` bat rieng loai nay: worker chuyen sang trang thai
`cancelled` va emit signal `cancelled`, **khong** emit `failed`. Nguoi dung bam
Huy thi khong duoc thay hop thoai bao loi.

### Ngoai le co chu y: `ALWAYS_EXECUTE`

`HistoryWriterWorker` dat `ALWAYS_EXECUTE = True`. Ly do: huy **khong duoc lam
mat** nhung ban ghi nguoi dung da tao ra. Worker nay luon chay `execute()`, va
`execute()` ghi not hang doi truoc khi thoat. So luot duoc chan tren bang kich
thuoc hang doi nen buoc nay luon ket thuc.

Co test: `test_history_writer_drains_queue_on_cancel`.

---

## 5. LIFECYCLE (NHIEM VU 5)

```text
Created ──start()──> Running ──┬──> Finished ──dispose()──> Disposed
                               ├──> Cancelled ─────────────> Disposed
                               └──> Failed ────────────────> Disposed
```

| Trang thai | Y nghia |
|---|---|
| `created` | Da tao, chua chay |
| `running` | Dang chay `execute()` |
| `finished` | Chay xong binh thuong |
| `cancelled` | Dung theo yeu cau (khong phai loi) |
| `failed` | Dung vi loi khong luong truoc |
| `disposed` | Da dung han va duoc thu don |

`ManagedWorker.run()` la **ban cuoi** - lop con khong duoc override. Nho vay moi
worker deu ket thuc o dung mot trong ba trang thai cuoi, khong the "quen" phat
signal hay "quen" doi trang thai.

`dispose(timeout_ms)` bat buoc `cancel()` roi `wait()`. Day la thu duy nhat ngan
loi `QThread: Destroyed while thread is still running` (loi da gap o Sprint 3).
Tra ve `False` neu het gio cho - luc do co dong log `worker_dispose_timeout`.

Trang thai duoc bao ve bang `threading.Lock`: worker thread ghi, GUI thread doc.
Co test truy cap dong thoi: `test_worker_state_read_is_thread_safe`.

---

## 6. THREAD POOL (NHIEM VU 3)

Quy tac ro rang trong `ui/workers/task_pool.py`:

| Loai tac vu | Co che | Vi du |
|---|---|---|
| Vong lap dai, can huy giua chung, emit nhieu signal | `ManagedWorker` (QThread) | Webcam, nhan dien anh, doc lich su, xac thuc |
| Ngan, ban roi quen, khong bao cao tien do | `PooledTask` (QRunnable) | Phat am mot tu |

Ly do: mot `QThread` rieng cho moi lan bam nut phat am la lang phi; nguoc lai, dat
vong lap webcam vao thread pool se chiem cho cua moi tac vu ngan khac.

`submit()` la diem vao duy nhat. Controller khong con goi thang
`QThreadPool.globalInstance()` - kiem chung bang:

```bash
grep -n "QThreadPool" ui/*.py
# (khong con ket qua)
```

---

## 7. BACKPRESSURE (NHIEM VU 6)

### Van de

`WebcamWorker` emit `frameReady` qua `QueuedConnection`. Moi lan emit la mot su
kien xep vao hang doi GUI. Neu GUI ve cham hon toc do doc frame:

- Hang doi phinh khong gioi han -> ton RAM.
- GUI hien frame **cu**, do tre tang dan theo thoi gian.

### Giai phap: `FrameGate`

```text
Worker Thread                      GUI Thread
-------------                      ----------
if gate.try_acquire():
    emit frameReady(image) ──────> ViewModel._on_frame_ready()
                                     -> FrameUpdated -> View
                                     -> gate.release()
else:
    dem "dropped", bo frame
```

Toi da **2 frame dang bay**. Vuot han muc thi bo frame moi nhat.

Bo frame la dung trong video truc tiep: nguoi dung can hinh **moi nhat**, khong
can xem lai hinh cu. **Ket qua nhan dien khong bi anh huong** vi AI chay theo nhip
rieng (`INFERENCE_INTERVAL_SECONDS = 0.25`), khong chay tren tung frame.

### So lieu do duoc

`python test/benchmark_thread.py` - camera gia, GUI ve 25 ms/frame, chay 2 giay:

| Chi so | Gia tri |
|---|---:|
| Frame worker doc duoc | 279 |
| Frame gui toi GUI | 75 |
| Frame bi bo | 204 |
| Ty le bo | **73%** |
| Frame GUI ve xong | 75 |

Khong co `FrameGate`, 204 frame do se **nam xep hang trong GUI**. GUI se mat them
204 x 25 ms = **5,1 giay** de ve het cho, trong khi camera van tiep tuc doc frame
moi - do tre tang dan khong gioi han.

Hang doi ghi lich su cung la mot dang backpressure: hang doi day thi bo ban ghi
(dem `history_save_dropped_queue_full`) thay vi chan vong lap doc frame.

---

## 8. AUTH KHONG CON CHAN GUI (NHIEM VU 2)

### Truoc

```text
QML: authController.login()
  -> AuthController.login()
       -> AuthViewModel.login()
            -> AuthService.login()     ← CHAY TREN GUI THREAD
                 -> UserRepository      (~400 ms qua Internet)
                 -> bcrypt.checkpw()    (~228 ms, co y thiet ke cham)
  <- GUI dung im ~630 ms
```

### Sau

```text
QML: authController.login()
  -> AuthController.login()
       -> AuthViewModel.login()
            -> loading = True          ← GUI cap nhat NGAY
            -> AuthWorker.start()  ─────────────┐
  <- tra ve sau ~1 ms                            │
                                                 v  Worker Thread
                                          AuthService.login()
                                            -> UserRepository
                                            -> bcrypt.checkpw()
                                                 │
     Signal completed(AuthResult) <──────────────┘  (queued -> GUI thread)
       -> _set_user() / LoginSucceeded
       -> loading = False
```

### So lieu do duoc tren database that

`python test/benchmark_thread.py`, 5 vong:

| Phep do | Trung binh | **Trung vi** | Max |
|---|---:|---:|---:|
| GUI bi chan - dong bo (truoc Sprint 5) | 585,6 ms | **402,3 ms** | 1.315,9 ms |
| GUI bi chan - qua Worker (sau Sprint 5) | 1,2 ms | **1,0 ms** | 2,8 ms |
| Tong thoi gian hoan tat (sau Sprint 5) | 409,8 ms | 409,1 ms | 414,5 ms |
| Chi phi `bcrypt.checkpw` | 226,8 ms | 228,0 ms | 231,9 ms |

**GUI bi chan it hon ~400 lan (402 ms -> 1,0 ms).**

Doc them tu so lieu:

1. **Tong thoi gian khong doi** (~409 ms) - dung nhu mong doi. Cong viec van ton
   ngan ay thoi gian, chi la khong con lam dung GUI.
2. Con so 402 ms do bang **ten dang nhap khong ton tai** nen chua chay bcrypt.
   Voi tai khoan that, GUI truoc day bi chan them 228 ms nua, **tong ~630 ms**.
3. Max 1.315,9 ms cho thay tinh huong xau: lan dau tao pool cong do tre mang.

### Hop dong voi QML khong doi

QML van dung `authController.loading`, `statusMessage`, `isLoggedIn`,
`currentUser`, `onIsLoggedInChanged`, `onLoginSucceeded`. Khong sua mot dong `.qml`.

Them mot bao ve moi: **bam hai lan chi chay mot lan**. `_start_operation()` bo qua
yeu cau moi khi con worker dang chay. Co test:
`test_second_submit_is_ignored_while_busy`.

---

## 9. RACE / DEADLOCK (NHIEM VU 7)

### 9.1 Ra soat shared state

| Trang thai chia se | Thread ghi | Thread doc | Bao ve |
|---|---|---|---|
| `ManagedWorker._state` | Worker | GUI | `threading.Lock` |
| `CancellationToken._event` | GUI | Worker | `threading.Event` (nguyen tu) |
| `FrameGate._in_flight` | Worker (acquire), GUI (release) | Ca hai | `threading.Lock` |
| `HistoryWriterWorker._queue` | Worker webcam | Worker ghi DB | `queue.Queue` (nguyen tu) |
| `HistoryRecordPolicy._last_saved_by_class` | Worker webcam | Worker webcam | Mot thread duy nhat |
| Connection pool | Moi worker | Moi worker | `ThreadedConnectionPool` + `Lock` (Sprint 4) |

### 9.2 Signal emit tu thread khong phai QThread

Sau Sprint 3 va 5, **khong con** truong hop nao. Moi thread trong du an deu la
`QThread` (qua `ManagedWorker`) hoac `QRunnable` chay tren `QThreadPool` - ca hai
deu co Qt affinity that su.

Kiem chung bang test: `test_every_webcam_signal_lands_on_gui_thread` chay worker
that, thu `threading.get_ident()` ben trong 4 slot khac nhau va khang dinh tat ca
bang thread ID cua GUI thread.

### 9.3 Deadlock da loai bo

| Nguy co | Truoc | Sau |
|---|---|---|
| `queue.get()` chan vo han khi stop token bi bo | **Co the treo** | `get(timeout=0.1)` |
| `wait()` tren GUI thread khi tat webcam | Da sua o Sprint 3 | `cancel()` khong chan |
| `dispose()` cho worker dang cho database | Co the vuot timeout | Tra ve `False` + ghi log, khong treo |

### 9.4 Race da sua o Sprint 3, gio da bien mat hoan toan

Race `_running = True` ghi de yeu cau dung (Sprint 3 phai vai co dung mot chieu)
gio khong con kha nang tai dien: co dung nam trong `CancellationToken`, worker
**khong bao gio** duoc phep ghi vao no.

---

## 10. REGRESSION TEST

### 10.1 Ket qua

| Bo test | Test | Ket qua |
|---|---:|---|
| `test_ai_engine.py` (Sprint 2) | 7 | PASS |
| `test_repository.py` (Sprint 4) | 40 | PASS |
| `test_database_service.py` (Sprint 4) | 32 | PASS |
| `test_worker.py` (Sprint 3) | 24 | PASS |
| `test_viewmodel.py` (Sprint 3, cap nhat) | 42 | PASS |
| `test_controller.py` (Sprint 3, cap nhat) | 34 | PASS |
| `test_cancellation.py` (Sprint 5, moi) | 31 | PASS |
| `test_thread_safety.py` (Sprint 5, moi) | 16 | PASS |
| **Tong** | **226** | **PASS, exit code 0** |

```bash
python -m unittest test.test_ai_engine test.test_repository test.test_database_service \
                  test.test_worker test.test_viewmodel test.test_controller \
                  test.test_cancellation test.test_thread_safety
```

Thoi gian chay: **5,63 giay**. Khong can PostgreSQL, YOLO hay webcam.

### 10.2 Test da cap nhat vi doi hanh vi

| Test | Ly do |
|---|---|
| `AuthViewModelTest` (4 test) | Xac thuc gio bat dong bo -> test phai cho signal thay vi doc ngay |
| `AuthControllerTest` (2 test) | Nhu tren |

Day la **thay doi hanh vi co chu y** cua NHIEM VU 2, khong phai loi hoi quy.
Da bo sung 3 test moi cho hanh vi moi: khong chan GUI, trang thai `loading`,
chan bam hai lan.

### 10.3 Test bao ve kien truc moi

| Test | Bao ve dieu gi |
|---|---|
| `test_login_does_not_block_gui_thread` | `login()` phai tra ve trong 50 ms |
| `test_cancel_does_not_block_caller` | `cancel()` phai tra ve trong 50 ms |
| `test_every_webcam_signal_lands_on_gui_thread` | 4 signal deu chay tren GUI thread |
| `test_worker_thread_id_differs_from_gui_thread` | `execute()` phai chay ngoai GUI thread |
| `test_concurrent_access_never_exceeds_limit` | 8 thread x 200 luot, `FrameGate` khong bao gio vuot han muc |
| `test_emitted_plus_dropped_equals_attempts` | Bo dem khong mat luot khi da luong |
| `test_worker_state_read_is_thread_safe` | 4 thread doc trang thai song song |
| `test_history_policy_under_concurrent_access` | 6 thread x 50 luot, cooldown khong hong |
| `test_app_context_shutdown_stops_every_worker` | Sau `shutdown()` khong con thread nen nao |
| `test_history_writer_drains_queue_on_cancel` | Huy khong lam mat du lieu |

### 10.4 File khong bi dong toi

```bash
git status --short ai/ ml/ detection/ dataset/ models/ ui/qml/
# (khong co ket qua)
```

---

## 11. PERFORMANCE

| Chi so | Truoc Sprint 5 | Sau Sprint 5 |
|---|---:|---:|
| GUI bi chan khi dang nhap (khong co tai khoan) | 402,3 ms | **1,0 ms** |
| GUI bi chan khi dang nhap (co tai khoan, kem bcrypt) | ~630 ms | **~1 ms** |
| Tong thoi gian dang nhap | ~409 ms | ~409 ms (khong doi) |
| Frame webcam xep hang trong GUI | Khong gioi han | Toi da **2** |
| Do tre webcam khi GUI cham | Tang dan khong gioi han | On dinh |
| Thread khong huy duoc | 5/8 | **0/8** |
| Thread khong co timeout dung | 8/8 | **0/8** |

Luu y: Sprint 5 **khong lam AI chay nhanh hon**. No lam GUI **phan hoi** nhanh
hon - cong viec nang van ton ngan ay thoi gian, chi la khong con lam dung man hinh.

---

## 12. RISK

| # | Risk | Muc do | Cach xu ly |
|---|---|---|---|
| 1 | Dang nhap bat dong bo -> code goi ngay sau `login()` thay `isLoggedIn` van False | Trung binh | QML chi phan ung theo signal, khong doc dong bo. `QmlContractTest` van xanh |
| 2 | Nguoi dung bam Dang nhap nhieu lan | Thap | `_start_operation()` bo qua khi dang ban; QML da khoa nut bang `loading` |
| 3 | Frame bi bo lam video giat | Thap | Chi bo khi GUI **da** khong theo kip; bo frame cu la dung cho video truc tiep |
| 4 | `max_in_flight = 2` qua chat tren may cham | Thap | La tham so constructor, chinh duoc; **se dua vao config o Sprint 6** |
| 5 | `dispose()` het gio khi worker cho database | Trung binh | Tra ve `False` + ghi log `worker_dispose_timeout`, khong treo GUI |
| 6 | `ALWAYS_EXECUTE` cua HistoryWriter chay du da huy | Thap | Co chu y, chan tren bang kich thuoc hang doi |
| 7 | Huy giua chung khi dang ghi lich su -> ghi mot phan | Thap | Moi ban ghi la mot transaction rieng (Sprint 4), khong co trang thai do dang |
| 8 | Thu tu shutdown sai lam worker truy cap pool da dong | Thap | `AppContext.shutdown()` co thu tu ro rang 1-2-3, co test |

---

## 13. CHANGELOG

### File tao moi (6)

| File | Noi dung |
|---|---|
| `ui/workers/cancellation.py` | `CancellationToken`, `OperationCancelledError`, `NEVER_CANCELLED` |
| `ui/workers/lifecycle.py` | `WorkerState`, `ManagedWorker` (vong doi + `dispose()`) |
| `ui/workers/backpressure.py` | `FrameGate` |
| `ui/workers/task_pool.py` | `PooledTask`, `submit()`, `wait_for_pool()` |
| `ui/workers/auth_worker.py` | `AuthWorker`, `AuthOperation` |
| `test/benchmark_thread.py` | Do thoi gian GUI bi chan + ty le bo frame |

### File test moi (2)

| File | Test |
|---|---:|
| `test/test_cancellation.py` | 31 |
| `test/test_thread_safety.py` | 16 |

### File sua (11)

| File | Thay doi |
|---|---|
| `ui/workers/image_worker.py` | `ManagedWorker`; huy tai moi moc tien do |
| `ui/workers/history_worker.py` | `ManagedWorker`; huy truoc/sau moi buoc |
| `ui/workers/stats_worker.py` | `ManagedWorker` |
| `ui/workers/webcam_worker.py` | `ManagedWorker`; `FrameGate`; `HistoryWriterWorker` khong con chan vo han + ghi not hang doi |
| `ui/workers/speech_worker.py` | `PooledTask`, huy duoc |
| `ui/workers/__init__.py` | Export lop moi + ghi quy tac Sprint 5 |
| `ui/viewmodels/base_viewmodel.py` | `_cancel_workers()`; `_await_workers()` dung `dispose()` |
| `ui/viewmodels/auth_viewmodel.py` | Bat dong bo qua `AuthWorker`; chan bam hai lan; `shutdown()` |
| `ui/viewmodels/image_viewmodel.py` | Slot `cancel()`; noi signal `cancelled` |
| `ui/viewmodels/webcam_viewmodel.py` | `_on_frame_ready()` tra suat cho `FrameGate`; `frame_stats` |
| `ui/image_controller.py`, `ui/vocabulary_controller.py` | Dung `submit()` thay cho `QThreadPool.globalInstance()`; them slot `cancelDetection` |
| `ui/app_context.py` | Shutdown 3 buoc: dispose worker -> cho thread pool -> dong DB pool |

### Test da cap nhat (2)

| File | Thay doi |
|---|---|
| `test/test_viewmodel.py` | `AuthViewModelTest` cho signal; them 2 test cho hanh vi bat dong bo |
| `test/test_controller.py` | `AuthControllerTest` cho signal; them 1 test cho `loading` |

### Khong thay doi

- Thuat toan AI: YOLO, KNN, KMeans, Vocabulary.
- Toan bo `ai/`, `ml/`, `detection/`, `dataset/`.
- Toan bo `database/` (Sprint 4 da xong).
- Toan bo `ui/qml/` (15 file).
- Nhip suy luan webcam `0.25 s`, nguong `CONFIDENCE = 0.5`, cooldown `5.0 s`.
- Dinh dang du lieu gui len View.

---

## 14. SAN SANG CHO SPRINT 6

Sprint 6 (Config & Dependency Injection) da co san diem bam:

1. Cac hang so moi phat sinh o Sprint 5 (`DEFAULT_MAX_IN_FLIGHT = 2`,
   `DEFAULT_DISPOSE_TIMEOUT_MS = 3000`, `HISTORY_POLL_SECONDS = 0.1`) deu la hang
   so o dau module, de gom vao `AppConfig`.
2. `max_frames_in_flight` va `token` da la tham so constructor -> tiem tu config
   khong phai sua ruot worker.
3. `AppContext.build()` da nhan 8 tham so tiem duoc; them `config` la du.
4. Danh sach magic number can gom da liet ke trong `SPRINT_PROMPTS.md`
   (0.25, 5.0, 200/500, 3000, 2).

---

Sprint 5 hoàn thành.

Thread Model đã được chuẩn hóa.

Không còn tác vụ chặn GUI.

Sẵn sàng chuyển sang Sprint 6: Config & Dependency Injection.
