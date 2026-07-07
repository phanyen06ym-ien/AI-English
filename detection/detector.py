from ultralytics import YOLO
from utils.config import MODEL_PATH, CONFIDENCE
from dataset.coco_classes import COCO_CLASSES


class ObjectDetector:
    def __init__(self, model_path=MODEL_PATH):
        self.model = YOLO(model_path)

    def detect(self, frame):
        results = self.model(frame, verbose=False)
        detected_objects = []

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                class_name = self.model.names[class_id]

                if confidence >= CONFIDENCE and class_name in COCO_CLASSES:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    detected_objects.append({
                        "class_name": class_name,
                        "confidence": confidence,
                        "box": (x1, y1, x2, y2)
                    })

        return detected_objects