import cv2

from detection.detector import ObjectDetector
from utils.config import CAMERA_ID
from utils.config import FRAME_WIDTH
from utils.config import FRAME_HEIGHT


def run_webcam():

    detector = ObjectDetector()

    cap = cv2.VideoCapture(CAMERA_ID)

    if not cap.isOpened():
        print("Không mở được webcam")
        return

    print("Đang mở webcam...")

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        # Resize
        frame = cv2.resize(
            frame,
            (FRAME_WIDTH, FRAME_HEIGHT)
        )

        # Lật ảnh
        frame = cv2.flip(frame, 1)

        # YOLO Detection
        results = detector.detect(frame)

        # Vẽ Bounding Box
        output = results[0].plot()

        cv2.imshow(
            "AI-English System",
            output
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()

    cv2.destroyAllWindows()