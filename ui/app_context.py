"""Composition root cua GUI layer.

Toan bo viec lap rap phu thuoc nam o day, tach khoi `main_qt.run()` de:

- `main_qt` chi con lo bootstrap Qt va nap QML.
- Test co the dung `AppContext.build(ai_engine=fake_engine)` de dung nguyen
  cay doi tuong ma khong can YOLO, khong can database that.

    AIEngine
       |
       +-> DetectionService --+--> ImageViewModel   -> ImageController
       |        ^             |
       |        |             +--> WebcamViewModel  -> WebcamController
       |   HistoryService ----+--> HistoryViewModel -> HistoryController
       |        ^
       |   StatsService ---------> StatisticsViewModel -> StatsController
       |
       +-------------------------> VocabularyViewModel -> VocabularyController

    AuthService --------------> AuthViewModel -> AuthController
"""

from __future__ import annotations

from dataclasses import dataclass

# Sprint 8: KHONG import `ai.*` o cap module.
# `ai/__init__.py` nap san `ObjectDetector` nen bat ky import nao tu `ai.*`
# cung keo theo torch + ultralytics + sklearn (~6,6 giay). Chi can kieu de
# chu thich thi dung TYPE_CHECKING; cho nao dung that su thi import trong ham.
from typing import TYPE_CHECKING

from config import AppConfig, load_config
from database import connection as database_connection
from database.connection import close_pool
from database.repositories.history_repository import HistoryRepository
from database.repositories.user_repository import UserRepository
from ui.auth_controller import AuthController
from ui.history_controller import HistoryController
from ui.image_controller import ImageController
from ui.services.ai_bootstrap import (
    LazyAIEngineParts,
    build_lazy_ai_engine,
)
from ui.services.auth_service import AuthService
from ui.services.detection_service import DetectionService
from ui.services.dialog_service import DialogService
from ui.services.history_service import HistoryService
from ui.services.stats_service import StatsService
from ui.stats_controller import StatsController
from ui.ui_logger import get_ui_logger, log_ui_event
from ui.viewmodels.auth_viewmodel import AuthViewModel
from ui.viewmodels.history_viewmodel import HistoryViewModel
from ui.viewmodels.image_viewmodel import ImageViewModel
from ui.viewmodels.statistics_viewmodel import StatisticsViewModel
from ui.viewmodels.vocabulary_viewmodel import VocabularyViewModel
from ui.viewmodels.webcam_viewmodel import WebcamViewModel
from ui.vocabulary_controller import VocabularyController
from ui.workers.task_pool import wait_for_pool
from ui.workers.warmup_worker import WarmupWorker
from ui.webcam_controller import WebcamController


if TYPE_CHECKING:  # pragma: no cover
    from ai.pipeline import AIEngine


logger = get_ui_logger("app_context")


@dataclass
class AppContext:
    """Giu tham chieu toi moi service, viewmodel va controller."""

    config: AppConfig
    ai_engine: AIEngine

    history_service: HistoryService
    stats_service: StatsService
    detection_service: DetectionService
    auth_service: AuthService
    dialog_service: DialogService

    image_view_model: ImageViewModel
    webcam_view_model: WebcamViewModel
    vocabulary_view_model: VocabularyViewModel
    history_view_model: HistoryViewModel
    statistics_view_model: StatisticsViewModel
    auth_view_model: AuthViewModel

    image_controller: ImageController
    webcam_controller: WebcamController
    vocabulary_controller: VocabularyController
    history_controller: HistoryController
    stats_controller: StatsController
    auth_controller: AuthController

    # --- Field co gia tri mac dinh phai nam CUOI trong dataclass ---

    #: Cac phan AI nap tre (Sprint 8). None khi engine duoc tiem san.
    ai_parts: LazyAIEngineParts | None = None

    #: Worker nap truoc AI (Sprint 8).
    _warmup_worker: WarmupWorker | None = None

    # ------------------------------------------------------------------
    # Lap rap
    # ------------------------------------------------------------------

    @classmethod
    def build(
        cls,
        config: AppConfig | None = None,
        ai_engine: "AIEngine | None" = None,
        camera_id: int | None = None,
        file_picker=None,
        history_service: HistoryService | None = None,
        auth_service: AuthService | None = None,
        history_repository: HistoryRepository | None = None,
        user_repository: UserRepository | None = None,
        capture_factory=None,
    ) -> "AppContext":
        """Tao day du cay phu thuoc cho GUI.

        Moi tham so deu co the inject de test khong can YOLO / camera /
        database that. `config` la nguon su that duy nhat cho moi tham so.
        """
        app_config = (
            config
            if config is not None
            else load_config()
        )

        log_ui_event(
            logger,
            "config_loaded",
            environment=app_config.environment.value,
        )

        # Tiem cau hinh database truoc khi bat ky repository nao duoc dung.
        database_connection.configure(app_config.database)

        # Sprint 8: KHONG nap AI o day. Nap tre de cua so hien ra ngay,
        # `warmup()` se nap that su tren thread nen sau do.
        ai_parts: LazyAIEngineParts | None = None

        if ai_engine is not None:
            engine = ai_engine
        else:
            engine, ai_parts = build_lazy_ai_engine()

        history_service = (
            history_service
            if history_service is not None
            else HistoryService(
                repository=history_repository,
                config=app_config.history,
            )
        )
        stats_service = StatsService(
            history_service,
            config=app_config.history,
        )
        detection_service = DetectionService(
            engine,
            history_service=history_service,
            ui_config=app_config.ui,
        )
        auth_service = (
            auth_service
            if auth_service is not None
            else AuthService(
                repository=user_repository
            )
        )
        dialog_service = DialogService()

        image_view_model = ImageViewModel(detection_service)
        webcam_view_model = WebcamViewModel(
            detection_service,
            camera_id=camera_id,
            capture_factory=capture_factory,
            config=app_config.camera,
        )
        vocabulary_view_model = VocabularyViewModel(
            engine,
            config=app_config.ai,
            # Nap tre: `WarmupWorker` day danh sach vao sau.
            load_on_init=ai_parts is None,
        )
        history_view_model = HistoryViewModel(history_service)
        statistics_view_model = StatisticsViewModel(stats_service)
        auth_view_model = AuthViewModel(auth_service)

        image_controller_kwargs = {}
        if file_picker is not None:
            image_controller_kwargs["file_picker"] = file_picker

        context = cls(
            config=app_config,
            ai_engine=engine,
            ai_parts=ai_parts,
            history_service=history_service,
            stats_service=stats_service,
            detection_service=detection_service,
            auth_service=auth_service,
            dialog_service=dialog_service,
            image_view_model=image_view_model,
            webcam_view_model=webcam_view_model,
            vocabulary_view_model=vocabulary_view_model,
            history_view_model=history_view_model,
            statistics_view_model=statistics_view_model,
            auth_view_model=auth_view_model,
            image_controller=ImageController(
                image_view_model,
                dialog_service=dialog_service,
                **image_controller_kwargs,
            ),
            webcam_controller=WebcamController(
                webcam_view_model,
                dialog_service=dialog_service,
            ),
            vocabulary_controller=VocabularyController(
                vocabulary_view_model
            ),
            history_controller=HistoryController(
                history_view_model,
                dialog_service=dialog_service,
            ),
            stats_controller=StatsController(
                statistics_view_model
            ),
            auth_controller=AuthController(auth_view_model),
        )

        context.wire_session()

        return context

    # ------------------------------------------------------------------
    # Phien dang nhap
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Nap truoc AI (Sprint 8)
    # ------------------------------------------------------------------

    def warmup(self) -> WarmupWorker | None:
        """Nap AI o thread nen. Goi NGAY SAU khi cua so da hien ra.

        Tra ve None neu engine duoc tiem san (test) - luc do khong co gi
        de nap tre.
        """
        if self.ai_parts is None:
            return None

        if self._warmup_worker is not None:
            return self._warmup_worker

        log_ui_event(logger, "ai_warmup_started")

        worker = WarmupWorker(self.ai_parts)
        worker.vocabularyReady.connect(
            self.vocabulary_view_model.setVocabulary
        )
        worker.warmupCompleted.connect(
            lambda: log_ui_event(logger, "ai_warmup_completed")
        )
        worker.failed.connect(
            lambda message: logger.error(
                "Nap truoc AI that bai: %s",
                message,
            )
        )
        worker.start()

        self._warmup_worker = worker

        return worker

    def wire_session(self) -> None:
        """Noi su kien doi nguoi dung toi moi ViewModel."""
        self.auth_controller.userChanged.connect(
            self.apply_current_user
        )

    def apply_current_user(
        self,
        user: dict,
    ) -> None:
        """Cap nhat user_id cho moi ViewModel khi phien dang nhap thay doi."""
        user_id = (
            int(user.get("id"))
            if user and user.get("id")
            else None
        )

        log_ui_event(
            logger,
            "session_changed",
            logged_in=user_id is not None,
        )

        self.image_view_model.set_user_id(user_id)
        self.webcam_view_model.set_user_id(user_id)
        self.history_view_model.set_user_id(user_id)
        self.statistics_view_model.set_user_id(user_id)

        if user_id is not None:
            self.history_view_model.refresh()
            self.statistics_view_model.refresh()
        else:
            self.webcam_view_model.stop()
            self.statistics_view_model.clear()

    # ------------------------------------------------------------------
    # Dang ky cho QML
    # ------------------------------------------------------------------

    def context_properties(self) -> dict[str, object]:
        """Ten context property -> object.

        Nhom `*Controller` la nhung ten QML hien tai dang bind (khong doi).
        Nhom `*ViewModel` va `dialogService` la bo sung cho Sprint sau, QML
        hien tai khong dung nen khong anh huong gi.
        """
        return {
            "vocabController": self.vocabulary_controller,
            "imageController": self.image_controller,
            "webcamController": self.webcam_controller,
            "historyController": self.history_controller,
            "statsController": self.stats_controller,
            "authController": self.auth_controller,
            "imageViewModel": self.image_view_model,
            "webcamViewModel": self.webcam_view_model,
            "vocabViewModel": self.vocabulary_view_model,
            "historyViewModel": self.history_view_model,
            "statsViewModel": self.statistics_view_model,
            "authViewModel": self.auth_view_model,
            "dialogService": self.dialog_service,
        }

    def shutdown(
        self,
        timeout_ms: int | None = None,
    ) -> None:
        """Dung moi worker nen truoc khi thoat ung dung.

        Bat buoc phai cho worker ket thuc, neu khong Qt se abort voi
        "QThread: Destroyed while thread is still running".
        """
        log_ui_event(logger, "app_shutdown")

        timeout = (
            timeout_ms
            if timeout_ms is not None
            else self.config.threads.dispose_timeout_ms
        )

        # 1. Dung moi QThread (Sprint 5: dispose = cancel + wait).
        if self._warmup_worker is not None:
            self._warmup_worker.dispose(timeout)
            self._warmup_worker = None

        self.webcam_view_model.shutdown(timeout)
        self.image_view_model.shutdown(timeout)
        self.history_view_model.shutdown(timeout)
        self.statistics_view_model.shutdown(timeout)
        self.auth_view_model.shutdown(timeout)

        # 2. Cho cac tac vu ngan tren QThreadPool ket thuc (Sprint 5).
        wait_for_pool(timeout)

        # 3. Dong connection pool sau khi moi worker da dung han (Sprint 4).
        close_pool()
