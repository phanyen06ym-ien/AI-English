from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from ml.features import build_vectorizer


def build_pipeline():
    return Pipeline([
        ("tfidf", build_vectorizer()),
        ("clf", MultinomialNB()),
    ])
