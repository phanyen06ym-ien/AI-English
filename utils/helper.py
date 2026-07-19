import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


FONT_PATH = "assets/fonts/NotoSans-Regular.ttf"


def open_camera(camera_id):
    """Mở webcam, ưu tiên backend DSHOW vì backend mặc định (MSMF) trên Windows
    hay không mở được camera sau khi cập nhật driver/Windows Update."""
    cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap.release()
        cap = cv2.VideoCapture(camera_id)
    return cap


def xu_ly_all(word):
    # Chỉ import khi thật sự cần dịch/phát âm, tránh webcam phụ thuộc gTTS.
    from utils.speech import phat_am
    from utils.translator import dich_tu

    meaning = dich_tu(word)
    audio_path = phat_am(word)
    return meaning, audio_path


def draw_vietnamese_text(image, text, position, color=(0, 255, 0), size=24):
    """Vẽ tiếng Việt lên ảnh bằng PIL vì cv2.putText không hỗ trợ Unicode tốt."""
    img_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    font = ImageFont.truetype(FONT_PATH, size)

    draw.text(
        position,
        text,
        font=font,
        fill=(color[2], color[1], color[0]),
    )

    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
