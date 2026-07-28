from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "dataset" / "vocabulary.csv"
RESULT_DIR = PROJECT_ROOT / "docs" / "experiment_results"
DETAIL_PATH = RESULT_DIR / "knn_test_details.csv"
SUMMARY_PATH = RESULT_DIR / "knn_summary.csv"
REPORT_PATH = RESULT_DIR / "knn_report.txt"

REQUIRED_COLUMNS = ["english", "vietnamese", "category", "level"]
PREFERRED_TEST_WORDS = [
    "laptop",
    "keyboard",
    "mouse",
    "book",
    "bottle",
    "cup",
    "chair",
    "person",
    "backpack",
    "clock",
]
TEST_N_VALUES = [3, 5, 7]


if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def print_section(title: str) -> None:
    """Print a numbered section title."""
    print()
    print(title)
    print("-" * 60)


def format_percent(value: float) -> str:
    """Format a ratio as a percentage."""
    return f"{value * 100:.2f}%"


def format_distance(value: float) -> str:
    """Format an Euclidean distance."""
    return f"{value:.4f}"


def format_ms(value: float) -> str:
    """Format milliseconds."""
    return f"{value:.3f} ms"


def import_knn_function() -> Any:
    """Import get_related_words with a clear error message."""
    try:
        from ml.knn import get_related_words
    except Exception as error:
        raise ImportError(
            "Không import được ml.knn.get_related_words. "
            "Hãy chạy lệnh từ thư mục gốc project và kiểm tra các thư viện phụ thuộc."
        ) from error

    return get_related_words


def load_raw_dataset() -> pd.DataFrame:
    """Read the real vocabulary dataset from CSV."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy vocabulary.csv tại: {DATA_PATH}"
        )

    dataframe = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in dataframe.columns
    ]
    if missing_columns:
        raise ValueError(
            "vocabulary.csv thiếu các cột bắt buộc: "
            + ", ".join(missing_columns)
        )

    return dataframe


def normalize_dataset(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Normalize data the same way ml.knn.read_vocabulary does."""
    normalized = dataframe[REQUIRED_COLUMNS].copy()
    normalized["english"] = (
        normalized["english"].astype(str).str.strip().str.lower()
    )
    normalized["vietnamese"] = normalized["vietnamese"].astype(str).str.strip()
    normalized["category"] = normalized["category"].astype(str).str.strip()
    normalized["level"] = normalized["level"].astype(str).str.strip()
    normalized = normalized[normalized["english"] != ""]
    normalized = normalized.drop_duplicates(subset=["english"])
    return normalized.reset_index(drop=True)


def count_missing_values(dataframe: pd.DataFrame) -> dict[str, int]:
    """Count missing or blank values in required columns."""
    missing_counts: dict[str, int] = {}
    for column in REQUIRED_COLUMNS:
        series = dataframe[column]
        missing_counts[column] = int(
            series.isna().sum()
            + series.dropna().astype(str).str.strip().eq("").sum()
        )
    return missing_counts


def build_dataset_statistics(
    raw_dataframe: pd.DataFrame,
    normalized_dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """Build dataset statistics for terminal output and report."""
    normalized_english = (
        raw_dataframe["english"].astype(str).str.strip().str.lower()
    )
    duplicate_count = int(
        normalized_english[normalized_english != ""].duplicated().sum()
    )
    category_counts = (
        normalized_dataframe["category"].value_counts().sort_index()
    )
    level_counts = normalized_dataframe["level"].value_counts()

    return {
        "raw_rows": int(len(raw_dataframe)),
        "normalized_words": int(len(normalized_dataframe)),
        "duplicate_english": duplicate_count,
        "missing_counts": count_missing_values(raw_dataframe),
        "category_count": int(normalized_dataframe["category"].nunique()),
        "categories": sorted(normalized_dataframe["category"].unique()),
        "category_counts": category_counts.to_dict(),
        "level_counts": {
            level: int(level_counts.get(level, 0))
            for level in ["Easy", "Medium", "Hard"]
        },
    }


def print_dataset_statistics(statistics: dict[str, Any]) -> None:
    """Print dataset statistics."""
    print(f"Tổng số dòng ban đầu: {statistics['raw_rows']}")
    print(f"Tổng số từ sau chuẩn hóa: {statistics['normalized_words']}")
    print(f"Số từ bị trùng theo cột english: {statistics['duplicate_english']}")
    print("Số dòng thiếu dữ liệu ở từng cột:")
    for column, count in statistics["missing_counts"].items():
        print(f"  - {column}: {count}")
    print(f"Số chủ đề khác nhau: {statistics['category_count']}")
    print("Danh sách các chủ đề:")
    for category in statistics["categories"]:
        print(f"  - {category}")
    print("Số từ thuộc từng chủ đề:")
    for category, count in statistics["category_counts"].items():
        print(f"  - {category}: {count}")
    print("Số từ thuộc từng mức độ:")
    for level, count in statistics["level_counts"].items():
        print(f"  - {level}: {count}")


def select_test_words(dataframe: pd.DataFrame, minimum: int = 10) -> list[str]:
    """Select test words from the real dataset across multiple categories."""
    available_words = set(dataframe["english"])
    selected: list[str] = [
        word for word in PREFERRED_TEST_WORDS if word in available_words
    ]

    target_count = min(minimum, len(dataframe))
    grouped = dataframe.sort_values(["category", "english"]).groupby("category")
    category_words = {
        category: list(group["english"])
        for category, group in grouped
    }

    while len(selected) < target_count:
        added = False
        for words in category_words.values():
            for word in words:
                if word not in selected:
                    selected.append(word)
                    added = True
                    break
            if len(selected) >= target_count:
                break
        if not added:
            break

    return selected


def get_input_lookup(dataframe: pd.DataFrame) -> dict[str, dict[str, str]]:
    """Create a lookup table for input word metadata."""
    return {
        row["english"]: {
            "category": row["category"],
            "level": row["level"],
        }
        for _, row in dataframe.iterrows()
    }


def evaluate_suggestions(
    input_word: str,
    input_category: str,
    input_level: str,
    n: int,
    suggestions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute evaluation metrics for one input word and n."""
    suggestion_count = len(suggestions)
    same_category_count = sum(
        item["category"] == input_category for item in suggestions
    )
    same_level_count = sum(item["level"] == input_level for item in suggestions)
    mean_distance = (
        sum(float(item["distance"]) for item in suggestions) / suggestion_count
        if suggestion_count
        else 0.0
    )

    first_same_category_rank = 0
    for rank, item in enumerate(suggestions, start=1):
        if item["category"] == input_category:
            first_same_category_rank = rank
            break

    reciprocal_rank = (
        1.0 / first_same_category_rank if first_same_category_rank else 0.0
    )

    return {
        "input_word": input_word,
        "input_category": input_category,
        "input_level": input_level,
        "n": n,
        "suggestion_count": suggestion_count,
        "same_category_count": same_category_count,
        "category_precision": (
            same_category_count / suggestion_count if suggestion_count else 0.0
        ),
        "same_level_count": same_level_count,
        "level_precision": (
            same_level_count / suggestion_count if suggestion_count else 0.0
        ),
        "mean_distance": mean_distance,
        "mrr_category": reciprocal_rank,
    }


def run_knn_experiment(
    test_words: list[str],
    lookup: dict[str, dict[str, str]],
    get_related_words: Any,
) -> tuple[pd.DataFrame, pd.DataFrame, list[float]]:
    """Run k-NN suggestions and return detail and metric dataframes."""
    detail_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    query_times_ms: list[float] = []

    for input_word in test_words:
        input_category = lookup[input_word]["category"]
        input_level = lookup[input_word]["level"]
        print()
        print(
            f"Từ đầu vào: {input_word} | "
            f"Chủ đề: {input_category} | Mức độ: {input_level}"
        )

        for n in TEST_N_VALUES:
            query_start = time.perf_counter()
            suggestions = get_related_words(input_word, n=n)
            query_times_ms.append((time.perf_counter() - query_start) * 1000)

            metrics = evaluate_suggestions(
                input_word,
                input_category,
                input_level,
                n,
                suggestions,
            )
            metric_rows.append(metrics)

            print(f"  n = {n}")
            print(f"  Số lượng từ gợi ý: {len(suggestions)}")
            for rank, item in enumerate(suggestions, start=1):
                same_category = item["category"] == input_category
                same_level = item["level"] == input_level
                detail_rows.append(
                    {
                        "input_word": input_word,
                        "input_category": input_category,
                        "input_level": input_level,
                        "n": n,
                        "rank": rank,
                        "suggested_word": item["english"],
                        "suggested_vietnamese": item["vietnamese"],
                        "suggested_category": item["category"],
                        "suggested_level": item["level"],
                        "distance": float(item["distance"]),
                        "same_category": same_category,
                        "same_level": same_level,
                    }
                )
                print(
                    "    "
                    f"{rank}. {item['english']} - {item['vietnamese']} | "
                    f"{item['category']} | {item['level']} | "
                    f"Distance = {format_distance(float(item['distance']))}"
                )
            print(
                "    "
                f"Same Category: {metrics['same_category_count']} | "
                f"Category Precision: {format_percent(metrics['category_precision'])} | "
                f"Same Level: {metrics['same_level_count']} | "
                f"Level Precision: {format_percent(metrics['level_precision'])} | "
                f"Mean Distance: {format_distance(metrics['mean_distance'])} | "
                f"MRR-category: {metrics['mrr_category']:.4f}"
            )

    return (
        pd.DataFrame(detail_rows),
        pd.DataFrame(metric_rows),
        query_times_ms,
    )


def build_summary(metrics_dataframe: pd.DataFrame) -> pd.DataFrame:
    """Aggregate evaluation metrics by n."""
    rows: list[dict[str, Any]] = []
    for n, group in metrics_dataframe.groupby("n", sort=True):
        total_suggestions = int(group["suggestion_count"].sum())
        total_same_category = int(group["same_category_count"].sum())
        total_same_level = int(group["same_level_count"].sum())
        rows.append(
            {
                "n": int(n),
                "tested_input_words": int(group["input_word"].nunique()),
                "total_suggestions": total_suggestions,
                "same_category_suggestions": total_same_category,
                "avg_category_precision": float(
                    group["category_precision"].mean()
                ),
                "same_level_suggestions": total_same_level,
                "avg_level_precision": float(group["level_precision"].mean()),
                "avg_mean_distance": float(group["mean_distance"].mean()),
                "avg_mrr_category": float(group["mrr_category"].mean()),
            }
        )
    return pd.DataFrame(rows)


def format_summary_for_terminal(summary_dataframe: pd.DataFrame) -> pd.DataFrame:
    """Create a display-friendly copy of the summary dataframe."""
    display = summary_dataframe.copy()
    display["avg_category_precision"] = display[
        "avg_category_precision"
    ].map(format_percent)
    display["avg_level_precision"] = display["avg_level_precision"].map(
        format_percent
    )
    display["avg_mean_distance"] = display["avg_mean_distance"].map(
        format_distance
    )
    display["avg_mrr_category"] = display["avg_mrr_category"].map(
        lambda value: f"{value:.4f}"
    )
    return display


def choose_best_n(summary_dataframe: pd.DataFrame) -> pd.Series:
    """Choose the best n based on measured metrics."""
    ranked = summary_dataframe.sort_values(
        by=[
            "avg_category_precision",
            "avg_mrr_category",
            "avg_mean_distance",
            "n",
        ],
        ascending=[False, False, True, True],
    )
    return ranked.iloc[0]


def run_special_cases(
    dataframe: pd.DataFrame,
    get_related_words: Any,
) -> list[dict[str, Any]]:
    """Run edge-case tests and print their outcomes."""
    results: list[dict[str, Any]] = []

    cases = [
        ("Từ không tồn tại", "this_word_does_not_exist", 3),
        ("Chuỗi rỗng", "", 3),
    ]
    if "laptop" in set(dataframe["english"]):
        cases.append(("Chữ hoa và khoảng trắng", "  LAPTOP  ", 3))
    large_n = len(dataframe) + 100
    cases.append(("n lớn hơn số lượng từ hiện có", dataframe.iloc[0]["english"], large_n))

    laptop_baseline = (
        get_related_words("laptop", n=3)
        if "laptop" in set(dataframe["english"])
        else None
    )

    for case_name, word, n in cases:
        started_at = time.perf_counter()
        suggestions = get_related_words(word, n=n)
        elapsed_ms = (time.perf_counter() - started_at) * 1000

        passed = True
        expected = ""
        if case_name in {"Từ không tồn tại", "Chuỗi rỗng"}:
            expected = "Danh sách rỗng"
            passed = suggestions == []
        elif case_name == "Chữ hoa và khoảng trắng":
            expected = 'Kết quả giống khi nhập "laptop"'
            passed = suggestions == laptop_baseline
        else:
            expected = "Không lỗi và giới hạn số kết quả hợp lệ"
            passed = len(suggestions) <= max(len(dataframe) - 1, 0)

        results.append(
            {
                "case": case_name,
                "input": repr(word),
                "n": n,
                "suggestion_count": len(suggestions),
                "expected": expected,
                "passed": passed,
                "elapsed_ms": elapsed_ms,
            }
        )

        print(
            f"{case_name}: input={word!r}, n={n}, "
            f"số gợi ý={len(suggestions)}, "
            f"kết quả={'ĐẠT' if passed else 'KHÔNG ĐẠT'}, "
            f"thời gian={format_ms(elapsed_ms)}"
        )
        if suggestions:
            preview = ", ".join(item["english"] for item in suggestions[:10])
            print(f"  Gợi ý: {preview}")

    return results


def build_report_text(
    statistics: dict[str, Any],
    test_words: list[str],
    summary_dataframe: pd.DataFrame,
    best_n_row: pd.Series,
    special_case_results: list[dict[str, Any]],
    total_elapsed_ms: float,
    average_query_ms: float,
) -> str:
    """Build the text report saved to disk."""
    lines: list[str] = []
    lines.append("THỰC NGHIỆM K-NN GỢI Ý TỪ VỰNG")
    lines.append("=" * 60)
    lines.append("")
    lines.append("1. Thống kê dataset")
    lines.append(f"- Tổng số dòng ban đầu: {statistics['raw_rows']}")
    lines.append(f"- Tổng số từ sau chuẩn hóa: {statistics['normalized_words']}")
    lines.append(f"- Số từ bị trùng theo cột english: {statistics['duplicate_english']}")
    lines.append("- Số dòng thiếu dữ liệu:")
    for column, count in statistics["missing_counts"].items():
        lines.append(f"  + {column}: {count}")
    lines.append(f"- Số chủ đề khác nhau: {statistics['category_count']}")
    lines.append(f"- Danh sách chủ đề: {', '.join(statistics['categories'])}")
    lines.append("- Số từ thuộc từng chủ đề:")
    for category, count in statistics["category_counts"].items():
        lines.append(f"  + {category}: {count}")
    lines.append("- Số từ thuộc từng mức độ:")
    for level, count in statistics["level_counts"].items():
        lines.append(f"  + {level}: {count}")
    lines.append("")
    lines.append("2. Cấu hình k-NN")
    lines.append("- Đặc trưng: word_length, level_encoded, one-hot category")
    lines.append("- Chuẩn hóa: StandardScaler")
    lines.append("- Trọng số: CATEGORY_WEIGHT=5.0, LEVEL_WEIGHT=2.0, WORD_LENGTH_WEIGHT=0.5")
    lines.append('- Mô hình: NearestNeighbors(metric="euclidean")')
    lines.append("")
    lines.append("3. Số từ kiểm thử")
    lines.append(f"- Số từ đầu vào đã kiểm thử: {len(test_words)}")
    lines.append(f"- Danh sách từ kiểm thử: {', '.join(test_words)}")
    lines.append("")
    lines.append("4. Kết quả n=3, n=5, n=7")
    lines.append(format_summary_for_terminal(summary_dataframe).to_string(index=False))
    lines.append("")
    lines.append("5. Giá trị n được chọn")
    lines.append(
        f"- Giá trị n phù hợp nhất trong thực nghiệm là {int(best_n_row['n'])}."
    )
    lines.append(
        "- Lý do: có Category Precision trung bình "
        f"{format_percent(float(best_n_row['avg_category_precision']))}, "
        f"MRR-category trung bình {float(best_n_row['avg_mrr_category']):.4f}, "
        f"Mean Distance trung bình {format_distance(float(best_n_row['avg_mean_distance']))}."
    )
    lines.append("")
    lines.append("6. Các trường hợp đặc biệt")
    for result in special_case_results:
        lines.append(
            f"- {result['case']}: input={result['input']}, n={result['n']}, "
            f"số gợi ý={result['suggestion_count']}, "
            f"kỳ vọng={result['expected']}, "
            f"kết quả={'ĐẠT' if result['passed'] else 'KHÔNG ĐẠT'}, "
            f"thời gian={format_ms(float(result['elapsed_ms']))}"
        )
    lines.append("")
    lines.append("7. Thời gian chạy thực nghiệm")
    lines.append(f"- Tổng thời gian chạy: {format_ms(total_elapsed_ms)}")
    lines.append(f"- Thời gian trung bình cho một truy vấn gợi ý: {format_ms(average_query_ms)}")
    lines.append("")
    return "\n".join(lines)


def save_results(
    detail_dataframe: pd.DataFrame,
    summary_dataframe: pd.DataFrame,
    report_text: str,
) -> None:
    """Save experiment outputs to docs/experiment_results."""
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    detail_dataframe.to_csv(DETAIL_PATH, index=False, encoding="utf-8-sig")
    summary_dataframe.to_csv(SUMMARY_PATH, index=False, encoding="utf-8-sig")
    REPORT_PATH.write_text(report_text, encoding="utf-8")


def main() -> None:
    """Run the complete k-NN experiment."""
    total_start = time.perf_counter()

    print("=" * 60)
    print("THỰC NGHIỆM K-NN GỢI Ý TỪ VỰNG")
    print("=" * 60)

    get_related_words = import_knn_function()
    raw_dataframe = load_raw_dataset()
    normalized_dataframe = normalize_dataset(raw_dataframe)
    statistics = build_dataset_statistics(raw_dataframe, normalized_dataframe)

    print_section("1. THỐNG KÊ DỮ LIỆU")
    print_dataset_statistics(statistics)

    test_words = select_test_words(normalized_dataframe)
    lookup = get_input_lookup(normalized_dataframe)
    print()
    print(f"Số từ đầu vào đã chọn để kiểm thử: {len(test_words)}")
    print(f"Danh sách từ kiểm thử: {', '.join(test_words)}")

    print_section("2. KẾT QUẢ CHI TIẾT")
    detail_dataframe, metrics_dataframe, query_times_ms = run_knn_experiment(
        test_words,
        lookup,
        get_related_words,
    )

    summary_dataframe = build_summary(metrics_dataframe)
    best_n_row = choose_best_n(summary_dataframe)

    print_section("3. BẢNG TỔNG HỢP")
    print(format_summary_for_terminal(summary_dataframe).to_string(index=False))

    print_section("4. KIỂM THỬ TRƯỜNG HỢP ĐẶC BIỆT")
    special_case_results = run_special_cases(normalized_dataframe, get_related_words)

    total_elapsed_ms = (time.perf_counter() - total_start) * 1000
    average_query_ms = (
        sum(query_times_ms) / len(query_times_ms) if query_times_ms else 0.0
    )

    print_section("5. KẾT LUẬN")
    print(
        "Giá trị n phù hợp nhất trong thực nghiệm là "
        f"{int(best_n_row['n'])}."
    )
    print(
        "Lý do: Category Precision trung bình = "
        f"{format_percent(float(best_n_row['avg_category_precision']))}, "
        f"MRR-category trung bình = {float(best_n_row['avg_mrr_category']):.4f}, "
        "Mean Distance trung bình = "
        f"{format_distance(float(best_n_row['avg_mean_distance']))}."
    )
    print(f"Tổng thời gian chạy thực nghiệm: {format_ms(total_elapsed_ms)}")
    print(
        "Thời gian trung bình cho một truy vấn gợi ý: "
        f"{format_ms(average_query_ms)}"
    )

    report_text = build_report_text(
        statistics,
        test_words,
        summary_dataframe,
        best_n_row,
        special_case_results,
        total_elapsed_ms,
        average_query_ms,
    )
    save_results(detail_dataframe, summary_dataframe, report_text)

    print_section("6. FILE KẾT QUẢ ĐÃ LƯU")
    print(DETAIL_PATH)
    print(SUMMARY_PATH)
    print(REPORT_PATH)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print()
        print("LỖI KHI CHẠY THỰC NGHIỆM K-NN")
        print("-" * 60)
        print(error)
        raise SystemExit(1) from error
