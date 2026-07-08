# ml/bayes.py
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import CountVectorizer

class VocabularyClassifier:
    def __init__(self):
        self.model = MultinomialNB()
        self.vectorizer = CountVectorizer()
        # Dữ liệu huấn luyện
        self.words = ["cat", "dog", "apple", "beautiful", "sophisticated", "mitigate"]
        self.labels = ["A1", "A1", "A1", "B2", "C2", "C2"]

    def train(self):
        X = self.vectorizer.fit_transform(self.words)
        self.model.fit(X, self.labels)

    def predict(self, word):
        X = self.vectorizer.transform([word])
        return self.model.predict(X)[0]

