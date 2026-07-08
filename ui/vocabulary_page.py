import customtkinter as ctk

from dataset.vocabulary import all_words
from utils.speech import speak


class VocabularyPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._render())
        ctk.CTkEntry(
            self,
            placeholder_text="Tìm từ (tiếng Anh hoặc tiếng Việt)...",
            textvariable=self.search_var,
        ).pack(fill="x", padx=16, pady=(16, 8))

        self.list_frame = ctk.CTkScrollableFrame(self, width=640, height=460)
        self.list_frame.pack(fill="both", expand=True, padx=16, pady=8)

        self._render()

    def _render(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        query = self.search_var.get().strip().lower()

        for english, row in all_words().items():
            if query and query not in english.lower() and query not in row["vietnamese"].lower():
                continue

            item = ctk.CTkFrame(self.list_frame)
            item.pack(fill="x", pady=4)

            text = f"{english} - {row['vietnamese']} | {row['category']} | {row['level']}"
            ctk.CTkLabel(item, text=text, anchor="w").pack(side="left", fill="x", expand=True, padx=8)
            ctk.CTkButton(
                item,
                text="Phát âm",
                width=80,
                command=lambda w=english: speak(w),
            ).pack(side="right", padx=8, pady=6)

        if not self.list_frame.winfo_children():
            ctk.CTkLabel(self.list_frame, text="Không tìm thấy từ nào.").pack(pady=8)
