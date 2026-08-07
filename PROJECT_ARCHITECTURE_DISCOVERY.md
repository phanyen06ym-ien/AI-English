# PROJECT ARCHITECTURE DISCOVERY - AI-English

Tài liệu này mô tả kiến trúc thực thi runtime của project theo source code hiện tại.

Phạm vi: chỉ đọc source code, không mô tả chức năng không tồn tại trong source.

## 1. Runtime Architecture

```text
Application
  |
  v
main.py
  |
  v
utils.console.use_utf8_console()
  |
  v
ui.main_qt.run()
  |
  v
QApplication
  |
  v
qmlRegisterType(VideoItem)
  |
  v
ObjectDetector
  |
  v
YOLO(models/best.pt)
  |
  v
Controllers
  |
  +--> AuthController
  +--> VocabularyController
  +--> ImageController
  +--> WebcamController
  +--> HistoryController
  +--> StatsController
  |
  v
QQmlApplicationEngine
  |
  v
QML Context Properties
  |
  v
Main.qml
  |
  v
Login/Register hoặc Main UI
```

### 1.1 Giải Thích Từng Bước

| Bước | Source | Runtime action |
|---|---|---|
| 1 | `main.py` | Hàm `main()` được gọi khi chạy trực tiếp file |
| 2 | `utils.console.use_utf8_console()` | Cấu hình stdout/stderr UTF-8 |
| 3 | `ui.main_qt.run()` | Khởi tạo GUI runtime |
| 4 | `QApplication(sys.argv)` | Tạo Qt application object |
| 5 | `qmlRegisterType(VideoItem, "AIEnglish", 1, 0, "VideoItem")` | Đăng ký custom QML item để hiển thị QImage |
| 6 | `ObjectDetector()` | Load YOLO model từ `models/best.pt` |
| 7 | Controllers | Tạo các QObject controller |
| 8 | `auth_controller.userChanged.connect(apply_current_user)` | Gắn lifecycle user vào image/webcam/history/stats |
| 9 | `engine.rootContext().setContextProperty(...)` | Expose controller sang QML |
| 10 | `engine.load(Main.qml)` | Load UI |
| 11 | `app.exec()` | Bắt đầu Qt event loop |

## 2. Runtime Flow

```text
User mở ứng dụng
  |
  v
main.py
  |
  v
Load YOLO trước khi load QML
  |
  v
Tạo controller
  |
  v
Expose controller cho QML
  |
  v
Nếu chưa đăng nhập: LoginPage/RegisterPage
  |
  v
Nếu đăng nhập thành công: Main.qml hiển thị sidebar + StackLayout
  |
  +--> HomePage
  +--> CameraPage
  +--> HistoryPage
  +--> StatisticsPage
  +--> AccountPage
```

Runtime chính dựa trên Qt event loop. QML gọi các method Python được đánh dấu `@Slot`. Python controller cập nhật QML bằng `Signal` và `Property notify`.

## 3. Sequence Flow

### 3.1 Đăng Nhập

```text
User
  |
  v
LoginPage.qml
  |
  | onClicked / Enter
  v
authController.login(username, password)
  |
  v
AuthController.login()
  |
  +--> validate username/password rỗng
  |
  +--> _set_loading(True)
  |
  v
database.auth.verify_login(username, password)
  |
  v
find_user_by_username(username)
  |
  v
database_cursor()
  |
  v
get_connection()
  |
  v
PostgreSQL SELECT users
  |
  v
_verify_password(password, stored_password)
  |
  +--> bcrypt.checkpw nếu stored password là bcrypt
  +--> so sánh plain text nếu không phải bcrypt
  |
  v
Nếu password cũ plain text:
  _update_password_hash(user_id, _hash_password(password))
  |
  v
AuthController._set_user(user)
  |
  +--> currentUserChanged
  +--> userChanged
  +--> isLoggedInChanged
  |
  v
ui.main_qt.apply_current_user(user)
  |
  +--> image_controller.set_user_id(user_id)
  +--> webcam_controller.set_user_id(user_id)
  +--> history_controller.set_user_id(user_id)
  +--> stats_controller.set_user_id(user_id)
  +--> history_controller.refresh()
  +--> stats_controller.refresh()
  |
  v
GUI chuyển từ LoginPage sang Main UI
```

### 3.2 Đăng Ký

```text
User
  |
  v
RegisterPage.qml
  |
  v
authController.register(fullname, username, password, confirmPassword)
  |
  v
AuthController.register()
  |
  +--> validate fullname
  +--> validate username
  +--> validate password length >= 6
  +--> validate confirm password
  +--> _set_loading(True)
  |
  v
username_exists(username)
  |
  v
find_user_by_username(username)
  |
  v
PostgreSQL SELECT users
  |
  v
Nếu username chưa tồn tại
  |
  v
register_user(fullname, username, password)
  |
  +--> _hash_password(password)
  +--> create_user(fullname, username, password_hash)
        |
        v
        PostgreSQL INSERT users RETURNING id, username, fullname
  |
  v
AuthController.registerSucceeded.emit()
  |
  v
RegisterPage.qml onRegisterSucceeded()
  |
  v
Quay lại LoginPage
```

### 3.3 Nhận Diện Ảnh

```text
User
  |
  v
CameraPage.qml
  |
  +--> imageController.chooseImage()
  |     |
  |     v
  |   QFileDialog.getOpenFileName()
  |     |
  |     v
  |   cv2.imread(image_path)
  |     |
  |     v
  |   to_qimage(image)
  |     |
  |     v
  |   imageChanged(QImage)
  |
  +--> imageController.detectSelectedImage()
        |
        v
      ImageController.detectSelectedImage()
        |
        +--> _set_busy(True)
        +--> _set_status("Đang nhận diện...")
        +--> ImageDetectThread(detector, image_path, user_id)
        +--> connect signals
        +--> thread.start()
        |
        v
      ImageDetectThread.run()
        |
        v
      detection.image_detect.detect_image()
        |
        +--> cv2.imread(image_path)
        +--> ObjectDetector.detect(image)
        |     |
        |     v
        |   YOLO.predict(frame, conf=0.5, imgsz=640)
        |
        +--> classify_word(class_name)
        |     |
        |     +--> get_word_info(class_name)
        |     +--> predict_category(class_name) nếu không có vocabulary
        |
        +--> save_history(class_name, vietnamese, category, confidence, user_id)
        +--> cv2.rectangle()
        +--> draw_vietnamese_text()
        |
        v
      image_ready(QImage), results_ready(list)
        |
        v
      ImageController._on_results_ready(results)
        |
        +--> sort theo confidence
        +--> get_related_words(primary_word, n=3)
        +--> get_words_in_same_cluster(primary_word)
        +--> resultsChanged
        +--> relatedWordsChanged
        +--> clusterWordsChanged
        +--> statusChanged
        |
        v
      CameraPage.qml cập nhật preview, list kết quả, từ gợi ý, cùng nhóm
```

### 3.4 Nhận Diện Webcam

```text
User
  |
  v
CameraPage.qml
  |
  v
webcamController.start()
  |
  v
WebcamController.start()
  |
  +--> set _running=True
  +--> runningChanged(True)
  +--> WebcamThread(detector, CAMERA_ID, user_id)
  +--> connect frame/results/related/cluster/status/history signals
  +--> thread.start()
  |
  v
WebcamThread.run()
  |
  +--> perf_monitor.start()
  +--> _start_history_worker()
  |     |
  |     v
  |   threading.Thread(name="webcam-history-writer")
  |
  +--> cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
  +--> fallback cv2.VideoCapture(camera_id)
  |
  v
Loop khi _running=True
  |
  +--> camera.read()
  +--> nếu đủ 0.25 giây:
  |     |
  |     +--> detector.detect(frame)
  |     +--> _format_detection(obj)
  |     |     └── classify_word(class_name)
  |     +--> results_ready(results)
  |     +--> _save_history_if_allowed(result, now)
  |     |     └── _history_queue.put_nowait(...)
  |     +--> _emit_word_suggestions(primary_word)
  |           ├── get_related_words(primary_word, n=3)
  |           └── get_words_in_same_cluster(primary_word)
  |
  +--> _draw_results(frame, last_results)
  +--> to_qimage(display_frame)
  +--> frame_ready(QImage)
  |
  v
CameraPage.qml preview.setImage(frame)
```

Stop webcam:

```text
CameraPage.qml
  |
  v
webcamController.stop()
  |
  v
WebcamThread.stop()
  |
  +--> _running=False
  +--> wait(3000)
  |
  v
WebcamThread.run() finally
  |
  +--> camera.release()
  +--> _stop_history_worker()
  +--> status_changed("Webcam đã tắt.")
  |
  v
WebcamController._on_finished()
  |
  +--> _thread=None
  +--> _running=False
  +--> runningChanged(False)
```

### 3.5 Gợi Ý KNN

Ảnh tĩnh:

```text
ImageController._on_results_ready(results)
  |
  v
primary_word = formatted_results[0]["english"]
  |
  v
get_related_words(primary_word, n=3)
  |
  v
load_knn_model()
  |
  +--> nếu cache hợp lệ: trả cache
  +--> nếu models/knn.pkl hợp lệ: joblib.load()
  +--> nếu không: train_knn_model()
  |
  v
scaler.transform(query_feature)
  |
  v
apply_feature_weights()
  |
  v
NearestNeighbors.kneighbors()
  |
  v
relatedWordsChanged(list)
```

Webcam:

```text
WebcamThread._emit_word_suggestions(primary_word)
  |
  +--> nếu primary_word rỗng: emit [] cho related và cluster
  +--> nếu primary_word giống lần trước: return
  +--> nếu chưa có cache cho word:
        get_related_words(primary_word, n=3)
  |
  v
related_ready(list)
  |
  v
WebcamController._on_related_ready()
  |
  v
relatedWordsChanged(list)
```

Vocabulary controller:

```text
VocabularyController.loadRelatedWords(word)
  |
  v
get_related_words(word, n=3)
  |
  v
relatedWordsChanged(words)
```

### 3.6 Phân Cụm KMeans

Ảnh tĩnh:

```text
ImageController._on_results_ready(results)
  |
  v
primary_word = formatted_results[0]["english"]
  |
  v
get_words_in_same_cluster(primary_word)
  |
  v
load_kmeans_model()
  |
  +--> nếu cache hợp lệ: trả cache
  +--> nếu models/kmeans.pkl hợp lệ: joblib.load()
  +--> nếu không: train_kmeans_model()
  |
  v
tìm row vocabulary theo english
  |
  v
lấy cluster_id
  |
  v
lọc dataframe cùng cluster
  |
  v
clusterWordsChanged(list)
```

Webcam:

```text
WebcamThread._emit_word_suggestions(primary_word)
  |
  +--> nếu chưa có cluster cache cho word:
        get_words_in_same_cluster(primary_word)
  |
  v
cluster_ready(list)
  |
  v
WebcamController._on_cluster_ready()
  |
  v
clusterWordsChanged(list)
```

Vocabulary controller:

```text
VocabularyController.loadClusterWords(word)
  |
  v
get_words_in_same_cluster(word)
  |
  v
clusterWordsChanged(words)
```

### 3.7 Lưu Lịch Sử

Ảnh tĩnh:

```text
detection.image_detect.detect_image()
  |
  v
save_history(class_name, vietnamese, category, confidence, user_id)
  |
  v
database.history.save_history()
  |
  +--> normalize english/vietnamese/category
  +--> nếu english rỗng: return False
  |
  v
database_cursor(commit=True)
  |
  v
PostgreSQL INSERT history
  |
  v
commit
```

Webcam:

```text
WebcamThread._save_history_if_allowed(result, now)
  |
  +--> kiểm tra confidence >= CONFIDENCE
  +--> kiểm tra cooldown 5 giây/class
  |
  v
_history_queue.put_nowait((class_name, vietnamese, category, confidence, user_id))
  |
  v
webcam-history-writer thread
  |
  v
save_history(...)
  |
  v
history_saved signal nếu lưu thành công
  |
  v
CameraPage.qml onHistorySaved()
  |
  +--> historyController.refresh()
  +--> statsController.refresh()
```

### 3.8 Xem Thống Kê

```text
StatisticsPage.qml hoặc Main.qml sidebar
  |
  v
statsController.refresh()
  |
  v
StatsController.refresh()
  |
  +--> nếu user_id is None: clear()
  +--> nếu worker đang chạy: return
  +--> StatsWorker(user_id)
  +--> connect loaded/failed/finished
  +--> start()
  |
  v
StatsWorker.run()
  |
  v
get_history(user_id, limit=500)
  |
  v
PostgreSQL SELECT history
  |
  v
Counter category, Counter word, average confidence
  |
  v
loaded(stats_dict)
  |
  v
statsChanged(stats)
  |
  v
StatisticsPage.qml cập nhật StatCard và category list
```

## 4. Thread Analysis

| Thread / Worker | Tạo ở đâu | Bắt đầu khi nào | Dừng khi nào | Nhiệm vụ | Giao tiếp UI | Queue | Race condition theo source |
|---|---|---|---|---|---|---|---|
| Main Qt Thread | `ui.main_qt.run()` | `app.exec()` | Khi app quit | Qt event loop, QML, controller slots mặc định | Signal/Slot trực tiếp và queued connection từ QThread | Không | Có shared controller state nhận signal từ worker; Qt signal xử lý qua event loop |
| `ImageDetectThread` | `ImageController.detectSelectedImage()` | Khi user bấm nhận diện ảnh đã chọn | Khi `run()` kết thúc, `_on_finished()` set `_thread=None` | Chạy `detect_image`, YOLO, classify, save history, convert QImage | `image_ready`, `results_ready`, `failed`, `finished` | Không | Dùng chung `ObjectDetector` với main/webcam nếu chạy đồng thời; source không có lock quanh detector |
| `WebcamThread` | `WebcamController.start()` | Khi user bấm bật camera | `WebcamController.stop()` gọi `thread.stop()` hoặc thread kết thúc | Đọc camera, chạy YOLO định kỳ, format result, emit frame/results | `frame_ready`, `results_ready`, `related_ready`, `cluster_ready`, `status_changed`, `history_saved`, `finished` | Có queue nội bộ cho history | Dùng chung `ObjectDetector`; `_running` được đổi từ controller thread và đọc trong worker thread |
| `webcam-history-writer` | `WebcamThread._start_history_worker()` | Đầu `WebcamThread.run()` | `_stop_history_worker()` gửi stop token và join timeout 1s | Ghi history DB bất đồng bộ cho webcam | Emit `history_saved` từ worker phụ | `queue.Queue(maxsize=20)` | Queue thread-safe; signal emit từ thread phụ về Qt |
| `HistoryWorker` | `HistoryController._start_worker()` | `historyController.refresh()` hoặc `clearHistory()` | Khi `run()` xong, `_on_finished()` set `_worker=None` | Đọc hoặc xóa rồi đọc history | `loaded`, `failed`, `finished` | Không | Controller chặn worker mới nếu `_worker is not None` |
| `StatsWorker` | `StatsController.refresh()` | Khi stats refresh và có user_id | Khi `run()` xong, `_on_finished()` set `_worker=None` | Đọc history và tính thống kê | `loaded`, `failed`, `finished` | Không | Controller chặn worker mới nếu `_worker is not None` |
| `SpeakTask` | `ImageController.speak()` và `VocabularyController.speak()` | Khi gọi `QThreadPool.globalInstance().start(SpeakTask(word))` | Khi `SpeakTask.run()` kết thúc | Tạo và mở audio phát âm | Không emit signal; lỗi được print | Không | Nhiều SpeakTask có thể cùng ghi `assets/audio/speech.mp3` vì source dùng một file cố định |

## 5. Runtime Object Graph

```text
QApplication
  |
  +--> QQmlApplicationEngine
  |     |
  |     +--> Main.qml root object
  |     |     |
  |     |     +--> LoginPage / RegisterPage khi chưa login
  |     |     +--> HomePage
  |     |     +--> CameraPage
  |     |     |     └── VideoItem instances
  |     |     +--> HistoryPage
  |     |     +--> StatisticsPage
  |     |     └── AccountPage
  |     |
  |     └── rootContext properties
  |           |
  |           +--> authController
  |           +--> vocabController
  |           +--> imageController
  |           +--> webcamController
  |           +--> historyController
  |           +--> statsController
  |
  +--> ObjectDetector
  |     └── YOLO model object
  |
  +--> VocabularyController
  |     └── VocabularyModel
  |
  +--> ImageController
  |     └── ImageDetectThread khi detect ảnh
  |
  +--> WebcamController
  |     └── WebcamThread khi bật webcam
  |           └── threading.Thread "webcam-history-writer"
  |
  +--> HistoryController
  |     ├── HistoryModel
  |     └── HistoryWorker khi refresh/clear
  |
  +--> StatsController
  |     └── StatsWorker khi refresh
  |
  └── AuthController
```

### 5.1 Lifecycle Object

| Object | Tạo khi nào | Sống đến khi nào | Ghi chú lifecycle theo source |
|---|---|---|---|
| `QApplication` | Trong `ui.main_qt.run()` | Đến khi `app.exec()` kết thúc | Qt application chính |
| `QQmlApplicationEngine` | Sau khi tạo controller | Đến khi app kết thúc | Load `Main.qml` |
| `ObjectDetector` | Trước khi tạo controller | Đến khi app kết thúc | Dùng chung cho `ImageController` và `WebcamController` |
| YOLO object | Trong `ObjectDetector.__init__()` | Theo vòng đời `ObjectDetector` | Load từ `models/best.pt` |
| Controllers | Trong `ui.main_qt.run()` | Đến khi app kết thúc | Exposed sang QML context |
| `VideoItem` | Khi QML tạo CameraPage/component | Theo vòng đời QML item | Nhận QImage qua slot `setImage` |
| `ImageDetectThread` | Mỗi lần detect ảnh | Kết thúc sau một lần detect | `_thread=None` trong `_on_finished()` |
| `WebcamThread` | Khi bật webcam | Khi stop hoặc lỗi camera | `_thread=None` trong `_on_finished()` |
| `HistoryWorker` | Mỗi refresh/clear history | Kết thúc sau query DB | `_worker=None` trong `_on_finished()` |
| `StatsWorker` | Mỗi refresh stats | Kết thúc sau query/tính stats | `_worker=None` trong `_on_finished()` |
| `SpeakTask` | Mỗi lần gọi speak | Kết thúc sau tạo/mở audio | Chạy trong global QThreadPool |
| DB connection | Mỗi lần `database_cursor()` | Đóng trong `finally` | Không giữ persistent connection |

## 6. Data Flow

### 6.1 Ảnh Tĩnh

```text
image_path: str
  |
  v
cv2.imread(image_path)
  |
  v
image: np.ndarray BGR
  |
  v
ObjectDetector.detect(image)
  |
  v
YOLO results
  |
  v
detected_objects: list[dict]
  - class_name: str
  - confidence: float
  - box: tuple[int, int, int, int]
  |
  v
classify_word(class_name)
  |
  v
info: dict
  - english
  - vietnamese
  - category
  - level
  - source
  |
  v
results append:
  - info fields
  - confidence
  - box
  |
  +--> save_history(...)
  |
  +--> cv2.rectangle + draw_vietnamese_text
  |     |
  |     v
  |   annotated image: np.ndarray BGR
  |
  v
to_qimage(annotated image)
  |
  v
QImage
  |
  v
QML VideoItem preview
```

### 6.2 Webcam

```text
cv2.VideoCapture(CAMERA_ID)
  |
  v
frame: np.ndarray BGR
  |
  +--> detector.detect(frame) mỗi 0.25s
  |     |
  |     v
  |   detected_objects
  |     |
  |     v
  |   formatted results
  |     |
  |     +--> results_ready(list)
  |     +--> history queue item
  |     +--> related/cluster calculation
  |
  +--> _draw_results(frame, last_results)
        |
        v
      display_frame
        |
        v
      to_qimage(display_frame)
        |
        v
      frame_ready(QImage)
```

### 6.3 Dữ Liệu ML

```text
dataset/vocabulary.csv
  |
  v
pandas.read_csv()
  |
  v
normalized dataframe
  |
  v
features dataframe
  - word_length
  - level_encoded
  - one-hot category
  |
  v
StandardScaler
  |
  v
weighted features
  |
  +--> NearestNeighbors.kneighbors()
  |     └── related words
  |
  └── KMeans cluster labels
        └── same cluster words
```

## 7. AI Pipeline

```text
Image / Webcam Frame
  |
  v
OpenCV
  |
  v
YOLOv8 ObjectDetector
  |
  v
Object Name + Confidence + Bounding Box
  |
  v
Vocabulary Lookup
  |
  v
English + Vietnamese + Category + Level
  |
  +--> k-NN
  |     |
  |     v
  |   Related Words
  |
  +--> K-Means
  |     |
  |     v
  |   Same Cluster Words
  |
  +--> History
  |     |
  |     v
  |   PostgreSQL INSERT
  |
  v
GUI
```

| Bước | Source | Nhiệm vụ |
|---|---|---|
| OpenCV | `cv2.imread`, `cv2.VideoCapture` | Tạo ảnh/frame BGR |
| YOLOv8 | `ObjectDetector.detect()` | Detect object, confidence, bbox |
| Class filtering | `COCO_CLASSES` | Chỉ giữ 12 class trong project |
| Vocabulary | `classify_word()` và `get_word_info()` | Lấy nghĩa tiếng Việt, category, level |
| Category fallback | `predict_category()` | Trả category theo lookup hoặc `Unknown` |
| k-NN | `get_related_words()` | Gợi ý từ liên quan |
| K-Means | `get_words_in_same_cluster()` | Lấy từ cùng cụm |
| History | `save_history()` | Lưu kết quả nhận diện |
| GUI | QML + controller signals | Hiển thị ảnh, kết quả, gợi ý, cụm |

## 8. Database Flow

### 8.1 Đọc

| Thao tác | Source | SQL runtime |
|---|---|---|
| Tìm user đăng nhập | `find_user_by_username()` | `SELECT id, username, fullname, password FROM users WHERE username = %s LIMIT 1` |
| Kiểm tra username tồn tại | `username_exists()` | Gọi `find_user_by_username()` |
| Lấy password để đổi mật khẩu | `change_password()` | `SELECT password FROM users WHERE id = %s LIMIT 1` |
| Lấy history | `get_history()` | `SELECT ... FROM history ORDER BY detected_time DESC LIMIT %s` hoặc có `WHERE user_id = %s` |
| Xem thống kê | `StatsWorker.run()` | Gọi `get_history(user_id, limit=500)` |

### 8.2 Ghi

| Thao tác | Source | SQL runtime |
|---|---|---|
| Đăng ký | `create_user()` | `INSERT INTO users (fullname, username, password) VALUES (...) RETURNING id, username, fullname` |
| Lưu history ảnh tĩnh | `detection.image_detect.detect_image()` -> `save_history()` | `INSERT INTO history (...) VALUES (...)` |
| Lưu history webcam | `WebcamThread._history_worker_loop()` -> `save_history()` | `INSERT INTO history (...) VALUES (...)` |

### 8.3 Cập Nhật

| Thao tác | Source | SQL runtime |
|---|---|---|
| Migrate password plain text sang bcrypt | `verify_login()` -> `_update_password_hash()` | `UPDATE users SET password = %s WHERE id = %s` |
| Đổi mật khẩu | `change_password()` -> `_update_password_hash()` | `UPDATE users SET password = %s WHERE id = %s` |

### 8.4 Xóa

| Thao tác | Source | SQL runtime |
|---|---|---|
| Xóa toàn bộ history | `clear_history(user_id=None)` | `DELETE FROM history` |
| Xóa history theo user | `clear_history(user_id)` | `DELETE FROM history WHERE user_id = %s` |
| Xóa history theo user wrapper | `delete_history_by_user(user_id)` | Gọi `clear_history(user_id)` |

### 8.5 Database Connection Lifecycle

```text
database_cursor()
  |
  v
get_connection()
  |
  v
psycopg2.connect(host, database, user, password, port)
  |
  v
cursor = connection.cursor()
  |
  v
execute/fetch
  |
  +--> commit nếu commit=True
  +--> rollback nếu exception
  |
  v
cursor.close()
connection.close()
```

## 9. Resource Map

| Resource | Source path | Runtime consumer | Runtime usage |
|---|---|---|---|
| YOLO weight | `models/best.pt` | `ObjectDetector` | Load bằng `YOLO(model_path)` |
| k-NN model | `models/knn.pkl` | `ml.knn.load_knn_model()` | Load bằng `joblib.load`; train lại nếu không hợp lệ |
| K-Means model | `models/kmeans.pkl` | `ml.kmeans.load_kmeans_model()` | Load bằng `joblib.load`; train lại nếu không hợp lệ |
| Category model | `models/word_category_model.joblib` | Không tìm thấy trong source code hiện tại | Không tìm thấy trong source code hiện tại |
| Vocabulary CSV | `dataset/vocabulary.csv` | `dataset.vocabulary`, `ml.knn`, `ml.kmeans`, `ml.features` | Lookup từ, build feature, train/load ML |
| Dataset YAML | `dataset/dataset.yaml` | Không tìm thấy runtime GUI load | Dùng cho YOLO dataset config |
| COCO class list | `dataset/coco_classes.py` | `ObjectDetector.detect()` | Lọc class detect hợp lệ |
| Object mapping | `dataset/object_mapping.py` | `utils.translator.dich_tu()` | Fallback dịch |
| Test images | `dataset/test_images/*.jpg` | `test.test_yolo_image`, `test.test_system_evaluation`, default script | Input test |
| Font | `assets/fonts/NotoSans-Regular.ttf` | `utils.helper.get_font()` | Vẽ tiếng Việt lên ảnh |
| Audio file | `assets/audio/speech.mp3` | `utils.speech.phat_am()`, `speak()` | File output phát âm |
| QML files | `ui/qml/*.qml` | `QQmlApplicationEngine` | GUI screens |
| QML components | `ui/qml/components/*.qml` | QML screens | Component dùng lại |
| `.env` | `.env` | `database.db` | DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT |
| Experiment reports | `docs/experiment_results/*` | Không tìm thấy runtime GUI load | Output test/report |

## 10. Configuration Map

### 10.1 `utils/config.py`

| Config | Giá trị source | Nơi sử dụng |
|---|---|---|
| `PROJECT_ROOT` | Parent của `utils/` | Config path nội bộ |
| `ASSETS_DIR` | `PROJECT_ROOT / "assets"` | `FONT_PATH`, `AUDIO_DIR` |
| `MODELS_DIR` | `PROJECT_ROOT / "models"` | `MODEL_PATH` |
| `DATASET_DIR` | `PROJECT_ROOT / "dataset"` | `TEST_IMAGE_PATH` |
| `MODEL_PATH` | `models/best.pt` | `detection.detector.ObjectDetector` |
| `CONFIDENCE` | `0.5` | `ObjectDetector.detect()`, `WebcamThread._save_history_if_allowed()` |
| `IMAGE_SIZE` | `640` | `ObjectDetector.detect()` |
| `CAMERA_ID` | `0` | `detection.webcam_detect.run_webcam()`, `WebcamController.start()` |
| `LEVELS` | Easy/Medium/Hard mapping tiếng Việt | Không tìm thấy runtime usage trong source hiện tại |
| `DEFAULT_LANGUAGE` | `"vi"` | Không tìm thấy runtime usage trong source hiện tại |
| `FONT_PATH` | `assets/fonts/NotoSans-Regular.ttf` | `utils.helper.get_font()` |
| `AUDIO_DIR` | `assets/audio` | `utils.speech.phat_am()` |
| `AUDIO_FILE` | `assets/audio/speech.mp3` | `utils.speech.phat_am()` |
| `TEST_IMAGE_PATH` | `dataset/test_images/test1.jpg` | Không tìm thấy runtime usage trong source hiện tại |

### 10.2 `database/db.py` Environment

| Config | Source | Nơi sử dụng |
|---|---|---|
| `DB_HOST` | `os.getenv("DB_HOST")` | `psycopg2.connect(host=...)` |
| `DB_NAME` | `os.getenv("DB_NAME")` | `psycopg2.connect(database=...)` |
| `DB_USER` | `os.getenv("DB_USER")` | `psycopg2.connect(user=...)` |
| `DB_PASSWORD` | `os.getenv("DB_PASSWORD")` | `psycopg2.connect(password=...)` |
| `DB_PORT` | `os.getenv("DB_PORT")` | `psycopg2.connect(port=...)` |
| `DATABASE_URL` | Không tìm thấy trong source code hiện tại | Không tìm thấy trong source code hiện tại |

### 10.3 `ml/knn.py`

| Config | Giá trị | Nơi sử dụng |
|---|---|---|
| `DATA_PATH` | `dataset/vocabulary.csv` | `read_vocabulary()` |
| `MODEL_PATH` | `models/knn.pkl` | `train_knn_model()`, `load_knn_model()` |
| `MODEL_VERSION` | `4` | Cache/model validation |
| `REQUIRED_COLUMNS` | `english`, `vietnamese`, `category`, `level` | CSV validation |
| `LEVEL_MAPPING` | Easy=0, Medium=1, Hard=2 | Feature |
| `CATEGORY_WEIGHT` | `5.0` | Feature weighting |
| `LEVEL_WEIGHT` | `2.0` | Feature weighting |
| `WORD_LENGTH_WEIGHT` | `0.5` | Feature weighting |

### 10.4 `ml/kmeans.py`

| Config | Giá trị | Nơi sử dụng |
|---|---|---|
| `DATA_PATH` | `dataset/vocabulary.csv` | `read_vocabulary()` |
| `MODEL_PATH` | `models/kmeans.pkl` | `train_kmeans_model()`, `load_kmeans_model()` |
| `MODEL_VERSION` | `4` | Cache/model validation |
| `REQUIRED_COLUMNS` | `english`, `vietnamese`, `category`, `level` | CSV validation |
| `LEVEL_MAPPING` | Easy=0, Medium=1, Hard=2 | Feature |
| `CATEGORY_WEIGHT` | `5.0` | Feature weighting |
| `LEVEL_WEIGHT` | `2.0` | Feature weighting |
| `WORD_LENGTH_WEIGHT` | `0.5` | Feature weighting |

### 10.5 Webcam Runtime Constants

| Config | Giá trị | File | Nơi sử dụng |
|---|---:|---|---|
| `INFERENCE_INTERVAL_SECONDS` | `0.25` | `detection/webcam_detect.py`, `ui/webcam_controller.py` | Khoảng cách giữa 2 lần YOLO inference |
| `HISTORY_COOLDOWN_SECONDS` | `5.0` | `detection/webcam_detect.py`, `ui/webcam_controller.py` | Cooldown lưu history theo class |

## 11. Runtime Dependency Graph

```text
AuthController
  |
  v
database.auth
  |
  v
database.db
  |
  v
PostgreSQL/Supabase

ImageController
  |
  v
ImageDetectThread
  |
  v
detection.image_detect.detect_image
  |
  +--> ObjectDetector
  |     |
  |     v
  |   YOLO
  |
  +--> detection.classify.classify_word
  |     |
  |     +--> dataset.vocabulary
  |     └--> ml.category_predictor
  |
  +--> database.history.save_history
  |
  +--> utils.helper.draw_vietnamese_text
  |
  v
ImageController._on_results_ready
  |
  +--> ml.knn.get_related_words
  └--> ml.kmeans.get_words_in_same_cluster

WebcamController
  |
  v
WebcamThread
  |
  +--> ObjectDetector
  +--> detection.classify
  +--> ml.knn
  +--> ml.kmeans
  +--> database.history
  +--> utils.helper
  └--> ui.qt_utils

HistoryController
  |
  v
HistoryWorker
  |
  v
database.history.get_history / clear_history

StatsController
  |
  v
StatsWorker
  |
  v
database.history.get_history
```

## 12. Import Graph

```text
main.py
└── utils.console
└── ui.main_qt
    ├── PySide6
    ├── detection.detector
    │   ├── ultralytics.YOLO
    │   ├── dataset.coco_classes
    │   └── utils.config
    ├── ui.auth_controller
    │   └── database.auth
    │       └── database.db
    ├── ui.history_controller
    │   └── database.history
    │       └── database.db
    ├── ui.image_controller
    │   ├── detection.image_detect
    │   │   ├── detection.detector
    │   │   ├── detection.classify
    │   │   │   ├── dataset.vocabulary
    │   │   │   └── ml.category_predictor
    │   │   └── database.history
    │   ├── ml.knn
    │   ├── ml.kmeans
    │   ├── ui.qt_utils
    │   └── ui.speech_worker
    ├── ui.stats_controller
    │   └── database.history
    ├── ui.video_item
    ├── ui.vocabulary_controller
    │   ├── dataset.vocabulary
    │   ├── ml.knn
    │   ├── ml.kmeans
    │   └── ui.speech_worker
    └── ui.webcam_controller
        ├── database.history
        ├── detection.classify
        ├── ml.knn
        ├── ml.kmeans
        ├── ui.qt_utils
        ├── utils.config
        └── utils.helper
```

## 13. Communication Graph

### 13.1 Controller Với Controller

| Source controller/module | Target controller | Cơ chế | Source code |
|---|---|---|---|
| `AuthController` | `ImageController` | `userChanged` signal -> `apply_current_user()` -> `set_user_id()` | `ui.main_qt.run()` |
| `AuthController` | `WebcamController` | `userChanged` signal -> `set_user_id()` hoặc `stop()` khi logout | `ui.main_qt.run()` |
| `AuthController` | `HistoryController` | `userChanged` signal -> `set_user_id()`, `refresh()` khi login | `ui.main_qt.run()` |
| `AuthController` | `StatsController` | `userChanged` signal -> `set_user_id()`, `refresh()` khi login, `clear()` khi logout | `ui.main_qt.run()` |
| `ImageController` | `HistoryController` | QML `onResultsChanged` gọi `historyController.refresh()` | `CameraPage.qml` |
| `ImageController` | `StatsController` | QML `onResultsChanged` gọi `statsController.refresh()` | `CameraPage.qml` |
| `WebcamController` | `HistoryController` | QML `onHistorySaved` gọi `historyController.refresh()` | `CameraPage.qml` |
| `WebcamController` | `StatsController` | QML `onHistorySaved` gọi `statsController.refresh()` | `CameraPage.qml` |
| `HistoryController` | `StatsController` | QML clear history xong gọi `statsController.refresh()` | `HistoryPage.qml` |

### 13.2 Module Với Module

| Module | Giao tiếp runtime với | Mục đích |
|---|---|---|
| `ui` | `detection` | Detect ảnh/webcam |
| `ui` | `ml` | Lấy related words và cluster words |
| `ui` | `database` | Auth, history, stats |
| `detection` | `dataset` | Class filter và vocabulary lookup |
| `detection` | `database` | Lưu history |
| `detection` | `ml.category_predictor` | Fallback category |
| `ml` | `dataset/vocabulary.csv` | Build feature và lookup |
| `ml` | `models/*.pkl` | Load/train cache model |
| `database` | PostgreSQL/Supabase | Query/insert/update/delete |
| `utils` | `assets` | Font/audio resources |

### 13.3 Giao Tiếp Vòng Tròn

```text
QML CameraPage
  -> ImageController resultsChanged
  -> QML onResultsChanged
  -> HistoryController.refresh()
  -> HistoryWorker.loaded
  -> HistoryModel update
  -> QML HistoryPage/ListView
```

```text
QML CameraPage
  -> WebcamController historySaved
  -> QML onHistorySaved
  -> HistoryController.refresh()
  -> StatsController.refresh()
```

Không tìm thấy import vòng tròn trực tiếp giữa các package chính trong các đường runtime đã khảo sát. Có giao tiếp vòng qua QML event handler giữa controller detection và controller history/stats.

### 13.4 Module Được Nhiều Nơi Phụ Thuộc

| Module/Object | Nơi phụ thuộc runtime |
|---|---|
| `ObjectDetector` | `ImageController`, `WebcamController`, `detection.image_detect`, `detection.webcam_detect`, test scripts |
| `database.history` | Image detection, webcam detection, history UI, statistics UI |
| `dataset.vocabulary` | classification, vocabulary UI, k-NN, K-Means, features |
| `ml.knn` | image UI, webcam UI, vocabulary UI, evaluate/test |
| `ml.kmeans` | image UI, webcam UI, vocabulary UI, evaluate/test |
| `utils.config` | detector, webcam, helper, speech |

## 14. Lifecycle

### 14.1 Application

```text
Process start
  |
  v
main()
  |
  v
QApplication + controllers + QML
  |
  v
app.exec()
  |
  v
aboutToQuit -> webcam_controller.stop()
  |
  v
Process exit
```

### 14.2 Controller

| Controller | Tạo | Hủy | Lifecycle note |
|---|---|---|---|
| `AuthController` | `ui.main_qt.run()` | App exit | Giữ trạng thái login/current user |
| `ImageController` | `ui.main_qt.run()` | App exit | Giữ selected image, results, related, cluster |
| `WebcamController` | `ui.main_qt.run()` | App exit | Tạo/hủy `WebcamThread` theo user action |
| `HistoryController` | `ui.main_qt.run()` | App exit | Giữ `HistoryModel`, tạo worker theo refresh |
| `StatsController` | `ui.main_qt.run()` | App exit | Tạo worker theo refresh |
| `VocabularyController` | `ui.main_qt.run()` | App exit | Load vocabulary vào `VocabularyModel` khi tạo |

### 14.3 YOLO Model

```text
ui.main_qt.run()
  |
  v
ObjectDetector()
  |
  v
YOLO(models/best.pt)
  |
  v
Dùng chung trong ImageController và WebcamController
  |
  v
Hủy khi process/app kết thúc
```

### 14.4 Database Connection

```text
Mỗi DB operation
  |
  v
database_cursor()
  |
  v
get_connection()
  |
  v
cursor()
  |
  v
execute/fetch
  |
  v
commit hoặc rollback
  |
  v
cursor.close()
connection.close()
```

### 14.5 Webcam

```text
User bấm Bật Camera
  |
  v
WebcamController.start()
  |
  v
WebcamThread.start()
  |
  v
cv2.VideoCapture
  |
  v
Loop đọc frame
  |
  v
User bấm Tắt Camera hoặc app quit
  |
  v
WebcamThread.stop()
  |
  v
camera.release()
```

### 14.6 History Worker

```text
historyController.refresh() hoặc clearHistory()
  |
  v
HistoryWorker(clear_first)
  |
  v
worker.start()
  |
  v
clear_history nếu clear_first
  |
  v
get_history
  |
  v
loaded(rows)
  |
  v
_on_finished -> _worker=None
```

### 14.7 Speech Worker

```text
imageController.speak(word) hoặc vocabController.speak(word)
  |
  v
QThreadPool.globalInstance().start(SpeakTask(word))
  |
  v
SpeakTask.run()
  |
  v
utils.speech.speak(word)
  |
  v
gTTS save assets/audio/speech.mp3
  |
  v
open_audio_file(speech.mp3)
  |
  v
Task kết thúc
```

## 15. Risk Map

| Tình huống | Source path liên quan | Runtime behavior theo source |
|---|---|---|
| Thiếu `models/best.pt` | `ui.main_qt.run()` -> `ObjectDetector()` | Exception khi load YOLO được catch, in `"Không thể tải mô hình YOLO: {error}"`, sau đó `raise`; app không tiếp tục load QML |
| YOLO load lỗi | `ui.main_qt.run()` | Giống thiếu `best.pt`: raise exception trước khi GUI chạy |
| YOLO không detect object | `ObjectDetector.detect()` trả `[]`; `detect_image()` trả ảnh và results rỗng | Image UI set related/cluster rỗng và status `"Không phát hiện vật thể nào."`; webcam emit status `"Chưa phát hiện vật thể."` và related/cluster rỗng |
| Class YOLO không nằm trong `COCO_CLASSES` | `ObjectDetector.detect()` | Object bị `continue`, không vào results |
| `vocabulary.csv` thiếu | `dataset.vocabulary._load()`, `ml.knn.read_vocabulary()`, `ml.kmeans.read_vocabulary()` | Lookup vocabulary sẽ raise FileNotFoundError khi mở file; k-NN/K-Means raise FileNotFoundError; ImageDetectThread catch exception và emit failed; webcam không có try/except quanh toàn bộ loop ngoài finally nên exception trong loop sẽ kết thúc thread |
| `vocabulary.csv` thiếu cột | `ml.knn.read_vocabulary()`, `ml.kmeans.read_vocabulary()` | Raise ValueError khi load/train ML |
| Từ không có trong vocabulary | `classify_word()`, `get_related_words()`, `get_words_in_same_cluster()` | `classify_word` trả Vietnamese `None`, category từ `predict_category` hoặc `Unknown`; k-NN trả `[]`; K-Means trả `[]` |
| Database mất kết nối khi login | `AuthController.login()` -> `verify_login()` | Exception được catch trong `AuthController.login()`, status message `"Không thể đăng nhập: {error}"`, loading false |
| Database mất kết nối khi register | `AuthController.register()` | Exception được catch, status message `"Không thể tạo tài khoản: {error}"`, loading false |
| Database mất kết nối khi save history ảnh | `database.history.save_history()` | Exception được catch trong `save_history`, in lỗi và trả `False`; detection tiếp tục vẽ/return result |
| Database mất kết nối khi history refresh | `database.history.get_history()` | Exception được catch trong `get_history`, in lỗi và trả `[]`; HistoryWorker emit loaded với list rỗng nếu không có exception ngoài |
| Database mất kết nối khi stats refresh | `get_history()` trả `[]` nếu lỗi | StatsWorker tính stats rỗng và emit loaded với total 0 |
| Webcam không mở được | `WebcamThread.run()` | Emit status `"Không mở được webcam."`, return khỏi thread; `finished` làm controller set `_running=False` |
| Webcam đọc frame lỗi | `WebcamThread.run()` | Nếu `success=False` thì `continue`; không emit frame mới |
| Queue lưu history webcam đầy | `WebcamThread._save_history_if_allowed()` | Catch `queue.Full`, increment perf counter, bỏ record đó |
| Thiếu font `NotoSans-Regular.ttf` | `utils.helper.get_font()` | In thông báo và dùng `ImageFont.load_default()` |
| gTTS lỗi hoặc mất mạng | `utils.speech.phat_am()` | Raise RuntimeError; `SpeakTask.run()` catch và print lỗi |
| File audio không tồn tại khi mở | `utils.speech.open_audio_file()` | Raise FileNotFoundError; nếu qua `SpeakTask`, exception được catch và print |
| KNN pickle thiếu/hết hạn | `ml.knn.load_knn_model()` | Train lại bằng `train_knn_model()` |
| KMeans pickle thiếu/hết hạn | `ml.kmeans.load_kmeans_model()` | Train lại bằng `train_kmeans_model()` |
| Vocabulary quá ít cho k-NN | `train_knn_model()` | Nếu dưới 2 từ, raise ValueError |
| Vocabulary quá ít cho K-Means | `train_kmeans_model()` | Nếu dưới 3 từ, raise ValueError |

