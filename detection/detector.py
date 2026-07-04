from ultralytics import YOLO

# Tải model YOLOv8
model = YOLO("yolov8n.pt")

def detect(image_path):
    results = model(image_path)

    detected_objects = []

    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            class_name = model.names[class_id]
            confidence = float(box.conf[0])

            detected_objects.append({
                "english": class_name,
                "confidence": confidence
            })

    return detected_objects