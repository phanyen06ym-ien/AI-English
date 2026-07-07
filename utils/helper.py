import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "assets/fonts/NotoSans-Regular.ttf"


def draw_vietnamese_text(image, text, position,
                         color=(0, 255, 0), size=24):
    img_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    draw = ImageDraw.Draw(img_pil)

    font = ImageFont.truetype(FONT_PATH, size)

    draw.text(position, text,
              font=font,
              fill=(color[2], color[1], color[0]))

    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)