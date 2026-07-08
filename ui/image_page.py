from tkinter import filedialog

import customtkinter as ctk
import cv2
from PIL import Image

from detection.image_detect import detect_image
from utils.speech import speak


class ImagePage(ctk.CTkFrame):
    def __init__(self, master, detector):
        super().__init__(master, fg_color="transparent")

        self.detector = detector

        self.image_label = ctk.CTkLabel(
            self, text="Chưa chọn ảnh", width=640, height=400, fg_color=("gray85", "gray20")
        )
        self.image_label.pack(pady=(16, 8))

        ctk.CTkButton(self, text="Chọn ảnh...", command=self.choose_image).pack(pady=4)

        self.results_frame = ctk.CTkScrollableFrame(self, width=640, height=160)
        self.results_frame.pack(pady=12, padx=16, fill="x")

    def choose_image(self):
        path = filedialog.askopenfilename(
            title="Chọn ảnh",
            filetypes=[("Ảnh", "*.jpg *.jpeg *.png *.bmp")],
        )
        if not path:
            return

        image, results = detect_image(path, detector=self.detector, show_window=False)
        if image is None:
            self.image_label.configure(text="Không đọc được ảnh", image=None)
            return

        self._show_image(image)
        self._show_results(results)

    def _show_image(self, cv_image):
        rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb)
        pil_image.thumbnail((640, 400))
        ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=pil_image.size)
        self.image_label.configure(image=ctk_image, text="")
        self.image_label.image = ctk_image

    def _show_results(self, results):
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        if not results:
            ctk.CTkLabel(self.results_frame, text="Không phát hiện vật thể nào.").pack(pady=8)
            return

        for item in results:
            row = ctk.CTkFrame(self.results_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)

            vietnamese = item["vietnamese"] or item["english"]
            text = f"{item['english']} - {vietnamese} [{item['category']}] ({item['confidence']:.2f})"
            ctk.CTkLabel(row, text=text, anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkButton(
                row,
                text="Phát âm",
                width=80,
                command=lambda w=item["english"]: speak(w),
            ).pack(side="right")
