# AI RESEARCH REVIEW - AI-English

Phạm vi: đánh giá học thuật, cơ sở toán học và khả năng bảo vệ của hệ thống AI-English dựa trên source code, dataset, model artifact và report thực nghiệm hiện có. Không sửa source code, không refactor, không thay đổi dataset, không thay đổi model và không tự tạo số liệu.

## 1. Mathematical Foundation

### 1.1 YOLOv8 Theo Project

Source sử dụng `ultralytics.YOLO` trong `detection/detector.py`. Project không tự cài đặt công thức YOLO, IoU hay NMS; các bước này nằm trong pipeline inference của thư viện Ultralytics. Source trực tiếp cấu hình:

| Thành phần | Theo source hiện tại |
|---|---|
| Model loader | `YOLO(model_path)` |
| Weight | `models/best.pt` |
| Confidence threshold | `CONFIDENCE = 0.5` trong `utils/config.py` |
| Image size | `IMAGE_SIZE = 640` trong `utils/config.py` |
| IOU threshold | Không tìm thấy trong source code hiện tại |
| NMS | Không triển khai trực tiếp; do Ultralytics xử lý trong `model.predict()` |
| Class mapping | `result.names[class_id]`, sau đó lọc theo `COCO_CLASSES` |

Pipeline toán học của YOLOv8 được project gọi:

```text
Image / Webcam frame
  |
  v
YOLOv8 model.predict(frame, conf=0.5, imgsz=640)
  |
  +-- dự đoán bounding box
  +-- dự đoán confidence
  +-- dự đoán class id
  +-- thư viện thực hiện postprocessing/NMS
  |
  v
ObjectDetector.detect()
  |
  +-- lấy xyxy
  +-- lấy confidence
  +-- lấy class_name
  +-- lọc class theo 12 class của project
```

Bounding box trong source được lấy từ `box.xyxy[0]`:

```text
B = (x1, y1, x2, y2)
```

Ý nghĩa:

| Đại lượng | Ý nghĩa trong project |
|---|---|
| `x1, y1` | Tọa độ góc trái trên của vật thể |
| `x2, y2` | Tọa độ góc phải dưới của vật thể |
| `confidence` | Độ tin cậy của detection, được trả về từ YOLOv8 |
| `class_id` | Mã lớp dự đoán |
| `class_name` | Tên vật thể tiếng Anh dùng để lookup vocabulary |

IoU thường được dùng trong YOLO/NMS:

```text
IoU(A, B) = Area(A ∩ B) / Area(A ∪ B)
```

Trong project hiện tại, IoU không được truyền rõ trong `model.predict()`, nên giá trị mặc định do Ultralytics quyết định. Không tìm thấy trong source code hiện tại việc tự tính IoU, precision, recall hoặc mAP.

NMS thường giữ lại box có confidence cao và loại bỏ box trùng lặp nếu IoU vượt ngưỡng:

```text
Boxes -> sort by confidence -> keep best box -> remove boxes with high IoU -> final detections
```

Trong project hiện tại, NMS không nằm trong code tự viết mà nằm trong hàm `YOLO.predict()`.

### 1.2 StandardScaler

Source dùng `StandardScaler` trong `ml/knn.py` và `ml/kmeans.py`.

Công thức:

```text
z = (x - μ) / σ
```

Trong đó:

| Ký hiệu | Ý nghĩa |
|---|---|
| `x` | Giá trị feature ban đầu |
| `μ` | Trung bình của feature trên vocabulary |
| `σ` | Độ lệch chuẩn của feature |
| `z` | Giá trị sau chuẩn hóa |

Feature trong project gồm:

```text
word_length
level_encoded
category_Daily
category_Furniture
category_Human
category_Study
category_Technology
```

Ý nghĩa chuẩn hóa trong project:

| Nếu chuẩn hóa | Nếu không chuẩn hóa |
|---|---|
| Các feature có thang đo tương đương trước khi gán trọng số | Feature có biên độ lớn hơn có thể chi phối khoảng cách |
| `word_length`, `level_encoded`, one-hot category được đưa về cùng không gian so sánh | KNN và KMeans bị lệch theo feature số có scale lớn |
| Trọng số 5.0, 2.0, 0.5 có tác động rõ hơn | Trọng số có thể bị scale tự nhiên của dữ liệu làm méo |

Ảnh hưởng với KNN:

```text
Nếu không chuẩn hóa
  |
  v
Khoảng cách Euclidean bị chi phối bởi feature có scale lớn
  |
  v
Ranking neighbor có thể không còn phản ánh category/level theo ý đồ
```

Ảnh hưởng với KMeans:

```text
Nếu không chuẩn hóa
  |
  v
Centroid dịch về phía feature có scale lớn
  |
  v
Cluster có thể phản ánh độ dài từ hơn là chủ đề từ vựng
```

### 1.3 k-NN

Project sử dụng `sklearn.neighbors.NearestNeighbors(metric="euclidean")`, không dùng classifier có nhãn. Vai trò thực tế là truy hồi các từ gần nhất trong không gian feature.

Vector đặc trưng của một từ:

```text
v(word) = [
  word_length,
  level_encoded,
  category_Daily,
  category_Furniture,
  category_Human,
  category_Study,
  category_Technology
]
```

Sau đó:

```text
scaled_v = StandardScaler(v)
weighted_v = [
  word_length * 0.5,
  level_encoded * 2.0,
  category_* * 5.0
]
```

Euclidean distance:

```text
d(x, y) = sqrt(Σ(x_i - y_i)^2)
```

Flow trong source:

```text
Input word
  |
  v
normalize: strip + lower
  |
  v
lookup exact word trong vocabulary
  |
  v
lấy feature row của word
  |
  v
StandardScaler.transform()
  |
  v
apply_feature_weights()
  |
  v
NearestNeighbors.kneighbors()
  |
  v
bỏ chính từ đầu vào
  |
  v
trả n related words
```

Vì project dùng Euclidean:

| Lý do phù hợp theo source | Nhận xét học thuật |
|---|---|
| Feature là vector số sau chuẩn hóa | Euclidean phù hợp cho không gian vector có scale đã được xử lý |
| Trọng số category/level tạo khoảng cách có chủ ý | Kết quả neighbor phản ánh thiết kế feature hơn là ngữ nghĩa tự nhiên |
| Vocabulary chỉ 12 từ | Brute nearest-neighbor đủ đơn giản |

Nếu đổi metric:

| Metric | Công thức / ý nghĩa | Khả năng thay đổi kết quả |
|---|---|---|
| Manhattan | `Σ|x_i - y_i|` | Ít nhạy hơn với sai khác lớn từng chiều, có thể làm ranking ổn định hơn khi feature rời rạc |
| Minkowski | `(Σ|x_i - y_i|^p)^(1/p)` | Tổng quát hóa Euclidean/Manhattan, cần chọn `p` |
| Cosine | `1 - cos(x, y)` | Tập trung hướng vector hơn độ lớn; có thể không phù hợp bằng Euclidean vì one-hot category và trọng số biên độ đang là tín hiệu chính |

### 1.4 K-Means

Project sử dụng `sklearn.cluster.KMeans` trong `ml/kmeans.py`, với:

| Tham số | Giá trị |
|---|---|
| `n_clusters` | mặc định bằng số category, hiện là 5 |
| `random_state` | 42 |
| `n_init` | 20 |
| `init` | `k-means++` theo report thực nghiệm |
| `max_iter` | 300 theo report thực nghiệm |

K-Means tối ưu tổng bình phương khoảng cách nội cụm:

```text
SSE = Σ Σ ||x_i - c_j||^2
```

Trong đó:

| Ký hiệu | Ý nghĩa |
|---|---|
| `x_i` | vector feature của từ |
| `c_j` | centroid của cluster `j` |
| `SSE` / inertia | tổng sai số nội cụm |

Vòng lặp K-Means:

```text
Khởi tạo centroid
  |
  v
Assignment: gán mỗi điểm vào centroid gần nhất
  |
  v
Update: tính lại centroid bằng trung bình các điểm trong cụm
  |
  v
Lặp lại đến khi hội tụ hoặc đạt max_iter
```

Metric đánh giá theo report:

| Metric | Ý nghĩa toán học | Ý nghĩa trong project |
|---|---|---|
| SSE/Inertia | Tổng bình phương khoảng cách từ điểm đến centroid | Cụm càng chặt thì SSE càng thấp |
| Silhouette | So sánh độ gần trong cụm và độ xa với cụm khác, miền `[-1, 1]` | `0.8106` tại K=5 cho thấy các cụm tách biệt tốt trên feature hiện tại |
| Davies-Bouldin | Tỷ lệ giữa độ phân tán trong cụm và khoảng cách giữa cụm | `0.1654` tại K=5 thấp, nghĩa là cụm tương đối tách biệt |
| Calinski-Harabasz | Tỷ lệ phân tán giữa cụm so với trong cụm | `108.4350` tại K=5 trong report |
| Purity | Tỷ lệ phần tử thuộc category chiếm đa số trong cụm | 100% trong report, nhưng chịu ảnh hưởng mạnh vì category one-hot có trọng số 5.0 |

## 2. Algorithm Validation

### 2.1 Bài Toán AI

```text
Ảnh hoặc webcam frame
  |
  v
YOLOv8 nhận diện object
  |
  v
Tên object tiếng Anh
  |
  v
Vocabulary mapping sang tiếng Việt/category/level
  |
  v
KNN gợi ý từ gần trong vocabulary
  |
  v
KMeans lấy nhóm chủ đề
  |
  v
GUI + history + statistics
```

Đây là hệ thống AI ứng dụng, không phải một mô hình học sâu end-to-end. YOLO xử lý thị giác máy tính; KNN/KMeans xử lý dữ liệu từ vựng nhỏ dựa trên feature thiết kế thủ công.

### 2.2 Tính Đúng Của Thuật Toán Theo Source

| Thành phần | Tính đúng thuật toán | Dẫn chứng |
|---|---|---|
| YOLOv8 | Đúng với cách gọi inference của Ultralytics | `detection/detector.py` gọi `YOLO.predict()` |
| Vocabulary lookup | Đúng với bài toán mapping class sang từ vựng | `dataset/vocabulary.py`, `detection/classify.py` |
| StandardScaler | Đúng quy trình cho distance-based ML | `ml/knn.py`, `ml/kmeans.py` |
| k-NN | Đúng nghĩa nearest-neighbor retrieval | `NearestNeighbors(metric="euclidean")` |
| K-Means | Đúng quy trình clustering | `KMeans(n_clusters=..., random_state=42, n_init=20)` |
| Category Predictor | Chưa phải model ML theo source hiện tại | `ml/category_predictor.py` chỉ lookup vocabulary và fallback `Unknown` |

### 2.3 Mức Đủ Cho Báo Cáo AI

| Phần | Đủ để viết báo cáo? | Lý do |
|---|---|---|
| YOLO application | Có ở mức ứng dụng | Có model weight, inference pipeline, confidence, detection report |
| YOLO training/evaluation học thuật | Chưa đủ | Không tìm thấy train/val/test YOLO dataset trong repo; không có mAP/precision/recall theo ground truth |
| Vocabulary mapping | Có | CSV rõ ràng, 12 từ khớp 12 class |
| KNN | Có ở mức demo thuật toán | Có feature, scaler, metric, n, report n=3/5/7 |
| KMeans | Có ở mức demo clustering | Có K, SSE, silhouette, Davies, Calinski, purity |
| Experimental validation | Chưa đủ để chứng minh toàn diện | Thiếu ground truth từng ảnh, confusion matrix, mAP50/mAP50-95, test độc lập cho vocabulary lớn |

## 3. Feature Engineering Review

### 3.1 Feature Hiện Tại

| Feature | Cách tạo | Vai trò |
|---|---|---|
| `word_length` | độ dài chuỗi `english` | Tín hiệu phụ về hình thức từ |
| `level_encoded` | Easy=0, Medium=1, Hard=2 | Mã hóa độ khó |
| `category_*` | one-hot category | Tín hiệu chủ đề chính |
| StandardScaler | chuẩn hóa toàn bộ feature | Đưa feature về cùng scale |
| Feature weight | category 5.0, level 2.0, word_length 0.5 | Chủ động ép category quan trọng nhất |

### 3.2 Feature Quyết Định Nhiều Nhất

Feature quyết định nhiều nhất là `category_*`, vì source nhân toàn bộ cột category với `CATEGORY_WEIGHT = 5.0`. Điều này làm khoảng cách KNN và centroid KMeans chủ yếu tách theo category.

```text
category weight = 5.0
level weight    = 2.0
length weight   = 0.5
```

Thứ tự ảnh hưởng theo source:

```text
Category > Level > Word Length
```

### 3.3 Feature Ít Ảnh Hưởng

`word_length` ít ảnh hưởng nhất vì có trọng số `0.5`. Với vocabulary hiện tại, độ dài từ không phản ánh ngữ nghĩa trực tiếp. Ví dụ `cup`, `book`, `chair`, `clock` có độ dài gần nhau nhưng không cùng chủ đề.

### 3.4 Feature Có Thể Dư Thừa

| Feature | Nhận xét |
|---|---|
| `word_length` | Có thể dư thừa nếu mục tiêu là gợi ý ngữ nghĩa/chủ đề |
| `level_encoded` | Có ích cho học tập, nhưng hiện chỉ có Easy/Medium, không có Hard |
| `category_*` | Không dư thừa với mục tiêu hiện tại, nhưng quá mạnh khiến KNN/KMeans gần như tái hiện category |

### 3.5 Feature Nên Bổ Sung

Đề xuất dựa trên hiện trạng source, không yêu cầu cài đặt:

| Feature đề xuất | Lý do |
|---|---|
| Word embedding | Bổ sung quan hệ ngữ nghĩa thật giữa từ |
| Sentence Transformer embedding | Gợi ý từ liên quan tự nhiên hơn category thủ công |
| Word2Vec/FastText | Nhẹ hơn transformer, phù hợp vocabulary lớn |
| Object co-occurrence | Gợi ý các vật thường xuất hiện cùng nhau |
| User history frequency | Cá nhân hóa từ gợi ý |
| Learning progress | Ưu tiên từ người học chưa nắm |
| Pronunciation difficulty | Phù hợp mục tiêu học tiếng Anh |

## 4. AI Decision Review

### 4.1 Vì Sao YOLO + Vocabulary + KNN + KMeans Hợp Lý

| Thành phần | Lý do lựa chọn theo mục tiêu project |
|---|---|
| YOLOv8 | Phù hợp nhận diện vật thể realtime từ ảnh/webcam |
| Vocabulary | Chuyển kết quả thị giác thành dữ liệu học tiếng Anh |
| KNN | Gợi ý các từ gần nhau trong không gian đặc trưng |
| KMeans | Nhóm từ theo chủ đề để hỗ trợ học theo cụm |

Quan hệ:

```text
YOLO trả object name
  |
  v
Vocabulary biến object thành nội dung học
  |
  v
KNN mở rộng từ vựng liên quan
  |
  v
KMeans tổ chức từ theo chủ đề
```

### 4.2 Nếu Bỏ KMeans

Hệ thống vẫn nhận diện vật thể, dịch nghĩa và gợi ý KNN được. Tuy nhiên mất chức năng phân cụm/chủ đề. Với mục tiêu đề tài có nêu K-Means, bỏ KMeans sẽ làm project không còn đủ ba thuật toán đã đăng ký.

### 4.3 Nếu Bỏ KNN

Hệ thống vẫn nhận diện vật thể, mapping vocabulary và phân cụm KMeans được. Tuy nhiên mất chức năng gợi ý từ liên quan theo truy vấn. Với mục tiêu học từ vựng, trải nghiệm học sẽ nghèo hơn vì chỉ còn object detect và nhóm cluster.

### 4.4 So Sánh Thuật Toán Thay Thế

| Thay thế | Có thể tốt hơn? | Phân tích |
|---|---|---|
| Decision Tree thay KNN | Không rõ với dữ liệu 12 từ | Cần nhãn dự đoán rõ ràng; hiện KNN là retrieval, không phải classification |
| Random Forest thay KNN | Chưa phù hợp với vocabulary nhỏ | Cần tập train/label đủ lớn; dễ quá mức với 12 từ |
| SVM thay KNN | Chưa phù hợp với chức năng gợi ý | SVM phân loại tốt, nhưng không trực tiếp trả danh sách từ liên quan |
| DBSCAN thay KMeans | Có thể hữu ích khi số cụm không biết trước | Với 12 từ và one-hot category mạnh, KMeans đơn giản hơn |
| Hierarchical clustering | Có thể trực quan hơn cho báo cáo học thuật | Phù hợp biểu diễn cây chủ đề nhưng chưa có trong source |
| Word2Vec/FastText | Tốt hơn về ngữ nghĩa từ | Cần embedding và xử lý OOV |
| Sentence Transformer | Tốt hơn rõ cho semantic similarity | Nặng hơn, cần model embedding |
| CLIP | Tốt hơn nếu muốn nối ảnh và text trong cùng embedding | Phù hợp hướng nghiên cứu mạnh hơn nhưng chưa có trong project |
| FAISS/Vector DB | Tốt khi vocabulary rất lớn | Không cần thiết với 12 từ |

## 5. Complexity Analysis

Ký hiệu:

| Ký hiệu | Ý nghĩa |
|---|---|
| `N` | số từ trong vocabulary |
| `D` | số chiều feature |
| `K` | số cluster KMeans |
| `I` | số vòng lặp KMeans |
| `M` | số ảnh/frame |
| `B` | số box YOLO trả về |
| `H` | số bản ghi history |

### 5.1 Time Complexity

| Thành phần | Time complexity | Theo project |
|---|---|---|
| YOLO inference | phụ thuộc kiến trúc model và kích thước ảnh | Bottleneck chính; report trung bình `153.909 ms` trên 24 ảnh |
| Postprocess YOLO trong source | `O(B)` | Lặp qua boxes và lọc class |
| Vocabulary lookup dict | xấp xỉ `O(1)` sau khi cache | `dataset/vocabulary.py` cache `_VOCAB_CACHE` |
| KNN train | `O(ND)` để fit NearestNeighbors brute structure | N=12 nên nhỏ |
| KNN query brute | `O(ND)` | Report system trung bình `10.344 ms` |
| KMeans train | `O(NKDI)` | Report train `3996.8391 ms` |
| KMeans word lookup | `O(N)` do lọc DataFrame theo `english` | N=12 nên nhỏ |
| Database insert history | thường `O(1)` theo thao tác insert | phụ thuộc mạng PostgreSQL/Supabase |
| History stats | `O(H)` | `StatsWorker` đọc tối đa 500 bản ghi |

### 5.2 Space Complexity

| Thành phần | Space complexity | Theo project |
|---|---|---|
| YOLO model | phụ thuộc weight | `models/best.pt` khoảng 6.23 MB |
| Vocabulary | `O(N)` | 12 dòng |
| Feature matrix | `O(ND)` | 12 x 7 hiện tại |
| KNN model data | `O(ND + N)` | lưu feature, scaler, vocabulary |
| KMeans model data | `O(ND + KD + N)` | lưu centroid/model, feature, labels |
| History result | `O(H)` | giới hạn query có `limit` |

### 5.3 Bottleneck

| Bottleneck | Bằng chứng |
|---|---|
| YOLO inference | Thời gian trung bình `153.909 ms`, cao hơn KNN/KMeans trong report hệ thống |
| KMeans training | Report riêng ghi train `3996.8391 ms`; runtime có cache nên thường không train lại |
| Database network | Source dùng PostgreSQL remote qua `.env`; thời gian phụ thuộc kết nối |
| GUI webcam loop | YOLO, drawing, KNN/KMeans, emit frame nằm trong luồng webcam |

## 6. Scalability Review

### 6.1 Vocabulary Scale

| Vocabulary size | Điều xảy ra với source hiện tại |
|---:|---|
| 12 | Hoạt động phù hợp demo; KNN/KMeans rất nhỏ |
| 500 | KNN brute force vẫn chấp nhận được; KMeans train nhanh; CSV vẫn ổn |
| 5,000 | KNN query bắt đầu tăng tuyến tính; DataFrame lookup vẫn dùng được nhưng nên index |
| 50,000 | KNN brute force và KMeans training có thể chậm; cần approximate nearest neighbor hoặc vector index |
| 500,000 | Cách hiện tại không còn phù hợp; cần embedding store, FAISS/vector DB, batch training và data pipeline rõ |

Tác động học thuật:

| Thành phần | Khi vocabulary lớn |
|---|---|
| One-hot category | Số chiều tăng theo số category, nhưng không theo số từ |
| Word length | Vẫn rẻ nhưng ít giá trị ngữ nghĩa |
| KNN brute force | Tăng tuyến tính theo N |
| KMeans | Tăng theo `N*K*D*I` |
| CSV | Có thể trở thành điểm nghẽn quản trị dữ liệu |

### 6.2 Dataset Image Scale

| Dataset ảnh | Điều xảy ra |
|---:|---|
| 24 | Chỉ đủ demo kiểm thử hệ thống, không đủ kết luận học thuật mạnh |
| 1,000 | Có thể tính precision/recall nếu có ground truth |
| 10,000 | Cần pipeline đánh giá tự động, annotation và thống kê class balance |
| 100,000 | Cần quản lý dataset chuẩn, split cố định, versioning, training/evaluation script rõ |

Điểm thiếu hiện tại khi scale ảnh: không tìm thấy ground truth cho từng ảnh test trong source code hiện tại, nên chưa tính được mAP, confusion matrix, precision, recall, F1-score.

## 7. Experiment Validation

### 7.1 Số Liệu Hiện Có

| Metric | Giá trị trong report |
|---|---:|
| Số ảnh report hệ thống | 24 |
| YOLO detect được | 21 |
| YOLO Detection Rate | 87.50% |
| YOLO Confidence trung bình trên ảnh detect | 89.34% |
| YOLO time trung bình | 153.909 ms |
| Vocabulary Coverage | 87.50% |
| KNN Success Rate trên tổng ảnh | 87.50% |
| KNN Success Rate trên ảnh YOLO detect | 100.00% |
| KNN Category Precision trung bình | 55.56% |
| KNN time trung bình | 10.344 ms |
| KMeans Success Rate trên tổng ảnh | 87.50% |
| KMeans Success Rate trên ảnh YOLO detect | 100.00% |
| KMeans Cluster Purity trung bình theo từ | 100.00% |
| KMeans time trung bình | 3.683 ms |
| KMeans Silhouette tại K=5 | 0.8106 |
| KMeans Davies tại K=5 | 0.1654 |
| KMeans Calinski tại K=5 | 108.4350 |

### 7.2 KNN Validation

Report KNN:

| n | Tested words | Suggestions | Category Precision | Level Precision | MRR Category |
|---:|---:|---:|---:|---:|---:|
| 3 | 10 | 30 | 60.00% | 70.00% | 0.9000 |
| 5 | 10 | 50 | 36.00% | 44.00% | 0.9000 |
| 7 | 10 | 70 | 25.71% | 51.43% | 0.9000 |

Nhận xét học thuật:

| Điểm | Nhận xét |
|---|---|
| n=3 tốt nhất trong report | Có category precision cao nhất và mean distance thấp nhất |
| MRR 0.9 | Gợi ý đúng category thường xuất hiện sớm |
| Precision giảm khi n tăng | Hợp lý vì vocabulary nhỏ, lấy nhiều neighbor sẽ kéo sang category khác |
| Hạn chế | Evaluation dùng chính vocabulary fit model, chưa có user study hoặc nhãn relevance độc lập |

### 7.3 KMeans Validation

Report KMeans:

| K | SSE | Silhouette | Calinski | Davies |
|---:|---:|---:|---:|---:|
| 2 | 1143.3566 | 0.3434 | 3.5653 | 0.8221 |
| 3 | 763.6936 | 0.5347 | 4.6391 | 0.6885 |
| 4 | 384.6031 | 0.7154 | 8.0873 | 0.5227 |
| 5 | 24.6336 | 0.8106 | 108.4350 | 0.1654 |
| 6 | 10.7192 | 0.7520 | 172.4327 | 0.1318 |
| 7 | 0.7123 | 0.6288 | 1813.6378 | 0.0337 |
| 8 | 0.3836 | 0.4700 | 2310.1020 | 0.0243 |

K=5 được chọn trong report. Điều này khớp với số category hiện tại là 5. Tuy nhiên cần lưu ý: vì category one-hot được nhân trọng số 5.0, cluster purity 100% chủ yếu chứng minh feature category chi phối clustering, chưa chứng minh hệ thống học được quan hệ ngữ nghĩa độc lập.

### 7.4 Metric Hiện Tại Có Đủ Không?

| Nhóm | Đủ chưa? | Lý do |
|---|---|---|
| Demo end-to-end | Tương đối đủ | Có detection rate, coverage, KNN/KMeans success, timing |
| Đánh giá YOLO học thuật | Chưa đủ | Thiếu ground truth, precision, recall, F1, mAP50, mAP50-95 |
| Đánh giá KNN học thuật | Chưa đủ mạnh | Thiếu nhãn relevance độc lập, user evaluation, top-k hit rate theo ground truth |
| Đánh giá KMeans học thuật | Có metric nội bộ nhưng còn yếu | Purity dùng category có sẵn và category cũng là feature đầu vào |
| Đánh giá hệ thống học tiếng Anh | Chưa đủ | Không có user study, retention, quiz score, learning outcome |

Metric còn thiếu:

```text
YOLO:
  - Precision
  - Recall
  - F1-score
  - mAP50
  - mAP50-95
  - Confusion Matrix
  - Per-class AP

KNN:
  - Top-k relevance accuracy
  - Hit@k
  - NDCG@k
  - User-rated relevance

KMeans:
  - External validation trên nhãn độc lập
  - Adjusted Rand Index nếu có label
  - Normalized Mutual Information
  - Stability across random seeds

Learning system:
  - User learning gain
  - Quiz accuracy before/after
  - Retention rate
```

## 8. Academic Critique

### 8.1 Điểm Mạnh

| Điểm mạnh | Dẫn chứng |
|---|---|
| Có pipeline AI hoàn chỉnh từ ảnh đến từ vựng | YOLO -> vocabulary -> KNN/KMeans -> GUI/history |
| Có dùng mô hình thị giác hiện đại | `ultralytics.YOLO`, weight `best.pt` |
| Có thuật toán supervised-like retrieval và unsupervised clustering | `NearestNeighbors`, `KMeans` |
| Có thực nghiệm hệ thống | `system_image_evaluation_report.txt` |
| Có metric cho KMeans | SSE, Silhouette, Davies-Bouldin, Calinski-Harabasz, purity |
| Có xử lý trường hợp từ không tồn tại | KNN report special cases |

### 8.2 Điểm Yếu Học Thuật

| Điểm yếu | Phân tích |
|---|---|
| YOLO thiếu ground truth evaluation | Detection Rate hiện chỉ đo có detect hay không, không xác nhận đúng object |
| Không có mAP | Chưa chứng minh chất lượng detection theo chuẩn object detection |
| Vocabulary quá nhỏ | 12 từ đủ demo nhưng yếu cho nghiên cứu ML |
| KNN/KMeans phụ thuộc category thủ công | Category vừa là input feature vừa là tiêu chí đánh giá |
| Cluster purity 100% có thể gây hiểu nhầm | Vì feature category one-hot trọng số cao làm cluster khớp category |
| Category Predictor chưa phải model ML | File artifact tồn tại nhưng source không load |
| Dataset YOLO train/valid/test không có trong repo | Không kiểm chứng được training và split |
| Không có ablation study | Chưa so sánh bỏ weight, bỏ scaler, đổi metric |
| Không có user study | Chưa chứng minh hiệu quả học tiếng Anh |

### 8.3 Điểm Chưa Thuyết Phục Khi Bảo Vệ

| Chủ đề | Điểm hội đồng có thể chất vấn |
|---|---|
| YOLO | `best.pt` được train như thế nào, dataset đâu, mAP bao nhiêu |
| KNN | Vì sao dùng category làm feature rồi lại đánh giá same-category |
| KMeans | Vì sao K=5, có phải vì đã biết 5 category từ trước |
| Vocabulary | 12 từ có đủ để gọi là hệ thống học từ vựng không |
| Experiment | Detection Rate không thay thế được accuracy/precision/recall |
| Learning outcome | Chưa đo người học tiến bộ như thế nào |

## 9. Defense Questions

### 9.1 Dataset

| # | Câu hỏi phản biện | Đáp án mẫu | Gợi ý trả lời |
|---:|---|---|---|
| 1 | Dataset YOLO train/valid/test nằm ở đâu? | Trong repo hiện tại chỉ có `dataset.yaml` trỏ tới `dataset/yolo_dataset`, nhưng thư mục này không tìm thấy. | Trả lời trung thực theo source; nếu có dữ liệu ngoài repo thì nói rõ không được đóng gói trong project hiện tại. |
| 2 | Vì sao vocabulary chỉ có 12 từ? | Vì project chọn 12 class COCO liên quan đến đồ vật/học tập/sinh hoạt. | Nhấn mạnh đây là phạm vi demo ban đầu. |
| 3 | Dataset có bị imbalance không? | Vocabulary có imbalance: Technology 4, Daily 3, Human 1, Hard 0. | Nêu số liệu cụ thể từ report. |
| 4 | Có ground truth cho ảnh test không? | Không tìm thấy ground truth từng ảnh trong source code hiện tại. | Không gọi Detection Rate là accuracy. |
| 5 | Có data leakage không? | YOLO không đánh giá được vì thiếu train/test trong repo; KNN/KMeans fit và evaluate trên cùng vocabulary. | Phân biệt rõ hai phần. |

### 9.2 YOLO

| # | Câu hỏi phản biện | Đáp án mẫu | Gợi ý trả lời |
|---:|---|---|---|
| 6 | YOLOv8 được dùng ở đâu? | `detection/detector.py` load `YOLO(model_path)` và gọi `model.predict()`. | Dẫn source cụ thể. |
| 7 | Confidence threshold là bao nhiêu? | `0.5` trong `utils/config.py`. | Nói rõ không thấy tuning threshold trong source. |
| 8 | IOU threshold là bao nhiêu? | Không tìm thấy trong source code hiện tại; Ultralytics dùng mặc định. | Không tự bịa giá trị. |
| 9 | NMS nằm ở đâu? | Không triển khai trực tiếp, nằm trong pipeline `YOLO.predict()` của Ultralytics. | Phân biệt code project và thư viện. |
| 10 | Detection Rate 87.50% có phải accuracy không? | Không. Report ghi không có ground truth, nên đây là tỷ lệ ảnh có detection. | Dùng thuật ngữ chính xác. |
| 11 | Có mAP không? | Không tìm thấy trong source/report hiện tại. | Đề xuất cần annotation để tính. |
| 12 | Model `best.pt` là pretrained hay custom? | Source comment nói đã fine-tune trên Google Colab, nhưng không có script train trong repo. | Nêu mức bằng chứng. |
| 13 | Vì sao chọn YOLO thay Faster R-CNN? | YOLO phù hợp realtime và GUI webcam hơn. | Nhấn mạnh tradeoff tốc độ. |
| 14 | Nếu YOLO detect sai thì hệ thống thế nào? | Tên object sai làm vocabulary, KNN, KMeans đều chạy theo từ sai. | Đây là lỗi lan truyền pipeline. |
| 15 | Nếu YOLO không detect thì KNN/KMeans có chạy không? | Theo report system, các ảnh `none` có KNN/KMeans success false và time 0. | Dựa vào report chi tiết. |

### 9.3 Vocabulary

| # | Câu hỏi phản biện | Đáp án mẫu | Gợi ý trả lời |
|---:|---|---|---|
| 16 | Vocabulary lưu ở đâu? | `dataset/vocabulary.csv`. | Nêu 4 cột english, vietnamese, category, level. |
| 17 | Vocabulary coverage là gì? | Tỷ lệ object detected có trong vocabulary; report hệ thống ghi 87.50% trên tổng ảnh. | Giải thích không phải coverage tiếng Anh tổng quát. |
| 18 | Nếu thiếu từ trong vocabulary thì sao? | Lookup không có; KNN/KMeans trả rỗng hoặc fallback Unknown tùy bước. | Nêu theo source `get_related_words` và `get_cluster_by_word`. |
| 19 | Có synonym không? | Không tìm thấy cột synonym trong vocabulary hiện tại. | Không tự thêm. |
| 20 | Có level Hard không? | Mapping có Hard=2 nhưng dữ liệu hiện tại không có dòng Hard. | Dẫn report KNN/KMeans. |

### 9.4 Feature

| # | Câu hỏi phản biện | Đáp án mẫu | Gợi ý trả lời |
|---:|---|---|---|
| 21 | Feature của KNN/KMeans là gì? | `word_length`, `level_encoded`, one-hot category. | Nêu giống source. |
| 22 | Vì sao phải StandardScaler? | Vì KNN/KMeans dựa trên khoảng cách; chuẩn hóa tránh scale tự nhiên chi phối. | Viết công thức z-score. |
| 23 | Feature nào quan trọng nhất? | Category, vì weight 5.0. | Nêu thứ tự category > level > length. |
| 24 | Word length có phản ánh ngữ nghĩa không? | Rất hạn chế; đây chỉ là feature phụ. | Thừa nhận điểm yếu. |
| 25 | Category có bị circular evaluation không? | Có rủi ro, vì category là feature và same-category/purity cũng là metric. | Đây là điểm cần cải thiện học thuật. |

### 9.5 KNN

| # | Câu hỏi phản biện | Đáp án mẫu | Gợi ý trả lời |
|---:|---|---|---|
| 26 | KNN trong project dùng để làm gì? | Gợi ý từ liên quan bằng nearest-neighbor retrieval. | Không gọi là classifier nếu không dự đoán nhãn. |
| 27 | Metric KNN là gì? | Euclidean distance. | Dẫn `NearestNeighbors(metric="euclidean")`. |
| 28 | Giá trị n tốt nhất trong report? | n=3, category precision 60.00%, MRR 0.9000. | Dẫn report KNN. |
| 29 | Vì sao precision giảm khi n tăng? | Vocabulary nhỏ; lấy nhiều neighbor sẽ kéo sang category khác. | Liên hệ n=5 và n=7. |
| 30 | Nếu dùng cosine distance thì sao? | Ranking có thể đổi vì cosine chú trọng hướng vector hơn độ lớn trọng số. | Nói cần thực nghiệm, chưa có trong source. |

### 9.6 KMeans

| # | Câu hỏi phản biện | Đáp án mẫu | Gợi ý trả lời |
|---:|---|---|---|
| 31 | KMeans dùng để làm gì? | Phân cụm vocabulary để lấy nhóm chủ đề/từ cùng cụm. | Dẫn `get_words_in_same_cluster`. |
| 32 | K được chọn thế nào? | Source mặc định lấy số category unique, hiện là 5; report cũng chọn K=5. | Tách source và report. |
| 33 | Silhouette K=5 là bao nhiêu? | 0.8106. | Nêu metric từ report. |
| 34 | Purity 100% có mạnh không? | Có nhưng cần thận trọng vì category one-hot là feature trọng số cao. | Tránh diễn giải quá mức. |
| 35 | Nếu K=7 SSE thấp hơn thì sao không chọn? | SSE luôn giảm khi K tăng; K=5 có silhouette cao nhất trong bảng và khớp số category. | Giải thích metric tradeoff. |

### 9.7 Experiment

| # | Câu hỏi phản biện | Đáp án mẫu | Gợi ý trả lời |
|---:|---|---|---|
| 36 | Report hệ thống chạy trên bao nhiêu ảnh? | 24 ảnh theo `system_image_evaluation_report.txt`. | Nêu folder hiện có 30 ảnh nhưng report dùng 24. |
| 37 | YOLO detect rate là bao nhiêu? | 87.50%, detect 21/24 ảnh. | Không gọi là accuracy. |
| 38 | Average confidence là bao nhiêu? | 89.34% trên ảnh detect. | Nêu đây là confidence model, không phải độ đúng ground truth. |
| 39 | KNN success rate là bao nhiêu? | 87.50% trên tổng ảnh, 100% trên ảnh YOLO detect. | Theo report system. |
| 40 | KMeans success rate là bao nhiêu? | 87.50% trên tổng ảnh, 100% trên ảnh YOLO detect. | Theo report system. |
| 41 | Có confusion matrix không? | Không tìm thấy trong source/report hiện tại. | Đề xuất cần ground truth. |
| 42 | Có mAP50-95 không? | Không tìm thấy trong source/report hiện tại. | Đây là điểm thiếu chính của object detection evaluation. |

### 9.8 Performance

| # | Câu hỏi phản biện | Đáp án mẫu | Gợi ý trả lời |
|---:|---|---|---|
| 43 | Thành phần chậm nhất là gì? | YOLO inference trong runtime hệ thống, trung bình 153.909 ms. | KMeans train riêng chậm nhưng runtime thường cache. |
| 44 | KNN time trung bình? | 10.344 ms trong report hệ thống. | Có thể tăng tuyến tính khi vocabulary lớn. |
| 45 | KMeans time trung bình? | 3.683 ms trong report hệ thống; train riêng 3996.8391 ms. | Phân biệt predict/lookup và train. |
| 46 | Webcam realtime có đảm bảo FPS không? | Không tìm thấy FPS benchmark đầy đủ trong source/report hiện tại. | Dựa trên thời gian YOLO có thể suy luận cần đo thêm, nhưng không kết luận chắc. |

### 9.9 Architecture

| # | Câu hỏi phản biện | Đáp án mẫu | Gợi ý trả lời |
|---:|---|---|---|
| 47 | Module AI có phụ thuộc GUI không? | `ml/knn.py` và `ml/kmeans.py` không phụ thuộc GUI; controller GUI gọi trực tiếp ML. | Phân biệt chiều phụ thuộc. |
| 48 | Database dùng khi nào? | Auth, lưu history detection, đọc history/statistics. | Theo `database/auth.py`, `database/history.py`. |
| 49 | Có thread nào chạy AI không? | Image detection dùng `ImageDetectThread`; webcam dùng `WebcamThread`. | Nêu shared detector là rủi ro kỹ thuật nếu bị hỏi. |
| 50 | Có model category thật không? | Có artifact `word_category_model.joblib`, nhưng source `category_predictor.py` không load model. | Trả lời đúng hiện trạng. |

### 9.10 Future Work

| # | Câu hỏi phản biện | Đáp án mẫu | Gợi ý trả lời |
|---:|---|---|---|
| 51 | Cải tiến AI ưu tiên nhất là gì? | Bổ sung ground truth và tính mAP/precision/recall cho YOLO. | Đây là P0 học thuật. |
| 52 | Làm sao cải thiện KNN? | Thay feature thủ công bằng embedding như Word2Vec/FastText/Sentence Transformer. | Gắn với mục tiêu semantic related words. |
| 53 | Làm sao cải thiện KMeans? | Cluster trên embedding ngữ nghĩa và đánh giá bằng stability/external labels. | Không chỉ cluster theo category thủ công. |
| 54 | Khi vocabulary 50.000 từ thì dùng gì? | Approximate nearest neighbor như FAISS hoặc vector database. | KNN brute force hiện tại không phù hợp scale lớn. |
| 55 | Làm sao chứng minh hiệu quả học tiếng Anh? | Thiết kế user study hoặc quiz trước/sau khi học. | Đây là metric giáo dục, khác metric AI. |

## 10. Future AI Roadmap

### P0 - Bằng Chứng Học Thuật Bắt Buộc

| Hạng mục | Mục tiêu |
|---|---|
| Ground truth cho ảnh test | Cho phép tính precision, recall, F1, confusion matrix |
| YOLO mAP50/mAP50-95 | Đánh giá đúng chuẩn object detection |
| Split dataset rõ ràng | Chứng minh train/validation/test không lẫn |
| Per-class report | Biết class nào tốt/yếu |

### P1 - Cải Thiện Feature Và Relevance

| Hạng mục | Mục tiêu |
|---|---|
| Sentence embedding | Gợi ý từ theo ngữ nghĩa thật |
| Word2Vec/FastText | Giải pháp nhẹ hơn transformer |
| Ablation study | So sánh có/không scaler, weight, category |
| Top-k relevance labels | Đánh giá KNN bằng nhãn liên quan độc lập |

### P2 - Mở Rộng Hệ Thống AI

| Hạng mục | Mục tiêu |
|---|---|
| CLIP | Liên kết ảnh và text trong cùng embedding |
| FAISS | Tìm kiếm vector nhanh khi vocabulary lớn |
| Vector database | Quản lý embedding và metadata |
| User learning model | Cá nhân hóa gợi ý theo lịch sử học |

### P3 - Nghiên Cứu Nâng Cao

| Hạng mục | Mục tiêu |
|---|---|
| LLM explanation | Sinh ví dụ câu, giải thích nghĩa, ngữ cảnh dùng từ |
| Active learning | Thu thập feedback người dùng để cải thiện vocabulary |
| Multimodal learning | Kết hợp object, scene, text, audio |
| Educational evaluation | Đánh giá hiệu quả học thật qua thử nghiệm người dùng |

## 11. Final Evaluation

Thang điểm: 10 là tốt nhất, dựa trên source/report hiện tại.

| Hạng mục | Điểm | Nhận xét |
|---|---:|---|
| Dataset | 5 | Vocabulary rõ nhưng nhỏ; YOLO dataset train/valid/test không có trong repo hiện tại |
| YOLO | 7 | Pipeline inference đúng, có weight và report; thiếu mAP/ground truth |
| Feature Engineering | 6 | Có scaler và weight rõ; feature còn thủ công và category chi phối mạnh |
| Vocabulary | 6 | Mapping đủ 12 class; thiếu synonym, examples, pronunciation metadata |
| KNN | 6 | Retrieval đúng, n=3 có report; validation chưa độc lập |
| KMeans | 6 | Có metric nội bộ tốt; purity bị ảnh hưởng bởi category feature |
| Experiment | 5 | Có số liệu end-to-end; thiếu metric chuẩn object detection |
| Architecture | 6 | Module AI tách file riêng; controller vẫn gọi trực tiếp nhiều logic |
| Academic Value | 6 | Có kết hợp CV + ML + education; độ sâu nghiên cứu còn hạn chế |
| Innovation | 5 | Kết hợp hợp lý nhưng chưa mới về thuật toán |
| Report Readiness | 6 | Đủ viết báo cáo demo nếu trình bày đúng giới hạn |
| Defense Readiness | 5 | Bảo vệ được nếu trung thực; dễ bị hỏi về dataset, mAP, feature leakage |

### Kết Luận Học Thuật

Hệ thống có cơ sở thuật toán đúng ở mức ứng dụng: YOLOv8 nhận diện vật thể, vocabulary mapping chuyển kết quả thành nội dung học tiếng Anh, KNN truy hồi từ liên quan và KMeans phân cụm từ vựng. Các bước StandardScaler, Euclidean distance, weighted feature và KMeans clustering đều có cơ sở toán học rõ trong source.

Điểm yếu học thuật chính là phần chứng minh thực nghiệm. Report hiện tại có Detection Rate, confidence, thời gian, KNN precision theo category và KMeans purity, nhưng không có ground truth cho ảnh nên chưa đủ để chứng minh chất lượng YOLO theo chuẩn nghiên cứu. Với KNN/KMeans, category vừa là feature quan trọng nhất vừa là tiêu chí đánh giá, nên kết quả tốt cần được diễn giải thận trọng.

Project đủ nền tảng để viết báo cáo AI dạng đồ án ứng dụng nếu báo cáo trung thực theo hiện trạng source code. Để bảo vệ thuyết phục hơn, ưu tiên cao nhất là bổ sung ground truth, tính mAP/precision/recall cho YOLO và đánh giá KNN/KMeans bằng nhãn relevance hoặc embedding ngữ nghĩa độc lập.

Giai đoạn 3.5 hoàn thành.

Đã đánh giá toàn bộ hệ thống dưới góc nhìn nghiên cứu khoa học và sẵn sàng chuyển sang Giai đoạn 4: Architecture Refactoring & System Improvement.
