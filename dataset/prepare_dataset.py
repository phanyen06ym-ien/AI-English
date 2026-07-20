from __future__ import annotations

import json
import random
import shutil
from collections import defaultdict
from pathlib import Path


# =========================================================
# 1. CẤU HÌNH ĐƯỜNG DẪN
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

COCO_ROOT = Path(r"D:\Dataset\coco2017_subset")

COCO_TRAIN_IMAGES = COCO_ROOT / "train2017"
COCO_VAL_IMAGES = COCO_ROOT / "val2017"

COCO_TRAIN_JSON = COCO_ROOT / "annotations" / "instances_train2017.json"
COCO_VAL_JSON = COCO_ROOT / "annotations" / "instances_val2017.json"

OUTPUT_ROOT = PROJECT_ROOT / "dataset" / "yolo_dataset"


# =========================================================
# 2. CÁC LỚP NHÓM SỬ DỤNG
# =========================================================

# Chỉ gồm các lớp thực sự có trong COCO 2017
SELECTED_CLASSES = [
     "person",
    "backpack",
    "book",
    "bottle",
    "cell phone",
    "chair",
    "clock",
    "cup",
    "dining table",
    "keyboard",
    "laptop",
    "mouse",
]


# =========================================================
# 3. THAM SỐ CHIA DỮ LIỆU
# =========================================================

RANDOM_SEED = 42

# Lấy 50% tập val2017 làm validation,
# 50% còn lại làm test.
VAL_RATIO = 0.5

# Giới hạn số ảnh để chạy thử.
# Đặt None nếu muốn lấy toàn bộ ảnh phù hợp.
MAX_TRAIN_IMAGES = None
MAX_VAL_IMAGES = None


# =========================================================
# 4. HÀM HỖ TRỢ
# =========================================================

def create_output_directories() -> None:
    """Tạo cấu trúc thư mục cho YOLO."""

    folders = [
        OUTPUT_ROOT / "train" / "images",
        OUTPUT_ROOT / "train" / "labels",
        OUTPUT_ROOT / "valid" / "images",
        OUTPUT_ROOT / "valid" / "labels",
        OUTPUT_ROOT / "test" / "images",
        OUTPUT_ROOT / "test" / "labels",
    ]

    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)


def validate_paths() -> None:
    """Kiểm tra dữ liệu COCO có tồn tại không."""

    required_paths = [
        COCO_TRAIN_IMAGES,
        COCO_VAL_IMAGES,
        COCO_TRAIN_JSON,
        COCO_VAL_JSON,
    ]

    missing_paths = [path for path in required_paths if not path.exists()]

    if missing_paths:
        print("\nKhông tìm thấy các đường dẫn sau:")

        for path in missing_paths:
            print(f"- {path}")

        print(
            "\nHãy sửa biến COCO_ROOT trong file prepare_dataset.py "
            "cho đúng nơi bạn đã giải nén coco2017_subset."
        )

        raise FileNotFoundError("Thiếu dữ liệu COCO hoặc annotation.")


def load_coco_json(json_path: Path) -> dict:
    """Đọc file annotation JSON của COCO."""

    print(f"Đang đọc annotation: {json_path}")

    with json_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def coco_bbox_to_yolo(
    bbox: list[float],
    image_width: int,
    image_height: int,
) -> tuple[float, float, float, float]:
    """
    Chuyển bbox COCO sang YOLO.

    COCO:
        x_min, y_min, width, height

    YOLO:
        x_center, y_center, width, height

    Các giá trị YOLO được chuẩn hóa về khoảng 0 đến 1.
    """

    x_min, y_min, box_width, box_height = bbox

    x_center = x_min + box_width / 2
    y_center = y_min + box_height / 2

    x_center /= image_width
    y_center /= image_height
    box_width /= image_width
    box_height /= image_height

    # Giới hạn về khoảng [0, 1] để tránh lỗi dữ liệu
    x_center = min(max(x_center, 0.0), 1.0)
    y_center = min(max(y_center, 0.0), 1.0)
    box_width = min(max(box_width, 0.0), 1.0)
    box_height = min(max(box_height, 0.0), 1.0)

    return x_center, y_center, box_width, box_height


def prepare_coco_records(
    coco_data: dict,
) -> list[dict]:
    """
    Lọc các ảnh chứa lớp được chọn và chuyển annotation
    thành danh sách record dễ xử lý.
    """

    category_name_by_id = {
        category["id"]: category["name"]
        for category in coco_data["categories"]
    }

    selected_category_ids = {
        category_id
        for category_id, category_name in category_name_by_id.items()
        if category_name in SELECTED_CLASSES
    }

    class_id_by_name = {
        class_name: index
        for index, class_name in enumerate(SELECTED_CLASSES)
    }

    image_by_id = {
        image["id"]: image
        for image in coco_data["images"]
    }

    annotations_by_image = defaultdict(list)

    for annotation in coco_data["annotations"]:
        category_id = annotation["category_id"]

        if category_id not in selected_category_ids:
            continue

        image_id = annotation["image_id"]
        image_info = image_by_id.get(image_id)

        if image_info is None:
            continue

        category_name = category_name_by_id[category_id]
        yolo_class_id = class_id_by_name[category_name]

        bbox = annotation.get("bbox")

        if not bbox or len(bbox) != 4:
            continue

        x_center, y_center, width, height = coco_bbox_to_yolo(
            bbox=bbox,
            image_width=image_info["width"],
            image_height=image_info["height"],
        )

        # Bỏ bounding box không hợp lệ
        if width <= 0 or height <= 0:
            continue

        yolo_line = (
            f"{yolo_class_id} "
            f"{x_center:.6f} "
            f"{y_center:.6f} "
            f"{width:.6f} "
            f"{height:.6f}"
        )

        annotations_by_image[image_id].append(yolo_line)

    records = []

    for image_id, yolo_labels in annotations_by_image.items():
        image_info = image_by_id[image_id]

        records.append(
            {
                "file_name": image_info["file_name"],
                "labels": yolo_labels,
            }
        )

    return records


def copy_records_to_split(
    records: list[dict],
    source_images_directory: Path,
    split_name: str,
    max_images: int | None = None,
) -> int:
    """Copy ảnh và tạo file label cho một tập dữ liệu."""

    destination_images = OUTPUT_ROOT / split_name / "images"
    destination_labels = OUTPUT_ROOT / split_name / "labels"

    selected_records = records.copy()
    random.shuffle(selected_records)

    if max_images is not None:
        selected_records = selected_records[:max_images]

    copied_count = 0

    for record in selected_records:
        file_name = record["file_name"]

        source_image = source_images_directory / file_name
        destination_image = destination_images / file_name

        if not source_image.exists():
            print(f"Bỏ qua vì không tìm thấy ảnh: {source_image}")
            continue

        shutil.copy2(source_image, destination_image)

        label_file_name = Path(file_name).with_suffix(".txt").name
        destination_label = destination_labels / label_file_name

        with destination_label.open("w", encoding="utf-8") as label_file:
            label_file.write("\n".join(record["labels"]))

        copied_count += 1

    return copied_count


def write_dataset_yaml() -> None:
    """Tự tạo lại file dataset.yaml theo đúng danh sách lớp."""

    yaml_path = PROJECT_ROOT / "dataset" / "dataset.yaml"

    class_lines = "\n".join(
        f"  {index}: {class_name}"
        for index, class_name in enumerate(SELECTED_CLASSES)
    )

    yaml_content = f"""path: {OUTPUT_ROOT.as_posix()}

train: train/images
val: valid/images
test: test/images

names:
{class_lines}
"""

    yaml_path.write_text(yaml_content, encoding="utf-8")

    print(f"Đã tạo file YAML: {yaml_path}")


def main() -> None:
    random.seed(RANDOM_SEED)

    print("=" * 60)
    print("CHUẨN BỊ DATASET COCO CHO YOLOV8")
    print("=" * 60)

    validate_paths()
    create_output_directories()

    train_data = load_coco_json(COCO_TRAIN_JSON)
    val_data = load_coco_json(COCO_VAL_JSON)

    print("\nĐang lọc annotation train...")
    train_records = prepare_coco_records(train_data)

    print("Đang lọc annotation validation...")
    val_records = prepare_coco_records(val_data)

    random.shuffle(train_records)
    random.shuffle(val_records)

    # Chia val2017 thành validation và test
    split_index = int(len(val_records) * VAL_RATIO)

    valid_records = val_records[:split_index]
    test_records = val_records[split_index:]

    print("\nĐang copy tập train...")
    train_count = copy_records_to_split(
        records=train_records,
        source_images_directory=COCO_TRAIN_IMAGES,
        split_name="train",
        max_images=MAX_TRAIN_IMAGES,
    )

    print("Đang copy tập validation...")
    valid_count = copy_records_to_split(
        records=valid_records,
        source_images_directory=COCO_VAL_IMAGES,
        split_name="valid",
        max_images=MAX_VAL_IMAGES,
    )

    print("Đang copy tập test...")
    test_count = copy_records_to_split(
        records=test_records,
        source_images_directory=COCO_VAL_IMAGES,
        split_name="test",
        max_images=MAX_VAL_IMAGES,
    )

    write_dataset_yaml()

    print("\n" + "=" * 60)
    print("HOÀN THÀNH")
    print("=" * 60)
    print(f"Số ảnh train:      {train_count}")
    print(f"Số ảnh validation: {valid_count}")
    print(f"Số ảnh test:       {test_count}")
    print(f"Dataset YOLO:      {OUTPUT_ROOT}")
    print("=" * 60)


if __name__ == "__main__":
    main()