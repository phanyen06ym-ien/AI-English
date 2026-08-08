"""Script chay TAY - KHONG nam trong bo test tu dong.

Vi sao tach ra (Sprint 8)
-------------------------

Cac file trong day deu ten `test_*.py` nen truoc Sprint 8, chay `pytest` la ca 7
file cung duoc thu gom va chay. Hau qua:

1. `test_knn.py` va `test_kmeans.py` **train lai va ghi de** `models/knn.pkl`,
   `models/kmeans.pkl` — bo test lam thay doi artifact cua mo hinh.
2. `test_connection.py`, `test_login.py` can **database that**.
3. `test_yolo_image.py`, `test_system_evaluation.py` can **YOLO that** (~12 giay).
4. `test_login.py` co the **tao du lieu that** trong bang `users`.

Bo test tu dong phai chay duoc moi luc, tren may bat ky, khong de lai dau vet.
Nen cac script nay duoc dua ra khoi pham vi thu gom.

Cach chay
---------

    python test/manual/test_connection.py          # can .env tro toi DB that
    python test/manual/test_knn.py                 # SE ghi de models/knn.pkl
    python test/manual/benchmark_app.py            # do hieu nang, can YOLO
    python test/manual/benchmark_database.py       # can DB that, chi doc
    python test/manual/benchmark_thread.py         # can DB that, chi doc

Sau khi chay `test_knn.py` / `test_kmeans.py` / `benchmark_app.py`, nho khoi phuc
artifact neu khong co chu dinh cap nhat:

    git checkout -- models/
"""
