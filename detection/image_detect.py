import cv2
from detection.detector import ObjectDetector
from detection.classify import classify_word
from utils.helper import draw_vietnamese_text
from database.history import save_history


def detect_image(image_path):
    detector = ObjectDetector()
    image = cv2.imread(image_path)

    if image is None:
        print("Không đọc được ảnh:", image_path)
        return

    objects = detector.detect(image)
    results = []

    for obj in objects:
        class_name = obj["class_name"]
        info = classify_word(class_name)
        vietnamese = info["vietnamese"] or class_name
        confidence = obj["confidence"]
        x1, y1, x2, y2 = obj["box"]

        label = f"{class_name} - {vietnamese} [{info['category']}] ({confidence:.2f})"
        results.append({**info, "confidence": confidence, "box": obj["box"]})
        save_history(class_name, vietnamese, info["category"], confidence)

        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

        image = draw_vietnamese_text(
            image,
            label,
            (x1, max(y1 - 35, 5)),
            color=(0, 255, 0),
            size=28
        )

    cv2.imshow("Image Detection", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return results


if __name__ == "__main__":
    from utils.console import use_utf8_console

    use_utf8_console()
    detect_image("dataset/test_images/test1.jpg")