from ultralytics import YOLO
from utils.config import YOLO_MODEL, CONFIDENCE


class ObjectDetector:

    def __init__(self):
        self.model = YOLO(YOLO_MODEL)

    def detect(self, frame):

        results = self.model(
            frame,
            conf=CONFIDENCE,
            verbose=False
        )

        return results