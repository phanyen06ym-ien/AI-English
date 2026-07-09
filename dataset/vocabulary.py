import csv
from pathlib import Path

_CSV_PATH = Path(__file__).parent / "vocabulary.csv"
_cache = None


def _load():
    global _cache
    if _cache is None:
        with open(_CSV_PATH, encoding="utf-8") as f:
            _cache = {row["english"]: row for row in csv.DictReader(f)}
    return _cache


def get_word_info(english_name):
    return _load().get(english_name)


def all_words():
    return _load()
