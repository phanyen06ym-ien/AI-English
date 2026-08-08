from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

import cv2
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
IMAGE_DIR = PROJECT_ROOT / "dataset" / "test_images"
VOCABULARY_PATH = PROJECT_ROOT / "dataset" / "vocabulary.csv"
RESULT_DIR = PROJECT_ROOT / "docs" / "experiment_results"
DETAIL_PATH = RESULT_DIR / "system_image_evaluation_details.csv"
SUMMARY_PATH = RESULT_DIR / "system_image_evaluation_summary.csv"
REPORT_PATH = RESULT_DIR / "system_image_evaluation_report.txt"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}
EXPECTED_IMAGE_COUNT = 25
KNN_N = 3


if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def format_percent(value: float) -> str:
    """Format ratio as percentage."""
    return f"{value * 100:.2f}%"


def format_float(value: float) -> str:
    """Format float with four decimals."""
    return f"{value:.4f}"


def format_ms(value: float) -> str:
    """Format milliseconds."""
    return f"{value:.3f} ms"


def print_section(title: str) -> None:
    """Print a clear terminal section."""
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def import_project_functions() -> tuple[Any, Any, Any]:
    """Import project model functions with clear errors."""
    try:
        from detection.detector import ObjectDetector
        from ml.kmeans import get_cluster_by_word, get_words_in_same_cluster
        from ml.knn import get_related_words
    except Exception as error:
        raise ImportError(
            "Không import được các module YOLO/KNN/KMeans. "
            "Hãy chạy từ thư mục gốc project và kiểm tra môi trường Python."
        ) from error

    return ObjectDetector, get_related_words, (get_cluster_by_word, get_words_in_same_cluster)


def load_vocabulary() -> pd.DataFrame:
    """Read real vocabulary data."""
    if not VOCABULARY_PATH.exists():
        raise FileNotFoundError(f"Không tìm thấy vocabulary.csv: {VOCABULARY_PATH}")

    dataframe = pd.read_csv(VOCABULARY_PATH, encoding="utf-8-sig")
    required_columns = ["english", "vietnamese", "category", "level"]
    missing_columns = [
        column for column in required_columns if column not in dataframe.columns
    ]
    if missing_columns:
        raise ValueError(
            "vocabulary.csv thiếu cột: " + ", ".join(missing_columns)
        )

    dataframe = dataframe[required_columns].copy()
    dataframe["english"] = dataframe["english"].astype(str).str.strip().str.lower()
    dataframe["vietnamese"] = dataframe["vietnamese"].astype(str).str.strip()
    dataframe["category"] = dataframe["category"].astype(str).str.strip()
    dataframe["level"] = dataframe["level"].astype(str).str.strip()
    dataframe = dataframe[dataframe["english"] != ""]
    dataframe = dataframe.drop_duplicates(subset=["english"])
    return dataframe.reset_index(drop=True)


def build_vocabulary_lookup(dataframe: pd.DataFrame) -> dict[str, dict[str, str]]:
    """Create lookup for vocabulary metadata."""
    return {
        row["english"]: {
            "vietnamese": row["vietnamese"],
            "category": row["category"],
            "level": row["level"],
        }
        for _, row in dataframe.iterrows()
    }


def iter_image_paths() -> list[Path]:
    """List real test images."""
    if not IMAGE_DIR.exists():
        raise FileNotFoundError(f"Không tìm thấy thư mục ảnh test: {IMAGE_DIR}")

    return sorted(
        path
        for path in IMAGE_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def detect_image(detector: Any, image_path: Path) -> dict[str, Any]:
    """Run YOLO detection and return the best object."""
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Không đọc được ảnh: {image_path}")

    started_at = time.perf_counter()
    detections = detector.detect(image)
    elapsed_ms = (time.perf_counter() - started_at) * 1000
    detections.sort(key=lambda item: item["confidence"], reverse=True)

    if not detections:
        return {
            "detected_word": "none",
            "confidence": 0.0,
            "yolo_time_ms": elapsed_ms,
            "detected": False,
        }

    best = detections[0]
    return {
        "detected_word": str(best["class_name"]).strip().lower(),
        "confidence": float(best["confidence"]),
        "yolo_time_ms": elapsed_ms,
        "detected": True,
    }


def evaluate_knn(
    detected_word: str,
    input_category: str | None,
    get_related_words: Any,
) -> dict[str, Any]:
    """Evaluate KNN suggestions for a detected word."""
    started_at = time.perf_counter()
    suggestions = get_related_words(detected_word, n=KNN_N)
    elapsed_ms = (time.perf_counter() - started_at) * 1000

    same_category_count = 0
    if input_category:
        same_category_count = sum(
            item["category"] == input_category for item in suggestions
        )

    suggestion_count = len(suggestions)
    return {
        "knn_suggestion_count": suggestion_count,
        "knn_same_category_count": same_category_count,
        "knn_category_precision": (
            same_category_count / suggestion_count if suggestion_count else 0.0
        ),
        "knn_success": suggestion_count > 0,
        "knn_time_ms": elapsed_ms,
    }


def evaluate_kmeans(
    detected_word: str,
    input_category: str | None,
    get_cluster_by_word: Any,
    get_words_in_same_cluster: Any,
) -> dict[str, Any]:
    """Evaluate KMeans cluster assignment for a detected word."""
    started_at = time.perf_counter()
    cluster = get_cluster_by_word(detected_word)
    same_cluster_words = (
        get_words_in_same_cluster(detected_word, include_input_word=True)
        if cluster is not None
        else []
    )
    elapsed_ms = (time.perf_counter() - started_at) * 1000

    same_category_count = 0
    if input_category:
        same_category_count = sum(
            item["category"] == input_category for item in same_cluster_words
        )

    cluster_size = len(same_cluster_words)
    return {
        "kmeans_cluster": cluster if cluster is not None else "none",
        "kmeans_cluster_size": cluster_size,
        "kmeans_same_category_count": same_category_count,
        "kmeans_cluster_purity_for_word": (
            same_category_count / cluster_size if cluster_size else 0.0
        ),
        "kmeans_success": cluster is not None,
        "kmeans_time_ms": elapsed_ms,
    }


def run_evaluation() -> tuple[pd.DataFrame, dict[str, Any]]:
    """Run YOLO, KNN, and KMeans on all test images."""
    ObjectDetector, get_related_words, kmeans_functions = import_project_functions()
    get_cluster_by_word, get_words_in_same_cluster = kmeans_functions

    vocabulary = load_vocabulary()
    vocabulary_lookup = build_vocabulary_lookup(vocabulary)
    image_paths = iter_image_paths()

    print_section("ĐÁNH GIÁ HỆ THỐNG TRÊN ẢNH TEST")
    print(f"Số ảnh tìm thấy: {len(image_paths)}")
    if len(image_paths) != EXPECTED_IMAGE_COUNT:
        print(
            f"Lưu ý: yêu cầu nói {EXPECTED_IMAGE_COUNT} ảnh, "
            f"nhưng thư mục hiện có {len(image_paths)} ảnh."
        )

    detector = ObjectDetector()
    rows: list[dict[str, Any]] = []

    for image_path in image_paths:
        yolo_result = detect_image(detector, image_path)
        detected_word = yolo_result["detected_word"]
        word_info = vocabulary_lookup.get(detected_word)
        input_category = word_info["category"] if word_info else None
        input_level = word_info["level"] if word_info else None

        if yolo_result["detected"] and word_info:
            knn_result = evaluate_knn(detected_word, input_category, get_related_words)
            kmeans_result = evaluate_kmeans(
                detected_word,
                input_category,
                get_cluster_by_word,
                get_words_in_same_cluster,
            )
        else:
            knn_result = {
                "knn_suggestion_count": 0,
                "knn_same_category_count": 0,
                "knn_category_precision": 0.0,
                "knn_success": False,
                "knn_time_ms": 0.0,
            }
            kmeans_result = {
                "kmeans_cluster": "none",
                "kmeans_cluster_size": 0,
                "kmeans_same_category_count": 0,
                "kmeans_cluster_purity_for_word": 0.0,
                "kmeans_success": False,
                "kmeans_time_ms": 0.0,
            }

        row = {
            "image": image_path.name,
            "detected_word": detected_word,
            "confidence": yolo_result["confidence"],
            "yolo_detected": yolo_result["detected"],
            "in_vocabulary": word_info is not None,
            "category": input_category or "Unknown",
            "level": input_level or "Unknown",
            "yolo_time_ms": yolo_result["yolo_time_ms"],
            **knn_result,
            **kmeans_result,
        }
        rows.append(row)

        print(
            f"{image_path.name}: YOLO={detected_word} "
            f"({row['confidence']:.2f}), "
            f"KNN={'OK' if row['knn_success'] else 'N/A'}, "
            f"KMeans={row['kmeans_cluster']}"
        )

    details = pd.DataFrame(rows)
    summary = calculate_summary(details)
    return details, summary


def calculate_summary(details: pd.DataFrame) -> dict[str, Any]:
    """Calculate measured system-level percentages."""
    total_images = int(len(details))
    detected = int(details["yolo_detected"].sum())
    in_vocabulary = int(details["in_vocabulary"].sum())
    knn_success = int(details["knn_success"].sum())
    kmeans_success = int(details["kmeans_success"].sum())

    detected_details = details[details["yolo_detected"]]
    valid_knn = details[details["knn_success"]]
    valid_kmeans = details[details["kmeans_success"]]

    return {
        "total_images": total_images,
        "expected_images": EXPECTED_IMAGE_COUNT,
        "detected_images": detected,
        "not_detected_images": total_images - detected,
        "yolo_detection_rate": detected / total_images if total_images else 0.0,
        "yolo_not_detected_rate": (
            (total_images - detected) / total_images if total_images else 0.0
        ),
        "avg_yolo_confidence_detected": (
            float(detected_details["confidence"].mean())
            if not detected_details.empty
            else 0.0
        ),
        "avg_yolo_time_ms": float(details["yolo_time_ms"].mean()) if total_images else 0.0,
        "in_vocabulary_count": in_vocabulary,
        "vocabulary_coverage_rate": in_vocabulary / total_images if total_images else 0.0,
        "knn_success_count": knn_success,
        "knn_success_rate_total": knn_success / total_images if total_images else 0.0,
        "knn_success_rate_detected": knn_success / detected if detected else 0.0,
        "avg_knn_category_precision": (
            float(valid_knn["knn_category_precision"].mean())
            if not valid_knn.empty
            else 0.0
        ),
        "avg_knn_time_ms": (
            float(valid_knn["knn_time_ms"].mean()) if not valid_knn.empty else 0.0
        ),
        "kmeans_success_count": kmeans_success,
        "kmeans_success_rate_total": kmeans_success / total_images if total_images else 0.0,
        "kmeans_success_rate_detected": kmeans_success / detected if detected else 0.0,
        "avg_kmeans_cluster_purity_for_word": (
            float(valid_kmeans["kmeans_cluster_purity_for_word"].mean())
            if not valid_kmeans.empty
            else 0.0
        ),
        "avg_kmeans_time_ms": (
            float(valid_kmeans["kmeans_time_ms"].mean()) if not valid_kmeans.empty else 0.0
        ),
    }


def build_summary_dataframe(summary: dict[str, Any]) -> pd.DataFrame:
    """Convert summary dictionary to a dataframe."""
    rows = [
        ("Tổng số ảnh trong thư mục", summary["total_images"]),
        ("Số ảnh theo yêu cầu", summary["expected_images"]),
        ("YOLO detect được", summary["detected_images"]),
        ("YOLO không detect được", summary["not_detected_images"]),
        ("YOLO Detection Rate", format_percent(summary["yolo_detection_rate"])),
        ("YOLO Not Detected Rate", format_percent(summary["yolo_not_detected_rate"])),
        ("YOLO Confidence TB trên ảnh detect", format_percent(summary["avg_yolo_confidence_detected"])),
        ("Thời gian YOLO TB", format_ms(summary["avg_yolo_time_ms"])),
        ("Từ detect có trong vocabulary", summary["in_vocabulary_count"]),
        ("Vocabulary Coverage", format_percent(summary["vocabulary_coverage_rate"])),
        ("KNN có gợi ý", summary["knn_success_count"]),
        ("KNN Success Rate trên tổng ảnh", format_percent(summary["knn_success_rate_total"])),
        ("KNN Success Rate trên ảnh YOLO detect", format_percent(summary["knn_success_rate_detected"])),
        ("KNN Category Precision TB", format_percent(summary["avg_knn_category_precision"])),
        ("Thời gian KNN TB", format_ms(summary["avg_knn_time_ms"])),
        ("KMeans phân cụm được", summary["kmeans_success_count"]),
        ("KMeans Success Rate trên tổng ảnh", format_percent(summary["kmeans_success_rate_total"])),
        ("KMeans Success Rate trên ảnh YOLO detect", format_percent(summary["kmeans_success_rate_detected"])),
        ("KMeans Cluster Purity TB theo từ", format_percent(summary["avg_kmeans_cluster_purity_for_word"])),
        ("Thời gian KMeans TB", format_ms(summary["avg_kmeans_time_ms"])),
    ]
    return pd.DataFrame(rows, columns=["metric", "value"])


def build_report(details: pd.DataFrame, summary: dict[str, Any]) -> str:
    """Build a report text for thesis writing."""
    summary_dataframe = build_summary_dataframe(summary)
    detected_distribution = (
        details["detected_word"].value_counts().rename_axis("word").reset_index(name="count")
    )
    cluster_distribution = (
        details["kmeans_cluster"].value_counts().rename_axis("cluster").reset_index(name="count")
    )

    lines: list[str] = []
    lines.append("ĐÁNH GIÁ KIỂM THỬ HỆ THỐNG AI-ENGLISH")
    lines.append("=" * 70)
    lines.append("")
    lines.append("Ghi chú quan trọng:")
    lines.append(
        "- Project hiện không có file ground truth cho từng ảnh test, "
        "nên báo cáo này không tính accuracy/precision/recall so với nhãn thật."
    )
    lines.append(
        "- Các tỷ lệ dưới đây được tính từ kết quả chạy thật của YOLO, KNN và KMeans "
        "trên ảnh thật trong dataset/test_images."
    )
    lines.append("")
    lines.append("1. Bảng tổng hợp")
    lines.append(summary_dataframe.to_string(index=False))
    lines.append("")
    lines.append("2. Phân bố kết quả YOLO")
    lines.append(detected_distribution.to_string(index=False))
    lines.append("")
    lines.append("3. Phân bố cụm KMeans trên các từ YOLO detect được")
    lines.append(cluster_distribution.to_string(index=False))
    lines.append("")
    lines.append("4. Chi tiết từng ảnh")
    display_details = details.copy()
    for column in ["confidence", "knn_category_precision", "kmeans_cluster_purity_for_word"]:
        display_details[column] = display_details[column].map(format_percent)
    for column in ["yolo_time_ms", "knn_time_ms", "kmeans_time_ms"]:
        display_details[column] = display_details[column].map(format_ms)
    lines.append(display_details.to_string(index=False))
    lines.append("")
    lines.append("5. Kết luận")
    lines.append(
        f"- YOLO detect được {summary['detected_images']}/{summary['total_images']} ảnh, "
        f"tương ứng {format_percent(summary['yolo_detection_rate'])}."
    )
    lines.append(
        f"- KNN sinh gợi ý cho {summary['knn_success_count']}/{summary['total_images']} ảnh, "
        f"Category Precision trung bình {format_percent(summary['avg_knn_category_precision'])}."
    )
    lines.append(
        f"- KMeans phân cụm được {summary['kmeans_success_count']}/{summary['total_images']} ảnh, "
        f"Cluster Purity trung bình theo từ {format_percent(summary['avg_kmeans_cluster_purity_for_word'])}."
    )
    return "\n".join(lines)


def save_results(details: pd.DataFrame, summary: dict[str, Any]) -> None:
    """Save detailed CSV, summary CSV, and report text."""
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    details.to_csv(DETAIL_PATH, index=False, encoding="utf-8-sig")
    build_summary_dataframe(summary).to_csv(SUMMARY_PATH, index=False, encoding="utf-8-sig")
    REPORT_PATH.write_text(build_report(details, summary), encoding="utf-8")


def print_summary(summary: dict[str, Any]) -> None:
    """Print final summary to terminal."""
    print_section("BẢNG TỔNG HỢP PHẦN TRĂM")
    print(build_summary_dataframe(summary).to_string(index=False))

    print_section("KẾT LUẬN")
    print(
        f"YOLO detect được {summary['detected_images']}/{summary['total_images']} ảnh "
        f"= {format_percent(summary['yolo_detection_rate'])}."
    )
    print(
        f"KNN có gợi ý cho {summary['knn_success_count']}/{summary['total_images']} ảnh "
        f"= {format_percent(summary['knn_success_rate_total'])}; "
        f"Category Precision TB = {format_percent(summary['avg_knn_category_precision'])}."
    )
    print(
        f"KMeans phân cụm được {summary['kmeans_success_count']}/{summary['total_images']} ảnh "
        f"= {format_percent(summary['kmeans_success_rate_total'])}; "
        f"Cluster Purity TB = {format_percent(summary['avg_kmeans_cluster_purity_for_word'])}."
    )
    print()
    print("File kết quả đã lưu:")
    print(DETAIL_PATH)
    print(SUMMARY_PATH)
    print(REPORT_PATH)


def main() -> None:
    """Run the full system evaluation."""
    details, summary = run_evaluation()
    save_results(details, summary)
    print_summary(summary)


if __name__ == "__main__":
    main()
