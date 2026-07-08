from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline

from ml.features import build_vectorizer


def build_pipeline(n_neighbors=3):
    return Pipeline([
        ("tfidf", build_vectorizer()),
        ("clf", KNeighborsClassifier(n_neighbors=n_neighbors)),
    ])
