# SPRINT 4 REPORT - DATABASE & REPOSITORY REFACTOR

Pham vi: bien `database/` thanh **Repository Layer**. Service khong con biet SQL.

Rang buoc da tuan thu:

| Rang buoc | Ket qua |
|---|---|
| Khong sua thuat toan AI (YOLO, KNN, KMeans) | Khong file nao trong `ai/`, `ml/`, `detection/`, `dataset/` bi sua |
| Khong sua QML | Khong file nao trong `ui/qml/` bi sua |
| Khong doi schema database | Khong co lenh DDL nao |
| Khong doi cau SQL dang chay dung | Moi cau SELECT/INSERT/UPDATE/DELETE giu nguyen van |
| Regression Test PASS | **176/176 test PASS** |

---

## 1. KIEN TRUC TRUOC

```text
ui/services/history_service.py
        |
        v
database/history.py          <- ham thu tuc
        |  - SQL viet thang trong ham
        |  - try/except nuot loi -> tra ve [] hoac False
        v
database/db.py
        |  - get_connection() mo ket noi MOI cho MOI cau lenh
        v
psycopg2 -> Supabase


ui/services/auth_service.py
        |
        v
database/auth.py             <- 3 trach nhiem tron lam mot
        |  - cau SQL
        |  - bcrypt (bam, kiem tra mat khau)
        |  - business rule (tu nang cap hash khi dang nhap)
        v
database/db.py
```

Van de do duoc:

1. **Moi cau lenh mo mot ket noi TCP + TLS moi.** Do thuc te: **1.092 ms**/cau lenh.
2. **Nuot loi.** `get_history()` loi ket noi tra ve `[]`; GUI hien "Da tai 0 ban ghi"
   trong khi that ra database dang hong.
3. **Tuple tho di len tang tren.** `row[0]`, `row[1]`, ... Doi thu tu cot trong
   cau SELECT la vo moi tang phia tren ma khong co canh bao.
4. **Khong test duoc** neu khong co PostgreSQL that.
5. **Mat ma hoc nam trong tang truy van.** `database/auth.py` vua viet SQL vua goi
   bcrypt vua quyet dinh khi nao nang cap hash.
6. **Ranh gioi transaction mo ho.** `commit=False` khong rollback, ket noi tra ve
   trong trang thai transaction dang mo.

---

## 2. KIEN TRUC SAU

```text
QML
 |
 v
Controller (thin adapter)
 |
 v
ViewModel
 |
 v
Worker (QThread)
 |
 v
Service            <- business rule, KHONG co SQL
 |
 v
Repository         <- SQL, tra ve Entity
 |
 v
Connection Pool
 |
 v
Database (PostgreSQL / Supabase)
```

Chi tiet:

```text
ui/services/history_service.py
        |
        v
database/repositories/history_repository.py
        |  SQL_INSERT_HISTORY / SQL_SELECT_BY_USER / SQL_DELETE_BY_USER
        |  -> tra ve list[HistoryEntry]
        v
database/connection.py
        |  ThreadedConnectionPool (1..8 ket noi)
        |  database_cursor(commit=...) -> ranh gioi transaction ro rang
        |  _translate() -> RepositoryError
        v
psycopg2 -> Supabase


ui/services/auth_service.py          <- luat validate + luat nang cap hash
        |
        +-- utils/password.py         <- bcrypt (hash, verify, needs_rehash)
        |
        v
database/repositories/user_repository.py
        |  SQL_FIND_BY_USERNAME / SQL_INSERT_USER / SQL_UPDATE_PASSWORD
        |  -> tra ve User
        v
database/connection.py
```

Lop tuong thich nguoc:

```text
database/auth.py     -> shim, goi UserRepository + utils.password
database/history.py  -> shim, goi HistoryRepository
database/db.py       -> shim, re-export database.connection
```

---

## 3. DATABASE REVIEW (NHIEM VU 1)

### 3.1 `database/db.py`

| Ham | Van de | Xu ly |
|---|---|---|
| `get_connection()` | Mo ket noi moi cho **moi** cau lenh. Voi Supabase qua Internet, moi lan bat tay ton ~1.000 ms | Them `ThreadedConnectionPool`, tai su dung ket noi |
| `database_cursor(commit=False)` | Khong rollback khi chi doc -> ket noi tra ve pool voi transaction dang mo | Luon ket thuc transaction: `COMMIT` neu `commit=True`, nguoc lai `ROLLBACK` |
| - | Loi psycopg2 ro ri thang len tang tren | `_translate()` doi sang `RepositoryError` |

### 3.2 `database/history.py`

| Ham | Van de | Xu ly |
|---|---|---|
| `save_history()` | SQL viet thang trong ham; `except Exception` -> `print()` + `return False` | SQL -> `HistoryRepository.add()`; loi -> `RepositoryError` |
| `get_history()` | Nuot loi -> `return []`. GUI khong phan biet "rong" voi "hong" | `HistoryRepository.list_by_user()` nem loi |
| `get_history()` | Tra ve `list[dict]` dung tay tu `row[0]`..`row[6]` | Tra ve `list[HistoryEntry]` |
| `clear_history()` | Nuot loi -> `return False` | `HistoryRepository.delete_by_user()` nem loi, tra ve so dong da xoa |
| Toan module | 5 lenh `print()` | Chuyen sang `logging` |

### 3.3 `database/auth.py`

| Ham | Van de | Xu ly |
|---|---|---|
| `_hash_password()`, `_verify_password()`, `_is_bcrypt_hash()` | Mat ma hoc nam trong tang SQL | Chuyen sang `utils/password.py` |
| `verify_login()` | **Business rule** (tu nang cap mat khau tho len bcrypt) nam trong tang truy van | Chuyen sang `AuthService._upgrade_password_if_needed()` |
| `find_user_by_username()` | Tra ve dict co **ca mat khau**; goi `print()` roi `raise` | `UserRepository` tra ve `User`; `to_public_dict()` khong bao gio kem mat khau |
| `change_password()` | Vua doc SQL, vua kiem tra mat khau, vua quyet dinh nghiep vu | SQL -> Repository; luat -> `AuthService.change_password()` |

### 3.4 Ham khong test duoc neu thieu database

**Truoc Sprint 4: toan bo.** Moi ham deu goi thang `database_cursor()`.

**Sau Sprint 4: khong con ham nao.** `BaseRepository` nhan `cursor_factory` qua
constructor, test tiem `FakeCursorFactory` vao.

---

## 4. REPOSITORY (NHIEM VU 3)

| Repository | File | Phuong thuc |
|---|---|---|
| `BaseRepository` | `database/repositories/base.py` | `fetch_one`, `fetch_all`, `execute`, `execute_returning` |
| `UserRepository` | `user_repository.py` | `find_by_username`, `exists`, `get_password_hash`, `create`, `update_password_hash` |
| `HistoryRepository` | `history_repository.py` | `add`, `list_by_user`, `delete_by_user` |

Nguyen tac (co test bao ve trong `RepositoryIsolationTest`):

- Repository **khong** import `ui`, `ai`, `PySide6`, `cv2`.
- Repository **khong** dung `print()`.
- Repository **khong** chua bcrypt hay bat ky business rule nao.
- Repository **khong** bat loi de tra ve gia tri rong.

Cau SQL duoc dua len hang so o dau module (`SQL_FIND_BY_USERNAME`,
`SQL_SELECT_BY_USER`, ...) — de doc, de soat, de so voi ban truoc.

---

## 5. ENTITY (NHIEM VU 4)

| Entity | Truong | Ghi chu |
|---|---|---|
| `User` | `id`, `username`, `fullname`, `password_hash` | `to_public_dict()` **khong bao gio** tra ve mat khau |
| `HistoryEntry` | `id`, `user_id`, `english_word`, `vietnamese_meaning`, `category`, `confidence`, `detected_time` | `to_dict()` giu dung key ma Service tu Sprint 2 dang dung |

Quy tac chuyen doi nam gon trong `from_row()`, tuc la **chi mot noi** biet thu tu
cot cua cau SELECT. Tang tren khong bao gio thay `row[0]`.

Xu ly gia tri NULL duoc giu dung nhu truoc:

| Cot NULL | Gia tri thay the |
|---|---|
| `vietnamese_meaning` | `""` |
| `category` | `"Unknown"` |
| `confidence` | `0.0` |

---

## 6. ERROR HANDLING (NHIEM VU 5)

### 6.1 Cay exception

```text
RepositoryError                 DB_REPOSITORY_ERROR
  ├── ConnectionFailedError     DB_CONNECTION_FAILED
  ├── QueryFailedError          DB_QUERY_FAILED
  ├── NotFoundError             DB_NOT_FOUND
  └── IntegrityError            DB_INTEGRITY_ERROR
```

Moi loi co:

- `error_code` — de tang tren nhan dien ma khong phai doc chuoi.
- `user_message` — thong diep tieng Viet cho nguoi dung.
- `cause` — exception goc, chi ghi vao log, **khong** hien cho nguoi dung.

### 6.2 Chinh sach loi cua Service

| Thao tac | Khi database loi | Ly do |
|---|---|---|
| **Ghi** lich su trong luc nhan dien | Ghi log, bo qua, tra ve `False` | Database hong khong duoc lam hong ket qua AI ma nguoi dung vua chup |
| **Doc** lich su | Nem `RepositoryError` -> Worker emit `failed` -> GUI bao loi | Nguoi dung bam "Làm mới" thi phai biet that bai |
| **Xoa** lich su | Nem `RepositoryError` -> Worker emit `failed` -> GUI bao loi | Nguoi dung bam "Xóa" thi phai biet that bai |
| **Dang nhap** | `AuthResult(success=False, error_code=..., message=user_message)` | Khong duoc lo chi tiet psycopg2 |

### 6.3 Thay doi hanh vi co chu y

> Truoc Sprint 4: database hong khi bam "Làm mới" -> GUI hien "Đã tải 0 bản ghi."
>
> Sau Sprint 4: GUI hien thong diep loi that su.

Day la **muc tieu** cua NHIEM VU 5, khong phai loi hoi quy. Duong dan `failed` da
co san trong `HistoryWorker` va `StatsWorker` tu Sprint 3, khong phai sua QML.

### 6.4 Chong ro ri du lieu nhay cam

| Kiem tra | Ket qua |
|---|---|
| `User.to_public_dict()` khong kem mat khau | Co test |
| `AuthResult.user` khong kem mat khau | Co test |
| Thong diep loi khong chua `psycopg2` | Co test |
| Thong diep loi khong chua mat khau nguoi dung | Co test |
| `INSERT INTO users` khong bao gio nhan mat khau dang tho | Co test |

---

## 7. TRANSACTION (NHIEM VU 6)

```text
with database_cursor(commit=False) as cursor:   # chi doc
    ...                                          -> ROLLBACK khi ra khoi khoi

with database_cursor(commit=True) as cursor:    # ghi
    ...                                          -> COMMIT khi ra khoi khoi

Co exception                                     -> ROLLBACK, danh dau ket noi
                                                    hong, dong han thay vi tra
                                                    lai pool, roi nem
                                                    RepositoryError
```

| Truoc Sprint 4 | Sau Sprint 4 |
|---|---|
| `commit=False` khong lam gi -> ket noi dong lai khi con transaction mo | `commit=False` luon `ROLLBACK` |
| Ket noi loi van duoc dung lai | Ket noi loi bi dong (`putconn(close=True)`) |
| Loi psycopg2 ro ri len tang tren | Doi sang `RepositoryError` |

Anh xa loi:

| Loi psycopg2 | Exception cua Repository |
|---|---|
| `IntegrityError` | `IntegrityError` |
| `OperationalError` | `ConnectionFailedError` |
| `psycopg2.Error` khac | `QueryFailedError` |

---

## 8. CONNECTION POOL (NHIEM VU 2)

`database/connection.py`:

| Tham so | Gia tri |
|---|---|
| Loai pool | `psycopg2.pool.ThreadedConnectionPool` (an toan da luong) |
| Toi thieu | 1 ket noi |
| Toi da | 8 ket noi |
| Khoi tao | Lazy, co khoa (`threading.Lock`) |
| Khi khong tao duoc pool | Tu dong quay ve mo ket noi truc tiep — ung dung van chay |
| Dong pool | `AppContext.shutdown()` goi `close_pool()` sau khi moi worker da dung |

Vi sao can an toan da luong: Sprint 3 tao `HistoryWorker`, `StatsWorker`,
`HistoryWriterWorker` chay tren cac thread khac nhau, tat ca deu truy cap database.

---

## 9. PERFORMANCE (NHIEM VU 11)

Do bang `test/benchmark_database.py` tren **database that** (Supabase PostgreSQL
17.6), 8 vong, **chi cau lenh doc**.

```bash
python test/benchmark_database.py --rounds 8
```

| Che do | Lan 1 | Trung binh | **Trung vi** | Min | Max | Tong 8 lan |
|---|---:|---:|---:|---:|---:|---:|
| Direct — truoc Sprint 4 | 1.116,9 ms | 1.094,4 ms | **1.092,7 ms** | 1.069,3 ms | 1.116,9 ms | 8.755,4 ms |
| Pooled — sau Sprint 4 | 1.227,9 ms | 503,7 ms | **400,5 ms** | 397,4 ms | 1.227,9 ms | 4.029,5 ms |
| `Repository.list_by_user` | 542,1 ms | 421,9 ms | 404,2 ms | 402,0 ms | 542,1 ms | 3.374,9 ms |

**Ket qua: nhanh hon 2,7 lan theo trung vi, tiet kiem 4.726 ms tren 8 cau lenh.**

Doc them tu so lieu:

1. **Lan dau cua pool cham hon** (1.227,9 ms) vi phai khoi tao pool. Tu lan thu
   hai tro di on dinh o ~400 ms.
2. **~400 ms con lai la do tre mang** toi Supabase, khong phai chi phi mo ket noi.
   Pool da loai bo gan nhu toan bo phan bat tay TCP + TLS.
3. **Loi ich lon nhat o luong webcam**: moi lan ghi lich su truoc day ton them
   ~700 ms chi de mo ket noi. Voi cooldown 5 giay va nhieu vat the trong khung
   hinh, day la khoan tiet kiem dang ke.

Luu y: benchmark chi chay `SELECT`, khong ghi, khong xoa, khong doi schema.

---

## 10. REGRESSION TEST

### 10.1 Ket qua

| Bo test | Test | Ket qua |
|---|---:|---|
| `test_ai_engine.py` (Sprint 2) | 7 | PASS |
| `test_controller.py` (Sprint 3) | 33 | PASS |
| `test_viewmodel.py` (Sprint 3) | 40 | PASS |
| `test_worker.py` (Sprint 3) | 24 | PASS |
| `test_repository.py` (Sprint 4, moi) | 40 | PASS |
| `test_database_service.py` (Sprint 4, moi) | 32 | PASS |
| **Tong** | **176** | **PASS, exit code 0** |

```bash
python -m unittest test.test_ai_engine test.test_controller test.test_viewmodel \
                  test.test_worker test.test_repository test.test_database_service
```

Thoi gian chay: **3,77 giay**. Khong can PostgreSQL, khong can YOLO, khong can webcam.

### 10.2 Kiem tra tuong thich nguoc (NHIEM VU 9)

| Kiem tra | Ket qua |
|---|---|
| `python test/test_connection.py` | PASS — ket noi that, tra ve `PostgreSQL 17.6` |
| `database.history` giu du 4 ham cu | PASS |
| `database.auth` giu du 7 ham cu | PASS |
| `database.db` giu `get_connection`, `database_cursor` | PASS |
| Shim `get_history()` van tra `[]` khi database loi | PASS |
| Shim `verify_login()` van tu nang cap mat khau tho | PASS |

### 10.3 Test bao ve kien truc moi

| Test | Bao ve dieu gi |
|---|---|
| `ServiceHasNoSqlTest.test_services_contain_no_sql` | Service khong duoc chua `SELECT`, `INSERT INTO`, `UPDATE`, `DELETE FROM` |
| `ServiceHasNoSqlTest.test_services_do_not_import_connection_layer` | Service khong duoc import `psycopg2`, `database.connection`, `database.db` |
| `RepositoryIsolationTest.test_repositories_do_not_import_ui_or_ai` | Repository doc lap voi GUI/AI |
| `RepositoryIsolationTest.test_repositories_do_not_print` | Repository khong dung `print()` |
| `UserRepositoryTest.test_repository_has_no_password_logic` | Repository khong chua `bcrypt`, `hashpw`, `checkpw` |

### 10.4 Hoi quy dinh dang du lieu

| Kiem tra | Ket qua |
|---|---|
| `format_history_rows()` — key va fallback | Khong doi |
| Dinh dang ngay `%d/%m/%Y %H:%M` | Khong doi |
| Cong thuc thong ke | Khong doi |
| Gioi han truy van `max(1, min(limit, 500))` | Khong doi |
| Chuan hoa truoc khi INSERT (`strip()`, `"Unknown"`) | Khong doi |
| Thuat toan bam mat khau (bcrypt + `gensalt()`) | Khong doi |
| Chap nhan mat khau dang tho (du lieu cu) | Khong doi |

### 10.5 File khong bi dong toi

```bash
git status --short ai/ ml/ detection/ dataset/ models/ ui/qml/
# (khong co ket qua)
```

---

## 11. RISK

| # | Risk | Muc do | Cach xu ly |
|---|---|---|---|
| 1 | Pool giu ket noi qua lau, Supabase ngat phia server | Trung binh | Ket noi loi bi dong han (`putconn(close=True)`), lan sau pool tu mo ket noi moi |
| 2 | Vuot 8 ket noi khi nhieu worker cung chay | Thap | Sprint 3 chi tao toi da 4 worker chay database; `getconn()` cho neu het |
| 3 | Khong tao duoc pool (moi truong han che) | Thap | Tu dong quay ve che do mo ket noi truc tiep, dung hanh vi Sprint 3 |
| 4 | GUI gio hien loi database thay vi im lang | **Co chu y** | Day la muc tieu NHIEM VU 5. Duong dan `failed` da co san tu Sprint 3, khong sua QML |
| 5 | Script cu goi `database.auth._hash_password` | Thap | Giu alias `_hash_password`, `_verify_password`, `_is_bcrypt_hash` trong shim |
| 6 | Shim `database/auth.py` lap lai luat nang cap hash cua `AuthService` | Thap | Co chu y: shim la lop tuong thich sap loai bo, duoc test rieng. Ung dung chinh **khong** di qua shim |
| 7 | Pool khong dong khi ung dung crash | Thap | Ket noi se bi server thu hoi khi tien trinh ket thuc |
| 8 | `AuthService` van goi database **dong bo tren GUI thread** | Trung binh | **Chuyen sang Sprint 5** (Worker & Thread Refactor) — da ghi trong ke hoach |
| 9 | Benchmark chay tren database that | Thap | Chi dung cau lenh `SELECT`; khong ghi, khong xoa, khong doi schema |

---

## 12. CHANGELOG

### File tao moi (9)

| File | Noi dung |
|---|---|
| `database/exceptions.py` | Cay exception: `RepositoryError`, `ConnectionFailedError`, `QueryFailedError`, `NotFoundError`, `IntegrityError` |
| `database/entities.py` | `User`, `HistoryEntry` |
| `database/connection.py` | Connection pool, `database_cursor()` voi transaction boundary, `_translate()` |
| `database/repositories/__init__.py` | Export Repository |
| `database/repositories/base.py` | `BaseRepository` — `fetch_one`, `fetch_all`, `execute`, `execute_returning` |
| `database/repositories/user_repository.py` | `UserRepository` |
| `database/repositories/history_repository.py` | `HistoryRepository` |
| `utils/password.py` | `hash_password`, `verify_password`, `is_bcrypt_hash`, `needs_rehash` |
| `test/db_fakes.py` | `FakeCursorFactory`, `failing_factory`, `integrity_factory` |

### File test moi (3)

| File | Test |
|---|---:|
| `test/test_repository.py` | 40 |
| `test/test_database_service.py` | 32 |
| `test/benchmark_database.py` | (script do hieu nang) |

### File sua (6)

| File | Thay doi |
|---|---|
| `database/db.py` | Thanh shim re-export `database.connection` |
| `database/history.py` | Thanh shim tren `HistoryRepository`; `print()` -> `logging` |
| `database/auth.py` | Thanh shim tren `UserRepository` + `utils.password`; bo `print()` lo loi database |
| `ui/services/history_service.py` | Goi `HistoryRepository`; them `load_entries()`; tach chinh sach loi ghi/doc |
| `ui/services/auth_service.py` | Goi `UserRepository` + `utils.password`; nhan luat nang cap hash; them `error_code` vao `AuthResult` |
| `ui/app_context.py` | Tiem `HistoryRepository` / `UserRepository`; goi `close_pool()` khi thoat |

### Khong thay doi

- Thuat toan AI: YOLO, KNN, KMeans, Vocabulary, feature, scaler, metric, weight.
- Toan bo `ai/`, `ml/`, `detection/`, `dataset/`.
- Toan bo `ui/qml/` (15 file).
- Schema database — khong co lenh DDL nao.
- Noi dung cau SQL — moi cau SELECT/INSERT/UPDATE/DELETE giu nguyen van.
- Thuat toan bam mat khau va viec chap nhan mat khau dang tho.
- Dinh dang du lieu gui len View.

---

## 13. SAN SANG CHO SPRINT 5

Sprint 5 (Worker & Thread Refactor) da co san diem bam:

1. `AuthService` nhan `UserRepository` qua constructor -> dua sang worker khong
   phai sua Repository.
2. Pool da an toan da luong -> them worker khong phai sua tang ket noi.
3. `RepositoryError` co `error_code` va `user_message` -> worker chi can chuyen
   tiep, khong phai dich loi.
4. `AppContext.shutdown()` da dong pool dung thu tu: worker dung truoc, pool dong sau.

---

Sprint 4 hoàn thành.

Database Layer đã được chuẩn hóa.

Service không còn biết SQL.

Sẵn sàng chuyển sang Sprint 5: Worker & Thread Refactor.
