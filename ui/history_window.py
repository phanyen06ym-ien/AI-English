import tkinter as tk
from tkinter import messagebox, ttk


class HistoryWindow(tk.Toplevel):
    """Cửa sổ hiển thị lịch sử nhận dạng từ database."""

    def __init__(self, master=None):
        super().__init__(master)
        self.title("Lịch sử nhận dạng")
        self.geometry("900x500")
        self.resizable(False, False)
        self.configure(bg="#f5fbff")

        self.selected_id = None
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        title = tk.Label(
            self,
            text="Lịch sử nhận dạng",
            bg="#f5fbff",
            fg="#1f5f99",
            font=("Segoe UI", 20, "bold"),
        )
        title.pack(pady=(16, 8))

        columns = ("stt", "time", "english", "vietnamese", "confidence")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=16)
        self.tree.heading("stt", text="STT")
        self.tree.heading("time", text="Time")
        self.tree.heading("english", text="English")
        self.tree.heading("vietnamese", text="Vietnamese")
        self.tree.heading("confidence", text="Confidence")

        self.tree.column("stt", width=60, anchor="center")
        self.tree.column("time", width=220)
        self.tree.column("english", width=180)
        self.tree.column("vietnamese", width=220)
        self.tree.column("confidence", width=120, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        button_frame = tk.Frame(self, bg="#f5fbff")
        button_frame.pack(pady=(0, 16))
        ttk.Button(button_frame, text="Refresh", command=self.refresh).pack(side="left", padx=8)
        ttk.Button(button_frame, text="Delete", command=self.delete_selected).pack(side="left", padx=8)

    def _connect(self):
        from database.db import get_connection

        return get_connection()

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, detected_time, english_word, vietnamese_meaning, confidence "
                "FROM history ORDER BY detected_time DESC LIMIT 100;"
            )
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as exc:
            messagebox.showwarning("Lịch sử", f"Không đọc được lịch sử:\n{exc}")
            return

        for index, row in enumerate(rows, start=1):
            history_id, detected_time, english, vietnamese, confidence = row
            value = f"{confidence:.2f}" if confidence is not None else ""
            self.tree.insert(
                "",
                "end",
                iid=str(history_id),
                values=(index, detected_time, english, vietnamese, value),
            )

    def _on_select(self, _event=None):
        selected = self.tree.selection()
        self.selected_id = selected[0] if selected else None

    def delete_selected(self):
        if not self.selected_id:
            messagebox.showinfo("Lịch sử", "Vui lòng chọn một dòng để xóa.")
            return

        if not messagebox.askyesno("Xóa lịch sử", "Bạn có chắc muốn xóa dòng này?"):
            return

        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute("DELETE FROM history WHERE id = %s;", (self.selected_id,))
            conn.commit()
            cur.close()
            conn.close()
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Lịch sử", f"Không xóa được lịch sử:\n{exc}")
