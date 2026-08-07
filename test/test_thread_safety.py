"""Sprint 5 - Unit test cho an toan da luong.

Kiem tra:

1. Moi signal tu Worker Thread deu duoc nhan tren GUI Thread.
2. Khong co update GUI nao xay ra tren worker thread.
3. `FrameGate` chan tran hang doi giua worker va GUI (backpressure).
4. Trang thai chia se co khoa, chiu duoc truy cap dong thoi.
5. Khong worker nao bi huy khi con dang chay.
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

from ui.services.detection_service import DetectionService
from ui.services.history_service import HistoryRecordPolicy
from ui.workers.backpressure import (
    DEFAULT_MAX_IN_FLIGHT,
    FrameGate,
)
from ui.workers.lifecycle import ManagedWorker, WorkerState
from ui.workers.webcam_worker import WebcamWorker


MAIN_THREAD_ID = threading.get_ident()


def build_detection_service(
    engine=None,
    history_service=None,
) -> DetectionService:
    return DetectionService(
        engine if engine is not None else FakeAIEngine(),
        history_service=(
            history_service
            if history_service is not None
            else FakeHistoryService()
        ),
        image_reader=lambda path: make_frame(),
    )


class FrameGateTest(unittest.TestCase):
    """NHIEM VU 6 - Backpressure."""

    def test_allows_up_to_limit(self):
        gate = FrameGate(max_in_flight=2)

        self.assertTrue(gate.try_acquire())
        self.assertTrue(gate.try_acquire())
        self.assertFalse(gate.try_acquire())

    def test_release_frees_a_slot(self):
        gate = FrameGate(max_in_flight=1)

        self.assertTrue(gate.try_acquire())
        self.assertFalse(gate.try_acquire())

        gate.release()

        self.assertTrue(gate.try_acquire())

    def test_counts_emitted_and_dropped(self):
        gate = FrameGate(max_in_flight=1)

        gate.try_acquire()
        gate.try_acquire()
        gate.try_acquire()

        stats = gate.stats()

        self.assertEqual(stats["emitted"], 1)
        self.assertEqual(stats["dropped"], 2)
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["drop_percent"], 67)

    def test_release_below_zero_is_ignored(self):
        gate = FrameGate(max_in_flight=1)

        gate.release()
        gate.release()

        self.assertEqual(gate.in_flight, 0)
        self.assertTrue(gate.try_acquire())

    def test_reset_clears_counters(self):
        gate = FrameGate(max_in_flight=1)
        gate.try_acquire()
        gate.try_acquire()

        gate.reset()

        stats = gate.stats()
        self.assertEqual(stats["emitted"], 0)
        self.assertEqual(stats["dropped"], 0)
        self.assertEqual(stats["in_flight"], 0)

    def test_minimum_limit_is_one(self):
        self.assertEqual(FrameGate(0).max_in_flight, 1)
        self.assertEqual(FrameGate(-5).max_in_flight, 1)

    def test_concurrent_access_never_exceeds_limit(self):
        """Nhieu thread cung xin suat: khong bao gio vuot han muc."""
        gate = FrameGate(max_in_flight=4)
        peak = {"value": 0}
        peak_lock = threading.Lock()
        barrier = threading.Barrier(8)

        def worker():
            barrier.wait()

            for _ in range(200):
                if gate.try_acquire():
                    with peak_lock:
                        peak["value"] = max(
                            peak["value"],
                            gate.in_flight,
                        )
                    gate.release()

        threads = [
            threading.Thread(target=worker)
            for _ in range(8)
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertLessEqual(peak["value"], 4)
        self.assertEqual(gate.in_flight, 0)

    def test_emitted_plus_dropped_equals_attempts(self):
        gate = FrameGate(max_in_flight=2)
        attempts = 500

        def worker():
            for _ in range(attempts // 5):
                gate.try_acquire()

        threads = [
            threading.Thread(target=worker)
            for _ in range(5)
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        stats = gate.stats()
        self.assertEqual(
            stats["emitted"] + stats["dropped"],
            attempts,
        )


class WebcamBackpressureTest(unittest.TestCase):
    """Worker phai bo frame khi GUI khong theo kip."""

    def setUp(self):
        ensure_app()
        self.workers = []

    def tearDown(self):
        for worker in self.workers:
            worker.dispose(3000)
        process_events(20)

    def _make_worker(
        self,
        camera,
        max_in_flight=DEFAULT_MAX_IN_FLIGHT,
    ) -> WebcamWorker:
        worker = WebcamWorker(
            build_detection_service(),
            camera_id=0,
            capture_factory=lambda camera_id: camera,
            max_frames_in_flight=max_in_flight,
        )
        self.workers.append(worker)
        return worker

    def test_slow_gui_causes_frames_to_be_dropped(self):
        """GUI khong release -> worker bo frame thay vi lam phinh hang doi."""
        worker = self._make_worker(
            FakeCamera(frames=100000),
            max_in_flight=2,
        )

        received = []
        worker.frameReady.connect(received.append)

        worker.start()

        self.assertTrue(
            wait_for(
                lambda: worker.frame_gate.dropped > 0,
                timeout=5.0,
            )
        )

        worker.dispose(3000)
        process_events(20)

        self.assertLessEqual(
            len(received),
            2,
            "GUI khong release thi khong duoc nhan them frame",
        )
        self.assertGreater(worker.frame_gate.dropped, 0)

    def test_fast_gui_keeps_receiving_frames(self):
        """GUI release deu -> khong bo frame nao dang ke."""
        worker = self._make_worker(
            FakeCamera(frames=100000),
            max_in_flight=2,
        )

        received = []

        def on_frame(image):
            received.append(image)
            worker.release_frame()

        worker.frameReady.connect(on_frame)

        worker.start()

        self.assertTrue(
            wait_for(lambda: len(received) >= 5, timeout=5.0)
        )

        worker.dispose(3000)
        process_events(20)

        self.assertGreaterEqual(len(received), 5)

    def test_gate_never_exceeds_limit_during_real_run(self):
        worker = self._make_worker(
            FakeCamera(frames=100000),
            max_in_flight=2,
        )

        peaks = []

        def on_frame(image):
            peaks.append(worker.frame_gate.in_flight)
            worker.release_frame()

        worker.frameReady.connect(on_frame)

        worker.start()
        wait_for(lambda: len(peaks) >= 5, timeout=5.0)
        worker.dispose(3000)
        process_events(20)

        self.assertTrue(peaks)
        self.assertLessEqual(max(peaks), 2)


class SignalThreadAffinityTest(unittest.TestCase):
    """Signal tu Worker Thread phai chay slot tren GUI Thread."""

    def setUp(self):
        ensure_app()
        self.workers = []

    def tearDown(self):
        for worker in self.workers:
            worker.dispose(3000)
        process_events(20)

    def test_every_webcam_signal_lands_on_gui_thread(self):
        camera = FakeCamera(frames=100000)
        worker = WebcamWorker(
            build_detection_service(),
            camera_id=0,
            capture_factory=lambda camera_id: camera,
        )
        self.workers.append(worker)

        thread_ids: dict[str, set] = {
            "frame": set(),
            "results": set(),
            "status": set(),
            "state": set(),
        }

        def record(key):
            def handler(*arguments):
                thread_ids[key].add(threading.get_ident())
                if key == "frame":
                    worker.release_frame()

            return handler

        worker.frameReady.connect(record("frame"))
        worker.resultsReady.connect(record("results"))
        worker.statusChanged.connect(record("status"))
        worker.stateChanged.connect(record("state"))

        worker.start()

        self.assertTrue(
            wait_for(
                lambda: (
                    thread_ids["frame"]
                    and thread_ids["results"]
                    and thread_ids["status"]
                ),
                timeout=5.0,
            )
        )

        worker.dispose(3000)
        process_events(20)

        for key, ids in thread_ids.items():
            self.assertTrue(ids, f"Khong nhan duoc signal `{key}`")
            self.assertEqual(
                ids,
                {MAIN_THREAD_ID},
                f"Signal `{key}` phai chay tren GUI thread",
            )

    def test_worker_thread_id_differs_from_gui_thread(self):
        """Cong viec nang phai chay o thread khac GUI."""
        observed: dict[str, int] = {}

        class _ProbeWorker(ManagedWorker):
            def __init__(self) -> None:
                super().__init__("probe_worker")

            def execute(self) -> None:
                observed["worker"] = threading.get_ident()

        worker = _ProbeWorker()
        self.workers.append(worker)

        worker.start()
        self.assertTrue(
            wait_for(
                lambda: worker.state is WorkerState.FINISHED
            )
        )

        self.assertIn("worker", observed)
        self.assertNotEqual(
            observed["worker"],
            MAIN_THREAD_ID,
            "execute() phai chay ngoai GUI thread",
        )


class SharedStateTest(unittest.TestCase):
    """Trang thai chia se giua cac thread phai co khoa."""

    def test_worker_state_read_is_thread_safe(self):
        ensure_app()

        class _SpinWorker(ManagedWorker):
            def __init__(self) -> None:
                super().__init__("spin_worker")

            def execute(self) -> None:
                while not self.token.is_cancelled:
                    self.token.wait(0.001)

        worker = _SpinWorker()
        worker.start()

        errors = []

        def reader():
            try:
                for _ in range(500):
                    state = worker.state
                    assert isinstance(state, WorkerState)
            except Exception as error:  # pragma: no cover
                errors.append(error)

        threads = [
            threading.Thread(target=reader)
            for _ in range(4)
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        worker.dispose(3000)

        self.assertEqual(errors, [])

    def test_history_policy_under_concurrent_access(self):
        """Nhieu thread cung ghi cooldown khong duoc lam hong bo dem."""
        policy = HistoryRecordPolicy(
            min_confidence=0.5,
            cooldown_seconds=5.0,
        )
        accepted = []
        accepted_lock = threading.Lock()
        barrier = threading.Barrier(6)

        def worker(index: int):
            barrier.wait()

            for _ in range(50):
                if policy.should_record(
                    f"word{index}",
                    0.9,
                    100.0,
                ):
                    policy.mark_recorded(
                        f"word{index}",
                        100.0,
                    )
                    with accepted_lock:
                        accepted.append(index)

        threads = [
            threading.Thread(target=worker, args=(index,))
            for index in range(6)
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Moi tu chi duoc chap nhan mot lan trong cung mot moc thoi gian.
        self.assertEqual(
            sorted(set(accepted)),
            list(range(6)),
        )


class NoDanglingThreadTest(unittest.TestCase):
    """Khong worker nao duoc bi huy khi con dang chay."""

    def setUp(self):
        ensure_app()

    def test_app_context_shutdown_stops_every_worker(self):
        from ui.app_context import AppContext

        context = AppContext.build(
            ai_engine=FakeAIEngine(),
            file_picker=lambda: "",
            history_service=FakeHistoryService(),
            capture_factory=lambda camera_id: FakeCamera(
                frames=100000
            ),
        )

        context.webcam_view_model.start()
        context.history_view_model.set_user_id(1)
        context.history_view_model.refresh()
        context.statistics_view_model.set_user_id(1)
        context.statistics_view_model.refresh()

        wait_for(lambda: context.webcam_view_model.running)

        before = threading.active_count()

        context.shutdown()
        process_events(20)

        self.assertFalse(context.webcam_view_model.running)

        # Cho cac thread da dung duoc he dieu hanh thu don.
        deadline = time.monotonic() + 3.0
        while (
            threading.active_count() > before
            and time.monotonic() < deadline
        ):
            process_events(5)
            time.sleep(0.01)

        self.assertLessEqual(
            threading.active_count(),
            before,
            "Shutdown phai dung het thread nen",
        )


if __name__ == "__main__":
    unittest.main()
