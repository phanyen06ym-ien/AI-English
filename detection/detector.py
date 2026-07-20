from ultralytics import YOLO

from dataset.coco_classes import COCO_CLASSES
from utils.config import MODEL_PATH, CONFIDENCE, IMAGE_SIZE
from utils import perf_monitor


class ObjectDetector:

    def __init__(self, model_path=MODEL_PATH):
        perf_monitor.start()
        with perf_monitor.timer("yolo_model_load"):
            self.model = YOLO(model_path)

    def detect(self, frame):

        with perf_monitor.timer(
            "yolo_infer",
            synchronize_cuda=True,
        ):
            results = self.model.predict(
                frame,
                conf=CONFIDENCE,
                imgsz=IMAGE_SIZE,
                verbose=False
            )

        detected_objects = []

        with perf_monitor.timer("yolo_parse_results"):
            for result in results:

                for box in result.boxes:

                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])

                    class_name = self.model.names[class_id]

                    if class_name not in COCO_CLASSES:
                        continue

                    x1, y1, x2, y2 = map(
                        int,
                        box.xyxy[0]
                    )

                    detected_objects.append({

                        "class_name": class_name,

                        "confidence": confidence,

                        "box": (x1, y1, x2, y2)

                    })

        return detected_objects
