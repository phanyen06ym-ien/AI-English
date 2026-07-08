import customtkinter as ctk

from detection.detector import ObjectDetector
from ui.image_page import ImagePage
from ui.vocabulary_page import VocabularyPage
from ui.webcam_page import WebcamPage

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

PAGES = (
    ("Nhận diện ảnh", ImagePage),
    ("Webcam", WebcamPage),
    ("Từ vựng", VocabularyPage),
)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI-English")
        self.geometry("1000x700")

        sidebar = ctk.CTkFrame(self, width=180, corner_radius=0)
        sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(
            sidebar, text="AI-English", font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(24, 16), padx=16)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(side="left", fill="both", expand=True)

        shared_detector = ObjectDetector()

        self.pages = {}
        for name, page_class in PAGES:
            if page_class is VocabularyPage:
                page = page_class(container)
            else:
                page = page_class(container, detector=shared_detector)
            self.pages[name] = page

            ctk.CTkButton(
                sidebar, text=name, command=lambda n=name: self.show_page(n)
            ).pack(pady=6, padx=16, fill="x")

        self.show_page(PAGES[0][0])

    def show_page(self, name):
        for page in self.pages.values():
            page.pack_forget()
        self.pages[name].pack(fill="both", expand=True, padx=8, pady=8)

    def on_close(self):
        for page in self.pages.values():
            if hasattr(page, "on_close"):
                page.on_close()
        self.destroy()


def run():
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()


if __name__ == "__main__":
    from utils.console import use_utf8_console

    use_utf8_console()
    run()
