"""Sprint 3 - Unit test cho Worker layer.

Kiem tra:

1. Worker chi giao tiep bang Signal.
2. Worker khong import QtWidgets / QML (khong cham GUI).
3. Business logic da nam o Service, khong con o Worker.
4. Signal tu Worker Thread duoc nhan tren GUI Thread (thread safety).
"""

from __future__ import annotations

import inspect
import unittest

from test.ui_fakes import (
    FakeAIEngine,
    FakeCamera,
    FakeHistoryService,
    ensure_app,
    make_analysis,
    make_frame,
    process_events,
    wait_for,
)

from ui.services.detection_service import DetectionService
from ui.services.history_service import HistoryRecordPolicy
from ui.workers.history_worker import HistoryWorker
from ui.workers.image_worker import ImageWorker, PreviewLoadWorker
from ui.workers.speech_worker import SpeakTask
from ui.workers.stats_worker import StatsWorker
from ui.workers.webcam_worker import HistoryWriterWorker, WebcamWorker


def build_detection_service(
    engine: FakeAIEngine | None = None,
    history_service: FakeHistoryService | None = None,
    image_reader=None,
) -> DetectionService:
    return DetectionService(
        engine if engine is not None else FakeAIEngine(),
        history_service=(
            history_service
            if history_service is not None
            else FakeHistoryService()
        ),
        image_reader=(
            image_reader
            if image_reader is not None
            else (lambda path: make_frame())
        ),
    )


class WorkerIsolationTest(unittest.TestCase):
    """Worker khong duoc cham vao View."""

    WORKER_MODULES = (
        "ui.workers.image_worker",
        "ui.workers.webcam_worker",
        "ui.workers.history_worker",
        "ui.workers.stats_worker",
        "ui.workers.speech_worker",
    )

    def test_workers_do_not_import_gui_modules(self):
        import importlib

        for module_name in self.WORKER_MODULES:
            module = importlib.import_module(module_name)
            source = inspect.getsource(module)

            self.assertNotIn(
                "QtWidgets",
                source,
                f"{module_name} khong duoc import QtWidgets",
            )
            self.assertNotIn(
                "QtQml",
                source,
                f"{module_name} khong duoc import QtQml",
            )

    def test_workers_do_not_call_database_directly(self):
        import importlib

        for module_name in self.WORKER_MODULES:
            module = importlib.import_module(module_name)
            source = inspect.getsource(module)

            self.assertNotIn(
                "from database",
                source,
                f"{module_name} phai di qua Service, khong goi database",
            )


class ImageWorkerTest(unittest.TestCase):
    def setUp(self):
        ensure_app()
        self.history_service = FakeHistoryService()
        self.engine = FakeAIEngine()
        self.service = build_detection_service(
            self.engine,
            self.history_service,
        )

    def test_run_emits_image_analysis_and_progress(self):
        worker = ImageWorker(
            self.service,
            "any.jpg",
            user_id=7,
        )

        images = []
        analyses = []
        progress = []
        failures = []

        worker.imageReady.connect(images.append)
        worker.analysisReady.connect(analyses.append)
        worker.progressChanged.connect(progress.append)
        worker.failed.connect(failures.append)

        worker.run()

        self.assertEqual(failures, [])
        self.assertEqual(len(images), 1)
        self.assertEqual(len(analyses), 1)
        self.assertEqual(self.engine.analyze_calls, 1)

        self.assertEqual(progress[0], 5)
        self.assertEqual(progress[-1], 100)
        self.assertEqual(
            progress,
            sorted(progress),
            "progress phai tang dan",
        )

    def test_history_is_saved_through_service(self):
        worker = ImageWorker(
            self.service,
            "any.jpg",
            user_id=7,
        )
        worker.run()

        self.assertEqual(len(self.history_service.saved), 1)
        self.assertEqual(
            self.history_service.saved[0][0],
            "laptop",
        )
        self.assertEqual(
            self.history_service.saved[0][4],
            7,
        )

    def test_unreadable_image_emits_failed(self):
        service = build_detection_service(
            image_reader=lambda path: None,
        )
        worker = ImageWorker(service, "missing.jpg")

        failures = []
        images = []

        worker.failed.connect(failures.append)
        worker.imageReady.connect(images.append)

        worker.run()

        self.assertEqual(images, [])
        self.assertEqual(len(failures), 1)
        self.assertIn("Không đọc được ảnh", failures[0])

    def test_engine_failure_emits_failed(self):
        engine = FakeAIEngine(
            analysis=make_analysis(
                success=False,
                message="AI loi",
            )
        )
        worker = ImageWorker(
            build_detection_service(engine),
            "any.jpg",
        )

        failures = []
        worker.failed.connect(failures.append)

        worker.run()

        self.assertEqual(failures, ["AI loi"])

    def test_preview_worker_emits_preview(self):
        worker = PreviewLoadWorker(self.service, "any.jpg")

        previews = []
        failures = []

        worker.previewReady.connect(previews.append)
        worker.failed.connect(failures.append)

        worker.run()

        self.assertEqual(failures, [])
        self.assertEqual(len(previews), 1)
        self.assertFalse(previews[0].isNull())


class WebcamWorkerTest(unittest.TestCase):
    def setUp(self):
        ensure_app()
        self.history_service = FakeHistoryService()
        self.engine = FakeAIEngine()
        self.service = build_detection_service(
            self.engine,
            self.history_service,
        )

        self.workers: list[WebcamWorker] = []

    def tearDown(self):
        """Bao dam khong con worker nao song sau moi test."""
        for worker in self.workers:
            worker.stop(3000)

        process_events(20)
        self.workers.clear()

    def _make_worker(
        self,
        camera: FakeCamera,
    ) -> WebcamWorker:
        worker = WebcamWorker(
            self.service,
            camera_id=0,
            user_id=3,
            history_service=self.history_service,
            capture_factory=lambda camera_id: camera,
        )
        self.workers.append(worker)
        return worker

    def test_camera_open_failure_emits_status(self):
        worker = self._make_worker(
            FakeCamera(opened=False)
        )

        statuses = []
        worker.statusChanged.connect(statuses.append)

        worker.run()

        self.assertIn(
            "Không mở được webcam.",
            statuses,
        )

    def test_run_emits_frames_and_results_then_stops(self):
        camera = FakeCamera(frames=1000)
        worker = self._make_worker(camera)

        frames = []
        results = []
        statuses = []

        worker.frameReady.connect(frames.append)
        worker.resultsReady.connect(results.append)
        worker.statusChanged.connect(statuses.append)

        worker.start()

        self.assertTrue(
            wait_for(lambda: len(frames) >= 2),
            "Worker phai emit frame",
        )

        worker.stop(3000)
        process_events(20)

        self.assertTrue(camera.released)
        self.assertGreaterEqual(len(results), 1)
        self.assertIn("Webcam đang hoạt động.", statuses)
        self.assertIn("Webcam đã tắt.", statuses)

    def test_signal_is_delivered_on_gui_thread(self):
        """NHIEM VU 6: Worker Thread -> Signal -> GUI Thread."""
        import threading

        camera = FakeCamera(frames=1000)
        worker = self._make_worker(camera)

        main_thread_id = threading.get_ident()
        receiver_thread_ids = []

        worker.frameReady.connect(
            lambda image: receiver_thread_ids.append(
                threading.get_ident()
            )
        )

        worker.start()
        wait_for(lambda: len(receiver_thread_ids) >= 1)
        worker.stop(3000)

        self.assertTrue(receiver_thread_ids)
        for thread_id in receiver_thread_ids:
            self.assertEqual(
                thread_id,
                main_thread_id,
                "Slot phai chay tren GUI thread",
            )

    def test_stop_before_run_reaches_loop_still_exits(self):
        """Regression: stop() ngay sau start() khong duoc lam worker treo."""
        worker = self._make_worker(
            FakeCamera(frames=1000)
        )

        worker.start()
        worker.request_stop()

        self.assertTrue(
            worker.wait(3000),
            "Worker phai thoat du stop() den truoc khi vao vong lap",
        )

    def test_request_stop_does_not_block(self):
        import time

        camera = FakeCamera(frames=1000)
        worker = self._make_worker(camera)
        worker.start()

        wait_for(lambda: worker.isRunning())

        started_at = time.perf_counter()
        worker.request_stop()
        elapsed = time.perf_counter() - started_at

        self.assertLess(
            elapsed,
            0.05,
            "request_stop() khong duoc chan GUI thread",
        )

        worker.wait(3000)


class HistoryWriterWorkerTest(unittest.TestCase):
    def setUp(self):
        ensure_app()
        self.history_service = FakeHistoryService()

    def test_queue_is_written_through_service(self):
        worker = HistoryWriterWorker(self.history_service)

        saved_signals = []
        worker.historySaved.connect(
            lambda: saved_signals.append(1)
        )

        worker.start()
        worker.enqueue("laptop", "May tinh", "Technology", 0.9, 1)
        worker.request_stop()
        worker.wait(3000)

        self.assertEqual(len(self.history_service.saved), 1)

    def test_queue_full_is_reported(self):
        worker = HistoryWriterWorker(self.history_service)

        accepted = [
            worker.enqueue("w", "v", "c", 0.9, 1)
            for _ in range(30)
        ]

        self.assertTrue(accepted[0])
        self.assertIn(
            False,
            accepted,
            "Hang doi day phai tra ve False thay vi chan thread",
        )


class HistoryWorkerTest(unittest.TestCase):
    def setUp(self):
        ensure_app()

    def test_loaded_rows_are_already_formatted(self):
        import datetime

        rows = [
            {
                "english_word": "laptop",
                "vietnamese_meaning": None,
                "category": None,
                "confidence": 0.9,
                "detected_time": datetime.datetime(
                    2026, 1, 2, 3, 4
                ),
            }
        ]
        service = FakeHistoryService(rows=rows)
        worker = HistoryWorker(service, user_id=1)

        loaded = []
        worker.loaded.connect(loaded.append)

        worker.run()

        self.assertEqual(len(loaded), 1)
        row = loaded[0][0]
        self.assertEqual(row["english"], "laptop")
        self.assertEqual(row["vietnamese"], "laptop")
        self.assertEqual(row["category"], "Unknown")
        self.assertEqual(row["detected_time"], "02/01/2026 03:04")

    def test_clear_first_calls_service(self):
        service = FakeHistoryService(rows=[])
        worker = HistoryWorker(
            service,
            user_id=5,
            clear_first=True,
        )
        worker.run()

        self.assertEqual(service.cleared, [5])

    def test_failure_emits_failed(self):
        service = FakeHistoryService(fail=True)
        worker = HistoryWorker(service, user_id=1)

        failures = []
        worker.failed.connect(failures.append)

        worker.run()

        self.assertEqual(len(failures), 1)


class StatsWorkerTest(unittest.TestCase):
    def setUp(self):
        ensure_app()

    def test_stats_are_computed_from_service(self):
        from ui.services.stats_service import StatsService

        rows = [
            {
                "english_word": "laptop",
                "category": "Technology",
                "confidence": 0.9,
            },
            {
                "english_word": "laptop",
                "category": "Technology",
                "confidence": 0.7,
            },
        ]
        service = StatsService(
            FakeHistoryService(rows=rows)
        )
        worker = StatsWorker(service, user_id=1)

        loaded = []
        worker.loaded.connect(loaded.append)

        worker.run()

        stats = loaded[0]
        self.assertEqual(stats["totalDetections"], 2)
        self.assertEqual(stats["uniqueWords"], 1)
        self.assertEqual(stats["mostCommonWord"], "laptop")
        self.assertAlmostEqual(
            stats["averageConfidence"],
            0.8,
        )

    def test_failure_emits_failed(self):
        from ui.services.stats_service import StatsService

        service = StatsService(
            FakeHistoryService(fail=True)
        )
        worker = StatsWorker(service, user_id=1)

        failures = []
        worker.failed.connect(failures.append)

        worker.run()

        self.assertEqual(len(failures), 1)


class SpeakTaskTest(unittest.TestCase):
    def test_speak_error_does_not_propagate(self):
        def boom(word):
            raise RuntimeError("no audio device")

        task = SpeakTask("laptop", speak_fn=boom)

        task.run()

    def test_speak_is_delegated(self):
        spoken = []
        task = SpeakTask("laptop", speak_fn=spoken.append)

        task.run()

        self.assertEqual(spoken, ["laptop"])


class HistoryRecordPolicyTest(unittest.TestCase):
    """Luat luu lich su da roi khoi Worker, test truc tiep tren Service."""

    def test_low_confidence_is_rejected(self):
        policy = HistoryRecordPolicy(
            min_confidence=0.5,
            cooldown_seconds=5.0,
        )

        self.assertFalse(
            policy.should_record("laptop", 0.4, 100.0)
        )

    def test_cooldown_blocks_repeat(self):
        policy = HistoryRecordPolicy(
            min_confidence=0.5,
            cooldown_seconds=5.0,
        )

        self.assertTrue(
            policy.should_record("laptop", 0.9, 100.0)
        )
        policy.mark_recorded("laptop", 100.0)

        self.assertFalse(
            policy.should_record("laptop", 0.9, 102.0)
        )
        self.assertTrue(
            policy.should_record("laptop", 0.9, 106.0)
        )

    def test_other_word_is_not_blocked(self):
        policy = HistoryRecordPolicy(
            min_confidence=0.5,
            cooldown_seconds=5.0,
        )
        policy.mark_recorded("laptop", 100.0)

        self.assertTrue(
            policy.should_record("mouse", 0.9, 101.0)
        )


if __name__ == "__main__":
    unittest.main()
