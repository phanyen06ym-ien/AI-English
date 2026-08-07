# SPRINT 3 REPORT - GUI LAYER REFACTOR (MVVM READY)

Pham vi: bien GUI thanh **Thin Controller**, dua Business Logic xuong Service /
Worker / ViewModel.

Rang buoc da tuan thu:

| Rang buoc | Ket qua |
|---|---|
| Khong sua thuat toan AI (YOLO, KNN, KMeans, Vocabulary) | Khong file nao trong `ai/`, `ml/`, `detection/`, `dataset/` bi sua |
| Khong sua Database | Khong file nao trong `database/` bi sua |
| Khong sua GUI (QML) | Khong file nao trong `ui/qml/` bi sua |
| Regression Test PASS | 104/104 test PASS |

---

## 1. KIEN TRUC TRUOC

```text
QML
 |
 v
Controller  <-- chua het moi thu
 |  - QThread noi bo (ImageDetectThread, WebcamThread, HistoryWorker, StatsWorker)
 |  - goi save_history() / get_history() / clear_history()
 |  - cv2.VideoCapture, cv2.rectangle, draw_vietnamese_text
 |  - luat nguong confidence + cooldown lich su
 |  - phep dem Counter cho thong ke
 |  - format row database cho View
 |  - luat kiem tra mat khau, goi verify_login()
 |  - QFileDialog + cv2.imread ngay tren GUI thread
 v
AIEngine / database.history / database.auth
```

Van de:

1. Controller vua la View adapter, vua la Service, vua la Thread manager.
2. Khong test duoc neu khong co YOLO + PostgreSQL + webcam that.
3. `ImageController.chooseImage()` doc anh bang `cv2.imread` ngay tren GUI thread.
4. `WebcamThread` ghi lich su bang mot `threading.Thread` thuan roi emit Qt Signal
   tu thread do (thread khong co Qt affinity).
5. `WebcamController.stop()` block GUI thread toi 3 giay.
6. Khong co State machine: moi man hinh tu quan ly co `_busy` / `_loading` rieng.

---

## 2. KIEN TRUC SAU

```text
QML  (khong doi)
 |
 v
Controller (Thin Adapter)          <- chi nhan event + doi ten signal
 |
 v
ViewModel (State + trang thai UI)  <- Idle/Loading/Detecting/Completed/Error
 |
 v
Worker (QThread)                   <- chi dieu phoi thread + emit Signal
 |
 v
Service                            <- Business Logic
 |
 v
AIEngine  |  Repository (database.*)
 |
 v
Database
```

Cay phu thuoc that su (`ui/app_context.py`):

```text
AIEngine
   |
   +--> DetectionService --+--> ImageViewModel      -> ImageController
   |         ^             |
   |         |             +--> WebcamViewModel     -> WebcamController
   |    HistoryService ----+--> HistoryViewModel    -> HistoryController
   |         ^
   |    StatsService ---------> StatisticsViewModel -> StatsController
   |
   +--------------------------> VocabularyViewModel -> VocabularyController

AuthService ------------------> AuthViewModel       -> AuthController

DialogService  <- moi Controller day status message qua day
```

### Ghi chu ve NHIEM VU 12

Dac ta yeu cau `QML -> ViewModel -> Controller`. Vi Sprint 3 **khong duoc sua QML**,
ma QML dang bind vao context property `imageController`, `webcamController`, ...
nen **Controller van la be mat QML**, con ViewModel nam ngay duoi. Doi thu tu nay
bat buoc phai sua tung file `.qml`.

De san sang cho Sprint sau, moi ViewModel **da duoc dang ky them** thanh context
property (`imageViewModel`, `webcamViewModel`, `historyViewModel`, `statsViewModel`,
`vocabViewModel`, `authViewModel`, `dialogService`). QML tuong lai co the bind
thang vao ViewModel ma khong can sua Python.

---

## 3. CONTROLLER REVIEW (NHIEM VU 1)

### 3.1 ImageController

| Function | Truoc Sprint 3 | Xu ly |
|---|---|---|
| `ImageDetectThread.run()` | Goi `AIEngine.analyze_frame()`, `save_history()`, `cv2.rectangle`, `draw_vietnamese_text` | Tach ra `DetectionService.analyze_image_file()` + `AnnotationService` + `HistoryService` |
| `chooseImage()` | `QFileDialog` + `cv2.imread` tren GUI thread | `QFileDialog` giu o Controller (viec cua View), doc anh chuyen sang `PreviewLoadWorker` |
| `detectSelectedImage()` | Tu tao QThread, tu noi 4 signal | `ImageViewModel.detectSelectedImage()` |
| `_on_analysis_ready()` | Format ket qua, doi status | `ImageViewModel._on_analysis_ready()` |
| `_set_busy()` | Co `_busy` rieng | `UiState.is_busy()` |

**Business Logic con lai trong Controller: 0.**

### 3.2 WebcamController

| Function | Truoc Sprint 3 | Xu ly |
|---|---|---|
| `WebcamThread.run()` | `cv2.VideoCapture`, vong lap frame, goi AI, ve box | `WebcamWorker.run()` + `DetectionService` |
| `_save_history_if_allowed()` | Nguong `CONFIDENCE` + cooldown 5s | `HistoryRecordPolicy` (Service) |
| `_history_worker_loop()` | `threading.Thread` thuan, goi `save_history()` | `HistoryWriterWorker(QThread)` + `HistoryService` |
| `_draw_results()` | `cv2.rectangle` + `draw_vietnamese_text` | `AnnotationService.for_webcam()` |
| `_emit_word_suggestions()` | Cache tu goi y | `WebcamWorker` (dieu phoi signal, khong con business rule) |
| `stop()` | `wait(3000)` block GUI | `request_stop()` khong block; ban block chi dung khi thoat app |

**Business Logic con lai trong Controller: 0.**

### 3.3 VocabularyController

| Function | Truoc Sprint 3 | Xu ly |
|---|---|---|
| `__init__()` | Goi `AIEngine.get_vocabulary_entries()` | `VocabularyViewModel` |
| `loadRelatedWords()` | Goi `AIEngine.get_related_word_dicts()` | `VocabularyViewModel` |
| `loadClusterWords()` | Goi `AIEngine.get_cluster_word_dicts()` | `VocabularyViewModel` |
| `VocabularyModel` | Nam trong file controller | Chuyen sang `ui/viewmodels/vocabulary_viewmodel.py` |

### 3.4 HistoryController

| Function | Truoc Sprint 3 | Xu ly |
|---|---|---|
| `HistoryWorker.run()` | Goi `clear_history()` + `get_history()` | `HistoryService` |
| `_on_loaded()` | Format row database (`english_word` -> `english`, format ngay thang) | `format_history_rows()` (Service) |
| `HistoryModel` | Nam trong file controller | `ui/viewmodels/history_viewmodel.py` |

### 3.5 StatsController (StatisticsController)

| Function | Truoc Sprint 3 | Xu ly |
|---|---|---|
| `StatsWorker.run()` | `Counter`, `most_common`, trung binh confidence | `compute_statistics()` (Service) |
| `EMPTY_STATS` | Hang so trong controller | `ui/services/stats_service.py` |
| `_on_failed()` | `print()` | `logger.warning()` |

### 3.6 AuthController (phat hien them)

Khong nam trong danh sach dac ta nhung vi pham cung mot nguyen tac:

| Function | Truoc Sprint 3 | Xu ly |
|---|---|---|
| `login()` | Kiem tra rong + goi `verify_login()` + chuan hoa dict user | `AuthService.login()` |
| `register()` | 4 luat validate + `username_exists()` + `register_user()` | `AuthService.register()` |
| `changePassword()` | 5 luat validate + `change_password()` | `AuthService.change_password()` |
| `print()` debug | Log mat username ra stdout | Bo, thay bang `log_ui_event` |

Luu y: `AuthService` van goi database **dong bo tren GUI thread**, giong Sprint 2.
Chuyen sang worker se lam doi timing cua man hinh dang nhap, nen de sang
**Sprint 4 (Database & Repository Refactor)**. Da ghi trong muc Risk.

### 3.7 Do dai file

| File | Truoc | Sau | Thay doi |
|---|---:|---:|---|
| `ui/image_controller.py` | 302 | 227 | -25% (het thread + AI + DB) |
| `ui/webcam_controller.py` | 432 | 136 | -69% |
| `ui/history_controller.py` | 276 | 94 | -66% |
| `ui/stats_controller.py` | 166 | 72 | -57% |
| `ui/vocabulary_controller.py` | 161 | 87 | -46% |
| `ui/auth_controller.py` | 278 | 141 | -49% |
| `ui/main_qt.py` | 185 | 107 | -42% |
| **Tong 7 file** | **1800** | **864** | **-52%** |

---

## 4. VIEW MODEL (NHIEM VU 2)

| ViewModel | File | Trach nhiem |
|---|---|---|
| `BaseViewModel` | `ui/viewmodels/base_viewmodel.py` | State machine, status message, busy, error |
| `ImageViewModel` | `image_viewmodel.py` | Chon anh -> nhan dien -> ket qua + tien do |
| `WebcamViewModel` | `webcam_viewmodel.py` | Start/stop webcam, frame, ket qua realtime |
| `VocabularyViewModel` | `vocabulary_viewmodel.py` | Danh sach tu vung, k-NN, K-Means |
| `HistoryViewModel` | `history_viewmodel.py` | Tai / xoa lich su, `HistoryModel` |
| `StatisticsViewModel` | `statistics_viewmodel.py` | Thong ke nguoi dung |
| `AuthViewModel` | `auth_viewmodel.py` | Phien dang nhap |

Nguyen tac da kiem chung bang test (`ViewModelIsolationTest`):

- ViewModel **khong** import `QtWidgets` (khong tao widget, khong mo dialog).
- ViewModel **khong** import `database.*`, `ml.*`, `detection.*`, `ObjectDetector`.
- ViewModel chi noi chuyen voi Service va Worker.

---

## 5. SIGNAL (NHIEM VU 3)

### 5.1 Signal chuan hoa tren ViewModel

Ten PascalCase theo dung dac ta Sprint 3, tach han khoi ten legacy camelCase ma
QML dang dung.

| Signal | ViewModel | Payload |
|---|---|---|
| `StateChanged` | Base | `str` |
| `StatusMessageChanged` | Base | `str` |
| `BusyChanged` | Base | `bool` |
| `ErrorRaised` | Base | `str` |
| `DetectionStarted` | Image | - |
| `DetectionCompleted` | Image, Webcam | `list` |
| `DetectionFailed` | Image, Webcam | `str` |
| `DetectionFinished` | Image | - |
| `PreviewUpdated` | Image | `QImage` |
| `ProgressChanged` | Image | `int` |
| `SelectedImageChanged` | Image | `str` |
| `FrameUpdated` | Webcam | `QImage` |
| `RunningChanged` | Webcam | `bool` |
| `HistoryUpdated` | Webcam, History | - / `list` |
| `HistoryFailed` | History | `str` |
| `LoadingChanged` | History, Auth | `bool` |
| `VocabularyChanged` | Vocabulary | `list` |
| `RelatedWordsUpdated` | Image, Webcam, Vocabulary | `list` |
| `ClusterWordsUpdated` | Image, Webcam, Vocabulary | `list` |
| `StatisticsUpdated` | Statistics | `dict` |
| `StatisticsFailed` | Statistics | `str` |
| `UserChanged` / `LoggedInChanged` | Auth | `dict` / `bool` |
| `LoginSucceeded` / `RegisterSucceeded` / `PasswordChanged` | Auth | - |

### 5.2 Bang anh xa sang signal legacy cua QML

Controller **chi lam mot viec**: doi ten. Khong bien doi du lieu.

| ViewModel (chuan hoa) | Controller (QML dang bind) |
|---|---|
| `ImageViewModel.PreviewUpdated` | `imageController.imageChanged` |
| `ImageViewModel.DetectionCompleted` | `imageController.resultsChanged` |
| `ImageViewModel.RelatedWordsUpdated` | `imageController.relatedWordsChanged` |
| `ImageViewModel.ClusterWordsUpdated` | `imageController.clusterWordsChanged` |
| `ImageViewModel.StatusMessageChanged` | `imageController.statusChanged` |
| `ImageViewModel.BusyChanged` | `imageController.busyChanged` |
| `ImageViewModel.SelectedImageChanged` | `imageController.selectedImagePathChanged` |
| `ImageViewModel.DetectionFinished` | `imageController.detectionFinished` |
| `WebcamViewModel.FrameUpdated` | `webcamController.frameChanged` |
| `WebcamViewModel.DetectionCompleted` | `webcamController.resultsChanged` |
| `WebcamViewModel.RunningChanged` | `webcamController.runningChanged` |
| `WebcamViewModel.HistoryUpdated` | `webcamController.historySaved` |
| `HistoryViewModel.LoadingChanged` | `historyController.loadingChanged` |
| `HistoryViewModel.StatusMessageChanged` | `historyController.statusChanged` |
| `StatisticsViewModel.StatisticsUpdated` | `statsController.statsChanged` |
| `VocabularyViewModel.RelatedWordsUpdated` | `vocabController.relatedWordsChanged` |
| `VocabularyViewModel.ClusterWordsUpdated` | `vocabController.clusterWordsChanged` |
| `AuthViewModel.UserChanged` | `authController.currentUserChanged` + `authController.userChanged` |
| `AuthViewModel.LoggedInChanged` | `authController.isLoggedInChanged` |
| `AuthViewModel.StatusMessageChanged` | `authController.statusMessageChanged` |

`QmlContractTest` doc truc tiep file `.qml`, lay ra moi `<controller>.<member>` va
moi `function on<Signal>()` roi kiem tra Controller that su co member do. Day la
luoi an toan chong vo GUI.

---

## 6. WORKER (NHIEM VU 4)

| Worker | File | Service goi vao |
|---|---|---|
| `ImageWorker` | `ui/workers/image_worker.py` | `DetectionService.analyze_image_file()` |
| `PreviewLoadWorker` | `ui/workers/image_worker.py` | `DetectionService.load_image()` |
| `WebcamWorker` | `ui/workers/webcam_worker.py` | `DetectionService.analyze_camera_frame()` |
| `HistoryWriterWorker` | `ui/workers/webcam_worker.py` | `HistoryService.save_detection()` |
| `HistoryWorker` | `ui/workers/history_worker.py` | `HistoryService.load_formatted_rows()` |
| `StatsWorker` | `ui/workers/stats_worker.py` | `StatsService.compute_for_user()` |
| `SpeakTask` | `ui/workers/speech_worker.py` | `utils.speech.speak()` |

Quy tac da kiem chung bang test (`WorkerIsolationTest`):

- Worker **khong** import `QtWidgets`, **khong** import `QtQml`.
- Worker **khong** import `database.*`.
- Worker chi giao tiep ra ngoai bang Signal.

```text
Worker  ->  Signal  ->  ViewModel  ->  Controller  ->  View
```

Khong worker nao goi truc tiep vao GUI object.

---

## 7. THREAD (NHIEM VU 6)

### 7.1 Mo hinh

```text
GUI Thread                    Worker Thread
-----------                   -------------
Controller.detectSelectedImage()
   |
   +--> ViewModel.detectSelectedImage()
            |
            +--> ImageWorker.start() ------> run()
                                               |
                                               +-- DetectionService
                                               +-- AIEngine
                                               +-- HistoryService
                                               |
      Signal (queued) <------------------------+
        |
   ViewModel slot  (chay tren GUI Thread)
        |
   Controller signal
        |
      QML binding
```

### 7.2 Van de da xu ly

| # | Van de truoc Sprint 3 | Xu ly |
|---|---|---|
| 1 | `WebcamThread._history_worker_loop()` chay tren `threading.Thread` thuan roi emit `history_saved`. Thread khong co Qt affinity that su. | Doi thanh `HistoryWriterWorker(QThread)`. Signal emit tu QThread that, Qt tu chon `QueuedConnection`. |
| 2 | `WebcamController.stop()` goi `wait(3000)` -> GUI dung toi 3 giay | `stop()` -> `request_stop()` khong block. Ban block chi dung o `AppContext.shutdown()` khi thoat app. |
| 3 | `cv2.imread` chay tren GUI thread trong `chooseImage()` | `PreviewLoadWorker` |
| 4 | **RACE CONDITION (moi phat hien)**: `WebcamThread.run()` set `self._running = True` sau khi mo camera. Neu `stop()` chay truoc do, co bi ghi de -> worker chay mai mai -> `wait()` timeout -> Qt abort `QThread: Destroyed while thread is still running`. | Doi sang co dung mot chieu `_stop_requested`, khong bao gio set lai trong `run()`. Co test hoi quy `test_stop_before_run_reaches_loop_still_exits`. |
| 5 | Khong ai doi worker ket thuc khi thoat app -> QThread bi huy trong luc dang chay | `AppContext.shutdown()` goi `shutdown()` cua tung ViewModel, moi ViewModel `wait()` worker cua no. |

### 7.3 Bang chung tu test

`test_worker.WebcamWorkerTest.test_signal_is_delivered_on_gui_thread` chay worker
that, thu `threading.get_ident()` ben trong slot va khang dinh no bang thread ID
cua GUI thread. Khong co update GUI nao xay ra tren worker thread.

---

## 8. GUI FLOW (NHIEM VU 5)

### 8.1 Chon anh

```text
User bam "Chọn ảnh"
  |
  v
QML: imageController.chooseImage()
  |
  v
ImageController          -- mo QFileDialog (viec cua View)
  |
  v
ImageViewModel.selectImage(path)
  |  State: Idle -> Loading
  |  Status: "Đang tải ảnh..."
  v
PreviewLoadWorker.start()        [Worker Thread]
  |
  +--> DetectionService.load_image()
  |
  v
Signal previewReady(QImage)      [queued -> GUI Thread]
  |
  v
ImageViewModel
  |  State: Loading -> Completed -> Idle
  |  Status: "Đã chọn ảnh. Bấm Nhận diện để chạy YOLO."
  v
Signal PreviewUpdated -> imageController.imageChanged -> QML preview.setImage()
```

### 8.2 Nhan dien anh

```text
User bam "Nhận diện"
  |
  v
QML: imageController.detectSelectedImage()
  |
  v
ImageController -> ImageViewModel.detectSelectedImage()
  |  State: Idle -> Detecting
  |  Status: "Đang nhận diện..."
  |  Signal: DetectionStarted
  v
ImageWorker.start()                        [Worker Thread]
  |
  +--> DetectionService.analyze_image_file()
  |       |
  |       +-- progress 5   : bat dau
  |       +-- load_image()
  |       +-- progress 25
  |       +-- AIEngine.analyze_frame()   (YOLO -> Vocabulary -> KNN -> KMeans)
  |       +-- progress 70
  |       +-- HistoryService.save_detections()
  |       +-- progress 85
  |       +-- AnnotationService.draw_detections()
  |       +-- progress 100
  |
  +--> Signal progressChanged(int)   ---> ProgressChanged -> DialogService
  +--> Signal imageReady(QImage)     ---> PreviewUpdated  -> imageChanged
  +--> Signal analysisReady(object)  ---> DetectionCompleted / RelatedWordsUpdated
  |                                       / ClusterWordsUpdated
  v                                       State: Detecting -> Completed
Signal finished                        -> State: Completed -> Idle
                                       -> DetectionFinished -> detectionFinished
                                       -> QML: historyController.refresh()
                                               statsController.refresh()
```

### 8.3 Webcam

```text
User bam "Bật Camera"
  |
  v
webcamController.start() -> WebcamViewModel.start()   [State: Idle -> Detecting]
  |
  v
WebcamWorker.start()                         [Worker Thread]
  |
  +-- capture_factory() -> cv2.VideoCapture
  +-- while not stop_requested:
  |      read frame
  |      moi 0.25s: DetectionService.analyze_camera_frame()
  |         |
  |         +-- AIEngine.analyze_frame()
  |         +-- HistoryRecordPolicy.should_record()  (confidence + cooldown 5s)
  |         |
  |         +--> HistoryWriterWorker.enqueue()   [Thread ghi DB rieng]
  |         |         |
  |         |         +--> HistoryService.save_detection()
  |         |         +--> Signal historySaved
  |         |
  |         +--> Signal resultsReady / relatedReady / clusterReady
  |      DetectionService.annotate_camera_frame()
  |      Signal frameReady(QImage)
  v
Signal (queued) -> WebcamViewModel -> WebcamController -> QML
```

### 8.4 Lich su va thong ke

```text
historyController.refresh()
  -> HistoryViewModel.refresh()      [State: Idle -> Loading, loadingChanged(True)]
  -> HistoryWorker.start()           [Worker Thread]
       -> HistoryService.clear()             (chi khi clearHistory)
       -> HistoryService.load_formatted_rows()
       -> Signal loaded(list)        [queued -> GUI Thread]
  -> HistoryModel.set_rows()
  -> HistoryUpdated + "Đã tải N bản ghi."
  -> State: Loading -> Idle, loadingChanged(False)

statsController.refresh()
  -> StatisticsViewModel.refresh()   [State: Idle -> Loading]
  -> StatsWorker.start()             [Worker Thread]
       -> StatsService.compute_for_user()
            -> HistoryService.load_rows()
            -> compute_statistics()  (Counter, most_common, avg confidence)
       -> Signal loaded(dict)
  -> StatisticsUpdated -> statsChanged -> QML
```

---

## 9. STATE MANAGEMENT (NHIEM VU 7)

`ui/state.py`:

```text
        +-----------------------------+
        |                             |
        v                             |
      Idle ---> Loading ---> Detecting ---> Completed
        |          |             |              |
        |          v             v              |
        +------> Error <---------+<-------------+
                   |
                   v
                 Idle
```

| State | `is_busy()` | Y nghia |
|---|---|---|
| `Idle` | False | San sang nhan input |
| `Loading` | True | Dang doc du lieu (anh, lich su, thong ke) |
| `Detecting` | True | Dang chay AI pipeline |
| `Completed` | False | Mot chu ky da xong |
| `Error` | False | Chu ky that bai |

- `ALLOWED_TRANSITIONS` khai bao ro chuyen trang thai hop le.
- `BaseViewModel.set_state()` tu choi chuyen sai va ghi `warning`, khong crash.
- `busy` cua Controller khong con la bien rieng ma **suy ra tu State**.
- Controller **chi doi State** thong qua ViewModel, khong tu tinh toan.

---

## 10. DIALOG (NHIEM VU 8)

`ui/services/dialog_service.py` chuan hoa 4 muc:

| Muc | Signal | Tieu de mac dinh |
|---|---|---|
| Loading | `loadingShown(str)`, `loadingProgressChanged(int)`, `loadingHidden()` | "Đang xử lý" |
| Success | `successShown(title, message)` | "Thành công" |
| Warning | `warningShown(title, message)` | "Cảnh báo" |
| Error | `errorShown(title, message)` | "Lỗi" |

Truoc Sprint 3, QML tu doan mau chu bang `statusMessage.indexOf("thành công")`.
Sprint 3 giu nguyen hanh vi do (khong sua QML) nhung dong thoi dinh tuyen moi
status message qua `DialogService.publish()`, tu phan loai bang `classify_message()`.

`dialogService` da duoc dang ky lam context property, QML Sprint sau co the bind
truc tiep va bo hoan toan viec do chuoi.

---

## 11. LOADING (NHIEM VU 9)

```text
YOLO  ->  Loading  ->  Progress  ->  Complete
```

| Buoc | % | Nguon |
|---|---:|---|
| Bat dau | 5 | `DetectionService.analyze_image_file()` |
| Da doc anh | 25 | sau `load_image()` |
| Da chay AI | 70 | sau `AIEngine.analyze_frame()` |
| Da luu lich su | 85 | sau `HistoryService.save_detections()` |
| Da ve nhan | 100 | sau `AnnotationService` |

GUI khong bi freeze vi:

1. `cv2.imread` cua anh xem truoc chuyen sang `PreviewLoadWorker`.
2. `AIEngine.analyze_frame()` va ve nhan chay trong `ImageWorker`.
3. Ghi lich su webcam chay trong `HistoryWriterWorker` rieng.
4. `webcamController.stop()` khong con `wait()` block GUI thread.
5. Doc/xoa lich su va tinh thong ke chay trong `HistoryWorker` / `StatsWorker`.

Test `test_run_emits_image_analysis_and_progress` khang dinh chuoi `progress`
tang dan va ket thuc o 100.

---

## 12. LOGGING (NHIEM VU 10)

`ui/ui_logger.py`:

- Moi logger GUI co ten `ui.<component>` -> loc de dang.
- Ham chuyen dung: `log_ui_event`, `log_button_click`, `log_navigation`,
  `log_state_change`.
- `FORBIDDEN_AI_KEYWORDS` liet ke tu khoa thuoc AI (`yolo`, `knn`, `kmeans`,
  `vocabulary`, `detector`, `cluster`, `model`, `inference`, `confidence`);
  `is_ui_event_name()` dung de kiem tra.
- GUI **khong** log ket qua AI. Log AI van thuoc `ai.pipeline` (Sprint 2).
- Da bo cac `print()` con sot trong `StatsController` va `AuthController`
  (`AuthController` truoc day in ca username ra stdout).

Vi du log GUI:

```text
INFO ui.image_controller   button_click=choose_image
INFO ui.image_viewmodel    state_change idle -> loading
INFO ui.image_worker       ui_event=detection_worker_started
INFO ui.image_viewmodel    state_change detecting -> completed
```

---

## 13. REGRESSION TEST

### 13.1 Ket qua

| Lenh | Test | Ket qua |
|---|---:|---|
| `python -m unittest test.test_ai_engine` | 7 | PASS (khong doi tu Sprint 2) |
| `python -m unittest test.test_controller` | 33 | PASS |
| `python -m unittest test.test_viewmodel` | 40 | PASS |
| `python -m unittest test.test_worker` | 24 | PASS |
| **Tong (chay chung 1 lenh)** | **104** | **PASS, exit code 0** |
| `python test/test_knn.py` | - | PASS |
| `python test/test_kmeans.py` | - | PASS |
| `python -m compileall ui ai -q` | - | PASS |

Lenh chay day du:

```bash
.venv/Scripts/python.exe -m unittest test.test_ai_engine test.test_controller test.test_viewmodel test.test_worker
```

Ghi chu: `test/test_knn.py` va `test/test_kmeans.py` sinh lai `models/knn.pkl` va
anh trong `docs/experiment_results/`. Cac artifact nay **da duoc `git checkout`
khoi phuc** sau khi chay, dung nguyen tac "khong doi AI" cua Sprint 3.

### 13.2 Test moi (NHIEM VU 11)

| File | Test | Noi dung |
|---|---:|---|
| `test/test_controller.py` | 33 | Thin Controller, signal relay, hop dong QML, `AppContext` |
| `test/test_viewmodel.py` | 40 | State machine, luong nghiep vu, isolation |
| `test/test_worker.py` | 24 | Worker -> Service -> Signal, thread safety |
| `test/ui_fakes.py` | - | Fake AIEngine / HistoryService / Camera dung chung |

### 13.3 Cac test bao ve kien truc

| Test | Bao ve dieu gi |
|---|---|
| `ControllerIsolationTest.test_controllers_have_no_business_logic_calls` | Controller khong con `save_history(`, `get_history(`, `analyze_frame(`, `cv2.`, `VideoCapture`, `Counter(`, `verify_login(` ... |
| `ControllerIsolationTest.test_controllers_do_not_create_threads` | Controller khong tu tao `QThread` |
| `ControllerIsolationTest.test_controllers_do_not_import_ai_or_database` | Controller khong import `database.*`, `ai.*`, `ml.*`, `detection.*` |
| `WorkerIsolationTest` | Worker khong import `QtWidgets` / `QtQml` / `database` |
| `ViewModelIsolationTest` | ViewModel khong import `QtWidgets` / `database` / `ObjectDetector` |
| `QmlContractTest.test_every_member_used_by_qml_exists` | Moi `<controller>.<member>` trong file `.qml` van ton tai |
| `QmlContractTest.test_every_signal_handler_used_by_qml_exists` | Moi `function on<Signal>()` trong `Connections` van ton tai |
| `QmlContractTest.test_context_property_names_are_preserved` | 6 context property cu con nguyen ten |

### 13.4 Regression ve dinh dang du lieu

| Kiem tra | Ket qua |
|---|---|
| Nhan tren anh tinh | `laptop - May tinh xach tay [Technology] (0.93)` - khong doi |
| Nhan tren webcam | `laptop - May tinh xach tay [Technology - Medium] (0.93)` - khong doi |
| Dict gui sang QML cho anh tinh | khong co key `box` (giong `include_box=False` cu) |
| Format ngay lich su | `%d/%m/%Y %H:%M` - khong doi |
| Fallback lich su | `vietnamese` rong -> lay `english_word`; `category` rong -> `Unknown` |
| Cong thuc thong ke | `totalDetections`, `uniqueWords`, `mostCommonWord`, `mostDetectedWord`, `averageConfidence`, `categories` - khong doi |
| Nguong luu lich su | `CONFIDENCE = 0.5`, cooldown `5.0s` - khong doi |
| Nhip suy luan webcam | `0.25s` - khong doi |

### 13.5 File AI / Database / QML

```bash
git status --short ai/ ml/ detection/ dataset/ database/ models/ ui/qml/ utils/
# (khong co ket qua)
```

Khong mot file nao thuoc AI, Database hay QML bi thay doi.

---

## 14. RISK

| # | Risk | Muc do | Cach xu ly |
|---|---|---|---|
| 1 | QML vo do doi ten Property/Signal | Cao | Giu nguyen 100% ten. `QmlContractTest` quet file `.qml` va kiem tra tung member. |
| 2 | Thu tu signal doi lam QML nhan nham | Trung binh | ViewModel emit dung thu tu cu; test khang dinh `DetectionCompleted` -> `RelatedWordsUpdated` -> `ClusterWordsUpdated`. |
| 3 | `chooseImage()` gio la bat dong bo, `selectedImagePath` set cham hon | Trung binh | Path chi set khi doc anh thanh cong (giong logic cu). Nut "Nhận diện" van bi khoa cho toi khi co path. |
| 4 | Trang thai `busy` bat trong luc tai anh xem truoc (truoc day khong bat) | Thap | Chi trong vai chuc ms; nut bi vo hieu la hanh vi dung. |
| 5 | `AuthService` van goi database dong bo tren GUI thread | Trung binh | Giu nguyen hanh vi Sprint 2 de khong doi timing man hinh dang nhap. **Chuyen sang worker o Sprint 4.** |
| 6 | `webcamController.stop()` khong con block -> code goi ngay sau do co the thay `running` van True | Thap | QML chi phan ung theo signal `runningChanged`, khong doc dong bo. `AppContext.shutdown()` van block khi thoat app. |
| 7 | Race condition khi `stop()` den truoc `run()` | Da xu ly | Co dung mot chieu `_stop_requested` + test hoi quy. |
| 8 | QThread bi huy khi dang chay lam Qt abort | Da xu ly | `AppContext.shutdown()` -> `ViewModel.shutdown()` -> `worker.wait()`. |
| 9 | `DialogService` chua duoc QML dung | Thap | La chuan bi cho Sprint sau; khong anh huong hanh vi hien tai. |
| 10 | Import cu (`from ui.speech_worker import SpeakTask`, `ui.history_controller.HistoryModel`) | Thap | Da giu shim re-export o moi file lien quan. |
| 11 | Test can QApplication tren may khong co man hinh | Thap | Test dung `QCoreApplication`, khong tao widget. |

---

## 15. CHANGELOG

### File tao moi (21)

**State & Logging**

- `ui/state.py` - `UiState`, `ALLOWED_TRANSITIONS`, `can_transition()`
- `ui/ui_logger.py` - logger GUI, chan log AI

**Service layer (7)**

- `ui/services/__init__.py`
- `ui/services/annotation_service.py` - ve box + nhan
- `ui/services/history_service.py` - `HistoryService`, `HistoryRecordPolicy`, `format_history_rows()`
- `ui/services/stats_service.py` - `StatsService`, `compute_statistics()`
- `ui/services/detection_service.py` - `DetectionService`, dieu phoi 1 lan nhan dien
- `ui/services/auth_service.py` - `AuthService`, luat validate
- `ui/services/dialog_service.py` - `DialogService`, 4 muc dialog

**Worker layer (6)**

- `ui/workers/__init__.py`
- `ui/workers/image_worker.py` - `ImageWorker`, `PreviewLoadWorker`
- `ui/workers/webcam_worker.py` - `WebcamWorker`, `HistoryWriterWorker`
- `ui/workers/history_worker.py` - `HistoryWorker`
- `ui/workers/stats_worker.py` - `StatsWorker`
- `ui/workers/speech_worker.py` - `SpeakTask`

**ViewModel layer (8)**

- `ui/viewmodels/__init__.py`
- `ui/viewmodels/base_viewmodel.py`
- `ui/viewmodels/image_viewmodel.py`
- `ui/viewmodels/webcam_viewmodel.py`
- `ui/viewmodels/vocabulary_viewmodel.py`
- `ui/viewmodels/history_viewmodel.py`
- `ui/viewmodels/statistics_viewmodel.py`
- `ui/viewmodels/auth_viewmodel.py`

**Composition root**

- `ui/app_context.py` - `AppContext.build()`, dependency injection

**Test**

- `test/ui_fakes.py`
- `test/test_controller.py`
- `test/test_viewmodel.py`
- `test/test_worker.py`

### File sua (8)

| File | Thay doi |
|---|---|
| `ui/image_controller.py` | Thin adapter; bo `ImageDetectThread`, bo `save_history`, bo `cv2` |
| `ui/webcam_controller.py` | Thin adapter; bo `WebcamThread`, bo vong lap camera, bo luat cooldown |
| `ui/vocabulary_controller.py` | Thin adapter; `VocabularyModel` chuyen sang ViewModel layer |
| `ui/history_controller.py` | Thin adapter; `HistoryModel` + `HistoryWorker` chuyen di, bo format row |
| `ui/stats_controller.py` | Thin adapter; bo `Counter`, bo `EMPTY_STATS`, bo `print()` |
| `ui/auth_controller.py` | Thin adapter; bo luat validate, bo goi database, bo `print()` username |
| `ui/speech_worker.py` | Shim re-export tu `ui.workers.speech_worker` |
| `ui/main_qt.py` | Chi con bootstrap Qt; lap rap chuyen sang `AppContext` |

### Sua loi trong qua trinh refactor

1. **Race condition** trong `WebcamThread`: `run()` set co "dang chay" sau khi mo
   camera, ghi de yeu cau `stop()` den som -> worker khong bao gio thoat. Doi sang
   co dung mot chieu `_stop_requested`.
2. **QThread bi huy khi dang chay**: khong ai `wait()` worker khi dong ung dung.
   Them `ViewModel.shutdown()` va `AppContext.shutdown()`.
3. **`WebcamController.stop()` block GUI 3 giay**: tach `request_stop()` (khong
   block) va `stop()` (block, chi dung khi thoat app).
4. **`AuthController` in username ra stdout**: bo `print()`, thay bang UI log.

### Khong thay doi

- Thuat toan AI: YOLO, KNN, KMeans, Vocabulary, feature, scaler, metric, weight.
- Tham so AI: `CONFIDENCE`, `IMAGE_SIZE`, `n_neighbors`, `n_clusters`.
- `ai/pipeline.py`, `ai/models.py` va toan bo package `ai/`, `ml/`, `detection/`,
  `dataset/`.
- Toan bo `database/` (schema, query, ham).
- Toan bo `ui/qml/` (15 file `.qml`).
- Format nhan, format dict gui sang QML, cong thuc thong ke.

---

## 16. SAN SANG CHO SPRINT 4

Sprint 4 (Database & Repository Refactor) da co san diem bam:

1. `HistoryService` va `AuthService` la lop duy nhat goi `database.*`. Chi can
   doi ruot cua 2 file nay sang Repository, khong file GUI nao bi anh huong.
2. `DetectionService` nhan `history_service` qua constructor -> thay Repository
   khong can sua Worker hay ViewModel.
3. `AppContext.build()` da cho phep inject `history_service` va `auth_service`.
4. Viec dua `AuthService` sang worker (bo dong bo tren GUI thread) da duoc ghi
   trong muc Risk #5.

---

Sprint 3 hoàn thành.

GUI Layer đã được chuẩn hóa.

Business Logic không còn nằm trong Controller.

Sẵn sàng chuyển sang Sprint 4: Database & Repository Refactor.
