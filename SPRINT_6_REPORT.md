# SPRINT 6 REPORT - CONFIG & DEPENDENCY INJECTION

Pham vi: gom toan bo cau hinh ve mot cay `AppConfig` co dinh kieu, tiem xuong moi
tang qua constructor.

Rang buoc da tuan thu:

| Rang buoc | Ket qua |
|---|---|
| Khong sua thuat toan AI | Khong file nao trong `ai/`, `ml/`, `detection/`, `dataset/` bi sua |
| Khong sua QML | Khong file nao trong `ui/qml/` bi sua |
| Khong doi gia tri tham so | Moi gia tri mac dinh **bang dung** gia tri truoc Sprint 6, co test khang dinh |
| Regression Test PASS | **303/303 test PASS** |

---

## 1. CONFIG TRUOC

Cau hinh nam rai rac o **ba noi khong lien quan gi den nhau**:

```text
1. utils/config.py                    ← hang so module
     CONFIDENCE = 0.5
     IMAGE_SIZE = 640
     CAMERA_ID = 0
     MODEL_PATH, FONT_PATH, AUDIO_DIR, ...

2. Bien moi truong (.env)             ← doc THANG bang os.getenv()
     database/connection.py:
         host = os.getenv("DB_HOST")
         database = os.getenv("DB_NAME")
         ...

3. Hang so trong tung file            ← khong ai biet chung ton tai
     ui/workers/webcam_worker.py     INFERENCE_INTERVAL_SECONDS = 0.25
                                     HISTORY_QUEUE_MAX_SIZE = 20
     ui/workers/backpressure.py      DEFAULT_MAX_IN_FLIGHT = 2
     ui/workers/lifecycle.py         DEFAULT_DISPOSE_TIMEOUT_MS = 3000
     ui/services/history_service.py  HISTORY_COOLDOWN_SECONDS = 5.0
                                     HISTORY_PAGE_LIMIT = 200
     ui/services/stats_service.py    STATS_HISTORY_LIMIT = 500
     ui/services/auth_service.py     MIN_PASSWORD_LENGTH = 6
     ui/services/annotation_service.py  4 hang so mau/co chu
     ui/viewmodels/vocabulary_viewmodel.py  RELATED_WORDS_COUNT = 3
     database/connection.py          POOL_MIN/MAX = 1 / 8
     database/repositories/...       MIN_LIMIT / MAX_LIMIT = 1 / 500
```

Van de do duoc:

| # | Van de | Hau qua |
|---|---|---|
| 1 | **Khong ai nhin duoc toan canh** | Muon biet ung dung co bao nhieu tham so chinh duoc phai doc het 12 file |
| 2 | **Khong doi duoc khi chay** | Doi nguong YOLO hay chi so camera phai **sua ma nguon** roi chay lai |
| 3 | **Khong kiem tra gi** | `CONFIDENCE = 5.0` khong bao gio bao loi — YOLO don gian la khong phat hien gi ca |
| 4 | **Hai cau hinh khong song song duoc** | Khong the chay test va production trong cung mot tien trinh |
| 5 | **`os.getenv()` rai rac** | Doi ten mot bien moi truong phai di tim khap noi |
| 6 | **Mat khau database co the ro ri** | Khong co co che che mat khau khi ghi log |
| 7 | **Thu vien khong ghim phien ban** | Chi `ultralytics` duoc ghim; hai may cai cach nhau vai thang chay hai ban `scikit-learn` khac nhau, model `.pkl` co the khong nap duoc |

---

## 2. CONFIG SAU

```text
                     load_config()
                          │
                          ▼
                      AppConfig
                          │
    ┌──────┬──────┬───────┼───────┬────────┬────────┬─────────┐
    ▼      ▼      ▼       ▼       ▼        ▼        ▼         ▼
  paths   ai   camera  database history threads    ui      logging
```

| Nhom | Lop | Tham so |
|---|---|---|
| `paths` | `PathConfig` | project_root, assets, models, dataset, font, audio, qml |
| `ai` | `AIConfig` | confidence, image_size, model_file_name, related_words_count |
| `camera` | `CameraConfig` | camera_id, inference_interval_seconds, max_frames_in_flight |
| `database` | `DatabaseConfig` | host, port, name, user, password, pool_min, pool_max |
| `history` | `HistoryConfig` | cooldown_seconds, page_limit, stats_limit, min/max_query_limit, write_queue_size |
| `threads` | `ThreadConfig` | dispose_timeout_ms, poll_interval_seconds |
| `ui` | `UIConfig` | application_name, qt_quick_style, min_password_length, 4 tham so ve nhan |
| `logging` | `LoggingConfig` | level, performance_enabled |

Thu tu uu tien:

```text
gia tri mac dinh trong config/schema.py
  ← bi ghi de boi .env
      ← bi ghi de boi bien moi truong that cua he thong
          ← bi ghi de boi tham so truyen thang vao load_config()
```

---

## 3. CONFIG REVIEW (NHIEM VU 1)

### 3.1 Hang so da gom

| Hang so | Truoc | Sau |
|---|---|---|
| `CONFIDENCE = 0.5` | `utils/config.py` | `AIConfig.confidence` |
| `IMAGE_SIZE = 640` | `utils/config.py` | `AIConfig.image_size` |
| `MODEL_PATH` | `utils/config.py` | `AIConfig.model_path(paths)` |
| `CAMERA_ID = 0` | `utils/config.py` | `CameraConfig.camera_id` |
| `INFERENCE_INTERVAL_SECONDS = 0.25` | `webcam_worker.py` | `CameraConfig.inference_interval_seconds` |
| `DEFAULT_MAX_IN_FLIGHT = 2` | `backpressure.py` | `CameraConfig.max_frames_in_flight` |
| `HISTORY_COOLDOWN_SECONDS = 5.0` | `history_service.py` | `HistoryConfig.cooldown_seconds` |
| `HISTORY_PAGE_LIMIT = 200` | `history_service.py` | `HistoryConfig.page_limit` |
| `STATS_HISTORY_LIMIT = 500` | `stats_service.py` | `HistoryConfig.stats_limit` |
| `MIN_LIMIT / MAX_LIMIT = 1 / 500` | `history_repository.py` | `HistoryConfig.min/max_query_limit` |
| `HISTORY_QUEUE_MAX_SIZE = 20` | `webcam_worker.py` | `HistoryConfig.write_queue_size` |
| `DEFAULT_DISPOSE_TIMEOUT_MS = 3000` | `lifecycle.py` | `ThreadConfig.dispose_timeout_ms` |
| `HISTORY_POLL_SECONDS = 0.1` | `webcam_worker.py` | `ThreadConfig.poll_interval_seconds` |
| `POOL_MIN / MAX = 1 / 8` | `connection.py` | `DatabaseConfig.pool_min/max_connections` |
| `MIN_PASSWORD_LENGTH = 6` | `auth_service.py` | `UIConfig.min_password_length` |
| `RELATED_WORDS_COUNT = 3` | `vocabulary_viewmodel.py` | `AIConfig.related_words_count` |
| 4 hang so mau/co chu nhan | `annotation_service.py` | `UIConfig.image_*` / `webcam_*` |
| `"AI-English"`, `"Basic"` | `main_qt.py` | `UIConfig.application_name` / `qt_quick_style` |

**18 nhom hang so** da roi khoi ma nguon vao cau hinh.

Cac hang so **van giu nguyen o module** nhung gio lay gia tri tu config, de chi
co **mot nguon su that**:

```python
# ui/workers/backpressure.py
DEFAULT_MAX_IN_FLIGHT = CameraConfig.max_frames_in_flight
```

Test `NoScatteredEnvReadTest.test_no_hardcoded_tuning_numbers_left` doc ma nguon
va khang dinh moi hang so nay deu tro ve mot lop `*Config`.

### 3.2 `os.getenv()` rai rac

| Module | Truoc | Sau |
|---|---|---|
| `database/connection.py` | 5 lan goi `os.getenv()` | Nhan `DatabaseConfig` qua `configure()`; van co duong lui doc env khi chua duoc tiem |
| `config/loader.py` | - | **Noi duy nhat** doc cau hinh nghiep vu tu bien moi truong |

Test `NoScatteredEnvReadTest` quet 16 module va khang dinh khong module nao ngoai
tang `config/` doc bien moi truong.

Ba ngoai le duoc ghi ro trong test:

| Module | Ly do |
|---|---|
| `database/connection.py` | Duong lui khi chua co config duoc tiem (che do tuong thich) |
| `utils/perf_monitor.py` | `AI_ENGLISH_PERF` la co bat/tat do hieu nang, khong phai cau hinh nghiep vu |
| `ui/main_qt.py` | **GHI** (khong doc) `QT_QUICK_CONTROLS_STYLE` tu gia tri lay o config — Qt chi doc bien nay mot lan luc nap thu vien |

---

## 4. SCHEMA (NHIEM VU 2)

Moi nhom la mot `@dataclass(frozen=True)`:

- **Bat bien** — khong ai doi duoc cau hinh giua chung. Co test khang dinh.
- **Co gia tri mac dinh** — chay duoc ngay khong can `.env`.
- **Co `validate()`** — gia tri vo ly bi chan ngay khi khoi dong.
- **Co `with_overrides()`** — tao ban sao doi mot nhom, dung trong test.

### Vi du kiem tra hop le

```
$ AI_CONFIDENCE=5.0 python -c "from config import load_config; load_config()"

ConfigValidationError
Cấu hình `ai.confidence` không hợp lệ: 5.0 — phải nằm trong khoảng (0, 1]
```

Truoc Sprint 6, cau hinh nay chay binh thuong va YOLO **khong bao gio** phat hien
duoc vat the nao — khong mot dong canh bao.

### Danh sach luat kiem tra

| Truong | Luat |
|---|---|
| `ai.confidence` | Trong khoang (0, 1] |
| `ai.image_size` | Boi so duong cua 32 |
| `ai.related_words_count` | >= 1 |
| `camera.camera_id` | Khong am |
| `camera.inference_interval_seconds` | > 0 |
| `camera.max_frames_in_flight` | >= 1 |
| `database.pool_min_connections` | >= 1 |
| `database.pool_max_connections` | >= pool_min |
| `database.port` | Phai la so |
| `history.cooldown_seconds` | Khong am |
| `history.page_limit` | >= 1 va <= max_query_limit |
| `history.stats_limit` | <= max_query_limit |
| `history.max_query_limit` | >= min_query_limit |
| `history.write_queue_size` | >= 1 |
| `threads.dispose_timeout_ms` | >= 100 ms |
| `threads.poll_interval_seconds` | Trong khoang (0, 5] |
| `ui.min_password_length` | >= 1 |
| `ui.*_box_color` | Bo 3 so trong 0..255 |
| `logging.level` | Mot trong DEBUG/INFO/WARNING/ERROR/CRITICAL |

**Gia tri sai KIEU khong lam sap ung dung.** `AI_CONFIDENCE=rat-cao` chi ghi mot
dong canh bao roi dung gia tri mac dinh — nguoi dung go nham khong bi mat ung dung.

---

## 5. ENVIRONMENT (NHIEM VU 3)

| Moi truong | Log level mac dinh | Duoc cham database that |
|---|---|---|
| `development` | INFO | Co |
| `testing` | ERROR | **Khong** |
| `production` | WARNING | Co |

Chon bang `AI_ENGLISH_ENV`. Chap nhan viet tat: `dev`, `test`, `prod`. Gia tri la
thi ve `development` thay vi bao loi.

`load_test_config()` tra ve cau hinh moi truong `testing`, **khong doc `.env`**,
**khong co thong tin dang nhap database**. Test `TestEnvironmentSafetyTest` khang
dinh dieu nay.

`.env.example` da duoc viet lai day du: **23 bien**, moi bien co ghi chu giai
thich va gia tri mac dinh. Test `DotEnvExampleTest` doi chieu danh sach bien ma
loader doc voi noi dung file — thieu mot bien la test do.

---

## 6. DEPENDENCY INJECTION (NHIEM VU 4)

### Truoc

```python
AppContext.build(ai_engine=..., camera_id=CAMERA_ID, ...)
                                          ↑
                                   hang so module toan cuc
```

### Sau

```python
AppContext.build(config=app_config, ...)
    │
    ├── database_connection.configure(config.database)
    ├── HistoryService(config=config.history)
    ├── StatsService(config=config.history)
    ├── DetectionService(ui_config=config.ui)
    ├── WebcamViewModel(config=config.camera)
    │     └── WebcamWorker(camera_config=..., history_config=...,
    │                      ai_config=..., thread_config=...)
    ├── VocabularyViewModel(config=config.ai)
    └── HistoryRepository(config=config.history)
```

`AppContext.build()` gio nhan **9 tham so tiem duoc**:
`config`, `ai_engine`, `camera_id`, `file_picker`, `history_service`,
`auth_service`, `history_repository`, `user_repository`, `capture_factory`.

### Bang chung: hai cau hinh song song duoc

```python
first  = AppContext.build(config=cfg.with_overrides(camera=CameraConfig(camera_id=1)))
second = AppContext.build(config=cfg.with_overrides(camera=CameraConfig(camera_id=2)))

first.webcam_view_model._camera_id   # 1
second.webcam_view_model._camera_id  # 2
```

Truoc Sprint 6 dieu nay khong the: ca hai deu doc cung mot hang so module.

Test `IsolatedContextTest` khang dinh hai context khong dung chung config,
khong dung chung service, khong dung chung viewmodel.

### Bien toan cuc con lai — noi ro va co ly do

Con **mot** bien toan cuc: `config._default_config`, dung boi `utils/config.py`.

Ly do: `detection/detector.py`, `utils/helper.py`, `utils/speech.py` doc hang so
**ngay luc import**, ma Sprint 6 **khong duoc sua** cac module do. Neu bo bien
nay thi phai sua `detection/` — vi pham rang buoc.

Doi lai, `utils/config.py` gio lay gia tri tu `AppConfig`, nen doi `.env` la doi
luon tham so ma tang AI dung — dieu truoc Sprint 6 khong lam duoc:

```
$ AI_CONFIDENCE=0.75 CAMERA_ID=2 HISTORY_PAGE_LIMIT=50 python ...

utils.config.CONFIDENCE  : 0.75   (mac dinh 0.5)
utils.config.CAMERA_ID   : 2      (mac dinh 0)
HistoryConfig.page_limit : 50     (mac dinh 200)
```

---

## 7. MAGIC NUMBER (NHIEM VU 5)

Bang doi chieu day du - **moi gia tri mac dinh bang dung gia tri truoc Sprint 6**:

| Gia tri | Y nghia | Bien moi truong |
|---:|---|---|
| `0.5` | Nguong confidence YOLO | `AI_CONFIDENCE` |
| `640` | Kich thuoc anh YOLO | `AI_IMAGE_SIZE` |
| `3` | So tu lien quan (k-NN) | `AI_RELATED_WORDS` |
| `0` | Chi so camera | `CAMERA_ID` |
| `0.25` | Nhip chay AI tren webcam (giay) | `CAMERA_INFERENCE_INTERVAL` |
| `2` | Frame toi da dang bay | `CAMERA_MAX_FRAMES_IN_FLIGHT` |
| `5.0` | Cooldown ghi lich su (giay) | `HISTORY_COOLDOWN_SECONDS` |
| `200` | So ban ghi man hinh lich su | `HISTORY_PAGE_LIMIT` |
| `500` | So ban ghi tinh thong ke | `HISTORY_STATS_LIMIT` |
| `1 / 500` | Gioi han an toan cau SELECT | (co dinh) |
| `20` | Kich thuoc hang doi ghi lich su | `HISTORY_WRITE_QUEUE_SIZE` |
| `3000` | Timeout dung worker (ms) | `THREAD_DISPOSE_TIMEOUT_MS` |
| `0.1` | Chu ky kiem tra co huy (giay) | `THREAD_POLL_INTERVAL` |
| `1 / 8` | Kich thuoc connection pool | `DB_POOL_MIN` / `DB_POOL_MAX` |
| `6` | Do dai mat khau toi thieu | (co dinh) |
| `(0,255,0)` / `28` | Mau + co chu nhan tren anh | (co dinh) |
| `(0,180,0)` / `24` | Mau + co chu nhan tren webcam | (co dinh) |

`DefaultValueTest` (7 test) khang dinh tung con so mot. Neu ai vo tinh doi mot
gia tri mac dinh, test do ngay.

---

## 8. DEPENDENCY VERSION (NHIEM VU 6)

### Truoc

```
ultralytics==8.4.72     ← chi mot dong nay duoc ghim
torch                   ← ban moi nhat
scikit-learn            ← ban moi nhat  ⚠ model .pkl co the khong nap duoc
PySide6                 ← ban moi nhat
... 14 thu vien khac khong ghim
```

### Sau

`requirements.txt` — **18 thu vien deu duoc ghim**, chia nhom co ghi chu:

| Nhom | Thu vien |
|---|---|
| Thi giac may tinh / AI | ultralytics 8.4.72, torch 2.12.1, torchvision 0.27.1, opencv-python 4.12.0.88, numpy 2.1.2 |
| Hoc may | scikit-learn 1.9.0, joblib 1.4.2 |
| Giao dien | PySide6 6.11.1, pillow 11.3.0 |
| Co so du lieu | psycopg2-binary 2.9.12, bcrypt 5.0.0 |
| Cau hinh | python-dotenv 1.2.2 |
| Am thanh / dich | gTTS 2.5.4, pyttsx3 2.99, googletrans 4.0.0rc1 |
| Bao cao | matplotlib 3.10.8, pandas 3.0.1, openpyxl 3.1.5 |

`requirements-dev.txt` — cong cu chi cai tren may phat trien:
pytest 8.4.2, pytest-cov 7.0.0, psutil 7.1.3, ruff 0.14.4.

```bash
pip install -r requirements.txt        # chay ung dung
pip install -r requirements-dev.txt    # them cong cu phat trien
```

Test `RequirementsTest` khang dinh **moi** dong trong ca hai file deu co `==`.

---

## 9. REGRESSION TEST

### 9.1 Ket qua

| Bo test | Test | Ket qua |
|---|---:|---|
| `test_ai_engine.py` (Sprint 2) | 7 | PASS |
| `test_config.py` (Sprint 6, moi) | 55 | PASS |
| `test_di.py` (Sprint 6, moi) | 22 | PASS |
| `test_repository.py` (Sprint 4) | 40 | PASS |
| `test_database_service.py` (Sprint 4) | 32 | PASS |
| `test_worker.py` (Sprint 3) | 24 | PASS |
| `test_viewmodel.py` (Sprint 3) | 42 | PASS |
| `test_controller.py` (Sprint 3) | 34 | PASS |
| `test_cancellation.py` (Sprint 5) | 31 | PASS |
| `test_thread_safety.py` (Sprint 5) | 16 | PASS |
| **Tong** | **303** | **PASS, exit code 0** |

```bash
python -m unittest test.test_ai_engine test.test_config test.test_di \
                  test.test_repository test.test_database_service test.test_worker \
                  test.test_viewmodel test.test_controller \
                  test.test_cancellation test.test_thread_safety
```

Thoi gian chay: **7,06 giay**. Khong can PostgreSQL, YOLO hay webcam.

**Khong test cu nao phai sua** — Sprint 6 khong doi hanh vi.

### 9.2 Test bao ve kien truc moi

| Test | Bao ve dieu gi |
|---|---|
| `DefaultValueTest` (7 test) | Moi gia tri mac dinh bang dung gia tri truoc Sprint 6 |
| `ModuleConstantsMatchConfigTest` | Hang so module lay tu config — chi mot nguon su that |
| `test_legacy_utils_config_shim` | 14 hang so ma module AI cu doc van con ton tai |
| `NoScatteredEnvReadTest.test_no_direct_env_read_outside_config_layer` | 16 module khong duoc doc bien moi truong |
| `NoScatteredEnvReadTest.test_no_hardcoded_tuning_numbers_left` | 6 hang so tinh chinh phai tro ve mot lop `*Config` |
| `ConstructorInjectionTest` | 8 thanh phan nhan phu thuoc qua constructor; 5 thanh phan nhan `config` |
| `IsolatedContextTest` | Hai cau hinh song song duoc, khong dung chung trang thai |
| `SecretHandlingTest` | Mat khau khong ro ri qua `masked()` / `summary()` |
| `DotEnvExampleTest` | 23 bien moi truong deu duoc ghi trong `.env.example` |
| `RequirementsTest` | Moi thu vien deu ghim phien ban |
| `TestEnvironmentSafetyTest` | Moi truong `testing` khong cham database that |

### 9.3 Hoi quy hanh vi

| Kiem tra | Ket qua |
|---|---|
| `utils.config.CONFIDENCE` | 0.5 — khong doi |
| `utils.config.IMAGE_SIZE` | 640 — khong doi |
| `utils.config.MODEL_PATH.name` | `best.pt` — khong doi |
| `utils.config.LEVELS` | Khong doi |
| Duong dan font / audio / dataset | Khong doi |
| Nhip webcam, cooldown, gioi han truy van | Khong doi |
| Dinh dang du lieu gui len View | Khong doi |

### 9.4 File khong bi dong toi

```bash
git status --short ai/ ml/ detection/ dataset/ models/ ui/qml/
# (khong co ket qua)
```

---

## 10. RISK

| # | Risk | Muc do | Cach xu ly |
|---|---|---|---|
| 1 | `.env` cu thieu bien moi | Thap | Moi bien deu co gia tri mac dinh; thieu thi dung mac dinh, khong bao loi |
| 2 | Cau hinh sai lam ung dung khong khoi dong duoc | **Co chu y** | Day la muc tieu NHIEM VU 2. Thong bao noi ro ten truong + gia tri + ly do |
| 3 | `utils/config.py` con mot bien toan cuc | Trung binh | Bat buoc, vi khong duoc sua `detection/`. Da ghi ro trong muc 6 |
| 4 | Ghim phien ban lam kho nang cap thu vien | Thap | Doi lai la hai may cai cung mot ban. Nang cap co chu dich thay vi tinh co |
| 5 | `database.connection` con duong lui doc `os.getenv()` | Thap | Chi dung khi chua duoc tiem config (script cu). Ung dung chinh luon tiem qua `AppContext` |
| 6 | Doi `AI_CONFIDENCE` trong `.env` lam doi ket qua nhan dien | **Co chu y** | Da ghi CANH BAO trong `.env.example` va docstring `AIConfig` |
| 7 | `AppConfig` bat bien — khong doi duoc khi dang chay | Thap | Co y: cau hinh doi giua chung la nguon goc cua bug kho tim. Dung `with_overrides()` de tao ban moi |
| 8 | `.env.example` va loader lech nhau | Thap | `DotEnvExampleTest` doi chieu tu dong |

---

## 11. CHANGELOG

### File tao moi (7)

| File | Noi dung |
|---|---|
| `config/__init__.py` | Export + `get_default_config()` cho lop tuong thich |
| `config/schema.py` | 9 dataclass cau hinh + `validate()` + `summary()` |
| `config/loader.py` | Doc tu bien moi truong, `load_config()`, `load_test_config()` |
| `config/environment.py` | `Environment` (development / testing / production) |
| `config/errors.py` | `ConfigError`, `ConfigValidationError`, `MissingConfigError` |
| `requirements-dev.txt` | Cong cu phat trien, ghim phien ban |
| `test/test_config.py` + `test/test_di.py` | 77 test moi |

### File sua (14)

| File | Thay doi |
|---|---|
| `utils/config.py` | Thanh shim tren `AppConfig`; giu du 14 hang so cho module AI cu |
| `requirements.txt` | Ghim 18 thu vien, chia nhom co ghi chu |
| `.env.example` | Viet lai day du 23 bien kem ghi chu va gia tri mac dinh |
| `database/connection.py` | Them `configure()` / `current_config()`; pool size tu config |
| `database/repositories/history_repository.py` | Nhan `HistoryConfig`; `clamp_limit()` nhan gioi han |
| `ui/services/history_service.py` | Nhan `HistoryConfig`; them `HistoryRecordPolicy.from_config()` |
| `ui/services/stats_service.py` | Nhan `HistoryConfig` |
| `ui/services/auth_service.py` | `MIN_PASSWORD_LENGTH` tu `UIConfig` |
| `ui/services/annotation_service.py` | `for_image()` / `for_webcam()` nhan `UIConfig` |
| `ui/services/detection_service.py` | Nhan `ui_config` |
| `ui/workers/lifecycle.py` | `DEFAULT_DISPOSE_TIMEOUT_MS` tu `ThreadConfig` |
| `ui/workers/backpressure.py` | `DEFAULT_MAX_IN_FLIGHT` tu `CameraConfig` |
| `ui/workers/webcam_worker.py` | Nhan 4 nhom config; `HistoryWriterWorker` nhan queue size + poll |
| `ui/viewmodels/webcam_viewmodel.py` | Nhan `CameraConfig` |
| `ui/viewmodels/vocabulary_viewmodel.py` | Nhan `AIConfig` |
| `ui/app_context.py` | `build(config=...)`; tiem xuong moi tang; `shutdown()` dung timeout tu config |
| `ui/main_qt.py` | Doc config truoc khi import Qt; ten app, style, QML dir, log level tu config |

### Khong thay doi

- Thuat toan AI: YOLO, KNN, KMeans, Vocabulary.
- Toan bo `ai/`, `ml/`, `detection/`, `dataset/`.
- Toan bo `database/` ngoai `connection.py` va `history_repository.py`.
- Toan bo `ui/qml/` (15 file).
- **Moi gia tri tham so** — chi doi cho cat giu, khong doi gia tri.

---

## 12. SAN SANG CHO SPRINT 7

Sprint 7 (Logging & Error Handling) da co san diem bam:

1. `LoggingConfig` da co `level` va `performance_enabled`, doc duoc tu `LOG_LEVEL`.
   Sprint 7 chi can them file handler va xoay vong file log.
2. `Environment.default_log_level` da phan biet development / testing / production.
3. Cay exception da co san mau o hai noi: `ConfigError` (Sprint 6) va
   `RepositoryError` (Sprint 4), deu co `error_code` + thong diep nguoi dung.
   Sprint 7 gom chung duoi mot `AppError`.
4. `DatabaseConfig.masked()` va `AppConfig.summary()` da chan ro ri mat khau —
   Sprint 7 mo rong nguyen tac nay cho toan bo log.
5. Con **68 lenh `print()`** trong `ml/`, `detection/`, `dataset/`, `utils/` —
   danh sach da co trong bao cao tong quan.

---

Sprint 6 hoàn thành.

Config đã được chuẩn hóa.

Dependency Injection đã hoàn chỉnh.

Sẵn sàng chuyển sang Sprint 7: Logging & Error Handling.
