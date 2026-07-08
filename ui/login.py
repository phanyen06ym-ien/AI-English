import tkinter as tk
from tkinter import messagebox, ttk

from database.auth import login_user
from ui.main_window import MainWindow


class LoginWindow:
    """Cửa sổ đăng nhập đơn giản cho ứng dụng."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI English - Login")
        self.root.geometry("1200x700")
        self.root.resizable(False, False)
        self.root.configure(bg="#f5fbff")

        self._build_style()
        self._build_ui()

    def _build_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Card.TFrame", background="white", relief="flat")
        style.configure("Title.TLabel", background="white", foreground="#1f5f99", font=("Segoe UI", 28, "bold"))
        style.configure("Logo.TLabel", background="white", foreground="#2b8bd8", font=("Segoe UI", 22, "bold"))
        style.configure("Text.TLabel", background="white", foreground="#2b2b2b", font=("Segoe UI", 11))
        style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), padding=10)
        style.configure("Exit.TButton", font=("Segoe UI", 11), padding=10)

    def _build_ui(self):
        wrapper = tk.Frame(self.root, bg="#f5fbff")
        wrapper.pack(fill="both", expand=True)

        card = ttk.Frame(wrapper, style="Card.TFrame", padding=40)
        card.place(relx=0.5, rely=0.5, anchor="center", width=430, height=430)

        ttk.Label(card, text="AI English", style="Logo.TLabel").pack(pady=(5, 16))
        ttk.Label(card, text="AI English Learning", style="Title.TLabel").pack(pady=(0, 28))

        ttk.Label(card, text="Username", style="Text.TLabel").pack(anchor="w")
        self.username_entry = ttk.Entry(card, font=("Segoe UI", 12))
        self.username_entry.pack(fill="x", pady=(6, 16), ipady=6)

        ttk.Label(card, text="Password", style="Text.TLabel").pack(anchor="w")
        self.password_entry = ttk.Entry(card, show="*", font=("Segoe UI", 12))
        self.password_entry.pack(fill="x", pady=(6, 26), ipady=6)

        ttk.Button(card, text="Đăng nhập", style="Primary.TButton", command=self.login).pack(fill="x", pady=(0, 10))
        ttk.Button(card, text="Thoát", style="Exit.TButton", command=self.root.destroy).pack(fill="x")

        self.username_entry.focus_set()
        self.root.bind("<Return>", lambda _event: self.login())

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        try:
            user = login_user(username, password)
        except Exception as exc:
            print("Lỗi đăng nhập:", exc)
            messagebox.showerror("Lỗi database", f"Không kết nối hoặc truy vấn được database:\n{exc}")
            return

        if user:
            self.root.destroy()
            MainWindow(
                user_id=user["id"],
                username=user["username"],
                fullname=user["fullname"],
            ).run()
            return

        messagebox.showerror("Đăng nhập thất bại", "Sai username hoặc password")

    def run(self):
        self.root.mainloop()
