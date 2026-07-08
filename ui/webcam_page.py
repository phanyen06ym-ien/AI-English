import customtkinter as ctk
import cv2
from PIL import Image

from detection.classify import classify_word
from utils.config import CAMERA_ID
from utils.helper import draw_vietnamese_text


class WebcamPage(ctk.CTkFrame):
    def __init__(self, master, detector):
        super().__init__(master, fg_color="transparent")

        self.detector = detector
        self.cap = None
        self.running = False

        self.video_label = ctk.CTkLabel(
            self, text="Webcam chưa bật", width=640, height=400, fg_color=("gray85", "gray20")
        )
        self.video_label.pack(pady=(16, 8))

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(pady=4)
        ctk.CTkButton(button_row, text="Bật webcam", command=self.start).pack(side="left", padx=6)
        ctk.CTkButton(button_row, text="Tắt webcam", command=self.stop).pack(side="left", padx=6)

    def start(self):
        if self.running:
            return

        self.cap = cv2.VideoCapture(CAMERA_ID)
        if not self.cap.isOpened():
            self.video_label.configure(text="Không mở được webcam", image=None)
            self.cap = None
            return

        self.running = True
        self._update_frame()

    def stop(self):
        self.running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.video_label.configure(text="Webcam đã tắt", image=None)

    def _update_frame(self):
        if not self.running or self.cap is None:
            return

        ret, frame = self.cap.read()
        if ret:
            objects = self.detector.detect(frame)

            for obj in objects:
                class_name = obj["class_name"]
                info = classify_word(class_name)
                vietnamese = info["vietnamese"] or class_name
                x1, y1, x2, y2 = obj["box"]
                label = f"{class_name} - {vietnamese} [{info['category']}]"

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                frame = draw_vietnamese_text(
                    frame,
                    label,
                    (x1, max(y1 - 35, 5)),
                    color=(0, 255, 0),
                    size=24,
                )

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb)
            pil_image.thumbnail((640, 400))
            ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=pil_image.size)
            self.video_label.configure(image=ctk_image, text="")
            self.video_label.image = ctk_image

        self.after(30, self._update_frame)

    def on_close(self):
        self.stop()
