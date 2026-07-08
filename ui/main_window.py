import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
from PIL import Image, ImageTk

from database.history import save_history
from detection.classify import classify_word
from detection.detector import ObjectDetector
from detection.image_detect import detect_image
from ml.bayes import predict_word_level
from ml.kmeans import get_cluster_by_word
from ml.knn import get_related_words
from ui.history_window import HistoryWindow
from utils.config import CAMERA_ID
from utils.speech import speak


class MainWindow:
    """Cửa sổ chính của ứng dụng AI English."""

    def __init__(self, username="admin", user_id=None, fullname=None):
        self.root = tk.Tk()
        self.root.title("AI English Learning")
        self.root.geometry("1200x700")
        self.root.resizable(False, False)
        self.root.configure(bg="#f5fbff")

        self.username = username
        self.user_id = user_id
        self.fullname = fullname or username
        self.detector = None
        self.cap = None
        self.webcam_running = False
        self.current_result = None
        self.current_image = None

        self._build_style()
        self._build_ui()
        self.show_home()

    def _build_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Menu.TButton", font=("Segoe UI", 11), padding=10)
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=8)
        style.configure("Info.TLabel", background="white", foreground="#1f2933", font=("Segoe UI", 10))
        style.configure("Header.TLabel", background="#f5fbff", foreground="#1f5f99", font=("Segoe UI", 18, "bold"))

    def _build_ui(self):
        self.left_menu = tk.Frame(self.root, bg="#d9efff", width=190)
        self.left_menu.pack(side="left", fill="y")
        self.left_menu.pack_propagate(False)

        tk.Label(
            self.left_menu,
            text="AI English",
            bg="#d9efff",
            fg="#145f9f",
            font=("Segoe UI", 18, "bold"),
        ).pack(pady=(24, 18))

        menu_items = [
            ("🏠 Trang chủ", self.show_home),
            ("📷 Nhận diện ảnh", self.choose_image),
            ("🎥 Webcam", self.start_webcam),
            ("📚 Lịch sử", self.open_history),
            ("📊 Machine Learning", self.show_machine_learning),
            ("👤 Thông tin", self.show_about),
            ("🚪 Đăng xuất", self.logout),
        ]
        for text, command in menu_items:
            ttk.Button(self.left_menu, text=text, style="Menu.TButton", command=command).pack(
                fill="x", padx=14, pady=5
            )

        self.center = tk.Frame(self.root, bg="#f5fbff", width=680)
        self.center.pack(side="left", fill="both", expand=True)

        self.right_panel = tk.Frame(self.root, bg="white", width=300, highlightbackground="#b8dcf5", highlightthickness=1)
        self.right_panel.pack(side="right", fill="y")
        self.right_panel.pack_propagate(False)

        ttk.Label(self.center, text="AI English Learning", style="Header.TLabel").pack(pady=(16, 8))

        self.display_frame = tk.Frame(self.center, bg="white", width=640, height=480, highlightbackground="#b8dcf5", highlightthickness=2)
        self.display_frame.pack(pady=8)
        self.display_frame.pack_propagate(False)

        self.image_label = tk.Label(self.display_frame, text="Khung hiển thị ảnh / webcam", bg="white", fg="#6b7280")
        self.image_label.pack(fill="both", expand=True)

        self.bottom_buttons = tk.Frame(self.center, bg="#f5fbff")
        self.bottom_buttons.pack(pady=10)
        actions = [
            ("Mở Webcam", self.start_webcam),
            ("Chọn ảnh", self.choose_image),
            ("Phát âm", self.play_sound),
            ("Lưu lịch sử", self.save_current_history),
            ("Thoát", self.close),
        ]
        for text, command in actions:
            ttk.Button(self.bottom_buttons, text=text, style="Action.TButton", command=command).pack(side="left", padx=6)

        self.content_box = tk.Frame(self.center, bg="#f5fbff")
        self.content_box.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self._build_info_panel()

    def _build_info_panel(self):
        tk.Label(
            self.right_panel,
            text="Thông tin nhận dạng",
            bg="white",
            fg="#145f9f",
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=(20, 12))

        self.info_vars = {}
        fields = [
            ("english", "English"),
            ("vietnamese", "Vietnamese"),
            ("confidence", "Confidence"),
            ("level", "Vocabulary Level"),
            ("category", "Category"),
            ("cluster", "Cluster"),
            ("related", "Related Words"),
        ]
        for key, label in fields:
            tk.Label(self.right_panel, text=f"{label}:", bg="white", fg="#334155", font=("Segoe UI", 10, "bold")).pack(
                anchor="w", padx=18, pady=(8, 0)
            )
            var = tk.StringVar(value="Chưa có dữ liệu")
            self.info_vars[key] = var
            tk.Label(
                self.right_panel,
                textvariable=var,
                bg="white",
                fg="#111827",
                wraplength=250,
                justify="left",
                font=("Segoe UI", 10),
            ).pack(anchor="w", padx=18)

    def _get_detector(self):
        if self.detector is None:
            self.detector = ObjectDetector()
        return self.detector

    def _clear_content(self):
        for widget in self.content_box.winfo_children():
            widget.destroy()

    def show_home(self):
        self._clear_content()
        tk.Label(
            self.content_box,
            text="Chào mừng bạn đến với hệ thống nhận dạng vật thể hỗ trợ học tiếng Anh.",
            bg="#f5fbff",
            fg="#334155",
            font=("Segoe UI", 12),
        ).pack(anchor="w", pady=10)

    def show_about(self):
        self._clear_content()
        text = (
            f"Người dùng: {self.fullname} ({self.username})\n"
            "Project: Hệ thống nhận dạng vật thể hỗ trợ học tiếng Anh\n"
            "Thuật toán: YOLOv8, Naive Bayes, K-Means, k-NN"
        )
        tk.Label(self.content_box, text=text, bg="#f5fbff", fg="#334155", justify="left", font=("Segoe UI", 12)).pack(
            anchor="w", pady=10
        )

    def show_machine_learning(self):
        self._clear_content()
        tk.Label(self.content_box, text="Machine Learning", bg="#f5fbff", fg="#145f9f", font=("Segoe UI", 15, "bold")).pack(
            anchor="w", pady=(8, 10)
        )

        self._add_ml_section("Naive Bayes", self._safe_bayes_demo())
        self._add_ml_section("K-Means", self._safe_kmeans_demo())
        self._add_ml_section("k-NN", self._safe_knn_demo())

    def _add_ml_section(self, title, lines):
        frame = tk.LabelFrame(self.content_box, text=title, bg="#f5fbff", fg="#145f9f", padx=10, pady=8)
        frame.pack(fill="x", pady=5)
        for line in lines:
            tk.Label(frame, text=line, bg="#f5fbff", fg="#334155", anchor="w").pack(fill="x")

    def _safe_bayes_demo(self):
        try:
            return [f"Easy: book -> {predict_word_level('book')}", f"Medium: keyboard -> {predict_word_level('keyboard')}", "Hard: Chưa có dữ liệu"]
        except Exception:
            return ["Chưa có dữ liệu"]

    def _safe_kmeans_demo(self):
        try:
            cluster = get_cluster_by_word("laptop")
            return [f"Tên cụm: Cluster {cluster}", "Danh sách từ trong cụm hiển thị ở phần thông tin khi nhận diện."]
        except Exception:
            return ["Chưa có dữ liệu"]

    def _safe_knn_demo(self):
        try:
            words = [item["english"] for item in get_related_words("laptop", n=3)]
            return ["Laptop", "↓", *words]
        except Exception:
            return ["Chưa có dữ liệu"]

    def choose_image(self):
        self.stop_webcam()
        path = filedialog.askopenfilename(
            title="Chọn ảnh",
            filetypes=[("Ảnh", "*.jpg *.jpeg *.png *.bmp")],
        )
        if not path:
            return

        try:
            image, results = detect_image(path, detector=self._get_detector(), show_window=False)
        except TypeError:
            # Tương thích nếu image_detect.py cũ chỉ nhận image_path.
            output = detect_image(path)
            image, results = output if isinstance(output, tuple) else (None, [])
        except Exception as exc:
            messagebox.showerror("Nhận diện ảnh", f"Không nhận diện được ảnh:\n{exc}")
            return

        if image is None:
            messagebox.showwarning("Nhận diện ảnh", "Không đọc được ảnh.")
            return

        self._show_cv_image(image)
        self._handle_results(results)

    def start_webcam(self):
        if self.webcam_running:
            return

        try:
            self.cap = cv2.VideoCapture(CAMERA_ID)
            if not self.cap.isOpened():
                messagebox.showerror("Webcam", "Không mở được webcam.")
                self.cap = None
                return
            self._get_detector()
        except Exception as exc:
            messagebox.showerror("Webcam", f"Không khởi động được webcam:\n{exc}")
            return

        self.webcam_running = True
        self._update_webcam()

    def _update_webcam(self):
        if not self.webcam_running or self.cap is None:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.stop_webcam()
            return

        try:
            objects = self.detector.detect(frame)
            results = []
            for obj in objects:
                x1, y1, x2, y2 = obj["box"]
                info = classify_word(obj["class_name"])
                result = {**info, "confidence": obj["confidence"], "box": obj["box"]}
                results.append(result)

                label = f"{result['english']} - {result['vietnamese'] or result['english']}"
                cv2.rectangle(frame, (x1, y1), (x2, y2), (65, 155, 255), 2)
                cv2.putText(frame, label, (x1, max(y1 - 10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (65, 155, 255), 2)

            if results:
                self._handle_results(results, update_image=False)
        except Exception:
            pass

        self._show_cv_image(frame)
        self.root.after(30, self._update_webcam)

    def stop_webcam(self):
        self.webcam_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def _show_cv_image(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb)
        image.thumbnail((640, 480))
        self.current_image = ImageTk.PhotoImage(image)
        self.image_label.configure(image=self.current_image, text="")

    def _handle_results(self, results, update_image=True):
        if not results:
            self.current_result = None
            self._set_info_empty()
            return

        self.current_result = results[0]
        self._update_info(self.current_result)

    def _set_info_empty(self):
        for var in self.info_vars.values():
            var.set("Chưa có dữ liệu")

    def _update_info(self, result):
        english = result.get("english") or result.get("class_name") or "Chưa có dữ liệu"
        vietnamese = result.get("vietnamese") or english
        confidence = result.get("confidence")
        category = result.get("category") or "Chưa có dữ liệu"

        self.info_vars["english"].set(english.title())
        self.info_vars["vietnamese"].set(vietnamese)
        self.info_vars["confidence"].set(f"{confidence:.2f}" if confidence is not None else "Chưa có dữ liệu")
        self.info_vars["category"].set(category)

        self.info_vars["level"].set(self._safe_level(english))
        self.info_vars["cluster"].set(self._safe_cluster(english))
        self.info_vars["related"].set(self._safe_related_words(english))

    def _safe_level(self, english):
        try:
            return predict_word_level(english)
        except Exception:
            return "Chưa có dữ liệu"

    def _safe_cluster(self, english):
        try:
            cluster = get_cluster_by_word(english)
            return f"Cluster {cluster}" if cluster is not None else "Chưa có dữ liệu"
        except Exception:
            return "Chưa có dữ liệu"

    def _safe_related_words(self, english):
        try:
            words = [item["english"].title() for item in get_related_words(english, n=3)]
            return "\n".join(words) if words else "Chưa có dữ liệu"
        except Exception:
            return "Chưa có dữ liệu"

    def play_sound(self):
        if not self.current_result:
            messagebox.showinfo("Phát âm", "Chưa có từ để phát âm.")
            return

        word = self.current_result.get("english")
        threading.Thread(target=lambda: speak(word), daemon=True).start()

    def save_current_history(self):
        if not self.current_result:
            messagebox.showinfo("Lưu lịch sử", "Chưa có kết quả nhận dạng để lưu.")
            return

        try:
            save_history(
                self.current_result.get("english"),
                self.current_result.get("vietnamese"),
                self.current_result.get("category"),
                self.current_result.get("confidence"),
                user_id=self.user_id,
            )
            messagebox.showinfo("Lưu lịch sử", "Đã lưu lịch sử.")
        except Exception as exc:
            messagebox.showwarning("Lưu lịch sử", f"Không lưu được lịch sử:\n{exc}")

    def open_history(self):
        HistoryWindow(self.root)

    def logout(self):
        self.close()
        from ui.login import LoginWindow

        LoginWindow().run()

    def close(self):
        self.stop_webcam()
        self.root.destroy()

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.mainloop()
