# AI ALGORITHM ANALYSIS - AI-English

Phạm vi: phân tích thuật toán AI, dữ liệu, pipeline và kết quả thực nghiệm theo source code, dataset, model artifact và report hiện có. Không thay đổi source, dataset, model hoặc tham số.

## 1. AI Problem Analysis

### 1.1 Bài Toán AI Theo Project

```text
Đầu vào
  |
  +-- Ảnh tĩnh từ file
  +-- Frame webcam realtime
  |
  v
Xử lý
  |
  +-- OpenCV đọc ảnh/frame
  +-- YOLOv8 phát hiện vật thể
  +-- Lọc object theo 12 class của project
  +-- Vocabulary lookup lấy tiếng Việt/category/level
  +-- k-NN gợi ý từ liên quan
  +-- K-Means lấy từ cùng cụm chủ đề
  +-- Lưu history vào database
  |
  v
Đầu ra
  |
  +-- Ảnh/frame đã vẽ bounding box và nhãn
  +-- Danh sách object detect được
  +-- Từ tiếng Anh, nghĩa tiếng Việt, category, level
  +-- Related words từ k-NN
  +-- Same-cluster words từ K-Means
  +-- History/statistics trong GUI
```

### 1.2 Nhiệm Vụ AI Trong Hệ Thống

| Thành phần | Nhiệm vụ AI | Source |
|---|---|---|
| YOLOv8 | Phát hiện vật thể trong ảnh/frame | `detection/detector.py` |
| Vocabulary Mapping | Biến class object thành dữ liệu học từ vựng | `dataset/vocabulary.py`, `detection/classify.py` |
| k-NN | Gợi ý các từ liên quan trong vocabulary | `ml/knn.py` |
| K-Means | Phân cụm từ vựng theo feature để lấy nhóm chủ đề | `ml/kmeans.py` |
| Category Predictor | Fallback category nếu vocabulary lookup không có | `ml/category_predictor.py` |

## 2. Dataset Analysis

### 2.1 YOLO Dataset Config

File: `dataset/dataset.yaml`

```yaml
path: D:/DEV/Projects/AI-English/dataset/yolo_dataset
train: train/images
val: valid/images
test: test/images
```

Class trong YAML:

| ID | Class |
|---:|---|
| 0 | person |
| 1 | backpack |
| 2 | book |
| 3 | bottle |
| 4 | cell phone |
| 5 | chair |
| 6 | clock |
| 7 | cup |
| 8 | dining table |
| 9 | keyboard |
| 10 | laptop |
| 11 | mouse |

Tình trạng theo repository hiện tại:

| Hạng mục | Kết quả |
|---|---|
| Train images | Không tìm thấy trong source code hiện tại |
| Validation images | Không tìm thấy trong source code hiện tại |
| Test images YOLO dataset | Không tìm thấy trong source code hiện tại |
| YOLO labels | Không tìm thấy trong source code hiện tại |
| `dataset/yolo_dataset` | Không tìm thấy trong source code hiện tại |
| Script tạo dataset | Có: `dataset/prepare_dataset.py` |

### 2.2 Script Dataset Preparation

File: `dataset/prepare_dataset.py`

Nguồn dữ liệu trong source:

```text
COCO_ROOT = D:\Dataset\coco2017_subset
COCO_TRAIN_IMAGES = train2017
COCO_VAL_IMAGES = val2017
COCO_TRAIN_JSON = annotations/instances_train2017.json
COCO_VAL_JSON = annotations/instances_val2017.json
```

Flow:

```text
COCO JSON
  |
  v
load_coco_json()
  |
  v
prepare_coco_records()
  |
  +-- lọc annotation theo SELECTED_CLASSES
  +-- đổi category COCO sang class id YOLO nội bộ
  +-- đổi bbox COCO sang YOLO format
  |
  v
copy_records_to_split()
  |
  +-- copy image
  +-- ghi label .txt
  |
  v
write_dataset_yaml()
```

### 2.3 Test Images Hiện Có

| Hạng mục | Số lượng |
|---|---:|
| Ảnh `.jpg` trong `dataset/test_images` hiện tại | 30 |
| Ảnh được dùng trong report hệ thống hiện có | 24 |
| Ground truth từng ảnh | Không tìm thấy trong source code hiện tại |

Lưu ý: `docs/experiment_results/system_image_evaluation_report.txt` ghi report được tạo trên 24 ảnh. Thư mục hiện tại có 30 ảnh. Báo cáo này giữ nguyên số liệu report hiện có, không tự tính lại.

### 2.4 Vocabulary Dataset

File: `dataset/vocabulary.csv`

| Hạng mục | Giá trị |
|---|---:|
| Tổng số dòng | 12 |
| Số category | 5 |
| Số level có dữ liệu | 2 (`Easy`, `Medium`) |
| Duplicate theo report KNN | 0 |
| Missing theo report KNN | 0 |

Category distribution:

| Category | Số từ |
|---|---:|
| Daily | 3 |
| Furniture | 2 |
| Human | 1 |
| Study | 2 |
| Technology | 4 |

Level distribution:

| Level | Số từ |
|---|---:|
| Easy | 8 |
| Medium | 4 |
| Hard | 0 |

Vocabulary:

| English | Vietnamese | Category | Level |
|---|---|---|---|
| person | Người | Human | Easy |
| backpack | Ba lô | Study | Easy |
| book | Sách | Study | Easy |
| bottle | Chai nước | Daily | Easy |
| cell phone | Điện thoại | Technology | Easy |
| chair | Ghế | Furniture | Easy |
| clock | Đồng hồ | Daily | Easy |
| cup | Cốc | Daily | Easy |
| dining table | Bàn | Furniture | Medium |
| keyboard | Bàn phím | Technology | Medium |
| laptop | Máy tính xách tay | Technology | Medium |
| mouse | Chuột máy tính | Technology | Medium |

### 2.5 Mapping

| Mapping | Source | Vai trò |
|---|---|---|
| YOLO class list | `dataset/coco_classes.py` | Lọc class detect hợp lệ |
| English -> Vietnamese | `dataset/object_mapping.py` | Fallback trong `utils/translator.py` |
| Vocabulary metadata | `dataset/vocabulary.csv` | Lookup chính trong pipeline detect |

### 2.6 Đánh Giá Dataset

| Câu hỏi | Trả lời theo source/report |
|---|---|
| Dataset YOLO đủ chưa? | Không kết luận được vì train/validation/test YOLO dataset không có trong repository hiện tại. |
| Vocabulary đủ chưa? | Vocabulary hiện có 12 từ, đúng với 12 class. Dữ liệu đủ cho demo 12 object nhưng nhỏ cho đánh giá ML tổng quát. |
| Có imbalance không? | Có imbalance trong vocabulary: Technology 4, Daily 3, Human 1; level Hard 0. |
| Có bias không? | Có khả năng bias theo source: vocabulary tập trung vào đồ vật học tập, sinh hoạt, công nghệ; không có bằng chứng định lượng khác. |
| Có data leakage không? | Không tìm thấy ground truth/train split trong repo nên không đánh giá được data leakage YOLO. Với KNN/KMeans, cùng vocabulary được dùng để fit và evaluate suggestion. |
| Có class thiếu dữ liệu không? | Với vocabulary: không thiếu class so với 12 class. Với YOLO train images/labels: Không tìm thấy trong source code hiện tại. |

## 3. YOLO Analysis

### 3.1 Cấu Hình YOLO Theo Source

| Hạng mục | Giá trị |
|---|---|
| Model loader | `ultralytics.YOLO` |
| Weight | `models/best.pt` |
| Pretrained hay custom | Source comment ghi: "mô hình YOLO đã fine-tune trên Google Colab" trong `utils/config.py`; không có script train YOLO trong repo |
| Confidence | `0.5` |
| IOU | Không tìm thấy trong source code hiện tại |
| Image size | `640` |
| Class filter | `dataset.coco_classes.COCO_CLASSES` gồm 12 class |
| Inference function | `ObjectDetector.detect(frame)` |

### 3.2 YOLO Pipeline Theo Source

```text
Image / Frame
  |
  v
OpenCV BGR ndarray
  |
  v
ObjectDetector.detect(frame)
  |
  v
self.model.predict(
    frame,
    conf=CONFIDENCE,
    imgsz=IMAGE_SIZE,
    verbose=False
)
  |
  v
results
  |
  v
for result in results:
  for box in result.boxes:
    class_id = int(box.cls[0])
    confidence = float(box.conf[0])
    class_name = self.model.names[class_id]
    if class_name not in COCO_CLASSES: continue
    x1,y1,x2,y2 = box.xyxy[0]
  |
  v
detected_objects:
  - class_name
  - confidence
  - box
```

### 3.3 Preprocessing

| Bước | Theo source |
|---|---|
| Đọc ảnh tĩnh | `cv2.imread(image_path)` trong `detection/image_detect.py` |
| Đọc webcam | `cv2.VideoCapture(CAMERA_ID)` trong webcam modules |
| Resize | Không tự resize trong project trước khi gọi YOLO; `imgsz=640` truyền vào Ultralytics |
| Normalize | Không tự normalize trong project; để Ultralytics xử lý nội bộ |
| Color conversion trước YOLO | Không thấy convert BGR->RGB trước YOLO; frame OpenCV được truyền trực tiếp vào `model.predict` |

### 3.4 Postprocessing

| Bước | Theo source |
|---|---|
| Lấy class id | `box.cls[0]` |
| Lấy confidence | `box.conf[0]` |
| Lấy class name | `self.model.names[class_id]` |
| Lọc class | Bỏ object nếu `class_name not in COCO_CLASSES` |
| Lấy bbox | `box.xyxy[0]`, ép `int` |
| Output | List dict `{class_name, confidence, box}` |
| Vẽ GUI | `cv2.rectangle` + `draw_vietnamese_text` |

### 3.5 Vì Sao Chọn YOLO Theo Project

Theo source, hệ thống cần nhận diện ảnh tĩnh và webcam realtime. YOLO phù hợp với mục tiêu runtime này vì:

- Source dùng một detector chung cho ảnh và webcam.
- Webcam inference được gọi định kỳ mỗi `0.25` giây.
- Output YOLO trực tiếp phù hợp pipeline: class name, confidence, bounding box.
- `models/best.pt` là weight có sẵn và được load một lần khi khởi động GUI.

Không tìm thấy trong source code hiện tại phần so sánh thực nghiệm YOLO với SSD/Faster R-CNN.

## 4. Vocabulary Analysis

### 4.1 Cấu Trúc Vocabulary

File `dataset/vocabulary.csv` có 4 cột:

| Cột | Vai trò runtime |
|---|---|
| `english` | Key lookup từ class YOLO |
| `vietnamese` | Nghĩa tiếng Việt hiển thị/lưu history |
| `category` | Chủ đề dùng cho hiển thị, KNN/KMeans feature |
| `level` | Độ khó dùng cho hiển thị, KNN/KMeans feature |

### 4.2 Lookup Flow

```text
class_name từ YOLO
  |
  v
detection.classify.classify_word(class_name)
  |
  v
dataset.vocabulary.get_word_info(class_name)
  |
  +-- Có trong CSV:
  |     return english, vietnamese, category, level, source="lookup"
  |
  +-- Không có:
        return english, vietnamese=None,
               category=predict_category(class_name),
               level=None,
               source="ml"
```

### 4.3 Đánh Giá Vocabulary

| Hạng mục | Nhận xét |
|---|---|
| Coverage với 12 class | Vocabulary có đủ 12 từ tương ứng 12 class. |
| Coverage trong report hệ thống | 21/24 ảnh trong report có object detect nằm trong vocabulary, Vocabulary Coverage 87.50%. |
| Thiếu synonym | Không có cột synonym trong CSV. |
| Thiếu example sentence | Không có trong CSV. |
| Thiếu pronunciation metadata | Không có trong CSV; phát âm dùng gTTS theo từ đầu vào. |
| Imbalance | Category và level không cân bằng; Human chỉ 1 từ, Hard 0 từ. |

## 5. Feature Engineering

### 5.1 Feature Theo Source

Feature được xây từ vocabulary trong `ml/features.py`, `ml/knn.py`, `ml/kmeans.py`.

```text
Vocabulary row
  |
  +-- english
  |     └── word_length = len(english)
  |
  +-- level
  |     └── level_encoded:
  |         Easy = 0
  |         Medium = 1
  |         Hard = 2
  |
  +-- category
        └── one-hot:
            category_Daily
            category_Furniture
            category_Human
            category_Study
            category_Technology
```

Feature columns trong model artifact hiện tại:

| Feature |
|---|
| `word_length` |
| `level_encoded` |
| `category_Daily` |
| `category_Furniture` |
| `category_Human` |
| `category_Study` |
| `category_Technology` |

### 5.2 StandardScaler

Source dùng:

```text
scaled_features = StandardScaler().fit_transform(features)
```

Ý nghĩa trong project:

- Đưa `word_length`, `level_encoded`, one-hot category về cùng thang đo trước khi tính khoảng cách hoặc cluster.
- Sau scaling, project tiếp tục nhân trọng số feature.

### 5.3 Feature Weight

| Weight | Giá trị | Áp dụng cho | Ý nghĩa trong source |
|---|---:|---|---|
| `CATEGORY_WEIGHT` | 5.0 | Feature bắt đầu bằng `category_` | Category ảnh hưởng mạnh nhất |
| `LEVEL_WEIGHT` | 2.0 | `level_encoded` | Level ảnh hưởng thứ hai |
| `WORD_LENGTH_WEIGHT` | 0.5 | `word_length` | Độ dài từ là feature phụ |

Thứ tự quan trọng theo code:

```text
Category one-hot (5.0)
  >
Level encoded (2.0)
  >
Word length (0.5)
```

### 5.4 Tại Sao Chọn Feature Này Theo Project

Không có phần giải thích học thuật riêng trong source. Dựa trên code:

- `category` được dùng để nhóm/gợi ý theo chủ đề học từ vựng.
- `level` được dùng để giữ các từ cùng độ khó gần nhau.
- `word_length` là đặc trưng phụ để tạo khoảng cách khác nhau giữa các từ.

### 5.5 Feature Dư Thừa / Hạn Chế

| Feature | Nhận xét |
|---|---|
| Category one-hot | Rất mạnh do weight 5.0; làm KNN/KMeans gần như nhóm theo category. |
| Level encoded | Có tác dụng nhưng dataset chỉ có Easy/Medium, Hard = 0 nên chưa kiểm chứng đủ 3 mức. |
| Word length | Ít ảnh hưởng do weight 0.5; không phản ánh ngữ nghĩa thật. |
| Semantic feature | Chưa triển khai; không có embedding hoặc synonym. |

## 6. KNN Analysis

### 6.1 Flow

```text
Input word
  |
  v
normalize: strip + lower
  |
  v
load_knn_model()
  |
  +-- cache hợp lệ -> dùng cache
  +-- models/knn.pkl hợp lệ -> joblib.load
  +-- không hợp lệ -> train_knn_model()
  |
  v
tìm word_index trong vocabulary dataframe
  |
  v
lấy query_feature từ model_data["features"]
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
bỏ chính input word
  |
  v
trả n related words theo distance tăng dần
```

### 6.2 Cấu Hình KNN

| Hạng mục | Giá trị |
|---|---|
| Model | `sklearn.neighbors.NearestNeighbors` |
| File model | `models/knn.pkl` |
| Metric | `euclidean` |
| n_neighbors khi fit | `len(dataframe)` |
| n mặc định khi truy vấn | `3` |
| Cache | `_MODEL_CACHE` trong `ml/knn.py` |
| Model version | `4` |
| sklearn version trong artifact | `1.9.0` |

### 6.3 Training

`train_knn_model()`:

```text
read_vocabulary()
  |
  v
build_features()
  |
  v
StandardScaler.fit_transform()
  |
  v
apply_feature_weights()
  |
  v
NearestNeighbors(n_neighbors=len(dataframe), metric="euclidean")
  |
  v
model.fit(weighted_features)
  |
  v
joblib.dump(model_data, models/knn.pkl)
```

KNN ở đây không học label theo nghĩa supervised classifier. Model lưu cấu trúc nearest neighbors trên vector vocabulary.

### 6.4 Prediction / Retrieval

Output mỗi suggestion:

| Field | Ý nghĩa |
|---|---|
| `english` | Từ tiếng Anh được gợi ý |
| `vietnamese` | Nghĩa tiếng Việt |
| `category` | Category |
| `level` | Level |
| `distance` | Euclidean distance trong feature space đã scale/weight |

### 6.5 Vì Sao KNN Phù Hợp Với Project

Theo mục tiêu project là gợi ý từ liên quan sau khi nhận diện object. KNN phù hợp trong phạm vi source hiện tại vì:

- Vocabulary nhỏ, số từ 12, nên tìm neighbors đơn giản.
- Output là danh sách từ gần nhất, đúng nhu cầu "gợi ý".
- Không cần label mới ngoài metadata `category`, `level`.
- Có thể cập nhật khi `vocabulary.csv` thay đổi.

### 6.6 Ưu Điểm Và Nhược Điểm

| Loại | Nội dung |
|---|---|
| Ưu điểm | Dễ giải thích, phù hợp vocabulary nhỏ, trả distance/ranking rõ ràng, không phụ thuộc GUI/DB. |
| Nhược điểm | Feature chưa biểu diễn ngữ nghĩa thật; category weight quá mạnh; dataset nhỏ; nếu từ không có trong vocabulary thì trả `[]`; không có embedding/synonym. |

## 7. KMeans Analysis

### 7.1 Flow

```text
Vocabulary CSV
  |
  v
read_vocabulary()
  |
  v
build_features()
  |
  v
StandardScaler
  |
  v
apply_feature_weights()
  |
  v
KMeans.fit_predict()
  |
  v
cluster label cho từng từ
  |
  v
joblib.dump(model_data)
```

Runtime query:

```text
Input word
  |
  v
load_kmeans_model()
  |
  v
tìm row vocabulary theo english
  |
  v
lấy cluster id
  |
  v
lọc các từ cùng cluster
  |
  v
Output same-cluster words
```

### 7.2 Cấu Hình KMeans

| Hạng mục | Giá trị |
|---|---|
| Model | `sklearn.cluster.KMeans` |
| File model | `models/kmeans.pkl` |
| K hiện tại | 5 |
| K mặc định trong code | số category unique, giới hạn từ 2 đến `len(dataframe)-1` |
| random_state | 42 |
| n_init | 20 |
| init | k-means++ theo report |
| max_iter | 300 theo report |
| Cache | `_MODEL_CACHE` |
| Model version | 4 |
| sklearn version trong artifact | 1.9.0 |
| Inertia artifact | 24.633561643835616 |
| Silhouette artifact | 0.810603833795211 |

### 7.3 K, Elbow, Silhouette

Nguồn: `docs/experiment_results/kmeans_summary.csv`.

| K | SSE | Silhouette | Calinski | Davies |
|---:|---:|---:|---:|---:|
| 2 | 1143.3566 | 0.3434 | 3.5653 | 0.8221 |
| 3 | 763.6936 | 0.5347 | 4.6391 | 0.6885 |
| 4 | 384.6031 | 0.7154 | 8.0873 | 0.5227 |
| 5 | 24.6336 | 0.8106 | 108.4350 | 0.1654 |
| 6 | 10.7192 | 0.7520 | 172.4327 | 0.1318 |
| 7 | 0.7123 | 0.6288 | 1813.6378 | 0.0337 |
| 8 | 0.3836 | 0.4700 | 2310.1020 | 0.0243 |

Report chọn K=5 vì Silhouette = 0.8106, Davies = 0.1654, Calinski = 108.4350.

### 7.4 Cluster Và Purity

Nguồn: `cluster_result.csv`, `cluster_purity.csv`.

| Cluster | Major category | Size | Purity |
|---:|---|---:|---:|
| 0 | Technology | 4 | 100% |
| 1 | Daily | 3 | 100% |
| 2 | Human | 1 | 100% |
| 3 | Furniture | 2 | 100% |
| 4 | Study | 2 | 100% |

Cluster detail:

| Cluster | Words |
|---:|---|
| 0 | cell phone, keyboard, laptop, mouse |
| 1 | bottle, clock, cup |
| 2 | person |
| 3 | chair, dining table |
| 4 | backpack, book |

### 7.5 Đánh Giá KMeans

| Hạng mục | Nhận xét |
|---|---|
| K=5 | Trùng số category unique trong vocabulary. |
| Purity 100% | Đạt trên vocabulary hiện tại, nhưng category là feature trọng số mạnh nên purity cao là kết quả trực tiếp của thiết kế feature. |
| Silhouette 0.8106 | Cao theo report hiện có. |
| Hạn chế | Dataset chỉ 12 từ; có cluster size 1 (`person`), chưa chứng minh khả năng khái quát với vocabulary lớn. |

## 8. AI Pipeline

```text
Image / Webcam Frame
  |
  v
OpenCV
  |
  v
YOLOv8
  |
  v
Object Name + Confidence + Bounding Box
  |
  v
Vocabulary Mapping
  |
  v
English + Vietnamese + Category + Level
  |
  +-------------------------------+
  |                               |
  v                               v
Feature Engineering               History
  |                               |
  +-- word_length                 v
  +-- level_encoded           Database
  +-- category one-hot
  +-- StandardScaler
  +-- Feature weights
  |
  +-------------------------------+
  |                               |
  v                               v
k-NN                            K-Means
  |                               |
  v                               v
Related Words                  Topic Cluster / Same Cluster Words
  |                               |
  +---------------+---------------+
                  |
                  v
                 GUI
```

## 9. Experimental Results

### 9.1 System-Level Evaluation

Nguồn:

- `docs/experiment_results/system_image_evaluation_report.txt`
- `docs/experiment_results/system_image_evaluation_summary.csv`
- `docs/experiment_results/system_image_evaluation_details.csv`

Ghi chú trong report: project không có file ground truth cho từng ảnh test, nên report không tính accuracy/precision/recall so với nhãn thật.

| Metric | Giá trị report |
|---|---:|
| Tổng số ảnh trong report | 24 |
| Số ảnh theo yêu cầu script | 25 |
| YOLO detect được | 21 |
| YOLO không detect được | 3 |
| Detection Rate | 87.50% |
| Not Detected Rate | 12.50% |
| Average YOLO Confidence trên ảnh detect | 89.34% |
| Average YOLO Time | 153.909 ms |
| Từ detect có trong vocabulary | 21 |
| Vocabulary Coverage | 87.50% |
| KNN có gợi ý | 21 |
| KNN Success Rate trên tổng ảnh | 87.50% |
| KNN Success Rate trên ảnh YOLO detect | 100.00% |
| Average KNN Category Precision | 55.56% |
| Average KNN Time | 10.344 ms |
| KMeans phân cụm được | 21 |
| KMeans Success Rate trên tổng ảnh | 87.50% |
| KMeans Success Rate trên ảnh YOLO detect | 100.00% |
| Average KMeans Cluster Purity theo từ | 100.00% |
| Average KMeans Time | 3.683 ms |

YOLO detected word distribution:

```text
laptop | ##### 5
cup    | ####  4
chair  | ####  4
person | ####  4
none   | ###   3
clock  | ##    2
bottle | ##    2
```

KMeans cluster distribution trong report:

```text
cluster 1 | ######## 8
cluster 0 | #####    5
cluster 3 | ####     4
cluster 2 | ####     4
none      | ###      3
```

### 9.2 KNN Experiment

Nguồn:

- `docs/experiment_results/knn_report.txt`
- `docs/experiment_results/knn_summary.csv`
- `docs/experiment_results/knn_test_details.csv`

| n | Tested input words | Total suggestions | Same category suggestions | Avg category precision | Same level suggestions | Avg level precision | Avg mean distance | Avg MRR category |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | 10 | 30 | 18 | 60.00% | 21 | 70.00% | 7.9696 | 0.9000 |
| 5 | 10 | 50 | 18 | 36.00% | 22 | 44.00% | 11.6536 | 0.9000 |
| 7 | 10 | 70 | 18 | 25.71% | 36 | 51.43% | 13.3418 | 0.9000 |

Report chọn `n=3`.

Special cases trong report:

| Case | Kết quả |
|---|---|
| Từ không tồn tại | Trả 0 gợi ý, đạt kỳ vọng |
| Chuỗi rỗng | Trả 0 gợi ý, đạt kỳ vọng |
| Chữ hoa + khoảng trắng | Có 3 gợi ý như `laptop`, đạt kỳ vọng |
| n lớn hơn số từ hiện có | Trả tối đa 11 gợi ý, không lỗi |

Thời gian:

| Metric | Giá trị |
|---|---:|
| Tổng thời gian thực nghiệm KNN | 13645.356 ms |
| Thời gian trung bình mỗi truy vấn | 125.632 ms |

### 9.3 KMeans Experiment

Nguồn:

- `docs/experiment_results/kmeans_report.txt`
- `docs/experiment_results/kmeans_summary.csv`
- `docs/experiment_results/cluster_purity.csv`
- `docs/experiment_results/cluster_result.csv`

| Metric | Giá trị |
|---|---:|
| K được chọn | 5 |
| SSE tại K=5 | 24.6336 |
| Silhouette tại K=5 | 0.8106 |
| Calinski tại K=5 | 108.4350 |
| Davies tại K=5 | 0.1654 |
| Average Cluster Purity | 100.0000% |
| Load model time | 4.0408 ms |
| Predict time | 0.7972 ms |
| Train time | 3996.8391 ms |
| Total time | 4127.1491 ms |

### 9.4 Metric Không Có

| Metric | Tình trạng |
|---|---|
| Precision YOLO theo ground truth | Không tìm thấy trong source/report hiện tại |
| Recall YOLO theo ground truth | Không tìm thấy trong source/report hiện tại |
| mAP YOLO | Không tìm thấy trong source/report hiện tại |
| Confusion matrix | Không tìm thấy trong source/report hiện tại |

## 10. Đánh Giá Kết Quả

### 10.1 YOLO

| Hạng mục | Nhận xét |
|---|---|
| Kết quả report | Detect được 21/24 ảnh, Detection Rate 87.50%. |
| Confidence | Average confidence trên ảnh detect 89.34%. |
| Thời gian | Average YOLO time 153.909 ms. |
| Đạt hay chưa | Đạt mức demo nhận diện ảnh test theo report hiện có. |
| Hạn chế | Không có ground truth nên chưa chứng minh được precision/recall/mAP. Report hiện chỉ đo detect/non-detect và confidence nội bộ YOLO. |
| Đáp ứng mục tiêu | Có đáp ứng luồng nhận diện vật thể hỗ trợ học từ vựng trong phạm vi class đã chọn. |

### 10.2 KNN

| Hạng mục | Nhận xét |
|---|---|
| Kết quả report | Với n=3, Avg Category Precision 60.00%, Avg MRR Category 0.9000. |
| Success rate hệ thống | 100.00% trên ảnh YOLO detect trong report. |
| Đạt hay chưa | Đạt chức năng tạo gợi ý cho từ có trong vocabulary. |
| Nguyên nhân category precision chưa cao hơn | Với category nhỏ như Human có 1 từ, bỏ input word khiến không còn từ cùng category để gợi ý; feature không phải semantic embedding. |
| Ưu điểm | Dễ giải thích, chạy nhanh sau khi model loaded, phù hợp vocabulary nhỏ. |
| Hạn chế | Gợi ý phụ thuộc category/level/word length; chưa phản ánh quan hệ ngữ nghĩa sâu. |

### 10.3 KMeans

| Hạng mục | Nhận xét |
|---|---|
| Kết quả report | K=5, Silhouette 0.8106, Average Cluster Purity 100%. |
| Success rate hệ thống | 100.00% trên ảnh YOLO detect trong report. |
| Đạt hay chưa | Đạt chức năng phân nhóm vocabulary hiện tại. |
| Nguyên nhân purity cao | Category one-hot có trọng số 5.0 và K=5 bằng số category, nên cluster tách đúng category. |
| Ưu điểm | Tạo nhóm chủ đề rõ ràng, dễ trình bày trong đồ án. |
| Hạn chế | Vocabulary nhỏ, có cluster size 1, chưa chứng minh khả năng mở rộng. |

## 11. Algorithm Comparison

### 11.1 Object Detection

| Thuật toán | So với mục tiêu project | Lý do lựa chọn/không lựa chọn theo phân tích |
|---|---|---|
| YOLO | Phù hợp ảnh tĩnh và webcam realtime | Source đã dùng YOLO với `best.pt`, output class/confidence/bbox trực tiếp cho GUI. |
| SSD | Có thể detect nhanh | Không tìm thấy source triển khai/so sánh SSD; không có weight/report SSD trong project. |
| Faster R-CNN | Thường ưu tiên accuracy hơn realtime | Không tìm thấy source triển khai/so sánh Faster R-CNN; pipeline webcam hiện cần tốc độ. |

### 11.2 Related Word / Classification Alternative

| Thuật toán | So với mục tiêu project | Lý do lựa chọn/không lựa chọn theo phân tích |
|---|---|---|
| k-NN | Phù hợp gợi ý nearest words trong vocabulary nhỏ | Source dùng feature đơn giản và distance để rank suggestion. |
| Decision Tree | Có thể phân loại category/level | Không phù hợp trực tiếp với nhiệm vụ "gợi ý danh sách từ gần nhất" nếu không thiết kế thêm retrieval. Không tìm thấy triển khai trong source. |
| Random Forest | Có thể phân loại mạnh hơn Decision Tree | Không tìm thấy source/report; cần label supervised và không trả neighbor ranking tự nhiên. |

### 11.3 Clustering

| Thuật toán | So với mục tiêu project | Lý do lựa chọn/không lựa chọn theo phân tích |
|---|---|---|
| K-Means | Phù hợp khi muốn số cụm K rõ ràng theo topic | Source chọn K=5 gần với số category; output cluster dễ hiển thị. |
| DBSCAN | Không cần chọn K, phát hiện noise | Không tìm thấy source triển khai; với 12 điểm feature nhỏ, density clustering chưa được chứng minh trong project. |
| Hierarchical | Có thể tạo cây phân cấp từ vựng | Không tìm thấy source triển khai; project hiện cần cluster id đơn giản để lấy từ cùng nhóm. |

## 12. Academic Evaluation

Điểm mang tính đánh giá học thuật dựa trên source/report hiện có, không phải số liệu thực nghiệm.

| Thành phần | Điểm / 10 | Nhận xét |
|---|---:|---|
| Dataset | 5 | Vocabulary đầy đủ cho 12 class nhưng nhỏ; YOLO train/val/test dataset không có trong repo; thiếu ground truth ảnh test. |
| YOLO | 7 | Có model weight, pipeline detect rõ, confidence/image size rõ; thiếu mAP/precision/recall và script train/evaluate YOLO. |
| Vocabulary | 6 | Có English/Vietnamese/category/level đủ cho 12 class; thiếu synonym, ví dụ, phát âm metadata, mở rộng dữ liệu. |
| Feature Engineering | 6 | Feature dễ giải thích; category/level/length phù hợp demo; chưa có semantic feature. |
| KNN | 7 | Pipeline rõ, metric Euclidean, cache model, report n=3/5/7; hạn chế do feature đơn giản và dataset nhỏ. |
| KMeans | 7 | Có K evaluation, silhouette, purity, visualization; K và category có quan hệ trực tiếp nên cần diễn giải cẩn thận. |
| Thực nghiệm | 6 | Có CSV/TXT report cho KNN, KMeans, system evaluation; thiếu ground truth và metric detection chuẩn. |
| Báo cáo AI | 6 | Có dữ liệu thực nghiệm để viết báo cáo; cần bổ sung mô tả dataset YOLO thực tế, cách train model, metric chuẩn. |
| Tính phù hợp mục tiêu đồ án | 7 | Hệ thống đáp ứng demo object detection + English learning + KNN + KMeans trong phạm vi 12 class. |

## 13. Risk Analysis

### 13.1 YOLO Detect Sai

```text
YOLO detect sai object
  |
  v
class_name sai
  |
  v
Vocabulary lookup theo class_name sai
  |
  v
Vietnamese/category/level sai
  |
  +--> KNN gợi ý theo từ sai
  +--> KMeans lấy cluster của từ sai
  +--> History lưu kết quả sai
  +--> GUI hiển thị từ học sai
```

Ảnh hưởng: lỗi YOLO lan truyền toàn bộ pipeline vì KNN/KMeans phụ thuộc `primary_word` từ YOLO.

### 13.2 Vocabulary Thiếu

```text
YOLO class_name không có trong vocabulary.csv
  |
  v
classify_word()
  |
  v
vietnamese = None
category = predict_category(class_name)
level = None
  |
  v
predict_category()
  |
  +-- lookup không có -> "Unknown"
  |
  v
GUI dùng vietnamese fallback = class_name
KNN get_related_words(class_name) -> []
KMeans get_words_in_same_cluster(class_name) -> []
History lưu category Unknown nếu được truyền
```

### 13.3 Object Không Có Trong Dataset/Class List

```text
YOLO output class_name
  |
  v
if class_name not in COCO_CLASSES:
    continue
  |
  v
Object bị loại khỏi detected_objects
```

Nếu object không thuộc 12 class hợp lệ, pipeline không đưa object đó sang vocabulary/KNN/KMeans/GUI.

### 13.4 YOLO Không Detect Được

```text
detector.detect(image/frame) -> []
  |
  v
Ảnh tĩnh:
  results = []
  related_words = []
  cluster_words = []
  status = "Không phát hiện vật thể nào."

Webcam:
  results = []
  related_ready([])
  cluster_ready([])
  status = "Chưa phát hiện vật thể."
```

### 13.5 KNN/KMeans Model Không Load Được

```text
load_knn_model/load_kmeans_model
  |
  +-- model file thiếu/hết hạn/version mismatch
  |     |
  |     v
  |   train lại từ vocabulary.csv
  |
  +-- vocabulary.csv lỗi/thiếu
        |
        v
      raise exception
```

Ảnh hưởng: nếu vocabulary lỗi, KNN/KMeans không có dữ liệu để train/load hợp lệ.

## 14. Conclusion

Hệ thống AI hiện tại gồm ba lớp thuật toán nối tiếp:

```text
YOLOv8
  -> nhận diện object từ ảnh/frame

Vocabulary Mapping
  -> biến object thành dữ liệu học từ vựng

k-NN + K-Means
  -> gợi ý từ liên quan và nhóm chủ đề
```

Theo source và report hiện có:

- YOLO đã thực hiện được object detection cho ảnh test với Detection Rate 87.50% trên report 24 ảnh.
- Vocabulary bao phủ đúng 12 class và có coverage 87.50% trong report hệ thống.
- k-NN tạo được gợi ý cho các object có trong vocabulary, với Category Precision 55.56% ở system evaluation và 60.00% trong thí nghiệm riêng với n=3.
- K-Means phân cụm vocabulary thành 5 cụm tương ứng 5 category, Average Cluster Purity 100% trên vocabulary hiện tại.
- Kết quả thực nghiệm chứng minh được pipeline demo hoạt động end-to-end, nhưng chưa chứng minh đầy đủ chất lượng detection theo chuẩn học thuật vì thiếu ground truth, precision, recall và mAP.
- Thuật toán hiện tại phù hợp với mục tiêu đồ án ở mức hệ thống demo nhận diện vật thể hỗ trợ học tiếng Anh, kèm gợi ý và phân cụm từ vựng.

