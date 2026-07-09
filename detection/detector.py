from ultralytics import YOLO
from utils.config import MODEL_PATH, CONFIDENCE

class ObjectDetector:
    def __init__(self):
        self.model = YOLO(MODEL_PATH)

    def detect(self, frame):
        results = self.model(frame, conf=CONFIDENCE, verbose=False)
        objects = []
        for r in results:
            boxes = r.boxes
            if boxes is None:
                continue
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                class_name = self.model.names[cls]
                objects.append({
                    "class_name": class_name,
                    "confidence": conf,
                    "box": [x1, y1, x2, y2]
                })
        return objects