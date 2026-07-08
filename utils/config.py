# utils/config.py

# 1. Cấu hình Camera
CAMERA_ID = 0

# 2. Cấu hình Model AI (YOLO)
MODEL_PATH = 'yolov8n.pt'
CONFIDENCE = 0.5

# 3. Cấu hình Cấp độ từ vựng (Dùng cho Naive Bayes)
LEVELS = {
    "A1": "Cơ bản",
    "B2": "Trung cấp",
    "C2": "Nâng cao"
}

# 4. Cấu hình Tệp tin
AUDIO_FILE = "speech.mp3"

# 5. Cấu hình khác (Tùy chọn)
# Thêm các cấu hình khác nếu sau này bạn cần (ví dụ: ngôn ngữ dịch)
DEFAULT_LANG = 'vi'