from dataset.vocabulary import get_word_info
from ml.category_predictor import predict_category


def classify_word(english_name):
    info = get_word_info(english_name)

    if info:
        return {
            "english": english_name,
            "vietnamese": info["vietnamese"],
            "category": info["category"],
            "level": info["level"],
            "source": "lookup",
        }

    return {
        "english": english_name,
        "vietnamese": None,
        "category": predict_category(english_name),
        "level": None,
        "source": "ml",
    }