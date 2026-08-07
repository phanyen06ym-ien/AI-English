import cv2
import logging

from ai.pipeline import AIEngine
from database.history import save_history
from utils.helper import draw_vietnamese_text


logger = logging.getLogger(__name__)


def detect_image(
    image_path,
    detector=None,
    ai_engine=None,
    show_window=True,
    user_id=None,
):
    """Detect objects in an image and return the annotated image and results."""
    if ai_engine is None:
        if detector is None:
            ai_engine = AIEngine.create_default()
        else:
            ai_engine = AIEngine.from_detector(detector)

    image = cv2.imread(image_path)

    if image is None:
        logger.error("Khong doc duoc anh: %s", image_path)
        return None, []

    analysis = ai_engine.analyze_frame(
        image,
        include_learning=False,
    )

    if not analysis.success:
        return image, []

    results = []

    for result in analysis.detections:
        x1, y1, x2, y2 = result.box
        label = (
            f"{result.english} - {result.vietnamese} "
            f"[{result.category}] ({result.confidence:.2f})"
        )

        results.append(
            {
                "english": result.english,
                "vietnamese": result.vietnamese,
                "category": result.category,
                "level": result.level,
                "source": result.source,
                "confidence": result.confidence,
                "box": result.box,
            }
        )
        save_history(
            result.english,
            result.vietnamese,
            result.category,
            result.confidence,
            user_id=user_id,
        )
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        image = draw_vietnamese_text(
            image,
            label,
            (x1, max(y1 - 35, 5)),
            color=(0, 255, 0),
            size=28,
        )

    if show_window:
        cv2.imshow("Image Detection", image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return image, results


if __name__ == "__main__":
    from utils.console import use_utf8_console

    use_utf8_console()
    detect_image("dataset/test_images/test1.jpg")
