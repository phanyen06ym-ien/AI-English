import os
import glob
import numpy as np
from PIL import Image, ImageEnhance
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from dataset.object_mapping import OBJECT_MAPPING

DATASET_DIR = os.path.join(os.path.dirname(__file__), "..", "dataset", "images")
IMG_SIZE = (64, 64)
N_AUGMENT = 30

def extract_features(img: Image.Image) -> np.ndarray:

    img = img.convert("RGB").resize(IMG_SIZE)
    hsv = np.array(img.convert("HSV"))

    features = []
    for channel in range(3):  # H, S, V
        hist, _ = np.histogram(hsv[:, :, channel], bins=16, range=(0, 255))
        hist = hist.astype("float32")
        hist /= (hist.sum() + 1e-6)  # chuan hoa ve ty le (0..1)
        features.extend(hist)

    return np.array(features)

def augment_image(img: Image.Image, n: int) -> list:

    variants = []
    rng = np.random.default_rng(42)

    for i in range(n):
        im = img.copy()

        if rng.random() < 0.5:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)

        angle = rng.uniform(-15, 15)
        im = im.rotate(angle, fillcolor=(255, 255, 255))

        brightness = rng.uniform(0.7, 1.3)
        im = ImageEnhance.Brightness(im).enhance(brightness)

        contrast = rng.uniform(0.8, 1.2)
        im = ImageEnhance.Contrast(im).enhance(contrast)

        variants.append(im)

    return variants

def load_dataset():

    X, y = [], []

    class_dirs = sorted(glob.glob(os.path.join(DATASET_DIR, "*")))
    if not class_dirs:
        raise RuntimeError(f"Khong tim thay du lieu trong {DATASET_DIR}")

    for class_dir in class_dirs:
        class_name = os.path.basename(class_dir)
        image_paths = glob.glob(os.path.join(class_dir, "*.jpg")) + \
                      glob.glob(os.path.join(class_dir, "*.png"))

        for path in image_paths:
            original = Image.open(path)

            # anh goc cung tinh la 1 mau
            X.append(extract_features(original))
            y.append(class_name)

            # sinh them cac ban augmentation
            for variant in augment_image(original, N_AUGMENT):
                X.append(extract_features(variant))
                y.append(class_name)

        print(f"  Lop '{class_name}': {len(image_paths)} anh goc "
              f"-> {len(image_paths) * (N_AUGMENT + 1)} mau sau augmentation")

    return np.array(X), np.array(y)


def train_and_evaluate(k: int = 5):
    print(f"Dang tai du lieu tu: {DATASET_DIR}")
    X, y = load_dataset()
    print(f"\nTong so mau: {len(X)}  |  So lop: {len(set(y))}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    knn = KNeighborsClassifier(n_neighbors=k, metric="euclidean")
    knn.fit(X_train, y_train)

    y_pred = knn.predict(X_test)

    print(f"\n===== KET QUA VOI K={k} =====")
    print(f"Do chinh xac (Accuracy): {accuracy_score(y_test, y_pred):.2f}")
    print("\nBao cao chi tiet theo tung lop:")
    print(classification_report(y_test, y_pred, zero_division=0))
    print("Ma tran nham lan (confusion matrix), thu tu lop:", sorted(set(y)))
    print(confusion_matrix(y_test, y_pred, labels=sorted(set(y))))

    return knn

def predict_image(knn_model, image_path: str):

    img = Image.open(image_path)
    feat = extract_features(img).reshape(1, -1)

    predicted_class = knn_model.predict(feat)[0]
    distances, _ = knn_model.kneighbors(feat)
    vietnamese = OBJECT_MAPPING.get(predicted_class, predicted_class)

    print(f"\nAnh: {image_path}")
    print(f"Du doan (kNN): {predicted_class} -> {vietnamese}")
    print(f"Khoang cach toi {knn_model.n_neighbors} lang gieng gan nhat: "
          f"{distances[0].round(3)}")

    return predicted_class, vietnamese


if __name__ == "__main__":
    model = train_and_evaluate(k=5)

    # Thu du doan lai chinh 1 anh goc trong dataset de minh hoa
    sample_path = glob.glob(os.path.join(DATASET_DIR, "cup", "*.jpg"))[0]
    predict_image(model, sample_path)