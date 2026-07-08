import joblib

from ml.evaluate import MODEL_PATH, run

_model = None


def _get_model():
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            _, _model = run()
        else:
            _model = joblib.load(MODEL_PATH)
    return _model


def predict_category(english_word):
    model = _get_model()
    return model.predict([english_word])[0]
