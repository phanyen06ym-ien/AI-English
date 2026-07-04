from detection.detector import detect
from dataset.object_mapping import OBJECT_MAPPING

results = detect("dataset/images/book.jpg")

for obj in results:
    english = obj["english"]
    vietnamese = OBJECT_MAPPING.get(english, english)

    print(f"{english} -> {vietnamese} ({obj['confidence']:.2f})")