from pathlib import Path

import joblib
from sklearn.model_selection import KFold, cross_val_score

from dataset.vocabulary import all_words
from ml.bayes import build_pipeline as build_bayes
from ml.knn import build_pipeline as build_knn
from ml.kmeans import build_pipeline as build_kmeans

MODEL_PATH = Path(__file__).parent.parent / "model" / "word_category_model.joblib"

ALGORITHMS = {
    "bayes": build_bayes,
    "knn": build_knn,
    "kmeans": build_kmeans,
}


def load_training_data():
    words = all_words()
    X = list(words.keys())
    y = [row["category"] for row in words.values()]
    return X, y


def compare_algorithms(X, y):
    # Dataset is tiny (a few words per category), so a plain shuffled KFold
    # is used instead of stratified CV to avoid failing on rare classes.
    # Accuracy numbers here are indicative only, not statistically reliable.
    cv = KFold(n_splits=min(3, len(X)), shuffle=True, random_state=42)
    scores = {}
    for name, builder in ALGORITHMS.items():
        pipeline = builder()
        result = cross_val_score(pipeline, X, y, cv=cv, scoring="accuracy")
        scores[name] = result.mean()
    return scores


def train_best_model(X, y, scores):
    best_name = max(scores, key=scores.get)
    best_pipeline = ALGORITHMS[best_name]()
    best_pipeline.fit(X, y)
    return best_name, best_pipeline


def run():
    X, y = load_training_data()
    scores = compare_algorithms(X, y)

    print("So sánh độ chính xác (cross-validation, dữ liệu nhỏ nên chỉ mang tính tham khảo):")
    for name, acc in sorted(scores.items(), key=lambda item: -item[1]):
        print(f"  {name}: {acc:.2f}")

    best_name, best_pipeline = train_best_model(X, y, scores)
    print(f"Chọn thuật toán tốt nhất: {best_name}")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_pipeline, MODEL_PATH)
    print(f"Đã lưu model vào {MODEL_PATH}")

    return best_name, best_pipeline


if __name__ == "__main__":
    from utils.console import use_utf8_console

    use_utf8_console()
    run()
