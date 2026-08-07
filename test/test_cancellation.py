"""Sprint 5 - Unit test cho co che huy va vong doi worker.

Kiem tra:

1. `CancellationToken` an toan da luong, danh thuc thread dang ngu.
2. `ManagedWorker` luon ket thuc o dung mot trang thai: finished/cancelled/failed.
3. Moi worker deu huy duoc, ke ca khi dang chay giua chung.
4. `dispose()` khong bao gio de QThread bi huy khi con chay.
5. Huy khong duoc lam mat du lieu da xep hang.
"""

from __future__ import annotations

import threading
import time
import unittest

from test.ui_fakes import (
    FakeAIEngine,
    FakeCamera,
    FakeHistoryService,
    ensure_app,
    make_frame,
    process_events,
    wait_for,
)

from PySide6.QtCore import Signal

from ui.services.detection_service import DetectionService
from ui.workers.cancellation import (
    NEVER_CANCELLED,
    CancellationToken,
    OperationCancelledError,
)
from ui.workers.history_worker import HistoryWorker
from ui.workers.image_worker import ImageWorker, PreviewLoadWorker
from ui.workers.lifecycle import ManagedWorker, WorkerState
from ui.workers.speech_worker import SpeakTask
from ui.workers.task_pool import PooledTask
from ui.workers.webcam_worker import HistoryWriterWorker, WebcamWorker


def build_detection_service(
    engine=None,
    history_service=None,
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


class CancellationTokenTest(unittest.TestCase):
    def test_starts_uncancelled(self):
        token = CancellationToken()

        self.assertFalse(token.is_cancelled)

    def test_cancel_sets_flag(self):
        token = CancellationToken()
        token.cancel()

        self.assertTrue(token.is_cancelled)

    def test_reset_clears_flag(self):
        token = CancellationToken()
        token.cancel()
        token.reset()

        self.assertFalse(token.is_cancelled)

    def test_raise_if_cancelled(self):
        token = CancellationToken()

        token.raise_if_cancelled()

        token.cancel()

        with self.assertRaises(OperationCancelledError):
            token.raise_if_cancelled()

    def test_wait_returns_false_on_timeout(self):
        token = CancellationToken()

        started_at = time.perf_counter()
        cancelled = token.wait(0.05)
        elapsed = time.perf_counter() - started_at

        self.assertFalse(cancelled)
        self.assertGreaterEqual(elapsed, 0.04)

    def test_wait_wakes_up_immediately_on_cancel(self):
        """Thread dang ngu phai phan hoi lenh huy ngay, khong cho het gio."""
        token = CancellationToken()

        def cancel_soon():
            time.sleep(0.02)
            token.cancel()

        threading.Thread(
            target=cancel_soon,
            daemon=True,
        ).start()

        started_at = time.perf_counter()
        cancelled = token.wait(5.0)
        elapsed = time.perf_counter() - started_at

        self.assertTrue(cancelled)
        self.assertLess(
            elapsed,
            1.0,
            "wait() phai tinh day ngay khi bi huy",
        )

    def test_cancel_from_many_threads_is_safe(self):
        token = CancellationToken()

        threads = [
            threading.Thread(target=token.cancel)
            for _ in range(20)
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertTrue(token.is_cancelled)

    def test_never_cancelled_token_stays_uncancelled(self):
        NEVER_CANCELLED.cancel()

        self.assertFalse(NEVER_CANCELLED.is_cancelled)


class WorkerStateTest(unittest.TestCase):
    def test_active_and_terminal(self):
        self.assertTrue(WorkerState.RUNNING.is_active())
        self.assertFalse(WorkerState.CREATED.is_active())

        for state in (
            WorkerState.FINISHED,
            WorkerState.CANCELLED,
            WorkerState.FAILED,
            WorkerState.DISPOSED,
        ):
            self.assertTrue(state.is_terminal())

        self.assertFalse(WorkerState.CREATED.is_terminal())
        self.assertFalse(WorkerState.RUNNING.is_terminal())


class _CountingWorker(ManagedWorker):
    """Worker demo: dem den `total`, kiem tra co huy sau moi buoc."""

    progressed = Signal(int)

    def __init__(
        self,
        total: int = 50,
        step_seconds: float = 0.005,
    ) -> None:
        super().__init__("counting_worker")

        self.total = total
        self.step_seconds = step_seconds
        self.completed_steps = 0

    def execute(self) -> None:
        for step in range(self.total):
            self.token.raise_if_cancelled()

            if self.token.wait(self.step_seconds):
                self.token.raise_if_cancelled()

            self.completed_steps = step + 1
            self.progressed.emit(self.completed_steps)


class _FailingWorker(ManagedWorker):
    def __init__(self) -> None:
        super().__init__("failing_worker")

    def execute(self) -> None:
        raise RuntimeError("hong roi")


class ManagedWorkerLifecycleTest(unittest.TestCase):
    def setUp(self):
        ensure_app()
        self.workers: list[ManagedWorker] = []

    def tearDown(self):
        for worker in self.workers:
            worker.dispose(3000)
        process_events(10)

    def _track(self, worker):
        self.workers.append(worker)
        return worker

    def test_initial_state_is_created(self):
        worker = self._track(_CountingWorker(total=1))

        self.assertIs(worker.state, WorkerState.CREATED)

    def test_successful_run_ends_in_finished(self):
        worker = self._track(
            _CountingWorker(total=3, step_seconds=0.001)
        )

        states = []
        worker.stateChanged.connect(states.append)

        worker.start()

        self.assertTrue(
            wait_for(
                lambda: worker.state is WorkerState.FINISHED
            )
        )
        self.assertEqual(worker.completed_steps, 3)
        self.assertIn("running", states)
        self.assertIn("finished", states)

    def test_failure_ends_in_failed_and_emits(self):
        worker = self._track(_FailingWorker())

        failures = []
        worker.failed.connect(failures.append)

        worker.start()

        self.assertTrue(
            wait_for(
                lambda: worker.state is WorkerState.FAILED
            )
        )
        self.assertEqual(failures, ["hong roi"])

    def test_cancel_mid_run_ends_in_cancelled(self):
        worker = self._track(
            _CountingWorker(total=10000, step_seconds=0.002)
        )

        cancelled_signals = []
        worker.cancelled.connect(
            lambda: cancelled_signals.append(1)
        )

        worker.start()
        wait_for(lambda: worker.completed_steps >= 1)

        worker.cancel()

        self.assertTrue(
            wait_for(
                lambda: worker.state is WorkerState.CANCELLED
            )
        )
        self.assertEqual(cancelled_signals, [1])
        self.assertLess(
            worker.completed_steps,
            10000,
            "Worker phai dung giua chung",
        )

    def test_cancel_before_start_skips_execute(self):
        worker = self._track(
            _CountingWorker(total=10, step_seconds=0.001)
        )

        worker.cancel()
        worker.start()

        self.assertTrue(
            wait_for(
                lambda: worker.state is WorkerState.CANCELLED
            )
        )
        self.assertEqual(worker.completed_steps, 0)

    def test_cancel_does_not_block_caller(self):
        worker = self._track(
            _CountingWorker(total=10000, step_seconds=0.002)
        )
        worker.start()
        wait_for(lambda: worker.isRunning())

        started_at = time.perf_counter()
        worker.cancel()
        elapsed = time.perf_counter() - started_at

        self.assertLess(
            elapsed,
            0.05,
            "cancel() khong duoc chan GUI thread",
        )

    def test_dispose_stops_and_marks_disposed(self):
        worker = _CountingWorker(
            total=10000,
            step_seconds=0.002,
        )
        worker.start()
        wait_for(lambda: worker.isRunning())

        self.assertTrue(worker.dispose(3000))
        self.assertFalse(worker.isRunning())
        self.assertIs(worker.state, WorkerState.DISPOSED)

    def test_dispose_is_idempotent(self):
        worker = _CountingWorker(total=2, step_seconds=0.001)
        worker.start()

        self.assertTrue(worker.dispose(3000))
        self.assertTrue(worker.dispose(3000))

    def test_dispose_on_never_started_worker(self):
        worker = _CountingWorker(total=2)

        self.assertTrue(worker.dispose(1000))


class RealWorkerCancellationTest(unittest.TestCase):
    """Moi worker that cua ung dung deu phai huy duoc."""

    def setUp(self):
        ensure_app()
        self.workers = []

    def tearDown(self):
        for worker in self.workers:
            worker.dispose(3000)
        process_events(10)

    def _track(self, worker):
        self.workers.append(worker)
        return worker

    def test_image_worker_cancel_before_start(self):
        engine = FakeAIEngine()
        worker = self._track(
            ImageWorker(
                build_detection_service(engine),
                "photo.jpg",
            )
        )

        worker.cancel()
        worker.start()

        self.assertTrue(
            wait_for(
                lambda: worker.state is WorkerState.CANCELLED
            )
        )
        self.assertEqual(
            engine.analyze_calls,
            0,
            "Huy truoc khi chay thi khong duoc goi AI",
        )

    def test_image_worker_stops_at_progress_checkpoint(self):
        """Huy giua pipeline: `_report_progress` la diem kiem tra."""

        class SlowEngine(FakeAIEngine):
            def analyze_frame(self, frame, include_learning=True):
                time.sleep(0.3)
                return super().analyze_frame(
                    frame,
                    include_learning,
                )

        engine = SlowEngine()
        worker = self._track(
            ImageWorker(
                build_detection_service(engine),
                "photo.jpg",
            )
        )

        progress = []
        analyses = []

        worker.progressChanged.connect(progress.append)
        worker.analysisReady.connect(analyses.append)

        worker.start()

        # Cho toi khi worker da vao giua pipeline (dang chay AI).
        self.assertTrue(
            wait_for(lambda: 25 in progress)
        )

        worker.cancel()

        self.assertTrue(
            wait_for(
                lambda: worker.state is WorkerState.CANCELLED,
                timeout=5.0,
            )
        )

        self.assertEqual(engine.analyze_calls, 1)
        self.assertNotIn(
            100,
            progress,
            "Pipeline phai dung o moc kiem tra, khong chay het",
        )
        self.assertEqual(
            analyses,
            [],
            "Ket qua cua tac vu bi huy khong duoc phat ra",
        )

    def test_preview_worker_cancel_before_start(self):
        worker = self._track(
            PreviewLoadWorker(
                build_detection_service(),
                "photo.jpg",
            )
        )

        previews = []
        worker.previewReady.connect(previews.append)

        worker.cancel()
        worker.start()

        self.assertTrue(
            wait_for(
                lambda: worker.state is WorkerState.CANCELLED
            )
        )
        self.assertEqual(previews, [])

    def test_history_worker_cancel_before_start(self):
        service = FakeHistoryService(rows=[])
        worker = self._track(
            HistoryWorker(service, user_id=1)
        )

        loaded = []
        worker.loaded.connect(loaded.append)

        worker.cancel()
        worker.start()

        self.assertTrue(
            wait_for(
                lambda: worker.state is WorkerState.CANCELLED
            )
        )
        self.assertEqual(loaded, [])

    def test_webcam_worker_cancel_stops_loop(self):
        camera = FakeCamera(frames=100000)
        worker = self._track(
            WebcamWorker(
                build_detection_service(),
                camera_id=0,
                capture_factory=lambda camera_id: camera,
            )
        )

        statuses = []
        worker.statusChanged.connect(statuses.append)

        worker.start()

        # Cho toi khi camera da mo that su, roi moi huy.
        self.assertTrue(
            wait_for(
                lambda: "Webcam đang hoạt động." in statuses
            )
        )

        worker.cancel()

        self.assertTrue(
            wait_for(
                lambda: worker.state is WorkerState.CANCELLED,
                timeout=5.0,
            )
        )
        self.assertTrue(camera.released)

    def test_webcam_worker_cancel_before_start_never_opens_camera(self):
        camera = FakeCamera(frames=100)
        worker = self._track(
            WebcamWorker(
                build_detection_service(),
                camera_id=0,
                capture_factory=lambda camera_id: camera,
            )
        )

        worker.cancel()
        worker.start()

        self.assertTrue(
            wait_for(
                lambda: worker.state is WorkerState.CANCELLED
            )
        )
        self.assertFalse(
            camera.released,
            "Camera khong duoc mo neu da huy truoc khi chay",
        )

    def test_history_writer_drains_queue_on_cancel(self):
        """Huy KHONG duoc lam mat ban ghi da xep hang."""
        service = FakeHistoryService()
        worker = HistoryWriterWorker(service)
        self.workers.append(worker)

        for index in range(5):
            worker.enqueue(
                f"word{index}",
                "nghia",
                "Technology",
                0.9,
                1,
            )

        worker.cancel()
        worker.start()
        worker.wait(3000)

        self.assertEqual(
            len(service.saved),
            5,
            "Phai ghi not hang doi truoc khi tat",
        )


class PooledTaskCancellationTest(unittest.TestCase):
    def test_cancelled_task_does_not_execute(self):
        spoken = []
        task = SpeakTask("laptop", speak_fn=spoken.append)

        task.cancel()
        task.run()

        self.assertEqual(spoken, [])

    def test_task_runs_when_not_cancelled(self):
        spoken = []
        task = SpeakTask("laptop", speak_fn=spoken.append)

        task.run()

        self.assertEqual(spoken, ["laptop"])

    def test_task_error_is_contained(self):
        def boom(word):
            raise RuntimeError("no audio device")

        task = SpeakTask("laptop", speak_fn=boom)

        task.run()

    def test_pooled_task_requires_execute(self):
        task = PooledTask("bare_task")

        # `run()` nuot loi -> khong duoc lam sap thread pool.
        task.run()


class ViewModelCancellationTest(unittest.TestCase):
    """Nguoi dung phai huy duoc viec dang chay tu GUI."""

    def setUp(self):
        ensure_app()

        from ui.viewmodels.image_viewmodel import ImageViewModel

        self.engine = FakeAIEngine()
        self.vm = ImageViewModel(
            build_detection_service(self.engine)
        )

    def tearDown(self):
        self.vm.shutdown()
        process_events(10)

    def test_cancel_when_idle_does_nothing(self):
        statuses = []
        self.vm.StatusMessageChanged.connect(statuses.append)

        self.vm.cancel()

        self.assertEqual(statuses, [])

    def test_cancel_returns_view_model_to_idle(self):
        from ui.state import UiState

        self.vm.selectImage("photo.jpg")
        self.vm.cancel()

        self.assertTrue(
            wait_for(
                lambda: self.vm.state == UiState.IDLE.value
            )
        )


if __name__ == "__main__":
    unittest.main()
