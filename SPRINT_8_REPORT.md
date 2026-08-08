# SPRINT 8 REPORT - TESTING & PERFORMANCE

Sprint cuoi. Pham vi: chuan hoa bo test, do do phu, do hieu nang end-to-end va
toi uu diem nghen.

Rang buoc da tuan thu:

| Rang buoc | Ket qua |
|---|---|
| Khong doi ket qua AI | Cung anh, cung 5 vat the, cung nhan, cung confidence |
| Khong sua QML | Khong file nao trong `ui/qml/` bi sua |
| Khong sua thuat toan | `ml/`, `detection/`, `dataset/` **nguyen ven** |
| Bo test khong duoc sua artifact mo hinh | Da co test tu dong khang dinh |
| Regression Test PASS | **392/392 test PASS** |

---

## 1. TEST INVENTORY (NHIEM VU 1)

### 1.1 Truoc Sprint 8

`test/` co 23 file `.py` tron lan ba loai hoan toan khac nhau:

| Loai | File | Van de |
|---|---|---|
| Unit test that | 12 file, 366 test | (khong co van de) |
| Script can moi truong that | `test_connection.py`, `test_login.py`, `test_yolo_image.py`, `test_system_evaluation.py`, `test_ml.py` | Can database that / YOLO that |
| Script **ghi de mo hinh** | `test_knn.py`, `test_kmeans.py` | Train lai va **ghi de `models/*.pkl`** |
| Benchmark | `benchmark_database.py`, `benchmark_thread.py` | Can database that |

Ca 7 script deu co ten `test_*.py` nen **`pytest` se thu gom va chay het**.
Hau qua khi chay `pytest` truoc Sprint 8:

1. Ghi de `models/knn.pkl` va `models/kmeans.pkl`.
2. Ket noi database that, `test_login.py` co the tao du lieu that.
3. Nap YOLO (~12 giay).

Bo test phai chay duoc **moi luc, tren may bat ky, khong de lai dau vet**.
Diem nay khong dat.

### 1.2 Sau Sprint 8

```text
test/                     <- BO TEST TU DONG (pytest thu gom)
  test_ai_engine.py            7   Sprint 2
  test_repository.py          40   Sprint 4
  test_database_service.py    32   Sprint 4
  test_worker.py              24   Sprint 3
  test_viewmodel.py           42   Sprint 3
  test_controller.py          34   Sprint 3
  test_cancellation.py        31   Sprint 5
  test_thread_safety.py       16   Sprint 5
  test_config.py              55   Sprint 6
  test_di.py                  22   Sprint 6
  test_logging.py             35   Sprint 7
  test_error_handling.py      28   Sprint 7
  test_integration.py         26   Sprint 8  (moi)
  ui_fakes.py / db_fakes.py        (ho tro)

test/manual/              <- SCRIPT CHAY TAY (pytest KHONG thu gom)
  test_connection.py             can database that
  test_login.py                  can database that, co the tao du lieu
  test_ml.py                     can model .pkl
  test_knn.py                    GHI DE models/knn.pkl
  test_kmeans.py                 GHI DE models/kmeans.pkl
  test_yolo_image.py             can YOLO that
  test_system_evaluation.py      can YOLO + database
  benchmark_database.py          can database that (chi doc)
  benchmark_thread.py            can database that (chi doc)
  benchmark_app.py               can YOLO (moi - Sprint 8)
```

`test/manual/__init__.py` ghi ro tung file can gi va file nao ghi de mo hinh.

---

## 2. TEST PYRAMID (NHIEM VU 2)

```text
                    ┌─────────────────┐
                    │  Manual (10)    │   Can DB / YOLO / webcam that
                    │  test/manual/   │   Chay tay, khong tu dong
                    └────────┬────────┘
                 ┌───────────┴───────────┐
                 │  Integration (26)     │   Nhieu tang that chay cung nhau
                 │  test_integration.py  │   Chi AI/camera/con tro DB la gia
                 └───────────┬───────────┘
      ┌──────────────────────┴──────────────────────┐
      │              Unit (366)                     │   Moi test soi mot lop
      │  12 module theo tang: AI, Repository,       │
      │  Service, Worker, ViewModel, Controller,    │
      │  Config, DI, Logging, Error                 │
      └─────────────────────────────────────────────┘
```

| Muc | So test | Chay trong | Can gi |
|---|---:|---|---|
| Unit | 366 | ~8 giay | Khong can gi |
| Integration | 26 | ~5 giay | Khong can gi |
| Manual | 10 script | thay doi | Database / YOLO / webcam |

### Integration test kiem gi

| Nhom | Noi dung |
|---|---|
| `FullStackDetectionTest` | Controller -> ViewModel -> Worker -> Service -> Repository, kiem tra cau `INSERT INTO history` that su chay voi dung `user_id` |
| `WebcamIntegrationTest` | Luong webcam that qua Controller, kiem tra backpressure end-to-end |
| `StartupBudgetTest` | Chot chan hieu nang (xem muc 5) |
| `LazyLoadingTest` / `WarmupWorkerTest` | Co che nap tre |
| `TestSuiteDisciplineTest` | Ky luat cua chinh bo test |

---

## 3. TEST RUNNER (NHIEM VU 4)

### Truoc

Moi bao cao ghi mot lenh khac nhau, khong ai nho het:

```bash
python -m unittest test.test_ai_engine test.test_config test.test_di ...
python test/test_knn.py
python test/benchmark_database.py
```

### Sau

```bash
python run_tests.py                # toan bo bo test tu dong
python run_tests.py --coverage     # kem do phu + bao cao HTML
python run_tests.py --unittest     # dung unittest, khong can pytest
python run_tests.py --list         # xem co nhung gi
```

`pytest.ini` khai bao:

- `testpaths = test` — chi thu gom trong `test/`.
- `norecursedirs = test/manual` — **script chay tay khong bao gio bi thu gom**.
- `--strict-markers` — sai ten marker la bao loi ngay.

`run_tests.py` tu quay ve `unittest` neu may chua cai `pytest`, nen luon chay duoc.

### Bao dam cua lenh nay

| Bao dam | Kiem chung bang |
|---|---|
| Khong can YOLO | 392 test chay xong trong 12,7 giay |
| Khong can PostgreSQL | Toan bo dung `FakeCursorFactory` |
| Khong can webcam | Toan bo dung `FakeCamera` |
| **Khong ghi de `models/*.pkl`** | `test_automated_suite_does_not_touch_model_artifacts` |
| Khong tao du lieu that | `test_manual_scripts_are_out_of_collection` |

---

## 4. COVERAGE (NHIEM VU 3)

```bash
python run_tests.py --coverage
```

Nguong toi thieu: **80%**. Ket qua: **84,69%** — dat.

Pham vi do: `core/`, `config/`, `database/`, `ui/` — tuc la ma nguon do Sprint 3-8
viet ra. `ml/`, `detection/`, `dataset/` la ma AI goc, khong nam trong pham vi
tai cau truc nen khong dat nguong.

### Do phu theo tang

| Tang | Do phu |
|---|---:|
| `config/` | 87-99% |
| `core/` | 94-98% |
| `ui/viewmodels/` | 74-97% |
| `ui/services/` | 35-97% |
| `ui/workers/` | 38-96% |
| `database/` | 37-82% |

### Cho co do phu thap - va ly do

| Module | Do phu | Ly do |
|---|---:|---|
| `ui/main_qt.py` | 0% | Bootstrap Qt, can cua so that |
| `ui/video_item.py` | 0% | Custom QML item, can QML runtime |
| `ui/speech_worker.py` | 0% | Shim tuong thich, test dung duong dan moi |
| `database/connection.py` | 37% | Duong ket noi that - test dung con tro gia (dung y do) |
| `database/auth.py` | 50% | Shim tuong thich cua Sprint 4 |
| `ui/workers/webcam_worker.py` | 54% | Vong lap camera chay trong QThread (xem ghi chu duoi) |

### Ghi chu quan trong ve con so nay

`coverage.py` **khong theo doi day du ma chay ben trong `QThread`**: than
`run()` duoc Qt goi tu C++ nen bo dem khong bat het. Vi vay `webcam_worker.py`
(54%) va `warmup_worker.py` (46%) bi bao **thap hon thuc te** — ca hai deu co test
chay that va khang dinh ket qua.

Con so 84,69% do la **uoc luong duoi**, khong phai uoc luong tren.

Bao cao HTML: `docs/coverage/index.html`.

---

## 5. PERFORMANCE BASELINE (NHIEM VU 5)

Do bang `python test/manual/benchmark_app.py` tren may that, YOLO that,
database Supabase that.

### 5.1 Diem nghen tim duoc

```text
1. KHOI DONG (truoc toi uu)
Buoc                                    Thoi gian    RAM tang
----------------------------------------------------------------
import torch                              2.386 ms   171,4 MB
import ultralytics                           94 ms    10,0 MB
import cv2                                    0 ms     0,0 MB
import PySide6.QtQuick                        90 ms    13,1 MB
nap cau hinh (load_config)                  243 ms     3,2 MB
nap tu vung (sklearn + pandas di kem)     4.848 ms   324,7 MB   <-- lon nhat
nap model k-NN (.pkl)                     1.888 ms    -1,0 MB
nap model K-Means (.pkl)                     88 ms     1,1 MB
nap YOLO (ObjectDetector)                   431 ms    18,0 MB
----------------------------------------------------------------
TONG                                     10.067 ms   571,0 MB
```

**Toan bo 10 giay nay xay ra TRUOC khi cua so hien ra.** Nguoi dung bam chay va
nhin man hinh trang trong 10 giay.

Va gan nhu toan bo la **chi phi import thu vien**, khong phai tinh toan:
`all_words()` chay xong trong **0 ms** sau khi module da nap.

### 5.2 Nhan dien anh (khong doi)

| Chi so | Gia tri |
|---|---:|
| Anh | `test1.jpg` 500x375 |
| Vat the phat hien | 5 |
| Trung vi | **61 ms** |
| Min / Max | 55 / 69 ms |
| Trong do YOLO | 61,4 ms |
| Tu vung / k-NN / K-Means | 0,0 ms (nho cache tu Sprint 2) |

### 5.3 Webcam

| Chi so | Gia tri |
|---|---:|
| FPS (camera gia) | **133,7** |
| Frame bi bo | 0 |
| RAM tang | ~0 MB |

Duong ong xu ly khong phai la diem nghen: 133 FPS trong khi AI chi chay 4 lan/giay.

---

## 6. TOI UU (NHIEM VU 6)

### 6.1 Ba nguyen nhan tim duoc

**Nguyen nhan 1 — `ai/__init__.py` nap san moi thu.**

```python
from ai.detector import ObjectDetector   # -> ultralytics + torch
from ai.kmeans import ...                # -> scikit-learn + pandas
from ai.knn import ...                   # -> scikit-learn
```

Nen **bat ky** import nao tu `ai.*` cung tra gia day du:

```
from ai.models import ImageAnalysisResult   # chi can 1 dataclass
   -> 6.662 ms
```

`AppContext.build()` chi can lop dieu phoi `AIEngine`, nhung phai cho gan 7 giay.

**Nguyen nhan 2 — `utils/perf_monitor.py` import `torch` o cap module.**

Ton **1.800 ms** moi lan khoi dong, chi de in mot dong
`torch_cuda_available=...` ma theo mac dinh khong ai thay (do hieu nang chi bat
khi `AI_ENGLISH_PERF=1`).

**Nguyen nhan 3 — nap AI nam trong duong khoi dong.**

`AppContext.build()` goi `AIEngine.create_default()`, va `VocabularyViewModel`
goi `get_vocabulary_entries()` ngay trong constructor.

### 6.2 Ba thay doi

| # | Thay doi | Ky thuat |
|---|---|---|
| 1 | `ai/__init__.py` nap tre | `__getattr__` cap module (PEP 562) |
| 2 | `perf_monitor` khong import `torch` nua | Chi nap khi `AI_ENGLISH_PERF=1` |
| 3 | AI nap sau khi cua so hien ra | `build_lazy_ai_engine()` + `WarmupWorker` |

Cho thay doi 3, `AIEngine` (Sprint 2) nhan ca 5 phu thuoc qua constructor — nen
chi can truyen vao nhung **ham nap tre**, khong phai sua `AIEngine`:

```text
AppContext.build()   ->  build_lazy_ai_engine()   ~0 ms
engine.load(Main.qml)                             cua so hien ra
context.warmup()     ->  WarmupWorker (thread nen)
```

`ui/` khong con import `ai.*` o cap module — dung `TYPE_CHECKING` cho chu thich
kieu, import trong ham cho cho dung that.

### 6.3 Ket qua

| Phep do | Truoc | Sau | Cai thien |
|---|---:|---:|---|
| **Den khi cua so hien ra** | **10.067 ms** | **962 ms** | **nhanh hon 10,5 lan** |
| Thu vien nang nap luc do | torch, sklearn, pandas | **khong co** | |
| Nap AI (chuyen sang nen) | trong duong khoi dong | 7.148 ms, thread nen | nguoi dung khong cho |
| Bo test tu dong | 9,9 giay | **7,8 giay** | nhanh hon 21% |

Nguoi dung gio thay cua so dang nhap sau **~1 giay** thay vi ~10 giay. AI nap
xong trong luc ho dang go ten dang nhap.

### 6.4 Kiem chung: ket qua AI KHONG doi

Cung anh `test1.jpg`, truoc va sau toi uu:

```
Vat the phat hien : 5
  laptop     - Máy tính xách tay [Technology - Medium] (0.94)
  cell phone - Điện thoại        [Technology - Easy]   (0.81)
  person     - Người             [Human - Easy]        (0.77)
```

Giong het. Thoi gian nhan dien trung vi cung khong doi (62 -> 61 ms, trong sai so).

### 6.5 Chot chan chong hoi quy

`StartupBudgetTest` chay `import ui.app_context` trong mot **tien trinh sach** roi
kiem tra `sys.modules`:

```python
def test_importing_app_context_loads_no_heavy_library(self):
    report = self._probe("import ui.app_context")
    self.assertEqual(report["heavy"], [])
```

Neu ai do them lai mot dong `from ai.pipeline import AIEngine` o cap module,
khoi dong quay ve ~10 giay va **test do ngay** — thay vi doi den luc nguoi dung
than phien.

### 6.6 Mot phat hien khong sua trong Sprint nay

Model `.pkl` duoc train bang **scikit-learn 1.8.0**, con phien ban duoc ghim o
Sprint 6 la **1.9.0**. Vi vay moi lan khoi dong deu co canh bao va **train lai**
K-Means, ton them thoi gian:

```
Khong the dung models K-Means cu, dang train lai:
Trying to unpickle estimator KMeans from version 1.8.0 when using version 1.9.0
```

**Khong sua trong Sprint 8** vi sinh lai `.pkl` la thay doi artifact mo hinh —
viec do can nguoi chu du an quyet dinh. Cach xu ly khi san sang:

```bash
python test/manual/test_kmeans.py     # train lai bang sklearn 1.9.0
python test/manual/test_knn.py
git add models/ && git commit -m "chore: train lai model bang scikit-learn 1.9.0"
```

---

## 7. REGRESSION SUITE (NHIEM VU 7)

```bash
python run_tests.py
# 392 passed in 12,66s
```

| Yeu cau | Trang thai |
|---|---|
| Chay duoc moi luc | Dat |
| Khong can YOLO | Dat |
| Khong can database | Dat |
| Khong can webcam | Dat |
| Khong sua artifact mo hinh | Dat, co test khang dinh |
| Mot lenh duy nhat | Dat |

### Ket qua day du

| Bo test | Test | Sprint |
|---|---:|---|
| `test_ai_engine.py` | 7 | 2 |
| `test_worker.py` | 24 | 3 |
| `test_viewmodel.py` | 42 | 3 |
| `test_controller.py` | 34 | 3 |
| `test_repository.py` | 40 | 4 |
| `test_database_service.py` | 32 | 4 |
| `test_cancellation.py` | 31 | 5 |
| `test_thread_safety.py` | 16 | 5 |
| `test_config.py` | 55 | 6 |
| `test_di.py` | 22 | 6 |
| `test_logging.py` | 35 | 7 |
| `test_error_handling.py` | 28 | 7 |
| `test_integration.py` | 26 | 8 |
| **Tong** | **392** | |

### Mot test cu da sua

`test_app_context_shutdown_stops_every_worker` truoc day dem
`threading.active_count()` toan cuc. Khi chay ca bo test bang `pytest`, module
khac cung co thread nen -> con so do khong noi len dieu gi va test do ngau nhien.

Da sua de kiem tra **dung dieu no muon khang dinh**: tung worker cua context do
co con chay hay khong. Day la sua mot test **kem**, khong phai ha thap yeu cau.

---

## 8. RISK

| # | Risk | Muc do | Cach xu ly |
|---|---|---|---|
| 1 | Nap tre lam lo loi tre hon (luc detect thay vi luc khoi dong) | Trung binh | `WarmupWorker` nap ngay sau khi cua so hien ra; loi nap duoc ghi log va khong lam sap app |
| 2 | Lan detect dau tien cham hon neu warmup chua xong | Thap | GUI da hien "Đang nhận diện..."; do do 156 ms cho lan dau |
| 3 | Sua `ai/__init__.py` | **Co chu y** | Day la facade re-export do Sprint 1 tao ra, **khong chua thuat toan**. `ml/`, `detection/`, `dataset/` nguyen ven. Co test khang dinh 18 ten cong khai khong doi |
| 4 | Model `.pkl` lech phien ban sklearn | Trung binh | Da ghi ro o muc 6.6, kem lenh xu ly. Khong tu y doi artifact |
| 5 | Coverage bao thap hon thuc te voi ma trong QThread | Thap | Da ghi chu; 84,69% la uoc luong duoi |
| 6 | Script trong `test/manual/` bi quen chay | Thap | `run_tests.py --list` liet ke day du kem yeu cau moi truong |
| 7 | Ai do chuyen script chay tay nguoc lai `test/` | Thap | `TestSuiteDisciplineTest` do ngay |
| 8 | `pytest.ini` bi sua bo `norecursedirs` | Thap | `test_pytest_excludes_manual_directory` do ngay |

---

## 9. CHANGELOG

### File tao moi (5)

| File | Noi dung |
|---|---|
| `run_tests.py` | Diem chay test duy nhat, co `--coverage` / `--unittest` / `--list` |
| `pytest.ini` | Cau hinh thu gom, loai `test/manual/` |
| `ui/services/ai_bootstrap.py` | `build_lazy_ai_engine()`, `LazyObjectDetector`, `LazyAIEngineParts` |
| `ui/workers/warmup_worker.py` | Nap truoc AI tren thread nen |
| `test/test_integration.py` | 26 test tich hop + chot chan hieu nang |
| `test/manual/__init__.py` | Tai lieu: file nao can gi, file nao ghi de mo hinh |
| `test/manual/benchmark_app.py` | Do khoi dong, nhan dien, FPS, RAM |

### File chuyen cho (9)

`test/test_connection.py`, `test_login.py`, `test_ml.py`, `test_knn.py`,
`test_kmeans.py`, `test_yolo_image.py`, `test_system_evaluation.py`,
`benchmark_database.py`, `benchmark_thread.py` -> `test/manual/`
(da sua duong dan goc project ben trong).

### File sua (7)

| File | Thay doi |
|---|---|
| `ai/__init__.py` | Nap tre bang `__getattr__` (PEP 562). API cong khai khong doi |
| `utils/perf_monitor.py` | `import torch` chuyen sang nap tre, chi khi `AI_ENGLISH_PERF=1` |
| `ui/app_context.py` | Dung `build_lazy_ai_engine()`; them `warmup()`; khong import `ai.*` o cap module |
| `ui/services/detection_service.py` | Khong import `ai.*` o cap module (dung `TYPE_CHECKING`) |
| `ui/viewmodels/vocabulary_viewmodel.py` | Them `load_on_init` va `setVocabulary()` |
| `ui/main_qt.py` | Goi `context.warmup()` NGAY SAU khi cua so hien ra |
| `test/test_thread_safety.py` | Sua test dem thread toan cuc thanh kiem tra worker cua context |

### Khong thay doi

- Thuat toan AI: YOLO, KNN, KMeans, Vocabulary.
- `ml/`, `detection/`, `dataset/` — **nguyen ven**.
- Toan bo `ui/qml/` (15 file).
- Ket qua nhan dien, thoi gian nhan dien, dinh dang du lieu.
- Artifact mo hinh `models/*.pkl`.

---

## 10. TONG KET 8 SPRINT

### 10.1 Hanh trinh

| Sprint | Noi dung | Ket qua chinh |
|---|---|---|
| 1 | AI Layer Facade | Gom 4 diem nhap AI ve mot package `ai/` |
| 2 | AI Engine Enhancement | `AIEngine` thanh trung tam dieu phoi, co DI va do thoi gian |
| 3 | GUI Layer Refactor (MVVM) | Controller giam 52%, business logic ve 0 |
| 4 | Database & Repository | Truy van nhanh hon **2,7 lan**, loi khong con bi nuot |
| 5 | Worker & Thread | Giao dien het treo: 630 ms -> ~1 ms |
| 6 | Config & DI | 23 tham so doi duoc khi chay, 18/18 thu vien ghim |
| 7 | Logging & Error Handling | Mat khau khong con lot vao log, 1 cay exception |
| 8 | Testing & Performance | Khoi dong nhanh hon **10,5 lan**, 392 test, 85% do phu |

### 10.2 Kien truc: truoc va sau

```text
TRUOC                          SAU
─────                          ───
QML                            QML                    (khong doi 1 dong)
 │                              │
 ▼                              ▼
Controller                     Controller             thin adapter
 - quan ly thread               │
 - goi AI                       ▼
 - ghi database                ViewModel               state machine
 - ve anh                       │
 - tinh thong ke                ▼
 - kiem tra mat khau           Worker                  vong doi + huy duoc
 - viet SQL                     │
 │                              ▼
 ▼                             Service                 business logic
AI / Database                   │
                                ▼
                               Repository              SQL + Entity
                                │
                                ▼
                               Database

                               core/    exception + logging + thong diep
                               config/  AppConfig co dinh kieu
```

### 10.3 Con so

| Tieu chi | Truoc Sprint 1 | Sau Sprint 8 |
|---|---|---|
| Tang kien truc ro rang | 2 | 7 |
| Business logic trong Controller | Rat nhieu | **0** |
| SQL trong tang Service | Co | **0** |
| Dong code Controller | 1.800 | 864 (**-52%**) |
| Unit test tu dong | 0 | **392** |
| Do phu kiem thu | 0% | **85%** |
| Chay test khong can YOLO/DB/webcam | Khong | **Co** |
| Thoi gian chay bo test | — | **12,7 giay** |
| Tham so doi duoc khi chay | 0 | **23** |
| Thu vien ghim phien ban | 1/18 | **18/18** |
| Tac vu nen huy duoc | 3/8 | **8/8** |
| Lenh `print()` | 68 | 18 (giu co chu y) |
| Ma loi co cau truc | 0 | **18** |
| **Thoi gian den khi cua so hien ra** | **10.067 ms** | **962 ms** |
| **Thoi gian 1 truy van database** | **1.092 ms** | **400 ms** |
| **Giao dien treo khi dang nhap** | **~630 ms** | **~1 ms** |

### 10.4 Bay loi that da phat hien va sua

Deu la loi co san trong ma nguon, tim ra trong qua trinh tai cau truc:

| # | Loi | Sprint |
|---|---|---|
| 1 | Race condition lam treo luong webcam (co dung bi ghi de trong `run()`) | 3 |
| 2 | QThread bi huy khi con dang chay luc thoat ung dung | 3 |
| 3 | Giao dien dung 3 giay khi tat camera | 3 |
| 4 | `HistoryWriterWorker` treo vinh vien khi hang doi day | 5 |
| 5 | Hang doi frame phinh khong gioi han | 5 |
| 6 | Thu tu mau che lam **lot token** ra log | 7 |
| 7 | Che truoc khi dinh dang lam **mat ban ghi log** | 7 |

### 10.5 Cam ket da giu duoc suot 8 sprint

```bash
git status --short ml/ detection/ dataset/ ui/qml/ models/
# (khong co ket qua)
```

- **Thuat toan AI**: khong mot dong nao trong `ml/`, `detection/`, `dataset/` bi sua.
- **Giao dien**: khong mot dong nao trong 15 file `.qml` bi sua.
- **Schema database**: khong mot lenh DDL nao.
- **Artifact mo hinh**: `models/*.pkl` nguyen ven.
- **Ket qua AI**: cung anh, cung vat the, cung nhan, cung confidence.

Ngoai le duy nhat da ghi ro: `ai/__init__.py` (facade re-export do Sprint 1 tao
ra, khong chua thuat toan) duoc doi sang nap tre o Sprint 8, co test khang dinh
18 ten cong khai khong doi.

### 10.6 Nhung gi con lai

| # | Viec | Muc do |
|---|---|---|
| 1 | Train lai `models/*.pkl` bang scikit-learn 1.9.0 (xem muc 6.6) | Trung binh |
| 2 | 18 `print()` trong `ml/knn.py`, `ml/kmeans.py` | Thap - quyet dinh co y |
| 3 | QML chua dung `dialogService` va cac `*ViewModel` da dang ky san | Thap |
| 4 | Chua co CI tu dong chay `run_tests.py` khi push | Trung binh |
| 5 | `database/auth.py`, `database/history.py`, `ui/speech_worker.py` la shim tuong thich - go duoc khi khong con script cu nao dung | Thap |

---

Sprint 8 hoàn thành.

Kiểm thử và hiệu năng đã được chuẩn hóa.

Toàn bộ 8 Sprint đã hoàn thành.

Dự án AI-English đã sẵn sàng bàn giao.
