from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from utils.config import FONT_PATH


def get_font(
    size: int = 24,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """
    Tải font Unicode để hiển thị tiếng Việt.

    Nếu không tìm thấy font trong project,
    chương trình sử dụng font mặc định.
    """
    font_path = Path(FONT_PATH)

    if font_path.exists():
        try:
            return ImageFont.truetype(
                str(font_path),
                size,
            )
        except OSError as error:
            print(
                f"Không thể tải font {font_path}: {error}"
            )

    print(
        "Không tìm thấy NotoSans-Regular.ttf. "
        "Đang sử dụng font mặc định."
    )

    return ImageFont.load_default()


def draw_vietnamese_text(
    image: np.ndarray,
    text: str,
    position: tuple[int, int],
    color: tuple[int, int, int] = (0, 255, 0),
    size: int = 24,
) -> np.ndarray:
    """
    Vẽ chữ tiếng Việt lên ảnh OpenCV.

    OpenCV sử dụng BGR.
    PIL sử dụng RGB.
    """
    if image is None:
        raise ValueError(
            "Ảnh đầu vào không được là None."
        )

    if not text:
        return image

    rgb_image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB,
    )

    pil_image = Image.fromarray(rgb_image)

    draw = ImageDraw.Draw(pil_image)

    font = get_font(size)

    blue, green, red = color

    rgb_color = (
        red,
        green,
        blue,
    )

    x, y = position

    draw.text(
        (
            max(0, x),
            max(0, y),
        ),
        text,
        font=font,
        fill=rgb_color,
    )

    result_image = np.array(pil_image)

    return cv2.cvtColor(
        result_image,
        cv2.COLOR_RGB2BGR,
    )


def resize_image(
    image: np.ndarray,
    max_width: int = 1280,
    max_height: int = 720,
) -> np.ndarray:
    """
    Thu nhỏ ảnh và giữ nguyên tỷ lệ.

    Ảnh nhỏ hơn kích thước giới hạn sẽ được giữ nguyên.
    """
    if image is None:
        raise ValueError(
            "Ảnh đầu vào không được là None."
        )

    height, width = image.shape[:2]

    scale = min(
        max_width / width,
        max_height / height,
        1.0,
    )

    if scale == 1.0:
        return image

    new_width = int(width * scale)
    new_height = int(height * scale)

    return cv2.resize(
        image,
        (
            new_width,
            new_height,
        ),
        interpolation=cv2.INTER_AREA,
    )


def xu_ly_all(
    word: str,
) -> tuple[str, str]:
    """
    Dịch từ và tạo file phát âm.

    Hàm này được giữ lại để tương thích
    với giao diện cũ của project.
    """
    from utils.speech import phat_am
    from utils.translator import dich_tu

    meaning = dich_tu(word)
    audio_path = phat_am(word)

    return meaning, audio_path