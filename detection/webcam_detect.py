import cv2
from detection.detector import ObjectDetector
from detection.classify import classify_word
from utils.config import CAMERA_ID


def run_webcam():
    detector = ObjectDetector()
    cap = cv2.VideoCapture(CAMERA_ID)

    if not cap.isOpened():
        print("Không mở được webcam")
        return

    print("Đang mở webcam... Nhấn Q để thoát.")

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Không đọc được frame từ webcam")
            break

        objects = detector.detect(frame)

        for obj in objects:
            class_name = obj["class_name"]
            info = classify_word(class_name)
            vietnamese = info["vietnamese"] or class_name
            confidence = obj["confidence"]
            x1, y1, x2, y2 = obj["box"]

            label = f"{class_name} - {vietnamese} [{info['category']}] ({confidence:.2f})"

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

        cv2.imshow("AI English - Webcam Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    from utils.console import use_utf8_console

    use_utf8_console()
    run_webcam()