from collections import Counter

from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline

from ml.features import build_vectorizer


class KMeansCategoryClassifier(BaseEstimator, ClassifierMixin):
    """Clusters words with K-means, then labels each cluster with the
    majority category among the training words assigned to it."""

    def __init__(self, n_clusters=None, random_state=42):
        self.n_clusters = n_clusters
        self.random_state = random_state

    def fit(self, X, y):
        y = list(y)
        n_clusters = min(self.n_clusters or len(set(y)), len(y))

        self.kmeans_ = KMeans(n_clusters=n_clusters, random_state=self.random_state, n_init=10)
        clusters = self.kmeans_.fit_predict(X)

        self.cluster_to_label_ = {
            cluster_id: Counter(
                label for label, c in zip(y, clusters) if c == cluster_id
            ).most_common(1)[0][0]
            for cluster_id in set(clusters)
        }
        return self

    def predict(self, X):
        clusters = self.kmeans_.predict(X)
        return [self.cluster_to_label_[c] for c in clusters]


def build_pipeline(n_clusters=None):
    return Pipeline([
        ("tfidf", build_vectorizer()),
        ("clf", KMeansCategoryClassifier(n_clusters=n_clusters)),
    ])
