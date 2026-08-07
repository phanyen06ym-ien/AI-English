# SPRINT 2 REPORT - AI Engine Enhancement

Pham vi: bien `AIEngine` thanh trung tam dieu phoi AI pipeline. Khong thay doi YOLO, Vocabulary, KNN, KMeans, model, dataset, confidence, image size, feature, metric, scaler, cluster hoac weight.

## 1. Kien Truc Truoc

```text
ui/main_qt.py
  -> ObjectDetector
  -> ImageController(detector)
  -> WebcamController(detector)
  -> VocabularyController()

ImageController
  -> detection.image_detect.detect_image()
  -> get_related_words()
  -> get_words_in_same_cluster()

WebcamThread
  -> detector.detect()
  -> classify_word()
  -> get_related_words()
  -> get_words_in_same_cluster()

VocabularyController
  -> all_words()
  -> get_related_words()
  -> get_words_in_same_cluster()
```

## 2. Kien Truc Sau

```text
ui/main_qt.py
  -> AIEngine.create_default()
  -> ImageController(ai_engine)
  -> WebcamController(ai_engine)
  -> VocabularyController(ai_engine)

ImageController
  -> AIEngine.analyze_frame()

WebcamThread
  -> AIEngine.analyze_frame()

VocabularyController
  -> AIEngine.get_vocabulary_entries()
  -> AIEngine.get_related_word_dicts()
  -> AIEngine.get_cluster_word_dicts()

AIEngine
  -> detector.detect()
  -> classifier()
  -> related_words_provider()
  -> cluster_words_provider()
  -> vocabulary_provider()
```

GUI khong con import truc tiep `ObjectDetector`, `get_related_words`, `get_words_in_same_cluster`, `classify_word` hoac `all_words`.

## 3. Danh Sach File Sua

| File | Thay doi |
|---|---|
| `ai/models.py` | Them dataclass cho AI pipeline |
| `ai/pipeline.py` | Nang cap `AIEngine`: DI, pipeline, timing, logging, error handling |
| `ai/__init__.py` | Export data model moi |
| `ui/main_qt.py` | Khoi tao `AIEngine` va inject vao controller |
| `ui/image_controller.py` | Image thread goi `AIEngine.analyze_frame()` |
| `ui/webcam_controller.py` | Webcam thread goi `AIEngine.analyze_frame()` |
| `ui/vocabulary_controller.py` | Vocabulary controller chi goi `AIEngine` |
| `detection/image_detect.py` | Standalone helper chuyen sang dung `AIEngine`, giu output cu |
| `test/test_ai_engine.py` | Them unit/regression test cho AIEngine |
| `SPRINT_2_REPORT.md` | Bao cao sprint |

## 4. Class Sua / Tao

| Class | File | Noi dung |
|---|---|---|
| `AIEngine` | `ai/pipeline.py` | Dieu phoi detect, classify, vocabulary, KNN, KMeans, timing, error handling |
| `DetectedObject` | `ai/models.py` | Dataclass raw detection |
| `VocabularyEntry` | `ai/models.py` | Dataclass vocabulary metadata |
| `RelatedWord` | `ai/models.py` | Dataclass KNN output |
| `ClusterResult` | `ai/models.py` | Dataclass KMeans output |
| `DetectionResult` | `ai/models.py` | Dataclass detection da format |
| `ImageAnalysisResult` | `ai/models.py` | Dataclass ket qua pipeline day du |
| `TimingInfo` | `ai/models.py` | Dataclass timing |

## 5. Function Sua / Tao

| Function | Thay doi |
|---|---|
| `AIEngine.__init__()` | Nhan dependency injection, khong tu tao detector trong constructor |
| `AIEngine.create_default()` | Composition factory cho runtime |
| `AIEngine.from_detector()` | Giu compatibility khi caller co detector san |
| `AIEngine.detect_objects()` | Goi YOLO va do `yolo_ms` |
| `AIEngine.classify_object()` | Goi vocabulary/classifier va do `vocabulary_ms` |
| `AIEngine.format_detection()` | Chuan hoa format result |
| `AIEngine.analyze_frame()` | Pipeline YOLO -> Vocabulary -> KNN -> KMeans -> Result |
| `AIEngine.analyze_frame(include_learning=False)` | Cho phep helper cu chay YOLO + Vocabulary ma khong kich hoat KNN/KMeans |
| `AIEngine.get_related_words()` | Goi KNN qua provider, cache, logging, fallback [] |
| `AIEngine.get_cluster_words()` | Goi KMeans qua provider, cache, logging, fallback [] |
| `ImageDetectThread.run()` | Chuyen tu `detect_image()` sang `AIEngine.analyze_frame()` |
| `WebcamThread.run()` | Chuyen tu detector/classify/KNN/KMeans truc tiep sang `AIEngine.analyze_frame()` |
| `VocabularyController.loadRelatedWords()` | Chuyen sang `AIEngine.get_related_word_dicts()` |
| `VocabularyController.loadClusterWords()` | Chuyen sang `AIEngine.get_cluster_word_dicts()` |
| `detect_image()` | Dung `AIEngine`, giu return `(image, results)` |

## 6. Pipeline Moi

```text
Image / Webcam frame
  |
  v
AIEngine.analyze_frame()
  |
  +-- detect_objects()
  |     -> YOLO detector.detect()
  |     -> DetectedObject[]
  |
  +-- classify_object()
  |     -> VocabularyEntry
  |
  +-- format_detection()
  |     -> DetectionResult[]
  |
  +-- get_related_words()
  |     -> RelatedWord[]
  |
  +-- get_cluster_words()
  |     -> ClusterResult[]
  |
  v
ImageAnalysisResult
  +-- success
  +-- message
  +-- error_code
  +-- exception
  +-- timing
  +-- detections
  +-- related_words
  +-- cluster_words
```

## 7. Regression Test

| Test | Ket qua |
|---|---|
| `python -m unittest test.test_ai_engine -v` | Pass: 7/7 |
| `python -m compileall ai ui detection ml -q` | Pass |
| Rar soat GUI import truc tiep YOLO/KNN/KMeans/Vocabulary | Pass |

Regression case trong `test_ai_engine.py` kiem tra output dict cua `AIEngine` khop format GUI cu:

```text
laptop - May tinh xach tay [Technology - Medium] (0.93)
```

## 8. Timing

`AIEngine.analyze_frame()` hien tra ve `TimingInfo`:

| Field | Y nghia |
|---|---|
| `yolo_ms` | Thoi gian detector.detect() |
| `vocabulary_ms` | Tong thoi gian classify/vocabulary lookup |
| `knn_ms` | Thoi gian lay related words cho primary detection |
| `kmeans_ms` | Thoi gian lay cluster words cho primary detection |
| `pipeline_ms` | Tong thoi gian pipeline |

Timing chi bo sung thong ke, khong thay doi logic AI.

## 9. Risk

| Risk | Cach xu ly |
|---|---|
| GUI QML bi vo vi doi result type | Controller van emit list dict nhu truoc |
| Sai format nhan ve tren anh tinh | Da giu format nhan ve cu: `[category]` |
| Standalone `detect_image()` bi them chi phi KNN/KMeans | Dung `include_learning=False` de giu hanh vi cu |
| Sai format result list GUI | Regression test kiem tra format `[category - level]` |
| AIEngine nuot loi lam mat thong tin | `ImageAnalysisResult` co `success`, `message`, `error_code`, `exception` |
| KNN/KMeans loi khi GUI goi truc tiep qua engine | Engine log error va tra `[]` |
| Model artifact bi thay doi khi test | Unit test Sprint 2 dung fake provider, khong load model |

## 10. Changelog

- Them typed data models cho AI layer.
- Hoan thien `AIEngine` thanh pipeline orchestration trung tam.
- Them dependency injection cho detector, classifier, KNN provider, KMeans provider va vocabulary provider.
- Them timing cho YOLO, vocabulary, KNN, KMeans va pipeline.
- Them logging trong AIEngine va helper image detection.
- Chuan hoa error handling cua pipeline qua `ImageAnalysisResult`.
- Chuyen `ImageController`, `WebcamController`, `VocabularyController` sang chi goi `AIEngine`.
- Them unit/regression test `test/test_ai_engine.py`.
