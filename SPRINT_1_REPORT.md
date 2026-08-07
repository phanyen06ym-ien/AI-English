# SPRINT 1 REPORT - AI Layer Refactor

Pham vi: refactor AI Layer theo huong facade/package `ai/` ma khong thay doi thuat toan, tham so, model, dataset hoac ket qua tra ve cua YOLO, Vocabulary, KNN va KMeans.

## 1. File Da Sua

| File | Loai thay doi | Ly do |
|---|---|---|
| `ai/__init__.py` | Tao moi | Tao public API cho AI layer |
| `ai/detector.py` | Tao moi | Facade cho `detection.detector.ObjectDetector` |
| `ai/feature_engineering.py` | Tao moi | Facade cho feature engineering hien co trong `ml.features` |
| `ai/vocabulary.py` | Tao moi | Facade cho vocabulary lookup va classify |
| `ai/knn.py` | Tao moi | Facade cho KNN hien co trong `ml.knn` |
| `ai/kmeans.py` | Tao moi | Facade cho KMeans hien co trong `ml.kmeans` |
| `ai/pipeline.py` | Tao moi | Them `AIEngine` de gom YOLO, Vocabulary, KNN, KMeans |
| `ai/evaluation.py` | Tao moi | Facade cho cac helper evaluation hien co |
| `ui/main_qt.py` | Sua import | GUI bootstrap lay `ObjectDetector` qua AI facade |
| `ui/image_controller.py` | Sua import | Controller lay KNN/KMeans qua AI facade |
| `ui/webcam_controller.py` | Sua import | Webcam worker lay classify/KNN/KMeans qua AI facade |
| `ui/vocabulary_controller.py` | Sua import | Vocabulary controller lay vocabulary/KNN/KMeans qua AI facade |
| `detection/image_detect.py` | Sua import | Image detection lay detector/classify qua AI facade |
| `ml/evaluate.py` | Sua import | Evaluation script lay feature/KNN/KMeans qua AI facade |
| `SPRINT_1_REPORT.md` | Tao moi | Bao cao sprint |

Tong so file trong sprint: 15.

## 2. Class Da Sua

| Class | File | Thay doi |
|---|---|---|
| `AIEngine` | `ai/pipeline.py` | Tao moi de dieu phoi detection va learning suggestion |

Khong sua body cua cac class hien co trong GUI, detector, KNN hoac KMeans.

## 3. Function Da Sua

Khong thay doi logic cua function hien co. Cac thay doi chi la import path.

Function moi trong `ai/pipeline.py`:

| Function | Chuc nang |
|---|---|
| `AIEngine.__init__()` | Nhan detector co san hoac tao `ObjectDetector` |
| `AIEngine.detect_objects()` | Goi `detector.detect(frame)` |
| `AIEngine.format_detection()` | Gan metadata vocabulary cho mot object detect |
| `AIEngine.detect_and_format()` | Detect va format, sort theo confidence |
| `AIEngine.get_related_words()` | Uy quyen sang KNN hien co |
| `AIEngine.get_cluster_words()` | Uy quyen sang KMeans hien co |

## 4. Truoc / Sau

### Truoc

```text
GUI Controller
  -> detection.detector
  -> detection.classify
  -> ml.knn
  -> ml.kmeans
  -> dataset.vocabulary
```

### Sau

```text
GUI Controller
  -> ai.detector
  -> ai.vocabulary
  -> ai.knn
  -> ai.kmeans

AIEngine
  -> ObjectDetector
  -> classify_word
  -> get_related_words
  -> get_words_in_same_cluster
```

Module goc `detection/*`, `ml/*`, `dataset/*` van duoc giu nguyen de tuong thich nguoc.

## 5. Anh Huong

| Hang muc | Anh huong |
|---|---|
| YOLO result | Khong doi |
| Vocabulary lookup | Khong doi |
| KNN feature/scaler/metric/weight | Khong doi |
| KMeans feature/scaler/K/metric | Khong doi |
| GUI QML binding | Khong doi |
| Database/history | Khong doi |
| Test script cu | Van co the import `ml.*` va `detection.*` |

## 6. Risk

| Risk | Trang thai |
|---|---|
| Circular import giua `ai` va module cu | Da kiem tra import facade thanh cong |
| Sai ket qua KNN/KMeans qua facade | Da chay regression compare voi module goc |
| GUI bi vo do doi import | Chi doi Python import, khong doi public property/slot |
| Model bi train lai do sklearn version | Co xay ra trong test, la behavior co san cua source khi version mismatch |

## 7. Test Result

| Lenh | Ket qua |
|---|---|
| `python -m pytest test/test_ml.py test/test_knn.py test/test_kmeans.py -q` | Khong chay duoc vi moi truong khong co `pytest` |
| `python -c "from ai.detector import ObjectDetector; ..."` | Pass, output `ai imports ok` |
| `python test\test_knn.py` | Pass |
| `python test\test_kmeans.py` | Pass |
| `$env:PYTHONPATH=(Get-Location).Path; python test\test_ml.py` | Pass |
| Facade regression compare `ai.*` voi `ml.*` | Pass, output `facade regression ok` |

Ghi chu: `python test\test_ml.py` chay truc tiep khong dat neu khong set `PYTHONPATH` vi script khong them project root vao `sys.path`. Khi set `PYTHONPATH` ve project root, test pass. Khong sua test trong Sprint 1 de giu pham vi AI layer.

Ghi chu artifact: `models/kmeans.pkl` da o trang thai modified truoc Sprint 1 va van dang modified sau khi chay test. Khong restore file nay de tranh ghi de thay doi co san trong workspace. `models/knn.pkl` va report KNN do test sinh ra da duoc restore ve trang thai truoc Sprint.

## 8. Changelog

- Them package `ai/` gom detector, vocabulary, feature_engineering, knn, kmeans, pipeline va evaluation facade.
- Them `AIEngine` de chuan bi cho giai doan sau, giup GUI co mot diem goi AI duy nhat.
- Cap nhat import runtime chinh sang `ai.*`.
- Giu nguyen implementation goc cua YOLO, KNN, KMeans, Vocabulary va Evaluation.
- Khong thay doi tham so AI: `CONFIDENCE`, `IMAGE_SIZE`, `CATEGORY_WEIGHT`, `LEVEL_WEIGHT`, `WORD_LENGTH_WEIGHT`, `n_neighbors`, `metric`, `n_clusters`.
