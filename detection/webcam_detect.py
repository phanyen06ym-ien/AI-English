import cv2
from time import monotonic

from database.history import save_history
from detection.classify import classify_word
from detection.detector import ObjectDetector
from utils.config import CAMERA_ID
from utils.helper import draw_vietnamese_text


WINDOW_NAME = "AI English - Webcam Detection"
INFERENCE_INTERVAL_SECONDS = 0.25
HISTORY_COOLDOWN_SECONDS = 5.0


def run_webcam():
    detector = ObjectDetector()
    cap = cv2.VideoCapture(CAMERA_ID)
    last_saved_by_class = {}
    last_inference_at = 0.0
    last_objects = []

    if not cap.isOpened():
        print("Không mở được webcam")
        return

    print("Đang mở webcam... Nhấn Q hoặc Esc để thoát.")

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                print("Không đọc được frame từ webcam")
                break

            now = monotonic()

            if now - last_inference_at >= INFERENCE_INTERVAL_SECONDS:
                last_inference_at = now
                last_objects = detector.detect(frame)

            for obj in last_objects:
                class_name = obj["class_name"]
                info = classify_word(class_name)
                vietnamese = info["vietnamese"] or class_name
                confidence = obj["confidence"]
                x1, y1, x2, y2 = obj["box"]

                label = f"{class_name} - {vietnamese} [{info['category']}] ({confidence:.2f})"
                last_saved_at = last_saved_by_class.get(
                    class_name,
                    0.0,
                )

                if now - last_saved_at >= HISTORY_COOLDOWN_SECONDS:
                    if save_history(
                        class_name,
                        vietnamese,
                        info["category"],
                        confidence,
                    ):
                        last_saved_by_class[class_name] = now

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # cv2.putText sẽ làm lỗi tiếng Việt, nên dùng font Unicode.
                frame = draw_vietnamese_text(
                    frame,
                    label,
                    (x1, max(y1 - 35, 5)),
                    color=(0, 255, 0),
                    size=28,
                )

            cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                break

            # Nếu người dùng bấm nút X của cửa sổ thì nhả webcam và thoát.
            if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    from utils.console import use_utf8_console

    use_utf8_console()
    run_webcam()
