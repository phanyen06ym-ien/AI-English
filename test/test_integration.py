"""Sprint 8 - Test tich hop va bao ve nguong hieu nang khoi dong.

Khac voi unit test (moi test soi mot lop), day la test **nhieu tang that chay
cung nhau**: Controller -> ViewModel -> Worker -> Service -> Repository.
Chi AI, camera va con tro database la gia.

Quan trong nhat trong file nay: `StartupBudgetTest`. No la chot chan chong hoi
quy cho toi uu cua Sprint 8 — neu ai do them lai mot import nang o cap module,
khoi dong quay ve ~10 giay va test se do NGAY, thay vi doi den luc nguoi dung
than phien.
"""

from __future__ import annotations

import subprocess
import sys
import time
import unittest
from pathlib import Path

from test.db_fakes import FakeCursorFactory
from test.ui_fakes import (
    FakeAIEngine,
    FakeCamera,
    FakeHistoryService,
    ensure_app,
    make_frame,
    process_events,
    wait_for,
)

from config import load_test_config
from config.schema import CameraConfig, HistoryConfig
from database.repositories.history_repository import HistoryRepository
from ui.app_context import AppContext


ROOT = Path(__file__).resolve().parent.parent


# ======================================================================
# 1. Nguong hieu nang khoi dong (chot chan chong hoi quy)
# ======================================================================


class StartupBudgetTest(unittest.TestCase):
    """Import tang GUI KHONG duoc keo theo thu vien nang.

    Truoc Sprint 8:

        import torch                     2.386 ms
        import ai.vocabulary (sklearn)   4.848 ms
        nap model k-NN                   1.888 ms
        nap YOLO                           431 ms
        --------------------------------------------
        ~10.000 ms truoc khi cua so hien ra

    Sau Sprint 8: ~1.085 ms, khong thu vien nang nao duoc nap.
    """

    #: Thu vien nang khong duoc co mat sau khi import tang GUI.
    HEAVY_MODULES = (
        "torch",
        "ultralytics",
        "sklearn",
        "pandas",
    )

    #: Nguong rong rai (giay). Muc tieu that su la ~1,1 giay.
    IMPORT_BUDGET_SECONDS = 4.0

    def _probe(
        self,
        statement: str,
    ) -> dict:
        """Chay `statement` trong mot tien trinh sach roi bao ve module da nap."""
        script = (
            "import json, sys, time\n"
            "t = time.perf_counter()\n"
            f"{statement}\n"
            "elapsed = time.perf_counter() - t\n"
            "heavy = [m for m in "
            f"{self.HEAVY_MODULES!r} if m in sys.modules]\n"
            "print(json.dumps({'elapsed': elapsed, 'heavy': heavy}))\n"
        )

        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=180,
        )

        self.assertEqual(
            result.returncode,
            0,
            f"Tien trinh con that bai:\n{result.stderr[-2000:]}",
        )

        import json

        return json.loads(
            result.stdout.strip().splitlines()[-1]
        )

    def test_importing_app_context_loads_no_heavy_library(self):
        report = self._probe("import ui.app_context")

        self.assertEqual(
            report["heavy"],
            [],
            "Import tang GUI khong duoc keo theo thu vien nang. "
            "Kiem tra xem co ai them lai `from ai...` o cap module khong.",
        )

    def test_importing_app_context_is_fast(self):
        report = self._probe("import ui.app_context")

        self.assertLess(
            report["elapsed"],
            self.IMPORT_BUDGET_SECONDS,
            f"Import tang GUI ton {report['elapsed']:.1f} s "
            f"(nguong {self.IMPORT_BUDGET_SECONDS} s)",
        )

    def test_ai_package_import_is_lazy(self):
        """`import ai` khong duoc nap YOLO hay sklearn."""
        report = self._probe("import ai")

        self.assertEqual(
            report["heavy"],
            [],
            "`ai/__init__.py` phai nap tre (PEP 562)",
        )

    def test_ai_models_import_is_lazy(self):
        """Lay mot dataclass tu `ai.models` khong duoc keo theo torch."""
        report = self._probe(
            "from ai.models import ImageAnalysisResult"
        )

        self.assertEqual(report["heavy"], [])

    def test_ai_public_api_is_unchanged(self):
        """Nap tre KHONG duoc lam mat mot ten cong khai nao."""
        import ai

        expected = {
            "AIEngine",
            "ClusterResult",
            "DetectedObject",
            "DetectionResult",
            "ImageAnalysisResult",
            "ObjectDetector",
            "RelatedWord",
            "TimingInfo",
            "VocabularyEntry",
            "all_words",
            "classify_word",
            "cluster_vocabulary",
            "get_cluster_by_word",
            "get_kmeans_metrics",
            "get_related_words",
            "get_topic_clusters",
            "get_word_info",
            "get_words_in_same_cluster",
        }

        self.assertEqual(set(ai.__all__), expected)
        self.assertEqual(set(dir(ai)), expected)

    def test_unknown_attribute_still_raises(self):
        import ai

        with self.assertRaises(AttributeError):
            ai.khong_ton_tai

    def test_perf_monitor_does_not_import_torch(self):
        report = self._probe("import utils.perf_monitor")

        self.assertNotIn(
            "torch",
            report["heavy"],
            "perf_monitor chi duoc nap torch khi AI_ENGLISH_PERF=1",
        )


# ======================================================================
# 2. Nap tre AI
# ======================================================================


class LazyLoadingTest(unittest.TestCase):
    """`ui/services/ai_bootstrap.py` - nap dung mot lan, an toan da luong."""

    def test_lazy_callable_loads_once(self):
        from ui.services.ai_bootstrap import _LazyCallable

        lazy = _LazyCallable("json", "dumps")

        self.assertFalse(lazy.is_loaded)

        self.assertEqual(lazy({"a": 1}), '{"a": 1}')
        self.assertTrue(lazy.is_loaded)

        first = lazy.load()
        second = lazy.load()
        self.assertIs(first, second)

    def test_lazy_callable_unknown_attribute(self):
        from ui.services.ai_bootstrap import _LazyCallable

        lazy = _LazyCallable("json", "khong_co_ham_nay")

        with self.assertRaises(AttributeError):
            lazy.load()

    def test_lazy_callable_is_thread_safe(self):
        import threading

        from ui.services.ai_bootstrap import _LazyCallable

        lazy = _LazyCallable("json", "dumps")
        results = []
        barrier = threading.Barrier(8)

        def worker():
            barrier.wait()
            results.append(lazy.load())

        threads = [
            threading.Thread(target=worker)
            for _ in range(8)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(len(results), 8)
        self.assertEqual(len(set(map(id, results))), 1)

    def test_lazy_detector_reports_state(self):
        from ui.services.ai_bootstrap import LazyObjectDetector

        detector = LazyObjectDetector()

        self.assertFalse(detector.is_loaded)
        self.assertTrue(hasattr(detector, "detect"))

    def test_engine_parts_start_unloaded(self):
        from ui.services.ai_bootstrap import LazyAIEngineParts

        parts = LazyAIEngineParts()

        self.assertFalse(parts.is_loaded)
        self.assertFalse(parts.detector.is_loaded)
        self.assertFalse(parts.vocabulary_provider.is_loaded)


class WarmupWorkerTest(unittest.TestCase):
    """Worker nap truoc AI sau khi cua so hien ra."""

    class FakePart:
        def __init__(self, value=None):
            self.value = value
            self.is_loaded = False

        def load(self):
            self.is_loaded = True
            return self.value

    class FakeParts:
        def __init__(self, outer):
            self.vocabulary_provider = outer.FakePart(
                lambda: {
                    "laptop": {"english": "laptop"},
                    "mouse": {"english": "mouse"},
                }
            )
            self.classifier = outer.FakePart()
            self.related_words_provider = outer.FakePart()
            self.cluster_words_provider = outer.FakePart()
            self.detector = outer.FakePart()

    def setUp(self):
        ensure_app()

    def test_warmup_loads_everything_and_emits(self):
        from ui.workers.warmup_worker import WarmupWorker

        parts = self.FakeParts(self)
        worker = WarmupWorker(parts)

        vocabulary = []
        completed = []

        worker.vocabularyReady.connect(vocabulary.append)
        worker.warmupCompleted.connect(
            lambda: completed.append(1)
        )

        worker.start()

        self.assertTrue(
            wait_for(lambda: completed == [1])
        )
        worker.dispose(3000)
        process_events(5)

        self.assertEqual(len(vocabulary[0]), 2)
        self.assertTrue(parts.detector.is_loaded)
        self.assertTrue(parts.classifier.is_loaded)
        self.assertTrue(parts.related_words_provider.is_loaded)
        self.assertTrue(parts.cluster_words_provider.is_loaded)

    def test_warmup_can_be_cancelled(self):
        from ui.workers.lifecycle import WorkerState
        from ui.workers.warmup_worker import WarmupWorker

        parts = self.FakeParts(self)
        worker = WarmupWorker(parts)

        worker.cancel()
        worker.start()

        self.assertTrue(
            wait_for(
                lambda: worker.state is WorkerState.CANCELLED
            )
        )
        worker.dispose(3000)

        self.assertFalse(parts.detector.is_loaded)

    def test_vocabulary_view_model_receives_warmup_data(self):
        from ui.viewmodels.vocabulary_viewmodel import (
            VocabularyViewModel,
        )

        view_model = VocabularyViewModel(
            FakeAIEngine(),
            load_on_init=False,
        )

        self.assertEqual(view_model.word_count, 0)

        emitted = []
        view_model.VocabularyChanged.connect(emitted.append)

        view_model.setVocabulary(
            [
                {
                    "english": "laptop",
                    "vietnamese": "May tinh",
                    "category": "Technology",
                    "level": "Medium",
                }
            ]
        )

        self.assertEqual(view_model.word_count, 1)
        self.assertEqual(len(emitted[0]), 1)


# ======================================================================
# 3. Tich hop nhieu tang
# ======================================================================


class FullStackDetectionTest(unittest.TestCase):
    """Controller -> ViewModel -> Worker -> Service -> Repository, chay that."""

    def setUp(self):
        ensure_app()

        self.cursor_factory = FakeCursorFactory(rowcount=1)
        self.engine = FakeAIEngine()

        self.context = AppContext.build(
            config=load_test_config(),
            ai_engine=self.engine,
            file_picker=lambda: "anh-thu-nghiem.jpg",
            history_repository=HistoryRepository(
                cursor_factory=self.cursor_factory,
                config=HistoryConfig(),
            ),
            capture_factory=lambda camera_id: FakeCamera(),
        )

        # Doc anh: thay bang khung hinh gia de khong can file that.
        self.context.detection_service._image_reader = (
            lambda path: make_frame()
        )

    def tearDown(self):
        self.context.shutdown()
        process_events(10)

    def test_choose_then_detect_writes_history(self):
        controller = self.context.image_controller

        self.context.apply_current_user({"id": 42})

        finished = []
        controller.detectionFinished.connect(
            lambda: finished.append(1)
        )

        controller.chooseImage()
        self.assertTrue(
            wait_for(
                lambda: controller.selectedImagePath
                == "anh-thu-nghiem.jpg"
            )
        )
        wait_for(lambda: not controller.busy)

        controller.detectSelectedImage()
        self.assertTrue(
            wait_for(lambda: finished == [1])
        )

        # Ket qua len toi Controller
        self.assertEqual(
            controller.detections[0]["english"],
            "laptop",
        )

        # Va di xuong toi cau lenh SQL that
        inserts = [
            parameters
            for query, parameters in self.cursor_factory.executed
            if "INSERT INTO history" in query
        ]
        self.assertEqual(len(inserts), 1)
        self.assertEqual(inserts[0][0], 42)
        self.assertEqual(inserts[0][1], "laptop")

    def test_history_refresh_reaches_the_model(self):
        import datetime

        self.cursor_factory.results = [
            [
                (
                    1,
                    42,
                    "laptop",
                    "May tinh",
                    "Technology",
                    0.9,
                    datetime.datetime(2026, 1, 2, 3, 4),
                )
            ]
        ]
        self.cursor_factory._result_index = 0

        controller = self.context.history_controller
        controller.set_user_id(42)

        statuses = []
        controller.statusChanged.connect(statuses.append)

        controller.refresh()

        self.assertTrue(
            wait_for(lambda: bool(statuses))
        )
        self.assertEqual(controller.model.rowCount(), 1)

    def test_login_propagates_user_to_every_layer(self):
        self.context.apply_current_user({"id": 7})

        self.assertEqual(
            self.context.image_view_model.user_id,
            7,
        )
        self.assertEqual(
            self.context.webcam_view_model.user_id,
            7,
        )

        self.context.apply_current_user({})

        self.assertIsNone(
            self.context.history_view_model.user_id
        )

    def test_warmup_is_noop_when_engine_is_injected(self):
        self.assertIsNone(self.context.ai_parts)
        self.assertIsNone(self.context.warmup())

    def test_qml_contract_still_holds_end_to_end(self):
        """Sau 8 sprint, moi context property QML dung van con day du."""
        properties = self.context.context_properties()

        for name in (
            "imageController",
            "webcamController",
            "vocabController",
            "historyController",
            "statsController",
            "authController",
        ):
            self.assertIn(name, properties)


class WebcamIntegrationTest(unittest.TestCase):
    """Luong webcam chay that qua Controller."""

    def setUp(self):
        ensure_app()

        self.context = AppContext.build(
            config=load_test_config().with_overrides(
                camera=CameraConfig(max_frames_in_flight=2)
            ),
            ai_engine=FakeAIEngine(),
            file_picker=lambda: "",
            history_service=FakeHistoryService(),
            capture_factory=lambda camera_id: FakeCamera(
                frames=10**6
            ),
        )

    def tearDown(self):
        self.context.shutdown()
        process_events(20)

    def test_start_produces_frames_and_results(self):
        controller = self.context.webcam_controller

        frames = []
        results = []

        controller.frameChanged.connect(frames.append)
        controller.resultsChanged.connect(results.append)

        controller.start()

        self.assertTrue(
            wait_for(lambda: len(frames) >= 2, timeout=5.0)
        )
        self.assertTrue(
            wait_for(lambda: len(results) >= 1, timeout=5.0)
        )

        controller.stop()

        self.assertTrue(
            wait_for(lambda: not controller.running)
        )

    def test_backpressure_limit_is_respected_end_to_end(self):
        controller = self.context.webcam_controller
        controller.start()

        wait_for(
            lambda: self.context.webcam_view_model.frame_stats["emitted"] > 0,
            timeout=5.0,
        )

        stats = self.context.webcam_view_model.frame_stats

        self.assertLessEqual(stats["in_flight"], 2)

        controller.stop()
        wait_for(lambda: not controller.running)


# ======================================================================
# 4. Ky luat cua bo test
# ======================================================================


class TestSuiteDisciplineTest(unittest.TestCase):
    """NHIEM VU 4 - bo test khong duoc doi hoi moi truong that."""

    def test_manual_scripts_are_out_of_collection(self):
        """Script can DB/YOLO/model phai nam trong `test/manual/`."""
        automated = {
            path.name
            for path in (ROOT / "test").glob("test_*.py")
        }

        for name in (
            "test_connection.py",
            "test_login.py",
            "test_knn.py",
            "test_kmeans.py",
            "test_ml.py",
            "test_yolo_image.py",
            "test_system_evaluation.py",
        ):
            self.assertNotIn(
                name,
                automated,
                f"{name} ghi de model hoac can moi truong that - "
                "phai nam trong test/manual/",
            )
            self.assertTrue(
                (ROOT / "test" / "manual" / name).exists(),
                f"Khong tim thay test/manual/{name}",
            )

    def test_pytest_excludes_manual_directory(self):
        content = (ROOT / "pytest.ini").read_text(
            encoding="utf-8"
        )

        self.assertIn("norecursedirs", content)
        self.assertIn("test/manual", content)

    def test_single_entry_point_exists(self):
        self.assertTrue(
            (ROOT / "run_tests.py").exists(),
            "Phai co mot lenh chay test duy nhat",
        )

    def test_automated_suite_does_not_touch_model_artifacts(self):
        """Bo test tu dong khong duoc doi `models/*.pkl`."""
        models = ROOT / "models"

        before = {
            path.name: (path.stat().st_mtime, path.stat().st_size)
            for path in models.glob("*.pkl")
        }

        self.assertTrue(before, "Khong tim thay model .pkl nao")

        # Cho mot nhip de moc thoi gian doi duoc neu co ai ghi.
        time.sleep(0.01)

        after = {
            path.name: (path.stat().st_mtime, path.stat().st_size)
            for path in models.glob("*.pkl")
        }

        self.assertEqual(
            before,
            after,
            "Bo test tu dong da lam thay doi artifact mo hinh",
        )


if __name__ == "__main__":
    unittest.main()
