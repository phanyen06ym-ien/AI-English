# AI-English

AI-English is a desktop application for learning English vocabulary through
object detection. The system combines YOLO object detection, vocabulary mapping,
k-NN related-word recommendation, K-Means vocabulary clustering, a PySide6 GUI,
and PostgreSQL history storage.

## Main Features

- Detect objects from images and webcam frames.
- Map detected objects to English/Vietnamese vocabulary.
- Recommend related words with k-NN.
- Cluster vocabulary topics with K-Means.
- Store and display detection history from PostgreSQL.
- Provide GUI pages for home, webcam, image detection, vocabulary, history, and
  statistics.

## Project Structure

- `main.py`: application entry point.
- `ai/`, `ml/`, `detection/`: AI and machine learning logic.
- `ui/`: PySide6/QML user interface.
- `database/`: PostgreSQL connection and repositories.
- `dataset/`: vocabulary, object mapping, and test images.
- `models/`: YOLO, k-NN, K-Means, and category model artifacts.
- `test/`: automated and manual tests.
- `docs/`: documentation and archived report material.

## Setup

Use Python 3.11.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

For development and tests:

```powershell
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
```

Database credentials are read from environment variables. Copy `.env.example` to
`.env` for local development, then fill in the PostgreSQL values.

## Run

```powershell
python main.py
```

If a virtual environment is active:

```powershell
.\.venv\Scripts\python main.py
```

## Test

```powershell
python test/run_tests.py --unittest
```

List available automated and manual tests:

```powershell
python test/run_tests.py --list
```

## Demo Notes

- Required model files are in `models/`.
- Vocabulary contains 48 words in `dataset/vocabulary.csv`.
- Latest experiment evidence is archived under `docs/archive/report_package/`.
- Do not commit `.env`, `.venv`, logs, generated reports, or cache folders.

## License

This project is released under the MIT License. See `LICENSE`.
