# PROJECT SURVEY - AI-English

## 1. Tổng Quan Project

| Hạng mục | Nội dung |
|---|---|
| Tên project | AI-English |
| Đề tài | Hệ thống nhận diện vật thể hỗ trợ học tiếng Anh sử dụng YOLOv8 kết hợp k-NN và K-Means |
| Ngôn ngữ | Python |
| IDE theo yêu cầu | PyCharm |
| Entry point | `main.py` |
| GUI | PySide6/QML |
| Object detection | YOLOv8 qua `ultralytics` |
| Machine learning | k-NN, K-Means qua `scikit-learn` |
| Database | PostgreSQL/Supabase qua `psycopg2` |
| Vocabulary | `dataset/vocabulary.csv` |
| Scope khảo sát | Loại trừ `.git`, `.venv`, `.idea`, `__pycache__` |

Mục tiêu theo source code hiện tại:

- Nhận diện vật thể từ ảnh tĩnh.
- Nhận diện vật thể từ webcam.
- Ánh xạ tên vật thể sang từ vựng tiếng Anh, nghĩa tiếng Việt, category và level.
- Gợi ý từ liên quan bằng k-NN.
- Phân cụm từ vựng bằng K-Means.
- Lưu lịch sử nhận diện theo user.
- Hiển thị lịch sử và thống kê trong GUI.

## 2. Cây Thư Mục

```text
AI-English/
├── .env
├── .gitignore
├── README.md
├── main.py
├── requirements.txt
├── assets/
│   ├── audio/
│   │   └── speech.mp3
│   └── fonts/
│       └── NotoSans-Regular.ttf
├── database/
│   ├── __init__.py
│   ├── auth.py
│   ├── db.py
│   └── history.py
├── dataset/
│   ├── __init__.py
│   ├── coco_classes.py
│   ├── dataset.yaml
│   ├── object_mapping.py
│   ├── prepare_dataset.py
│   ├── vocabulary.csv
│   ├── vocabulary.py
│   └── test_images/
│       ├── test1.jpg
│       ├── test2.jpg
│       ├── test3.jpg
│       ├── test4.jpg
│       ├── test5.jpg
│       ├── test6.jpg
│       ├── test7.jpg
│       ├── test8.jpg
│       ├── test9.jpg
│       ├── test10.jpg
│       ├── test11.jpg
│       ├── test12.jpg
│       ├── test13.jpg
│       ├── test14.jpg
│       ├── test15.jpg
│       ├── test16.jpg
│       ├── test17.jpg
│       ├── test18.jpg
│       ├── test19.jpg
│       ├── test20.jpg
│       ├── test21.jpg
│       ├── test22.jpg
│       ├── test23.jpg
│       ├── test24.jpg
│       ├── test25.jpg
│       ├── test26.jpg
│       ├── test27.jpg
│       ├── test28.jpg
│       ├── test29.jpg
│       └── test30.jpg
├── detection/
│   ├── __init__.py
│   ├── classify.py
│   ├── detector.py
│   ├── image_detect.py
│   └── webcam_detect.py
├── docs/
│   ├── .gitkeep
│   ├── AI-English-source-code-report.txt
│   └── experiment_results/
│       ├── cluster_purity.csv
│       ├── cluster_result.csv
│       ├── cluster_visualization.png
│       ├── elbow_curve.png
│       ├── kmeans_report.txt
│       ├── kmeans_summary.csv
│       ├── knn_report.txt
│       ├── knn_summary.csv
│       ├── knn_test_details.csv
│       ├── silhouette_curve.png
│       ├── system_image_evaluation_details.csv
│       ├── system_image_evaluation_report.txt
│       └── system_image_evaluation_summary.csv
├── ml/
│   ├── __init__.py
│   ├── category_predictor.py
│   ├── evaluate.py
│   ├── features.py
│   ├── kmeans.py
│   └── knn.py
├── models/
│   ├── best.pt
│   ├── kmeans.pkl
│   ├── knn.pkl
│   └── word_category_model.joblib
├── test/
│   ├── __init__.py
│   ├── test_connection.py
│   ├── test_kmeans.py
│   ├── test_knn.py
│   ├── test_login.py
│   ├── test_ml.py
│   ├── test_system_evaluation.py
│   └── test_yolo_image.py
├── ui/
│   ├── auth_controller.py
│   ├── history_controller.py
│   ├── image_controller.py
│   ├── main_qt.py
│   ├── qt_utils.py
│   ├── speech_worker.py
│   ├── stats_controller.py
│   ├── video_item.py
│   ├── vocabulary_controller.py
│   ├── webcam_controller.py
│   └── qml/
│       ├── AccountPage.qml
│       ├── CameraPage.qml
│       ├── HistoryPage.qml
│       ├── HomePage.qml
│       ├── LoginPage.qml
│       ├── Main.qml
│       ├── RegisterPage.qml
│       ├── StatisticsPage.qml
│       └── components/
│           ├── Card.qml
│           ├── Divider.qml
│           ├── PasswordField.qml
│           ├── PrimaryButton.qml
│           ├── SectionTitle.qml
│           ├── SidebarButton.qml
│           └── StatCard.qml
└── utils/
    ├── __init__.py
    ├── config.py
    ├── console.py
    ├── helper.py
    ├── perf_monitor.py
    ├── speech.py
    └── translator.py
```

### 2.1 Vai Trò Thư Mục

| Thư mục | Vai trò | Chức năng | Liên quan module |
|---|---|---|---|
| `assets/` | Tài nguyên runtime | Chứa audio và font Unicode | `utils.helper`, `utils.speech`, `utils.config` |
| `assets/audio/` | Âm thanh | Chứa `speech.mp3` do gTTS tạo/ghi | `utils.speech` |
| `assets/fonts/` | Font | Chứa `NotoSans-Regular.ttf` để vẽ tiếng Việt | `utils.helper` |
| `database/` | Data access layer | Kết nối DB, auth, history | `ui.auth_controller`, `ui.history_controller`, `ui.stats_controller`, `detection.image_detect`, `ui.webcam_controller` |
| `dataset/` | Dữ liệu và metadata | Class list, YAML YOLO, vocabulary, script chuẩn bị dataset | `detection`, `ml`, `utils.translator` |
| `dataset/test_images/` | Ảnh test | 30 ảnh `.jpg` | `test.test_yolo_image`, `test.test_system_evaluation` |
| `detection/` | Object detection layer | Load YOLO, detect ảnh/webcam, classify object | `ui.image_controller`, `ui.webcam_controller`, `test.test_yolo_image` |
| `docs/` | Tài liệu | Chứa báo cáo khảo sát và kết quả thí nghiệm | Không tìm thấy module runtime import |
| `docs/experiment_results/` | Kết quả thực nghiệm | CSV/TXT/PNG của KNN, KMeans, system evaluation | `test.test_knn`, `test.test_kmeans`, `test.test_system_evaluation` |
| `ml/` | Machine learning layer | Feature, k-NN, K-Means, category predictor | `detection.classify`, `ui.image_controller`, `ui.webcam_controller`, `ui.vocabulary_controller` |
| `models/` | Model artifacts | YOLO weight, KNN/KMeans pickle, category model joblib | `detection.detector`, `ml.knn`, `ml.kmeans` |
| `test/` | Script test/thực nghiệm | Kiểm tra DB, YOLO, KNN, KMeans, hệ thống | `docs/experiment_results` |
| `ui/` | Presentation/controller layer | PySide6 controllers và QML UI | `main.py`, `detection`, `ml`, `database`, `utils` |
| `ui/qml/` | QML screens | Các màn hình chính | `ui.main_qt` |
| `ui/qml/components/` | QML components | Component dùng lại | QML pages |
| `utils/` | Shared utilities | Config, console, helper image, speech, translator, perf | Gần như toàn bộ project |

## 3. Thống Kê Project

Scope: không tính `.git`, `.venv`, `.idea`, `__pycache__`.

| Loại | Số lượng |
|---|---:|
| Số thư mục | 24 |
| Tổng số file | 118 |
| Số file Python | 46 |
| Số file QML | 15 |
| Số model | 4 |
| Số file CSV | 8 |
| Số ảnh | 33 |
| Số file test Python | 8 |
| Số tài liệu | 6 |
| Số script | 9 |

### 3.1 Thống Kê Theo Extension

| Extension | Số lượng |
|---|---:|
| `.csv` | 8 |
| `.env` | 1 |
| `.gitignore` | 1 |
| `.gitkeep` | 1 |
| `.joblib` | 1 |
| `.jpg` | 30 |
| `.md` | 1 |
| `.mp3` | 1 |
| `.pkl` | 2 |
| `.png` | 3 |
| `.pt` | 1 |
| `.py` | 46 |
| `.qml` | 15 |
| `.ttf` | 1 |
| `.txt` | 5 |
| `.yaml` | 1 |

## 4. Kiến Trúc

### 4.1 Layer

```text
Application Entry
└── main.py
    └── ui.main_qt.run()

Presentation Layer
├── ui/*.py controllers
└── ui/qml/*.qml screens

Detection Layer
├── detection.detector.ObjectDetector
├── detection.image_detect.detect_image
└── detection.webcam_detect.run_webcam

Vocabulary/Data Layer
├── dataset.vocabulary
├── dataset.object_mapping
└── dataset.coco_classes

ML Layer
├── ml.knn
├── ml.kmeans
├── ml.features
└── ml.category_predictor

Database Layer
├── database.db
├── database.auth
└── database.history

Utility Layer
├── utils.config
├── utils.helper
├── utils.speech
├── utils.translator
├── utils.console
└── utils.perf_monitor
```

### 4.2 Quan Hệ Package

```text
main
└── ui
    ├── detection
    │   ├── ultralytics YOLO
    │   ├── dataset.coco_classes
    │   └── dataset.vocabulary
    ├── ml
    │   ├── dataset.vocabulary
    │   ├── sklearn
    │   └── models/*.pkl
    ├── database
    │   ├── psycopg2
    │   └── .env
    └── utils
        ├── OpenCV/Pillow/QImage helpers
        ├── speech
        └── perf monitor
```

## 5. Module

| Module | Mục đích | Input | Output | Module phụ thuộc | Module sử dụng nó |
|---|---|---|---|---|---|
| `dataset` | Chứa vocabulary, class list, mapping, YAML dataset, prepare dataset | CSV, YAML, COCO JSON ngoài repo | Dict vocabulary, class list, YOLO labels | `csv`, `json`, `pathlib`, `shutil` | `detection`, `ml`, `utils.translator` |
| `detection` | Nhận diện vật thể bằng YOLO và classify kết quả | Ảnh/frame OpenCV | List object, ảnh đã vẽ label | `ultralytics`, `cv2`, `dataset`, `ml`, `database`, `utils` | `ui`, `test` |
| `ml` | k-NN, K-Means, feature engineering, category predictor | `vocabulary.csv`, input word | Related words, clusters, metrics | `pandas`, `numpy`, `sklearn`, `joblib`, `dataset` | `detection.classify`, `ui`, `test` |
| `ui` | GUI controller và QML | User event, QImage, DB state | Signals, QML state, rendered UI | `PySide6`, `detection`, `ml`, `database`, `utils` | `main.py` |
| `database` | Auth và history persistence | Credentials, detection result | User dict, history rows, bool status | `psycopg2`, `dotenv`, `bcrypt`, `utils.perf_monitor` | `ui`, `detection` |
| `utils` | Tiện ích dùng chung | Config path, image, text, word, perf env | QImage helper data, text-drawn image, audio path, translated text | `cv2`, `PIL`, `gTTS`, `googletrans`, `torch` optional | `ui`, `detection`, `database`, `ml` |
| `models` | Chứa model artifacts | Không có input source code | Files `.pt`, `.pkl`, `.joblib` | Không áp dụng | `detection.detector`, `ml.knn`, `ml.kmeans` |
| `test` | Script kiểm thử/thực nghiệm | Project functions, test images, vocabulary | Console output, CSV/TXT/PNG reports | `detection`, `ml`, `database`, `cv2`, `pandas`, `matplotlib` | Người chạy test |
| `docs` | Lưu tài liệu và kết quả | Output từ test/report | `.txt`, `.csv`, `.png`, `.md` | Không tìm thấy import runtime | Người đọc, báo cáo |

## 6. Entry Point

Entry point theo source:

```text
main.py
└── main()
    ├── utils.console.use_utf8_console()
    └── from ui.main_qt import run
        └── run()
            ├── QApplication
            ├── qmlRegisterType(VideoItem)
            ├── ObjectDetector()
            │   └── YOLO(models/best.pt)
            ├── VocabularyController()
            ├── ImageController(detector)
            ├── WebcamController(detector)
            ├── HistoryController()
            ├── StatsController()
            ├── AuthController()
            ├── context.setContextProperty(...)
            └── engine.load(ui/qml/Main.qml)
```

## 7. Call Graph

### 7.1 GUI Startup

```text
main.py:main()
└── ui.main_qt.run()
    ├── ObjectDetector.__init__()
    │   └── ultralytics.YOLO(model_path)
    ├── VocabularyController.__init__()
    │   └── dataset.vocabulary.all_words()
    ├── ImageController.__init__()
    ├── WebcamController.__init__()
    ├── HistoryController.__init__()
    ├── StatsController.__init__()
    ├── AuthController.__init__()
    └── QQmlApplicationEngine.load(Main.qml)
```

### 7.2 Đăng Nhập

```text
LoginPage.qml
└── authController.login(username, password)
    └── AuthController.login()
        └── database.auth.verify_login()
            ├── find_user_by_username()
            │   └── database_cursor()
            │       └── get_connection()
            ├── _verify_password()
            │   └── bcrypt.checkpw() nếu password là bcrypt hash
            └── _update_password_hash() nếu password cũ là plain text
```

### 7.3 Đăng Ký

```text
RegisterPage.qml
└── authController.register(...)
    └── AuthController.register()
        ├── username_exists()
        │   └── find_user_by_username()
        └── register_user()
            ├── _hash_password()
            └── create_user()
                └── database_cursor(commit=True)
```

### 7.4 Nhận Diện Ảnh Tĩnh

```text
CameraPage.qml
└── imageController.detectSelectedImage()
    └── ImageController.detectSelectedImage()
        └── ImageDetectThread.run()
            └── detection.image_detect.detect_image()
                ├── cv2.imread(image_path)
                ├── ObjectDetector.detect(image)
                │   └── YOLO.predict(frame, conf=CONFIDENCE, imgsz=IMAGE_SIZE)
                ├── classify_word(class_name)
                │   ├── dataset.vocabulary.get_word_info()
                │   └── ml.category_predictor.predict_category() nếu không lookup được
                ├── database.history.save_history()
                ├── cv2.rectangle()
                └── utils.helper.draw_vietnamese_text()
            ├── ui.qt_utils.to_qimage()
            └── ImageController._on_results_ready()
                ├── ml.knn.get_related_words(primary_word, n=3)
                └── ml.kmeans.get_words_in_same_cluster(primary_word)
```

### 7.5 Nhận Diện Webcam Trong GUI

```text
CameraPage.qml
└── webcamController.start()
    └── WebcamController.start()
        └── WebcamThread.run()
            ├── cv2.VideoCapture(CAMERA_ID)
            ├── ObjectDetector.detect(frame) mỗi 0.25 giây
            ├── WebcamThread._format_detection()
            │   └── classify_word(class_name)
            ├── WebcamThread._save_history_if_allowed()
            │   └── queue.put_nowait(...)
            ├── WebcamThread._history_worker_loop()
            │   └── database.history.save_history()
            ├── WebcamThread._emit_word_suggestions()
            │   ├── ml.knn.get_related_words()
            │   └── ml.kmeans.get_words_in_same_cluster()
            ├── WebcamThread._draw_results()
            │   ├── cv2.rectangle()
            │   └── draw_vietnamese_text()
            └── ui.qt_utils.to_qimage()
```

### 7.6 History Và Statistics

```text
HistoryPage.qml
└── historyController.refresh()
    └── HistoryController._start_worker()
        └── HistoryWorker.run()
            └── database.history.get_history(user_id, limit=200)

StatisticsPage.qml
└── statsController.refresh()
    └── StatsWorker.run()
        └── database.history.get_history(user_id, limit=500)
```

### 7.7 k-NN

```text
get_related_words(word, n)
├── load_knn_model()
│   ├── joblib.load(models/knn.pkl)
│   └── train_knn_model() nếu model thiếu/hết hạn
│       ├── read_vocabulary()
│       ├── build_features()
│       ├── StandardScaler.fit_transform()
│       ├── apply_feature_weights()
│       ├── NearestNeighbors.fit()
│       └── joblib.dump()
├── scaler.transform(query_feature)
├── apply_feature_weights()
└── model.kneighbors()
```

### 7.8 K-Means

```text
get_words_in_same_cluster(word)
├── load_kmeans_model()
│   ├── joblib.load(models/kmeans.pkl)
│   └── train_kmeans_model() nếu model thiếu/hết hạn
│       ├── read_vocabulary()
│       ├── get_default_cluster_count()
│       ├── build_features()
│       ├── StandardScaler.fit_transform()
│       ├── apply_feature_weights()
│       ├── KMeans.fit_predict()
│       ├── silhouette_score()
│       └── joblib.dump()
└── lọc vocabulary theo cluster của input word
```

## 8. Dependency Graph

```text
GUI/QML
└── PySide6 Controllers
    ├── Detection
    │   ├── OpenCV
    │   ├── Ultralytics YOLO
    │   ├── models/best.pt
    │   └── dataset.coco_classes
    ├── Vocabulary
    │   ├── dataset/vocabulary.csv
    │   ├── dataset.vocabulary
    │   └── dataset.object_mapping
    ├── Machine Learning
    │   ├── ml.knn
    │   │   ├── models/knn.pkl
    │   │   └── scikit-learn NearestNeighbors
    │   └── ml.kmeans
    │       ├── models/kmeans.pkl
    │       └── scikit-learn KMeans
    ├── Database
    │   ├── database.auth
    │   ├── database.history
    │   ├── database.db
    │   └── PostgreSQL/Supabase
    └── Utils
        ├── config
        ├── helper
        ├── speech
        ├── translator
        └── perf_monitor
```

## 9. Knowledge Map

```text
AI-English
├── Entry Point
│   └── main.py -> ui.main_qt.run()
├── UI
│   ├── QML screens
│   │   ├── Login
│   │   ├── Register
│   │   ├── Home
│   │   ├── Camera
│   │   ├── History
│   │   ├── Statistics
│   │   └── Account
│   └── Controllers
│       ├── AuthController
│       ├── ImageController
│       ├── WebcamController
│       ├── HistoryController
│       ├── StatsController
│       └── VocabularyController
├── Detection
│   ├── ObjectDetector
│   │   └── YOLO(models/best.pt)
│   ├── image_detect.detect_image()
│   └── webcam_detect.run_webcam()
├── Vocabulary
│   ├── vocabulary.csv
│   ├── vocabulary.py
│   ├── object_mapping.py
│   └── coco_classes.py
├── Machine Learning
│   ├── k-NN
│   │   ├── ml/knn.py
│   │   └── models/knn.pkl
│   ├── K-Means
│   │   ├── ml/kmeans.py
│   │   └── models/kmeans.pkl
│   └── Category Predictor
│       ├── ml/category_predictor.py
│       └── models/word_category_model.joblib
├── Database
│   ├── db.py
│   ├── auth.py
│   └── history.py
├── Reports
│   └── docs/experiment_results
└── Tests
    ├── test_yolo_image.py
    ├── test_knn.py
    ├── test_kmeans.py
    ├── test_system_evaluation.py
    ├── test_ml.py
    ├── test_login.py
    └── test_connection.py
```

## 10. Danh Sách Class

| Class | File | Vai trò |
|---|---|---|
| `ObjectDetector` | `detection/detector.py` | Load YOLO model và detect object |
| `AuthController` | `ui/auth_controller.py` | Controller đăng nhập, đăng ký, đăng xuất, đổi mật khẩu |
| `HistoryModel` | `ui/history_controller.py` | QAbstractListModel cho lịch sử |
| `HistoryWorker` | `ui/history_controller.py` | QThread tải/xóa lịch sử |
| `HistoryController` | `ui/history_controller.py` | Controller lịch sử |
| `ImageDetectThread` | `ui/image_controller.py` | QThread detect ảnh tĩnh |
| `ImageController` | `ui/image_controller.py` | Controller chọn ảnh, detect ảnh, gợi ý từ |
| `SpeakTask` | `ui/speech_worker.py` | QRunnable phát âm nền |
| `StatsWorker` | `ui/stats_controller.py` | QThread tải thống kê |
| `StatsController` | `ui/stats_controller.py` | Controller thống kê |
| `VideoItem` | `ui/video_item.py` | QQuickPaintedItem hiển thị QImage trong QML |
| `VocabularyModel` | `ui/vocabulary_controller.py` | QAbstractListModel cho vocabulary |
| `VocabularyController` | `ui/vocabulary_controller.py` | Controller vocabulary, related words, cluster words |
| `WebcamThread` | `ui/webcam_controller.py` | QThread đọc webcam, detect realtime |
| `WebcamController` | `ui/webcam_controller.py` | Controller bật/tắt webcam |

## 11. Danh Sách Function

| Function | File | Chức năng |
|---|---|---|
| `main` | `main.py` | Entry point, set UTF-8 console và chạy GUI |
| `_load_bcrypt` | `database/auth.py` | Import bcrypt hoặc báo lỗi thiếu dependency |
| `_hash_password` | `database/auth.py` | Hash password bằng bcrypt |
| `_is_bcrypt_hash` | `database/auth.py` | Kiểm tra chuỗi hash bcrypt |
| `_verify_password` | `database/auth.py` | Verify password bcrypt/plain text |
| `find_user_by_username` | `database/auth.py` | Tìm user theo username |
| `username_exists` | `database/auth.py` | Kiểm tra username tồn tại |
| `create_user` | `database/auth.py` | Tạo user mới |
| `_update_password_hash` | `database/auth.py` | Cập nhật password hash |
| `verify_login` | `database/auth.py` | Xác thực đăng nhập |
| `register_user` | `database/auth.py` | Đăng ký user |
| `change_password` | `database/auth.py` | Đổi mật khẩu |
| `login_user` | `database/auth.py` | Alias đăng nhập |
| `get_connection` | `database/db.py` | Tạo kết nối PostgreSQL |
| `database_cursor` | `database/db.py` | Context manager cho cursor DB |
| `save_history` | `database/history.py` | Lưu lịch sử nhận diện |
| `get_history` | `database/history.py` | Lấy lịch sử nhận diện |
| `delete_history_by_user` | `database/history.py` | Xóa lịch sử theo user |
| `clear_history` | `database/history.py` | Xóa lịch sử |
| `create_output_directories` | `dataset/prepare_dataset.py` | Tạo thư mục YOLO dataset |
| `validate_paths` | `dataset/prepare_dataset.py` | Kiểm tra đường dẫn COCO |
| `load_coco_json` | `dataset/prepare_dataset.py` | Đọc annotation JSON |
| `coco_bbox_to_yolo` | `dataset/prepare_dataset.py` | Chuyển bbox COCO sang YOLO |
| `prepare_coco_records` | `dataset/prepare_dataset.py` | Lọc annotation theo class |
| `copy_records_to_split` | `dataset/prepare_dataset.py` | Copy ảnh và tạo label theo split |
| `write_dataset_yaml` | `dataset/prepare_dataset.py` | Ghi dataset.yaml |
| `main` | `dataset/prepare_dataset.py` | Chạy chuẩn bị dataset |
| `_load` | `dataset/vocabulary.py` | Load vocabulary CSV vào cache |
| `get_word_info` | `dataset/vocabulary.py` | Tra metadata của từ |
| `all_words` | `dataset/vocabulary.py` | Trả toàn bộ vocabulary |
| `classify_word` | `detection/classify.py` | Ánh xạ class YOLO sang vocabulary/category |
| `detect_image` | `detection/image_detect.py` | Detect ảnh tĩnh, vẽ label, lưu history |
| `run_webcam` | `detection/webcam_detect.py` | Detect webcam bằng OpenCV window |
| `predict_category` | `ml/category_predictor.py` | Dự đoán/lookup category cho từ |
| `evaluate_kmeans` | `ml/evaluate.py` | Gom kết quả K-Means theo cluster |
| `evaluate_knn` | `ml/evaluate.py` | Chạy thử k-NN với vài từ |
| `run` | `ml/evaluate.py` | In đánh giá ML |
| `read_vocabulary` | `ml/features.py` | Đọc và chuẩn hóa vocabulary |
| `build_features` | `ml/features.py` | Tạo feature cho vocabulary |
| `get_dataset_modified_time` | `ml/features.py` | Lấy mtime vocabulary |
| `read_vocabulary` | `ml/kmeans.py` | Đọc vocabulary cho K-Means |
| `build_features` | `ml/kmeans.py` | Tạo feature K-Means |
| `apply_feature_weights` | `ml/kmeans.py` | Áp trọng số feature |
| `get_dataset_modified_time` | `ml/kmeans.py` | Lấy mtime vocabulary |
| `get_default_cluster_count` | `ml/kmeans.py` | Chọn số cụm mặc định |
| `train_kmeans_model` | `ml/kmeans.py` | Train và lưu K-Means |
| `load_kmeans_model` | `ml/kmeans.py` | Load hoặc train lại K-Means |
| `cluster_vocabulary` | `ml/kmeans.py` | Trả vocabulary kèm cluster |
| `get_cluster_by_word` | `ml/kmeans.py` | Lấy cluster của từ |
| `get_words_in_same_cluster` | `ml/kmeans.py` | Lấy từ cùng cluster |
| `get_topic_clusters` | `ml/kmeans.py` | Gom cluster theo topic |
| `get_kmeans_metrics` | `ml/kmeans.py` | Trả metric K-Means |
| `read_vocabulary` | `ml/knn.py` | Đọc vocabulary cho k-NN |
| `build_features` | `ml/knn.py` | Tạo feature k-NN |
| `apply_feature_weights` | `ml/knn.py` | Áp trọng số feature |
| `get_dataset_modified_time` | `ml/knn.py` | Lấy mtime vocabulary |
| `train_knn_model` | `ml/knn.py` | Train và lưu NearestNeighbors |
| `load_knn_model` | `ml/knn.py` | Load hoặc train lại k-NN |
| `get_related_words` | `ml/knn.py` | Gợi ý từ liên quan |
| `run` | `ui/main_qt.py` | Khởi tạo QApplication, controller, QML |
| `to_qimage` | `ui/qt_utils.py` | Chuyển OpenCV BGR frame sang QImage |
| `use_utf8_console` | `utils/console.py` | Set stdout/stderr UTF-8 |
| `get_font` | `utils/helper.py` | Load font Unicode |
| `draw_vietnamese_text` | `utils/helper.py` | Vẽ chữ tiếng Việt lên ảnh |
| `resize_image` | `utils/helper.py` | Resize ảnh giữ tỷ lệ |
| `xu_ly_all` | `utils/helper.py` | Dịch từ và tạo audio |
| `start` | `utils/perf_monitor.py` | Bật perf instrumentation |
| `cuda_available` | `utils/perf_monitor.py` | Kiểm tra CUDA |
| `cuda_synchronize` | `utils/perf_monitor.py` | Đồng bộ CUDA nếu có |
| `timer` | `utils/perf_monitor.py` | Context manager đo thời gian |
| `increment` | `utils/perf_monitor.py` | Tăng counter perf |
| `add_time` | `utils/perf_monitor.py` | Cộng thời gian perf |
| `maybe_report` | `utils/perf_monitor.py` | In báo cáo perf định kỳ |
| `phat_am` | `utils/speech.py` | Tạo MP3 bằng gTTS |
| `open_audio_file` | `utils/speech.py` | Mở file audio |
| `speak` | `utils/speech.py` | Tạo và phát âm |
| `dich_tu` | `utils/translator.py` | Dịch từ EN sang VI |
| `print_section` | `test/test_knn.py`, `test/test_system_evaluation.py` | In tiêu đề section |
| `format_percent` | `test/test_knn.py`, `test/test_system_evaluation.py` | Format phần trăm |
| `format_distance` | `test/test_knn.py` | Format distance |
| `format_ms` | `test/test_knn.py`, `test/test_system_evaluation.py` | Format milliseconds |
| `import_knn_function` | `test/test_knn.py` | Import hàm k-NN |
| `load_raw_dataset` | `test/test_knn.py` | Đọc raw vocabulary |
| `normalize_dataset` | `test/test_knn.py` | Chuẩn hóa vocabulary |
| `count_missing_values` | `test/test_knn.py` | Đếm missing values |
| `build_dataset_statistics` | `test/test_knn.py` | Tạo thống kê dataset |
| `print_dataset_statistics` | `test/test_knn.py` | In thống kê dataset |
| `select_test_words` | `test/test_knn.py` | Chọn từ test |
| `get_input_lookup` | `test/test_knn.py` | Tạo lookup input |
| `evaluate_suggestions` | `test/test_knn.py` | Đánh giá suggestion |
| `run_knn_experiment` | `test/test_knn.py` | Chạy thực nghiệm k-NN |
| `build_summary` | `test/test_knn.py` | Tạo summary k-NN |
| `format_summary_for_terminal` | `test/test_knn.py` | Format summary |
| `choose_best_n` | `test/test_knn.py` | Chọn n tốt nhất |
| `run_special_cases` | `test/test_knn.py` | Test edge cases k-NN |
| `build_report_text` | `test/test_knn.py` | Tạo report text k-NN |
| `save_results` | `test/test_knn.py`, `test/test_system_evaluation.py` | Lưu kết quả |
| `read_vocabulary` | `test/test_kmeans.py` | Đọc vocabulary cho test K-Means |
| `build_features` | `test/test_kmeans.py` | Tạo feature test K-Means |
| `apply_feature_weights` | `test/test_kmeans.py` | Áp trọng số |
| `prepare_features` | `test/test_kmeans.py` | Scale và weight feature |
| `load_kmeans_model` | `test/test_kmeans.py` | Load K-Means model |
| `evaluate_k` | `test/test_kmeans.py` | Đánh giá K=2..8 |
| `plot_elbow_curve` | `test/test_kmeans.py` | Vẽ elbow curve |
| `plot_silhouette_curve` | `test/test_kmeans.py` | Vẽ silhouette curve |
| `get_model_features_for_pca` | `test/test_kmeans.py` | Lấy feature cho PCA |
| `get_model_labels` | `test/test_kmeans.py` | Lấy label K-Means |
| `plot_cluster_pca` | `test/test_kmeans.py` | Vẽ cluster PCA |
| `print_user` | `test/test_login.py` | In kết quả login |
| `print_words` | `test/test_ml.py` | In danh sách từ |
| `test_kmeans` | `test/test_ml.py` | Test K-Means |
| `test_knn` | `test/test_ml.py` | Test k-NN |
| `format_float` | `test/test_system_evaluation.py` | Format float |
| `import_project_functions` | `test/test_system_evaluation.py` | Import ObjectDetector, k-NN, K-Means |
| `load_vocabulary` | `test/test_system_evaluation.py` | Đọc vocabulary |
| `build_vocabulary_lookup` | `test/test_system_evaluation.py` | Tạo lookup vocabulary |
| `iter_image_paths` | `test/test_system_evaluation.py`, `test/test_yolo_image.py` | Liệt kê ảnh |
| `detect_image` | `test/test_system_evaluation.py` | Detect ảnh test bằng YOLO |
| `evaluate_knn` | `test/test_system_evaluation.py` | Đánh giá k-NN theo detected word |
| `evaluate_kmeans` | `test/test_system_evaluation.py` | Đánh giá K-Means theo detected word |
| `run_evaluation` | `test/test_system_evaluation.py` | Chạy evaluation toàn hệ thống |
| `calculate_summary` | `test/test_system_evaluation.py` | Tính summary |
| `build_summary_dataframe` | `test/test_system_evaluation.py` | Tạo dataframe summary |
| `build_report` | `test/test_system_evaluation.py` | Tạo report text |
| `print_summary` | `test/test_system_evaluation.py` | In summary |
| `detect_one` | `test/test_yolo_image.py` | Detect một ảnh |

## 12. Danh Sách Model AI

| Model | File | Nơi load | Nơi sử dụng |
|---|---|---|---|
| YOLOv8 custom/fine-tuned weight | `models/best.pt` | `detection/detector.py` qua `YOLO(model_path)` | `ObjectDetector.detect`, `detection.image_detect`, `detection.webcam_detect`, `ui.image_controller`, `ui.webcam_controller`, `test.test_yolo_image`, `test.test_system_evaluation` |
| k-NN / NearestNeighbors | `models/knn.pkl` | `ml/knn.py:load_knn_model()` | `ml.knn.get_related_words`, `ui.image_controller`, `ui.webcam_controller`, `ui.vocabulary_controller`, `ml.evaluate`, `test.test_knn`, `test.test_system_evaluation` |
| K-Means | `models/kmeans.pkl` | `ml/kmeans.py:load_kmeans_model()` | `ml.kmeans.get_words_in_same_cluster`, `get_cluster_by_word`, `get_topic_clusters`, `ui.image_controller`, `ui.webcam_controller`, `ui.vocabulary_controller`, `ml.evaluate`, `test.test_kmeans`, `test.test_system_evaluation` |
| Category Model | `models/word_category_model.joblib` | Không tìm thấy trong source code hiện tại | Không tìm thấy trong source code hiện tại |

## 13. Danh Sách Giao Diện

| Màn hình / Component | File | Controller |
|---|---|---|
| Main window/navigation | `ui/qml/Main.qml` | `authController`, `historyController`, `statsController`, `webcamController` |
| Login | `ui/qml/LoginPage.qml` | `AuthController` |
| Register | `ui/qml/RegisterPage.qml` | `AuthController` |
| Home | `ui/qml/HomePage.qml` | `StatsController` |
| Camera | `ui/qml/CameraPage.qml` | `ImageController`, `WebcamController`, `HistoryController`, `StatsController` |
| History | `ui/qml/HistoryPage.qml` | `HistoryController`, `StatsController` |
| Statistics | `ui/qml/StatisticsPage.qml` | `StatsController` |
| Account | `ui/qml/AccountPage.qml` | `AuthController` |
| Card component | `ui/qml/components/Card.qml` | Không tìm thấy controller trực tiếp |
| Divider component | `ui/qml/components/Divider.qml` | Không tìm thấy controller trực tiếp |
| PasswordField component | `ui/qml/components/PasswordField.qml` | Dùng bởi Login/Register/Account |
| PrimaryButton component | `ui/qml/components/PrimaryButton.qml` | Dùng bởi nhiều màn hình |
| SectionTitle component | `ui/qml/components/SectionTitle.qml` | Dùng bởi nhiều màn hình |
| SidebarButton component | `ui/qml/components/SidebarButton.qml` | `Main.qml` |
| StatCard component | `ui/qml/components/StatCard.qml` | Home/Statistics |

## 14. Danh Sách Dataset, Dữ Liệu, Reports

### 14.1 Dataset

| File/Thư mục | Loại | Nội dung |
|---|---|---|
| `dataset/dataset.yaml` | YOLO dataset config | Path train/valid/test và 12 class |
| `dataset/vocabulary.csv` | Vocabulary CSV | 12 từ, 4 cột `english`, `vietnamese`, `category`, `level` |
| `dataset/test_images/` | Test images | 30 ảnh `.jpg` |
| `dataset/coco_classes.py` | Class metadata | 12 class hợp lệ cho detector |
| `dataset/object_mapping.py` | Mapping | English -> Vietnamese |
| `dataset/prepare_dataset.py` | Dataset script | Tạo YOLO dataset từ COCO subset ngoài repo |

### 14.2 Vocabulary

| English | Category | Level |
|---|---|---|
| person | Human | Easy |
| backpack | Study | Easy |
| book | Study | Easy |
| bottle | Daily | Easy |
| cell phone | Technology | Easy |
| chair | Furniture | Easy |
| clock | Daily | Easy |
| cup | Daily | Easy |
| dining table | Furniture | Medium |
| keyboard | Technology | Medium |
| laptop | Technology | Medium |
| mouse | Technology | Medium |

### 14.3 CSV

| File | Nội dung |
|---|---|
| `dataset/vocabulary.csv` | Vocabulary chính |
| `docs/experiment_results/cluster_purity.csv` | Purity theo cluster |
| `docs/experiment_results/cluster_result.csv` | Từ và cluster |
| `docs/experiment_results/kmeans_summary.csv` | Metric K-Means theo K |
| `docs/experiment_results/knn_summary.csv` | Summary k-NN theo n |
| `docs/experiment_results/knn_test_details.csv` | Chi tiết suggestion k-NN |
| `docs/experiment_results/system_image_evaluation_details.csv` | Chi tiết evaluation theo ảnh |
| `docs/experiment_results/system_image_evaluation_summary.csv` | Summary evaluation hệ thống |

### 14.4 TXT

| File | Nội dung |
|---|---|
| `docs/AI-English-source-code-report.txt` | Báo cáo phân tích source code |
| `docs/experiment_results/kmeans_report.txt` | Report K-Means |
| `docs/experiment_results/knn_report.txt` | Report k-NN |
| `docs/experiment_results/system_image_evaluation_report.txt` | Report evaluation hệ thống |
| `requirements.txt` | Danh sách dependency |

### 14.5 PNG

| File | Nội dung |
|---|---|
| `docs/experiment_results/cluster_visualization.png` | Visualization cluster |
| `docs/experiment_results/elbow_curve.png` | Elbow curve |
| `docs/experiment_results/silhouette_curve.png` | Silhouette curve |

### 14.6 Weights / Models

| File | Loại |
|---|---|
| `models/best.pt` | YOLO weight |
| `models/knn.pkl` | k-NN model data |
| `models/kmeans.pkl` | K-Means model data |
| `models/word_category_model.joblib` | Category model artifact |

### 14.7 Reports

| File | Loại report |
|---|---|
| `docs/experiment_results/knn_report.txt` | k-NN |
| `docs/experiment_results/kmeans_report.txt` | K-Means |
| `docs/experiment_results/system_image_evaluation_report.txt` | YOLO + k-NN + K-Means |
| `docs/AI-English-source-code-report.txt` | Source code analysis |

## 15. Danh Sách Thư Viện

| Thư viện | Phiên bản | Vai trò | Được import ở file nào |
|---|---|---|---|
| `ultralytics` | `8.4.72` | Load/chạy YOLOv8 | `detection/detector.py` |
| `torch` | Không pin | Backend YOLO, kiểm tra CUDA trong perf monitor | `utils/perf_monitor.py` |
| `torchvision` | Không pin | Dependency vision cho PyTorch/Ultralytics | Không tìm thấy import trực tiếp trong source code hiện tại |
| `opencv-python` / `cv2` | Không pin | Đọc ảnh/webcam, vẽ rectangle, đổi màu ảnh | `detection/image_detect.py`, `detection/webcam_detect.py`, `ui/image_controller.py`, `ui/qt_utils.py`, `ui/webcam_controller.py`, `utils/helper.py`, `test/test_system_evaluation.py`, `test/test_yolo_image.py` |
| `numpy` | Không pin | Mảng ảnh và ma trận feature | `ml/kmeans.py`, `ml/knn.py`, `test/test_kmeans.py`, `ui/qt_utils.py`, `utils/helper.py` |
| `scikit-learn` | Không pin | KNN, KMeans, scaler, metrics | `ml/kmeans.py`, `ml/knn.py`, `test/test_kmeans.py` |
| `matplotlib` | Không pin | Vẽ biểu đồ thí nghiệm | `test/test_kmeans.py` |
| `pillow` / `PIL` | Không pin | Vẽ tiếng Việt lên ảnh bằng font Unicode | `utils/helper.py` |
| `joblib` | Không pin | Load/dump model pickle/joblib | `ml/kmeans.py`, `ml/knn.py`, `test/test_kmeans.py` |
| `python-dotenv` | Không pin | Load biến môi trường database | `database/db.py` |
| `pyttsx3` | Không pin | Text-to-speech offline theo requirements | Không tìm thấy import trong source code hiện tại |
| `gTTS` | Không pin | Tạo file MP3 phát âm | `utils/speech.py` |
| `googletrans` | `4.0.0rc1` | Fallback dịch từ | `utils/translator.py` |
| `psycopg2-binary` / `psycopg2` | Không pin | Kết nối PostgreSQL/Supabase | `database/db.py` |
| `pandas` | Không pin | Đọc CSV, xử lý dataframe, lưu report | `ml/features.py`, `ml/kmeans.py`, `ml/knn.py`, `test/test_kmeans.py`, `test/test_knn.py`, `test/test_system_evaluation.py` |
| `openpyxl` | Không pin | Excel support theo requirements | Không tìm thấy import trực tiếp trong source code hiện tại |
| `PySide6` | Không pin | GUI Qt/QML | `ui/auth_controller.py`, `ui/history_controller.py`, `ui/image_controller.py`, `ui/main_qt.py`, `ui/qt_utils.py`, `ui/speech_worker.py`, `ui/stats_controller.py`, `ui/video_item.py`, `ui/vocabulary_controller.py`, `ui/webcam_controller.py` |
| `bcrypt` | Không pin | Hash/verify password | `database/auth.py` |

## 16. Danh Sách File Python Theo Module

| Module | File Python |
|---|---|
| root | `main.py` |
| `database` | `__init__.py`, `auth.py`, `db.py`, `history.py` |
| `dataset` | `__init__.py`, `coco_classes.py`, `object_mapping.py`, `prepare_dataset.py`, `vocabulary.py` |
| `detection` | `__init__.py`, `classify.py`, `detector.py`, `image_detect.py`, `webcam_detect.py` |
| `ml` | `__init__.py`, `category_predictor.py`, `evaluate.py`, `features.py`, `kmeans.py`, `knn.py` |
| `test` | `__init__.py`, `test_connection.py`, `test_kmeans.py`, `test_knn.py`, `test_login.py`, `test_ml.py`, `test_system_evaluation.py`, `test_yolo_image.py` |
| `ui` | `auth_controller.py`, `history_controller.py`, `image_controller.py`, `main_qt.py`, `qt_utils.py`, `speech_worker.py`, `stats_controller.py`, `video_item.py`, `vocabulary_controller.py`, `webcam_controller.py` |
| `utils` | `__init__.py`, `config.py`, `console.py`, `helper.py`, `perf_monitor.py`, `speech.py`, `translator.py` |

