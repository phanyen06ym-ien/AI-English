from sklearn.feature_extraction.text import TfidfVectorizer


def build_vectorizer():
    return TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
