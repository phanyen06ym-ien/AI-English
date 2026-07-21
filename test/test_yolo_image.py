from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from detection.detector import ObjectDetector  # noqa: E402
from utils.console import use_utf8_console  # noqa: E402


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}


def iter_image_paths(path: Path) -> list[Path]:
    if path.is_dir():
        return sorted(
            item
            for item in path.iterdir()
            if item.is_file()
            and item.suffix.lower() in IMAGE_EXTENSIONS
        )

    return [path]


def detect_one(
    detector: ObjectDetector,
    image_path: Path,
) -> tuple[str, str, float, float]:
    if not image_path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(
            f"Cannot read image: {image_path}"
        )

    started_at = time.perf_counter()
    detections = detector.detect(image)
    elapsed_ms = (time.perf_counter() - started_at) * 1000

    detections.sort(
        key=lambda item: item["confidence"],
        reverse=True,
    )

    if detections:
        best = detections[0]
        return (
            image_path.name,
            best["class_name"],
            float(best["confidence"]),
            elapsed_ms,
        )

    return (
        image_path.name,
        "none",
        0.0,
        elapsed_ms,
    )


def main() -> None:
    use_utf8_console()

    parser = argparse.ArgumentParser(
        description="Test YOLO detection on one image or a directory.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=str(
            PROJECT_ROOT
            / "dataset"
            / "test_images"
        ),
        help="Image file or directory. Default: dataset/test_images",
    )
    args = parser.parse_args()

    image_paths = iter_image_paths(
        Path(args.path)
    )
    if not image_paths:
        raise FileNotFoundError(
            f"No images found in: {args.path}"
        )

    detector = ObjectDetector()

    for image_path in image_paths:
        name, detected, confidence, elapsed_ms = detect_one(
            detector,
            image_path,
        )
        print(f"Image: {name}")
        print(f"Detected: {detected}")
        print(f"confidence: {confidence:.2f}")
        print(f"time: {elapsed_ms:.0f} ms")
        print()


if __name__ == "__main__":
    main()
