"""Compatibility shim cho cau hinh.

Cau hinh da chuyen sang package `config/` trong Sprint 6. Module nay duoc giu vi
cac module AI doc hang so ngay luc import va Sprint 6 KHONG duoc sua chung:

    detection/detector.py       -> MODEL_PATH, CONFIDENCE, IMAGE_SIZE
    detection/webcam_detect.py  -> CAMERA_ID
    utils/helper.py             -> FONT_PATH
    utils/speech.py             -> AUDIO_DIR, AUDIO_FILE

Gia tri xuat ra o day lay tu `AppConfig`, nen doi `.env` la doi luon tham so ma
tang AI dang dung — dieu truoc Sprint 6 khong lam duoc.

**Code moi KHONG dung module nay.** Hay nhan `AppConfig` qua constructor.
"""

from __future__ import annotations

import logging

from config import get_default_config
from config.errors import ConfigError
from config.schema import AppConfig


logger = logging.getLogger(__name__)


def _resolve_config() -> AppConfig:
    """Doc cau hinh mac dinh. Cau hinh hong thi quay ve gia tri goc."""
    try:
        return get_default_config()

    except ConfigError as error:
        logger.error(
            "Cau hinh khong hop le, dung gia tri mac dinh: %s",
            error,
        )
        return AppConfig()


_config = _resolve_config()


# =========================================================
# 1. ĐƯỜNG DẪN PROJECT
# =========================================================

PROJECT_ROOT = _config.paths.project_root

ASSETS_DIR = _config.paths.assets_dir
MODELS_DIR = _config.paths.models_dir
DATASET_DIR = _config.paths.dataset_dir


# =========================================================
# 2. CẤU HÌNH YOLO
# =========================================================

# Mô hình YOLO đã fine-tune trên Google Colab
MODEL_PATH = _config.ai.model_path(_config.paths)

# Ngưỡng confidence tối thiểu
CONFIDENCE = _config.ai.confidence

# Kích thước ảnh đầu vào YOLO
IMAGE_SIZE = _config.ai.image_size


# =========================================================
# 3. CẤU HÌNH WEBCAM
# =========================================================

CAMERA_ID = _config.camera.camera_id


# =========================================================
# 4. CẤU HÌNH TỪ VỰNG
# =========================================================

LEVELS = {
    "Easy": "Cơ bản",
    "Medium": "Trung bình",
    "Hard": "Nâng cao",
}

DEFAULT_LANGUAGE = "vi"


# =========================================================
# 5. CẤU HÌNH FONT
# =========================================================

FONT_PATH = _config.paths.font_path


# =========================================================
# 6. CẤU HÌNH ÂM THANH
# =========================================================

AUDIO_DIR = _config.paths.audio_dir
AUDIO_FILE = _config.paths.audio_file


# =========================================================
# 7. ẢNH KIỂM THỬ
# =========================================================

TEST_IMAGE_PATH = _config.paths.test_image_path


__all__ = [
    "PROJECT_ROOT",
    "ASSETS_DIR",
    "MODELS_DIR",
    "DATASET_DIR",
    "MODEL_PATH",
    "CONFIDENCE",
    "IMAGE_SIZE",
    "CAMERA_ID",
    "LEVELS",
    "DEFAULT_LANGUAGE",
    "FONT_PATH",
    "AUDIO_DIR",
    "AUDIO_FILE",
    "TEST_IMAGE_PATH",
]
