# CODE REVIEW REPORT - AI-English

Phạm vi: đánh giá chất lượng source code theo Clean Code, Clean Architecture, SOLID, DRY, KISS, YAGNI, Python best practice, ML project structure, GUI architecture, thread safety.

Quy tắc áp dụng: không sửa code, không refactor, không tối ưu, không commit. Báo cáo chỉ dựa trên source code hiện tại.

## 1. Code Smell

### 1.1 Findings Theo Severity

| Severity | Vấn đề | Dẫn chứng | Nhận xét |
|---|---|---|---|
| Critical | Secret database nằm trong workspace | `.env` chứa `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT` | Credential runtime có trong file local. Nếu file này bị commit/chia sẻ thì lộ database. |
| High | GUI controller gọi AI/ML trực tiếp | `ui/image_controller.py:225`, `ui/image_controller.py:257`, `ui/image_controller.py:261` | `ImageController._on_results_ready()` format UI state đồng thời gọi k-NN và K-Means. |
| High | Webcam thread dùng chung `ObjectDetector` với image detection không có lock | `ui/main_qt.py:72`, `ui/main_qt.py:76`, `ui/webcam_controller.py:290`, `ui/image_controller.py:39` | Cùng instance detector được truyền cho `ImageController` và `WebcamController`; cả hai có thể gọi `detector.detect()` từ thread khác nhau. |
| High | `WebcamThread` là long class/gần God Object | `ui/webcam_controller.py:31` đến `ui/webcam_controller.py:358` | Class xử lý camera, YOLO, classify, history queue, KNN, KMeans, drawing, QImage signal. |
| High | Database schema/migration không có trong source | `database/auth.py`, `database/history.py` chỉ có SQL runtime | Source dùng bảng `users` và `history`, nhưng không có file tạo bảng/quan hệ. |
| High | Category model artifact không được load | `models/word_category_model.joblib`; `ml/category_predictor.py:9` | `predict_category()` chỉ lookup vocabulary và trả `Unknown`, không dùng file category model. |
| Medium | Duplicate feature engineering | `ml/features.py:89`, `ml/knn.py:144`, `ml/kmeans.py:140` | `read_vocabulary()` và `build_features()` bị lặp giữa 3 module. |
| Medium | Duplicate webcam flow | `detection/webcam_detect.py:16`, `ui/webcam_controller.py:259` | Có hai implementation webcam: OpenCV window trực tiếp và GUI thread. |
| Medium | Long function | `ui/main_qt.py:54` đến `ui/main_qt.py:181` | `run()` tạo app, model, controller, user binding, QML context, load engine. |
| Medium | Long function | `ml/knn.py:356` đến `ml/knn.py:451` | `get_related_words()` normalize input, load model, query feature, scale, weight, kneighbors, format output. |
| Medium | Long function | `ml/kmeans.py:243` đến `ml/kmeans.py:338` | `train_kmeans_model()` đọc data, chọn K, build feature, scale, train, metric, dump model. |
| Medium | Long function | `ml/kmeans.py:341` đến `ml/kmeans.py:432` | `load_kmeans_model()` xử lý cache, file model, version validation, fallback train. |
| Medium | Long function | `database/history.py:84` đến `database/history.py:166` | `get_history()` vừa build SQL, query, handle exception, format row dict. |
| Medium | Magic number | `ui/webcam_controller.py:25`, `ui/webcam_controller.py:26` | `0.25`, `5.0` được khai báo hằng trong module; có duplicate với `detection/webcam_detect.py`. |
| Medium | Magic number/model constants duplicate | `ml/knn.py:47`, `ml/kmeans.py:47`, `ml/knn.py:54`, `ml/kmeans.py:54` | `MODEL_VERSION`, feature weights và mappings lặp giữa KNN/KMeans. |
| Medium | Hard-coded dataset path ngoài repo | `dataset/prepare_dataset.py:14` | `COCO_ROOT = Path(r"D:\Dataset\coco2017_subset")`. |
| Medium | Hard-coded output dataset path trong YAML | `dataset/dataset.yaml` | `path: D:/DEV/Projects/AI-English/dataset/yolo_dataset`. |
| Medium | QML controller communication qua global context | `ui/main_qt.py:140` đến `ui/main_qt.py:164`, `ui/qml/CameraPage.qml` | QML trực tiếp gọi nhiều controller và điều phối refresh history/stats. |
| Medium | Blocking DB call trong auth controller main thread | `ui/auth_controller.py:99`, `ui/auth_controller.py:148`, `ui/auth_controller.py:216` | Login/register/change password gọi DB trực tiếp từ slot UI, không dùng worker thread. |
| Medium | Speech tasks ghi chung một file | `utils/config.py:62`, `utils/speech.py:35` | Mọi phát âm ghi vào `assets/audio/speech.mp3`; nhiều SpeakTask song song có thể ghi đè. |
| Medium | Exception handling bằng `print` thay vì logging | `database/auth.py:82`, `database/history.py:75`, `utils/translator.py:54`, `ui/speech_worker.py:25` | Runtime error được in console, không có structured logging. |
| Low | README quá ngắn | `README.md` | Không có hướng dẫn runtime, database, model, test. |
| Low | Unused dependency theo source | `requirements.txt` có `pyttsx3`, `openpyxl` | Không tìm thấy import trực tiếp trong source hiện tại. |
| Low | UI vocabulary controller chưa thấy màn hình QML dùng trực tiếp | `ui/vocabulary_controller.py:107`, `ui/qml/Main.qml` | Controller được expose nhưng navigation không có Vocabulary page. |
| Low | Comment/encoding tiếng Việt bị mojibake khi đọc console hiện tại | Nhiều file có chuỗi hiển thị lỗi encoding khi `Get-Content` | Nội dung source có text tiếng Việt nhưng console hiện tại hiển thị sai encoding. |
| Low | Test scripts không thống nhất style unit test | `test/test_connection.py`, `test/test_login.py`, `test/test_ml.py` | Nhiều file in console/chạy trực tiếp, ít assertion tự động. |
| Low | TODO/FIXME/HACK | Không tìm thấy TODO/FIXME/HACK rõ ràng trong source đã quét | Không tìm thấy trong source code hiện tại. |

### 1.2 Long Class / Long Function

| Loại | File | Item | Số dòng xấp xỉ |
|---|---|---|---:|
| Long Class | `ui/webcam_controller.py` | `WebcamThread` | 328 |
| Long Class | `ui/auth_controller.py` | `AuthController` | 261 |
| Long Class | `ui/image_controller.py` | `ImageController` | 247 |
| Long Class | `ui/history_controller.py` | `HistoryController` | 154 |
| Long Function | `ui/main_qt.py` | `run()` | 128 |
| Long Function | `ml/kmeans.py` | `train_kmeans_model()` | 96 |
| Long Function | `ml/knn.py` | `get_related_words()` | 96 |
| Long Method | `ui/webcam_controller.py` | `WebcamThread.run()` | 96 |
| Long Function | `ml/kmeans.py` | `load_kmeans_model()` | 92 |
| Long Function | `dataset/prepare_dataset.py` | `prepare_coco_records()` | 84 |
| Long Function | `database/history.py` | `get_history()` | 83 |

### 1.3 Dead Code / Unused Artifacts

| Item | Dẫn chứng | Trạng thái |
|---|---|---|
| `models/word_category_model.joblib` | `ml/category_predictor.py` không load joblib | Không tìm thấy nơi sử dụng trong source code hiện tại |
| `pyttsx3` | Có trong `requirements.txt` | Không tìm thấy import trong source code hiện tại |
| `openpyxl` | Có trong `requirements.txt` | Không tìm thấy import trực tiếp trong source code hiện tại |
| `LEVELS`, `DEFAULT_LANGUAGE`, `TEST_IMAGE_PATH` | `utils/config.py` | Không tìm thấy runtime usage trong source code đã khảo sát |
| `VocabularyController` | Expose trong `ui/main_qt.py`, không thấy QML page vocabulary | Có thể chưa được nối vào UI hiện tại |

## 2. SOLID

Điểm: 1 = yếu, 5 = tốt theo source hiện tại.

| Class | SRP | OCP | LSP | ISP | DIP | Giải thích ngắn |
|---|---:|---:|---:|---:|---:|---|
| `ObjectDetector` | 4 | 3 | 4 | 4 | 2 | Tập trung YOLO detect; phụ thuộc trực tiếp `ultralytics.YOLO` và config global. |
| `AuthController` | 3 | 3 | 4 | 3 | 2 | Controller UI kiêm validation và gọi DB auth trực tiếp. |
| `HistoryModel` | 5 | 4 | 4 | 4 | 4 | Chỉ làm list model cho QML history. |
| `HistoryWorker` | 4 | 3 | 4 | 4 | 2 | Worker đọc/xóa history, phụ thuộc trực tiếp DB function. |
| `HistoryController` | 3 | 3 | 4 | 3 | 2 | Quản lý model, worker, format row và status UI. |
| `ImageDetectThread` | 4 | 3 | 4 | 4 | 3 | Worker detect ảnh; nhận detector injection nhưng gọi use-case trực tiếp. |
| `ImageController` | 2 | 2 | 4 | 3 | 2 | Chọn file, preview, detect, format result, gọi KNN/KMeans/speech. |
| `SpeakTask` | 5 | 4 | 4 | 4 | 3 | Chỉ chạy speech trong background. |
| `StatsWorker` | 3 | 3 | 4 | 4 | 2 | Đọc DB và tính aggregate trong cùng worker. |
| `StatsController` | 4 | 3 | 4 | 4 | 3 | Điều phối stats worker và emit stats. |
| `VideoItem` | 5 | 4 | 4 | 4 | 4 | Chỉ paint QImage. |
| `VocabularyModel` | 4 | 3 | 4 | 4 | 3 | Model vocabulary + filter. |
| `VocabularyController` | 3 | 3 | 4 | 3 | 2 | Expose vocabulary, speech, KNN, KMeans trực tiếp. |
| `WebcamThread` | 1 | 2 | 4 | 2 | 1 | Nhiều trách nhiệm: camera, YOLO, DB queue, ML, drawing, signal. |
| `WebcamController` | 3 | 3 | 4 | 3 | 2 | Quản lý thread và state webcam; phụ thuộc concrete thread/detector. |

### 2.1 Nhận Xét SOLID Theo Nguyên Tắc

| Nguyên tắc | Tình trạng theo source |
|---|---|
| Single Responsibility | Các model nhỏ như `HistoryModel`, `VideoItem`, `SpeakTask` tốt. Các controller lớn và `WebcamThread` làm nhiều việc. |
| Open/Closed | Các module dùng function trực tiếp và config global; thay thế backend/model cần sửa nhiều điểm. |
| Liskov Substitution | Các class Qt kế thừa đúng base class, không thấy override trái contract rõ ràng. |
| Interface Segregation | Không có interface/protocol rõ; QML nhận controller lớn với nhiều slot/property. |
| Dependency Inversion | Phụ thuộc concrete module/function nhiều: DB, ML, YOLO, config global. `ImageDetectThread` có injection detector là điểm tốt. |

## 3. Clean Architecture

### 3.1 Layer Hiện Tại

| Layer | Module | Tách biệt theo source |
|---|---|---|
| Presentation | `ui/*.py`, `ui/qml/*.qml` | Có tách QML và controller |
| AI Detection | `detection/*` | Có module riêng cho YOLO/classify/image/webcam |
| ML | `ml/*` | Có module riêng cho KNN/KMeans/features |
| Data/Vocabulary | `dataset/*` | Có data access CSV và constants |
| Database | `database/*` | Có DB access/auth/history |
| Utility | `utils/*` | Có config/helper/speech/translator/perf |
| Use Case/Business | Không có package riêng | Logic use-case nằm trong controller, detection function và ML function |

### 3.2 Module Làm Quá Nhiều Việc

| Module/Class | Việc đang làm |
|---|---|
| `ui/webcam_controller.py::WebcamThread` | Camera capture, YOLO inference, format detection, save history queue, KNN, KMeans, draw frame, emit GUI signal |
| `ui/image_controller.py::ImageController` | File dialog, image preview, thread management, result formatting, KNN, KMeans, speech |
| `detection/image_detect.py::detect_image` | Read image, detect, classify, save DB, draw UI label |
| `ui/main_qt.py::run` | Bootstrap app, model, controllers, user lifecycle, QML engine |
| `ml/knn.py` và `ml/kmeans.py` | Data loading, feature engineering, model cache, training, inference cùng module |

### 3.3 Coupling Cao Theo Layer

| Source | Coupled tới |
|---|---|
| `ui` | `detection`, `ml`, `database`, `utils`, `PySide6`, `cv2` |
| `detection.image_detect` | `cv2`, `database`, `classify`, `detector`, `utils.helper` |
| `ui.webcam_controller` | `cv2`, `database`, `detection`, `ml`, `utils`, `PySide6`, `queue`, `threading` |
| `ml.knn`/`ml.kmeans` | `dataset/vocabulary.csv`, `joblib`, `sklearn`, `pandas`, `numpy`, `utils.perf_monitor` |

## 4. Coupling

### 4.1 Module Phụ Thuộc Nhiều Nhất Theo Import

| File | Số nhóm import khác nhau | Nhóm phụ thuộc chính |
|---|---:|---|
| `ui/main_qt.py` | 16 | Qt, detector, toàn bộ controller |
| `ui/webcam_controller.py` | 15 | Qt, cv2, DB, detection, ML, utils, threading |
| `test/test_kmeans.py` | 15 | sklearn, matplotlib, pandas, numpy, joblib |
| `ml/kmeans.py` | 13 | sklearn, pandas, numpy, joblib, utils |
| `ml/knn.py` | 12 | sklearn, pandas, numpy, joblib, utils |
| `ui/image_controller.py` | 10 | Qt, cv2, detection, ML, speech |

### 4.2 Class Phụ Thuộc Nhiều Nhất

| Class | Runtime dependencies |
|---|---|
| `WebcamThread` | detector, OpenCV camera, classify, KNN, KMeans, history DB, queue/threading, QImage conversion, drawing helper |
| `ImageController` | QFileDialog, OpenCV, ImageDetectThread, KNN, KMeans, speech worker, QImage conversion |
| `AuthController` | database auth functions, Qt signals/properties |
| `HistoryController` | HistoryModel, HistoryWorker, DB history functions |
| `StatsWorker` | DB history, Counter aggregation |

### 4.3 Circular Dependency

| Loại | Kết quả |
|---|---|
| Circular import trực tiếp | Không tìm thấy trong các đường import chính đã khảo sát |
| Communication loop runtime qua QML | Có: detection result -> QML handler -> history/stats refresh -> QML model update |
| Shared service vòng qua function | Không tìm thấy circular dependency rõ trong source code hiện tại |

## 5. Cohesion

### 5.1 Cohesion Cao

| Module/Class | Lý do |
|---|---|
| `database/db.py` | Chỉ quản lý connection/cursor |
| `database/auth.py` | Tập trung vào user auth/password |
| `database/history.py` | Tập trung vào CRUD history |
| `detection/detector.py` | Tập trung vào YOLO inference |
| `dataset/vocabulary.py` | Tập trung CSV vocabulary lookup |
| `utils/console.py` | Chỉ xử lý UTF-8 console |
| `utils/perf_monitor.py` | Chỉ instrumentation perf |
| `ui/video_item.py` | Chỉ paint QImage |

### 5.2 Cohesion Thấp / Pha Trộn Trách Nhiệm

| Module/Class | Lý do |
|---|---|
| `ui/webcam_controller.py::WebcamThread` | Camera, AI, DB, ML, drawing, threading trong cùng class |
| `ui/image_controller.py::ImageController` | UI state, file dialog, ML post-processing, speech |
| `detection/image_detect.py` | Detection use-case gắn DB và drawing |
| `ml/knn.py`, `ml/kmeans.py` | Data loading + feature + training + inference + persistence trong cùng module |
| `dataset/prepare_dataset.py` | Script hợp lý cho CLI, nhưng nhiều bước prepare nằm trong một file lớn |

## 6. Controller Review

| Controller | Làm quá nhiều việc? | Gọi AI trực tiếp? | Xử lý DB trực tiếp? | Vi phạm MVC theo source |
|---|---|---|---|---|
| `AuthController` | Trung bình | Không | Có, qua `database.auth` | Controller gọi DB/auth service trực tiếp và validate input |
| `ImageController` | Có | Có, gọi k-NN/K-Means; detect qua thread | Gián tiếp qua `detect_image()` lưu history | Controller chứa post-processing AI và formatting UI |
| `WebcamController` | Trung bình | Thread của nó gọi YOLO/KNN/KMeans | Thread của nó lưu history | Controller/thread trộn camera, AI, DB, UI signal |
| `HistoryController` | Trung bình | Không | Có qua `HistoryWorker` | Controller quản lý worker và format dữ liệu view |
| `StatsController` | Trung bình | Không | Có qua `StatsWorker` | Worker vừa query DB vừa tính aggregate |
| `VocabularyController` | Trung bình | Có, gọi KNN/KMeans | Không | Controller gọi ML trực tiếp |

## 7. AI Module Review

| Module AI | Tách riêng? | Phụ thuộc GUI? | Phụ thuộc Database? | Nhận xét theo source |
|---|---|---|---|---|
| YOLO / `ObjectDetector` | Có | Không | Không | `detection/detector.py` độc lập với GUI/DB, phụ thuộc config global và `ultralytics`. |
| `detection.image_detect` | Một phần | Không import GUI, nhưng có drawing UI label | Có | Use-case ảnh tĩnh gắn detection với DB history và drawing. |
| k-NN / `ml.knn` | Có | Không | Không | Tách khỏi GUI/DB; nhưng tự đọc CSV, train, cache, infer trong cùng module. |
| K-Means / `ml.kmeans` | Có | Không | Không | Tách khỏi GUI/DB; tự đọc CSV, train, cache, infer trong cùng module. |
| Category Predictor | Có module riêng | Không | Không | Không dùng artifact `word_category_model.joblib`; chỉ lookup vocabulary. |

## 8. Database Review

| Hạng mục | Source | Đánh giá |
|---|---|---|
| Connection | `database/db.py:get_connection()` | Mỗi operation mở connection mới bằng `psycopg2.connect`. |
| Cursor | `database/db.py:database_cursor()` | Cursor tạo trong context manager và đóng trong `finally`. |
| Transaction commit | `database_cursor(commit=True)` | Commit khi `commit=True`; dùng cho insert/update/delete. |
| Rollback | `database_cursor()` | Rollback trong `except Exception`. |
| Connection leak | `finally` đóng cursor/connection | Không thấy leak rõ nếu `get_connection()` thành công. Nếu `get_connection()` fail trước `connection` assignment thì context không vào phần close. |
| Exception | `auth.py` một số hàm re-raise; `history.py` catch và trả `False`/`[]` | Hành vi exception không thống nhất giữa auth và history. |
| Schema | Không có migration/schema | Bảng `users`, `history` chỉ suy ra từ query runtime. |
| SQL injection | Query dùng placeholder `%s` | Các query chính dùng parameterized SQL. |
| Pooling | Không có | Mỗi lần mở/đóng connection riêng. |

## 9. Thread Review

| Thread | Race Condition | Deadlock | Shared State | Thread-safe mechanism | Signal/Slot |
|---|---|---|---|---|---|
| Main Qt Thread | Nhận state update từ workers | Không thấy deadlock rõ | Controller fields | Qt event loop | Có |
| `ImageDetectThread` | Có thể gọi chung detector với webcam | Không thấy wait chéo | `detector` shared | Không có lock | `image_ready`, `results_ready`, `failed` |
| `WebcamThread` | `_running` đổi từ controller thread; detector shared | `stop()` gọi `wait(3000)`, không thấy lock chéo | `_running`, detector, caches, `_last_results` | Một số state chỉ trong worker; detector không lock | Nhiều signal |
| `webcam-history-writer` | Signal emit từ Python thread phụ; audio không liên quan | Join timeout 1s; nếu queue full stop token có thể không vào queue | `_history_queue`, DB function | `queue.Queue` thread-safe | Emit `history_saved` |
| `HistoryWorker` | Controller chặn worker song song | Không thấy | `_worker`, model rows sau loaded | QThread signal | `loaded`, `failed` |
| `StatsWorker` | Controller chặn worker song song | Không thấy | `_worker` | QThread signal | `loaded`, `failed` |
| `SpeakTask` | Nhiều task ghi chung `speech.mp3` | Không thấy | `assets/audio/speech.mp3` | Không có lock | Không emit signal |

## 10. Resource Review

| Resource | Quản lý hiện tại | Nhận xét |
|---|---|---|
| YOLO weight `models/best.pt` | Load khi app start | Nếu thiếu/lỗi thì app raise trước khi load UI. |
| `models/knn.pkl` | Load lazy khi gọi KNN; train lại nếu invalid | Có cache `_MODEL_CACHE`; phụ thuộc sklearn version. |
| `models/kmeans.pkl` | Load lazy khi gọi KMeans; train lại nếu invalid | Có cache `_MODEL_CACHE`; phụ thuộc sklearn version. |
| `models/word_category_model.joblib` | Không tìm thấy nơi load | Artifact chưa nối runtime. |
| `dataset/vocabulary.csv` | Load bằng csv hoặc pandas | Không có schema object riêng; lỗi file/cột sẽ raise ở ML. |
| `assets/audio/speech.mp3` | Ghi đè mỗi lần phát âm | Không có per-word/per-task file. |
| `assets/fonts/NotoSans-Regular.ttf` | Fallback default font nếu thiếu | Có handling nếu font thiếu. |
| Database connection | Mở/đóng mỗi operation | Không có pool, nhưng context manager đóng connection. |
| Test images | Đọc trực tiếp từ folder | Không có ground truth đi kèm trong source hiện tại. |

## 11. Test Review

| Loại test | File | Tình trạng |
|---|---|---|
| DB connection test | `test/test_connection.py` | Script connect DB và print version, không phải unit test tự động có assertion. |
| Login test | `test/test_login.py` | Gọi `login_user` và print user. |
| ML smoke test | `test/test_ml.py` | Gọi KMeans/KNN và print. |
| KNN experiment | `test/test_knn.py` | Có logic đánh giá và lưu report CSV/TXT. |
| KMeans experiment | `test/test_kmeans.py` | Có logic đánh giá K, vẽ PNG. |
| YOLO image test | `test/test_yolo_image.py` | CLI detect ảnh/folder, print kết quả. |
| System evaluation | `test/test_system_evaluation.py` | Chạy YOLO+KNN+KMeans trên test_images và lưu report. |
| GUI test | Không tìm thấy | Không tìm thấy trong source code hiện tại. |
| Unit test theo pytest/unittest | Không thấy structure/assertion đầy đủ | Không tìm thấy trong source code hiện tại. |
| Coverage config/report | Không tìm thấy | Không tìm thấy trong source code hiện tại. |

Thiếu test theo source hiện tại:

- Unit test cho `dataset.vocabulary`.
- Unit test cho `classify_word`.
- Unit test cho DB layer bằng mock connection.
- Unit test cho `ObjectDetector.detect` bằng mock YOLO output.
- Test thread lifecycle cho webcam/history/stats.
- Test GUI/QML flow.
- Test failure path: thiếu model, thiếu vocabulary, DB down, webcam unavailable.
- Ground truth detection test để tính precision/recall/mAP.

## 12. Performance Review

| Khu vực | Dẫn chứng | Bottleneck tiềm năng |
|---|---|---|
| App startup | `ui/main_qt.py:66` | YOLO load xảy ra trước khi QML hiển thị; UI không hiện nếu model load chậm/lỗi. |
| YOLO inference | `detection/detector.py:18` | Inference là bước nặng nhất; webcam gọi mỗi 0.25 giây. |
| Webcam drawing | `ui/webcam_controller.py:231` | Mỗi frame vẽ text bằng PIL qua `draw_vietnamese_text`, có convert BGR/RGB. |
| QImage conversion | `ui/qt_utils.py:10` | Mỗi frame webcam convert BGR->RGB, contiguous, QImage copy. |
| DB connection | `database/db.py:14` | Mỗi query mở connection mới, không có pooling. |
| Auth DB calls | `ui/auth_controller.py` | Login/register/change password chạy trong UI slot, có thể block UI. |
| KNN/KMeans first call | `ml/knn.py:288`, `ml/kmeans.py:341` | Lazy load hoặc train lại model khi pickle invalid; có thể xảy ra trên UI path. |
| Vocabulary CSV read | `ml/knn.py:75`, `ml/kmeans.py:71` | `load_*_model()` đọc CSV để check mtime/expected clusters. |
| Speech | `utils/speech.py:28` | gTTS network call chạy trong `SpeakTask`, không block UI nhưng phụ thuộc mạng. |
| Perf monitor | `utils/perf_monitor.py` | Có instrumentation optional qua `AI_ENGLISH_PERF=1`. |

## 13. Security Review

| Hạng mục | Dẫn chứng | Nhận xét |
|---|---|---|
| Password hashing | `database/auth.py:21` | Dùng bcrypt cho đăng ký và migrate plain text khi login. |
| Plain text password legacy | `database/auth.py:51`, `database/auth.py:174` | `_verify_password` chấp nhận plain text password cũ và update sang bcrypt sau login. |
| SQL injection | `database/auth.py`, `database/history.py` | Query dùng `%s` parameter binding, không thấy string interpolation với user input trong SQL. |
| Credentials | `.env` | Có DB credential trong workspace. |
| Secret logging | `AuthController.login` print username | Không print password; username được log ra console. |
| DB errors | `print(f"...{error}")` | DB error có thể lộ chi tiết connection/schema qua UI status hoặc console. |
| Audio file writing | `assets/audio/speech.mp3` | Ghi file cố định trong workspace. |
| Pickle/joblib model loading | `ml/knn.py`, `ml/kmeans.py`, `test/test_kmeans.py` | `joblib.load` trên model file local; pickle/joblib không an toàn nếu artifact không tin cậy. |
| Environment management | `database/db.py` | Dùng `python-dotenv`; không có validation missing env trước connect. |

## 14. Python Style

| Hạng mục | Tình trạng theo source |
|---|---|
| PEP8 line length | Nhiều file format line ngắn; QML không áp dụng PEP8. Không chạy linter trong phase này. |
| Type hints | Có ở nhiều module mới (`database`, `ml`, `ui`), nhưng một số function thiếu type hint như `classify_word`, `detect_image`, `ObjectDetector.detect`. |
| Naming | Python function/class naming nhìn chung theo snake_case/PascalCase; một số tên tiếng Việt như `phat_am`, `dich_tu`, `xu_ly_all` tồn tại trong utils. |
| Module structure | Có package rõ: `database`, `dataset`, `detection`, `ml`, `ui`, `utils`, `test`. |
| Import order | Không thấy chuẩn hóa tuyệt đối theo stdlib/third-party/local ở mọi file; nhiều file tương đối rõ. |
| Exception handling | Có try/except ở DB/history/speech/UI worker; logging chủ yếu là `print`. |
| Logging | Không dùng `logging` module. |
| Comments | Có comment tiếng Việt mô tả pipeline; một số comment/docstring hiển thị mojibake trong console hiện tại. |
| Encoding | Source đọc được bằng UTF-8 nhưng PowerShell output hiện tại hiển thị lỗi dấu tiếng Việt. |

## 15. Tổng Hợp Điểm

Điểm: 1 = yếu, 10 = tốt theo source hiện tại.

| Hạng mục | Điểm | Nhận xét |
|---|---:|---|
| Architecture | 6 | Có module layer rõ, nhưng thiếu use-case/service layer và controller gọi AI/DB trực tiếp. |
| Code Quality | 6 | Chạy được pipeline, nhưng có long class/function và duplicate logic. |
| Python | 6 | Type hint một phần, naming ổn, logging/lint/test style chưa đầy đủ. |
| GUI | 6 | QML/controller hoạt động theo Signal/Slot, nhưng QML điều phối nhiều controller. |
| YOLO | 7 | `ObjectDetector` tách riêng, config rõ; training/evaluation không nằm trong runtime module. |
| KNN | 6 | Tách khỏi GUI/DB, nhưng data/feature/train/infer trong cùng module và duplicate với KMeans. |
| KMeans | 6 | Tách khỏi GUI/DB, có metrics/cache; duplicate feature/data logic. |
| Database | 6 | Context manager đóng cursor/connection và dùng parameterized SQL; thiếu schema, pooling, error policy thống nhất. |
| Testing | 4 | Có script thực nghiệm, thiếu unit/integration/GUI tests chuẩn và coverage. |
| Performance | 6 | Có interval webcam và perf monitor; model load startup, DB connection per operation, PIL draw per frame là bottleneck. |
| Security | 5 | Có bcrypt và parameterized SQL; credential nằm trong workspace, joblib/pickle artifact risk. |
| Maintainability | 5 | Module hóa cơ bản tốt, nhưng coupling UI-AI-DB và duplicate logic làm khó mở rộng. |

## 16. Checklist

| Checklist | Trạng thái theo source |
|---|---|
| Duplicate Code | Có |
| Long Function | Có |
| Long Class | Có |
| God Object | Có dấu hiệu ở `WebcamThread` |
| Magic Number | Có |
| Hard Code Path | Có |
| Deep Nesting | Mức vừa, rõ nhất ở worker/detection loops |
| Dead Code / Unused Artifact | Có |
| Unused Import/Dependency | Có dấu hiệu trong requirements |
| TODO/FIXME/HACK | Không tìm thấy rõ |
| Missing Exception Handling | Có một số runtime path chưa thống nhất |
| Missing Logging | Có |
| Missing DB Schema | Có |
| Missing Unit Tests | Có |
| Missing GUI Tests | Có |
| Missing Ground Truth Evaluation | Có |
| Controller Calls AI Directly | Có |
| Controller Calls DB Directly | Có |
| Shared Detector Across Threads | Có |
| Shared Audio Output File | Có |
| Credentials In Workspace | Có |
| Parameterized SQL | Có |
| Password Hashing | Có |
| Model Load Cache | Có |

## 17. Roadmap

Không sửa trong giai đoạn này. Đây chỉ là đề xuất thứ tự ưu tiên.

### P0

| Ưu tiên | Việc cần làm |
|---|---|
| P0 | Đưa credential ra khỏi workspace/git, tạo `.env.example`, rotate credential nếu đã lộ. |
| P0 | Bổ sung database schema/migration cho `users` và `history`. |
| P0 | Kiểm soát shared `ObjectDetector` khi image thread và webcam thread có thể chạy đồng thời. |
| P0 | Tách đường xử lý lỗi thiếu `best.pt` để app có thông báo rõ thay vì crash trước UI. |

### P1

| Ưu tiên | Việc cần làm |
|---|---|
| P1 | Tách use-case/service layer cho image detection, webcam detection, ML suggestion, history save. |
| P1 | Refactor `WebcamThread` thành các phần camera capture, inference, postprocess, history writer. |
| P1 | Gộp feature engineering chung cho k-NN và K-Means. |
| P1 | Đưa DB auth operations dài sang worker thread hoặc async pattern phù hợp Qt. |
| P1 | Thêm unit test cho vocabulary, KNN/KMeans feature, classify, DB repository bằng mock. |

### P2

| Ưu tiên | Việc cần làm |
|---|---|
| P2 | Chuẩn hóa logging thay cho `print`. |
| P2 | Bổ sung ground truth cho test images và metric precision/recall/mAP. |
| P2 | Tách model artifact loading policy và validate model file. |
| P2 | Tạo file audio theo request hoặc khóa ghi file để tránh `SpeakTask` ghi đè. |
| P2 | Chuẩn hóa config path, tránh hard-coded absolute path. |

### P3

| Ưu tiên | Việc cần làm |
|---|---|
| P3 | Tích hợp hoặc loại bỏ `word_category_model.joblib`. |
| P3 | Thêm Vocabulary page nếu `VocabularyController` là tính năng runtime cần dùng. |
| P3 | Rà soát dependency không dùng trong `requirements.txt`. |
| P3 | Bổ sung lint/format/type-check workflow. |
| P3 | Cải thiện README vận hành project, test, model, database. |

