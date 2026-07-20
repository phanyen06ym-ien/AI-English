from pathlib import Path


# =========================================================
# 1. ĐƯỜNG DẪN PROJECT
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ASSETS_DIR = PROJECT_ROOT / "assets"
MODELS_DIR = PROJECT_ROOT / "models"
DATASET_DIR = PROJECT_ROOT / "dataset"


# =========================================================
# 2. CẤU HÌNH YOLO
# =========================================================

# Mô hình YOLO đã fine-tune trên Google Colab
MODEL_PATH = MODELS_DIR / "best.pt"

# Ngưỡng confidence tối thiểu
CONFIDENCE = 0.5

# Kích thước ảnh đầu vào YOLO
IMAGE_SIZE = 640


# =========================================================
# 3. CẤU HÌNH WEBCAM
# =========================================================

CAMERA_ID = 0


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

FONT_PATH = (
    ASSETS_DIR
    / "fonts"
    / "NotoSans-Regular.ttf"
)


# =========================================================
# 6. CẤU HÌNH ÂM THANH
# =========================================================

AUDIO_DIR = ASSETS_DIR / "audio"
AUDIO_FILE = AUDIO_DIR / "speech.mp3"


# =========================================================
# 7. ẢNH KIỂM THỬ
# =========================================================

TEST_IMAGE_PATH = (
    DATASET_DIR
    / "test_images"
    / "test1.jpg"
)