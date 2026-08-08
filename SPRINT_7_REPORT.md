# SPRINT 7 REPORT - LOGGING & ERROR HANDLING

Pham vi: gom moi loi ve mot cay `AppError`, thay `logging.basicConfig` mot dong
bang logger phan cap co file xoay vong, va chan ro ri du lieu nhay cam.

Rang buoc da tuan thu:

| Rang buoc | Ket qua |
|---|---|
| Khong sua thuat toan AI | `ml/knn.py`, `ml/kmeans.py`, `ai/` **nguyen ven** — `git status` sach |
| Khong sua QML | Khong file nao trong `ui/qml/` bi sua |
| Khong doi thong diep nguoi dung | Noi dung giu nguyen tung ky tu, chi doi cho cat giu |
| Regression Test PASS | **366/366 test PASS** |

---

## 1. LOGGING TRUOC

```python
# ui/main_qt.py
logging.basicConfig(level=logging.INFO)
```

Mot dong. Va **68 lenh `print()`** rai rac.

| # | Van de | Hau qua |
|---|---|---|
| 1 | Khong ghi ra file | Nguoi dung bao loi thi khong co gi de xem lai |
| 2 | Khong chinh duoc muc cho tung tang | Bat DEBUG cho database la ngap log cua `ultralytics` va `matplotlib` |
| 3 | Khong co gi chan mat khau | `f"Không thể đăng nhập: {error}"` — loi psycopg2 kem **ca chuoi ket noi** |
| 4 | 68 `print()` | Khong tat duoc, khong loc duoc, khong ghi vao file duoc |
| 5 | Hai cay exception roi rac | `ConfigError` va `RepositoryError` khong co goc chung — khong bat chung duoc |
| 6 | Thong diep tron lan | Mot chuoi vua lam log ky thuat vua lam thong bao nguoi dung |
| 7 | Thong diep rai rac 7 file | Sua mot cach dien dat phai di tim khap noi |

---

## 2. LOGGING SAU

```text
                    setup_from_app_config(config)
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
              Console handler      File handler
              muc theo config      LUON o DEBUG
              dinh dang ngan       xoay vong 5 x 2 MB
                    │                   │
                    └─────────┬─────────┘
                              ▼
                    SensitiveDataFilter
                    RedactingFormatter
                              │
                              ▼
                     khong con bi mat nao
```

Logger phan cap, moi tang chinh muc doc lap:

```text
ai.*          ui.*          database.*    config.*
core.*        utils.*       ml.*          detection.*    dataset.*

PIL, matplotlib, torch, ultralytics, urllib3, gtts  ->  WARNING
```

---

## 3. `print()` REVIEW (NHIEM VU 1)

### 3.1 Kiem ke va phan loai

| File | So luong | Phan loai | Xu ly |
|---|---:|---|---|
| `dataset/prepare_dataset.py` | 22 | Bao cao cua script CLI | `logger.info` + tu lap dat logging |
| `ml/evaluate.py` | 15 | Bao cao cua script CLI | `logger.info` + tu lap dat logging |
| **`ml/kmeans.py`** | **13** | **Bao cao trong thuat toan AI** | **GIU NGUYEN** |
| `utils/perf_monitor.py` | 6 | Bao cao do hieu nang | `logger.info` (`utils.perf`) |
| **`ml/knn.py`** | **5** | **Bao cao trong thuat toan AI** | **GIU NGUYEN** |
| `detection/webcam_detect.py` | 3 | Script demo doc lap | `logger.info` + tu lap dat logging |
| `utils/helper.py` | 2 | Canh bao tai font | `logger.warning` |
| `utils/translator.py` | 1 | Canh bao dich that bai | `logger.warning` |
| `utils/console.py` | 1 | Canh bao dat UTF-8 | `logger.warning` |
| **Tong** | **68** | | **50 da chuyen, 18 giu nguyen** |

### 3.2 Vi sao giu 18 lenh trong `ml/knn.py` va `ml/kmeans.py`

Day la **quyet dinh co y**, khong phai bo sot.

Cam ket xuyen suot 7 sprint la *"khong sua AI"*, va bang chung la
`git status ml/ detection/ dataset/` luon sach. Doi `print` sang `logging`
khong lam doi mot phep tinh nao, nhung se **pha vo bang chung do**.

Khi duoc hoi, nguoi chu du an chon **giu nguyen hai file thuat toan**.
Cac script (`prepare_dataset.py`, `evaluate.py`, `webcam_detect.py`) khong phai
thuat toan nen duoc chuyen.

Ket qua: `ai/`, `ml/knn.py`, `ml/kmeans.py` van nguyen ven.

### 3.3 Bay da tranh duoc

Script CLI ma doi thang `print` -> `logger.info` se **im lang hoan toan** khi
chay doc lap, vi khong co handler nao. Ca ba script gio tu lap dat logging:

```python
if __name__ == "__main__":
    from core.logging_config import setup_logging

    setup_logging(level="INFO")
```

Test `test_scripts_bootstrap_logging` khang dinh dieu nay.

---

## 4. EXCEPTION HIERARCHY (NHIEM VU 3)

```text
AppError                            APP_ERROR
  ├── ConfigError                   CONFIG_ERROR
  │     ├── ConfigValidationError   CONFIG_VALIDATION_ERROR
  │     └── MissingConfigError      CONFIG_MISSING
  ├── RepositoryError               REPOSITORY_ERROR
  │     ├── ConnectionFailedError   DB_CONNECTION_FAILED
  │     ├── QueryFailedError        DB_QUERY_FAILED
  │     ├── NotFoundError           DB_NOT_FOUND
  │     └── IntegrityError          DB_INTEGRITY_ERROR
  ├── AIError                       AI_ERROR
  │     ├── ModelLoadError          AI_MODEL_LOAD_FAILED
  │     └── InferenceError          AI_INFERENCE_FAILED
  ├── UIError                       UI_ERROR
  │     ├── MediaError              UI_MEDIA_ERROR
  │     └── OperationCancelled      UI_OPERATION_CANCELLED
  └── ExternalServiceError          EXTERNAL_SERVICE_ERROR
        ├── SpeechError             EXTERNAL_SPEECH_ERROR
        └── TranslationError        EXTERNAL_TRANSLATION_ERROR
```

**18 ma loi, khong ma nao trung.** Co test khang dinh.

Truoc Sprint 7, `ConfigError` va `RepositoryError` khong co goc chung — muon bat
"moi loi cua ung dung" phai liet ke tung lop, va se quen. Gio `except AppError`
la du.

### Hai thong diep tach bach (NHIEM VU 5)

Moi loi mang **hai** thong diep:

| Truong | Danh cho | Vi du |
|---|---|---|
| `technical_message` | Log, lap trinh vien | `INSERT INTO history that bai o cot confidence` |
| `display_message` | Nguoi dung cuoi | `Không thực hiện được thao tác dữ liệu.` |

`user_message_for(error)` la ham duy nhat duoc dung khi hien loi cho nguoi dung.
Loi **khong phai** `AppError` khong bao gio duoc hien noi dung goc — noi dung do
co the chua chuoi ket noi, duong dan he thong hoac ten dang nhap.

```python
user_message_for(RuntimeError("postgresql://admin:bimat@db/postgres"))
# -> "Đã xảy ra lỗi. Vui lòng thử lại."   (KHONG lo gi)
```

API cu duoc giu: `.message`, `.error_code`, `.user_message`, `.cause` — code
Sprint 4 khong bi vo.

---

## 5. ERROR BOUNDARY (NHIEM VU 4)

| Tang | Gap loi thi lam gi |
|---|---|
| **Repository** | **NEM** `RepositoryError`. Khong bao gio nuot roi tra ve `[]` / `False` |
| **Service - doc/xoa** | Cho loi di tiep len Worker |
| **Service - ghi lich su** | Chan lai, ghi log, tra ve `False`. Database hong khong duoc lam hong ket qua AI |
| **Service - xac thuc** | Doi sang `AuthResult` co `error_code` + thong diep **an toan** |
| **Worker** | `ManagedWorker.run()` bat het: loi -> signal `failed`; huy -> signal `cancelled` |
| **ViewModel** | Doi signal thanh trang thai `Error` + status message |
| **Controller** | Chuyen tiep sang `DialogService` |
| **DialogService** | `publishError()` — luon di qua `user_message_for()` |

### Huy KHONG phai loi

`OperationCancelledError` duoc `ManagedWorker` bat rieng: worker chuyen sang
trang thai `cancelled` va emit signal `cancelled`, **khong** emit `failed`.
Nguoi dung bam Huy thi khong duoc thay hop thoai bao loi.

Test `test_cancellation_is_not_reported_as_failure`.

### Khong con nuot loi im lang

Truoc Sprint 7 co **3 cho** `except: pass` khong mot dong giai thich. Gio:

| Vi tri | Xu ly |
|---|---|
| `database/connection.py` — tra ket noi ve pool | `logger.warning` |
| `database/connection.py` — rollback that bai | `logger.warning`, kem loai loi goc |
| `core/logging_config.py` — dong handler | Ghi chu ro: khong the log vi handler dang bi go |

Test `NoSilentSwallowTest` quet toan bo `ui/`, `database/`, `config/`, `core/`
va bat moi `except: pass` **khong co ghi chu giai thich**.

---

## 6. USER MESSAGE (NHIEM VU 5)

`core/messages.py` gom **34 thong diep** tu 7 file khac nhau.

| Nhom | So luong |
|---|---:|
| Xac thuc | 16 |
| Nhan dien anh | 7 |
| Webcam | 4 |
| Lich su | 3 |
| Du lieu | 5 |
| Chung + tieu de hop thoai | 8 |

Cac module cu **import lai** tu catalog nen noi dung khong doi mot ky tu nao —
moi test hien co van xanh, khong test nao phai sua.

### Nguyen tac (co test tu dong ra soat)

1. Tieng Viet, co dau, du dau cau.
2. Noi nguoi dung can lam gi, khong noi he thong hong o dau.
3. TUYET DOI khong kem: ten bang, cau SQL, chuoi ket noi, ten lop Python,
   stack trace, ten dang nhap.

`contains_technical_detail()` kiem tra 10 tu khoa cam. Test
`test_no_message_leaks_technical_detail` chay qua **ca 34 thong diep** va ca
`user_message` cua 18 lop loi.

Test `test_no_module_formats_raw_exception_into_user_text` quet 6 module va cam
mau `f"...{error}"` trong chuoi hien thi.

---

## 7. SENSITIVE DATA (NHIEM VU 6)

### Hai lop bao ve

**1. Theo mau** — `password=...`, `token=...`, `api_key=...`,
`postgresql://user:pass@host`, `Bearer ...`

**2. Theo gia tri** — `register_secret(value)` dang ky mot chuoi bi mat cu the.
Chuoi do bi che o **bat ky** dau no xuat hien, ke ca trong mot thong bao loi cua
thu vien ben thu ba ma khong the doan truoc dinh dang.

Cach 2 quan trong hon: khong the doan truoc moi kieu in loi cua `psycopg2`.

### Ba diem chan

| Diem | Nhiem vu |
|---|---|
| `SensitiveDataFilter` (tren moi handler) | Che noi dung ban ghi |
| `RedactingFormatter` (tren moi handler) | Che lan cuoi, **ke ca stack trace** |
| `register_secret()` luc nap config | Mat khau vao bo loc truoc khi bat ky log nao chay |

Can ca `Filter` **va** `Formatter`: bo loc khong voi toi duoc stack trace vi noi
dung do chi duoc sinh ra luc dinh dang.

### Bang chung tren mat khau Supabase THAT

```
ERROR  database.demo  connect postgresql://postgres.ydjg...:***@aws-0-...supabase.com/postgres
ERROR  database.demo  password=***
Mat khau that co lot ra khong? False
```

### Hai loi that phat hien khi viet test

**Loi 1 — thu tu mau lam lot token.** Mau `keyword_assignment` khop
`Authorization: Bearer` truoc, coi `Bearer` la gia tri bi mat va che **chu
"Bearer"**, khien token that di qua nguyen ven:

```
"Authorization: Bearer abc.def.ghi"  ->  "Authorization: *** abc.def.ghi"
```

Da sua bang cach cho mau `bearer_token` chay **truoc**.

**Loi 2 — che truoc khi dinh dang lam hong log.** Bo loc ban dau che
`record.msg` khi con nguyen placeholder:

```python
logger.error("connect: postgresql://u:%s@host", password)
```

Mau `connection_string` coi `%s` la mat khau va thay bang `***`. Sau do `logging`
khong con cho de dat tham so nua va nem
`not all arguments converted during string formatting` — **mat luon ban ghi log**.

Da sua: **dinh dang xong roi moi che** (`record.getMessage()` truoc, `redact()` sau).

---

## 8. REGRESSION TEST

### 8.1 Ket qua

| Bo test | Test | Ket qua |
|---|---:|---|
| `test_ai_engine.py` (Sprint 2) | 7 | PASS |
| `test_config.py` (Sprint 6) | 55 | PASS |
| `test_di.py` (Sprint 6) | 22 | PASS |
| `test_repository.py` (Sprint 4) | 40 | PASS |
| `test_database_service.py` (Sprint 4) | 32 | PASS |
| `test_worker.py` (Sprint 3) | 24 | PASS |
| `test_viewmodel.py` (Sprint 3) | 42 | PASS |
| `test_controller.py` (Sprint 3) | 34 | PASS |
| `test_cancellation.py` (Sprint 5) | 31 | PASS |
| `test_thread_safety.py` (Sprint 5) | 16 | PASS |
| `test_logging.py` (Sprint 7, moi) | 35 | PASS |
| `test_error_handling.py` (Sprint 7, moi) | 28 | PASS |
| **Tong** | **366** | **PASS, exit code 0** |

```bash
python -m unittest test.test_ai_engine test.test_config test.test_di \
                  test.test_repository test.test_database_service test.test_worker \
                  test.test_viewmodel test.test_controller \
                  test.test_cancellation test.test_thread_safety \
                  test.test_logging test.test_error_handling
```

Thoi gian chay: **9,88 giay**. **Khong test cu nao phai sua.**

### 8.2 Test bao ve kien truc moi

| Test | Bao ve dieu gi |
|---|---|
| `NoPrintLeftTest` | Quet 9 package bang `ast`, khong file nao ngoai danh sach mien tru duoc goi `print()` |
| `test_allowed_files_are_documented` | File mien tru phai **that su** con `print()` — het thi phai go khoi danh sach |
| `test_scripts_bootstrap_logging` | 3 script CLI phai tu lap dat logging |
| `NoSilentSwallowTest` | `except: pass` phai co ghi chu giai thich |
| `HierarchyTest` | 18 lop loi deu ke thua `AppError` |
| `test_codes_are_unique` | Khong ma loi nao trung |
| `test_no_message_leaks_technical_detail` | 34 thong diep + 18 `user_message` khong lo chi tiet ky thuat |
| `NoRawErrorInUserTextTest` | 6 module khong duoc ghep `{error}` vao chuoi hien thi |
| `DatabasePasswordNeverLeaksTest` | Mat khau khong toi duoc file log |
| `test_third_party_loggers_are_quietened` | 8 thu vien bi ha xuong WARNING |
| `test_setup_is_idempotent` | Goi lai `setup_logging()` khong nhan doi handler |
| `test_unwritable_log_directory_does_not_crash` | Khong ghi duoc file log van chay duoc |

### 8.3 File khong bi dong toi

```bash
git status --short ai/ ui/qml/ models/ ml/knn.py ml/kmeans.py
# (khong co ket qua)
```

---

## 9. RISK

| # | Risk | Muc do | Cach xu ly |
|---|---|---|---|
| 1 | Con 18 `print()` trong `ml/knn.py`, `ml/kmeans.py` | **Co chu y** | Quyet dinh cua nguoi chu du an de giu cam ket "khong sua AI". Da ghi ro o muc 3.2 |
| 2 | `RedactingFormatter` chay `redact()` tren MOI dong log | Thap | Chi chay khi ban ghi duoc emit that su; console mac dinh o INFO |
| 3 | Mau che qua rong, che nham du lieu vo hai | Thap | Chi khop khi co tu khoa (`password=`, `Bearer`) hoac dung dinh dang chuoi ket noi. Co test `test_harmless_text_is_untouched` |
| 4 | Bi mat qua ngan (< 4 ky tu) khong duoc dang ky | **Co chu y** | Chuoi ngan se thay the nham khap noi. Mat khau 3 ky tu la van de bao mat lon hon nhieu |
| 5 | File log phinh to | Thap | Xoay vong 5 file x 2 MB = toi da 10 MB. `logs/` da vao `.gitignore` |
| 6 | File log chua thong tin chan doan | Trung binh | Da che mat khau/token. Van nen coi `logs/` la du lieu rieng tu |
| 7 | Script chay khong qua `setup_logging()` | Thap | `register_secret()` da chay ngay luc nap config, khong doi luc lap dat logging |
| 8 | `core/` khong duoc import `config/` o cap module | Trung binh | Da co ghi chu ro trong `core/logging_config.py`. Vi pham se tao vong lap import |

---

## 10. CHANGELOG

### File tao moi (6)

| File | Noi dung |
|---|---|
| `core/__init__.py` | Export + 5 quy tac cua Sprint 7 |
| `core/errors.py` | `AppError` + 17 lop con, `user_message_for()`, `error_code_for()` |
| `core/logging_config.py` | Logger phan cap, console + file xoay vong, `setup_from_app_config()` |
| `core/redaction.py` | `SensitiveDataFilter`, `RedactingFormatter`, `register_secret()` |
| `core/messages.py` | Catalog 34 thong diep + `contains_technical_detail()` |
| `test/test_logging.py` + `test/test_error_handling.py` | 63 test moi |

### File sua (16)

| File | Thay doi |
|---|---|
| `config/errors.py` | `ConfigError` ke thua `AppError` |
| `config/loader.py` | `register_secret()` ngay khi nap mat khau database |
| `database/exceptions.py` | `RepositoryError` ke thua `AppError`; thong diep lay tu catalog |
| `database/connection.py` | 2 cho `except: pass` -> `logger.warning` |
| `ui/services/auth_service.py` | 15 thong diep lay tu catalog |
| `ui/services/detection_service.py` | Thong diep lay tu catalog |
| `ui/services/dialog_service.py` | Tieu de tu catalog; them `publishError()` an toan |
| `ui/viewmodels/image_viewmodel.py` | 6 thong diep tu catalog |
| `ui/viewmodels/history_viewmodel.py` | 2 thong diep tu catalog |
| `ui/workers/webcam_worker.py` | 4 thong diep tu catalog |
| `ui/main_qt.py` | `setup_from_app_config()` thay `logging.basicConfig` |
| `main.py` | Ghi chu thu tu bootstrap console/logging |
| `utils/console.py`, `utils/helper.py`, `utils/translator.py` | 4 `print()` -> `logger.warning` |
| `utils/perf_monitor.py` | 6 `print()` -> `logger.info` (`utils.perf`) |
| `dataset/prepare_dataset.py` | 22 `print()` -> `logger.info` + bootstrap logging |
| `ml/evaluate.py` | 15 `print()` -> `logger.info` + bootstrap logging |
| `detection/webcam_detect.py` | 3 `print()` -> `logger.info` + bootstrap logging |
| `.gitignore` | Da co san `logs/` va `*.log` |

### Khong thay doi

- Thuat toan AI: YOLO, KNN, KMeans, Vocabulary.
- `ai/`, `ml/knn.py`, `ml/kmeans.py` — **nguyen ven**.
- Toan bo `ui/qml/` (15 file).
- **Noi dung** moi thong diep gui cho nguoi dung — chi doi cho cat giu.
- Schema database, cau SQL, tham so cau hinh.

---

## 11. SAN SANG CHO SPRINT 8

Sprint 8 (Testing & Performance) da co san diem bam:

1. **366 test** chia theo tang, chay 9,88 giay, khong can YOLO/database/webcam.
2. `requirements-dev.txt` (Sprint 6) da ghim `pytest`, `pytest-cov`, `psutil` —
   chi can cai la do duoc do phu.
3. `utils/perf_monitor.py` da ghi qua logger `utils.perf`, bat bang
   `AI_ENGLISH_PERF=1` — so lieu hieu nang gio vao duoc file log.
4. Da co 2 script benchmark tu Sprint 4 va 5:
   `test/benchmark_database.py`, `test/benchmark_thread.py`.
5. Chua co: do phu (coverage), test tich hop, do thoi gian nap YOLO va FPS webcam.

---

Sprint 7 hoàn thành.

Logging và Error Handling đã được chuẩn hóa.

Không còn print() ngoài hai file thuật toán được giữ nguyên có chủ ý, và không còn lỗi bị nuốt.

Sẵn sàng chuyển sang Sprint 8: Testing & Performance.
