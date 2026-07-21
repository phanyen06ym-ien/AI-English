from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.knn import get_related_words  # noqa: E402


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def print_related_words(word: str) -> None:
    print(f"Tu lien quan voi {word}:")
    related_words = get_related_words(word, n=3)

    if not related_words:
        print("[]")
        return

    for item in related_words:
        print(item["english"])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test k-NN related word suggestions.",
    )
    parser.add_argument(
        "words",
        nargs="*",
        default=["laptop"],
        help="Words to test. Default: laptop",
    )
    args = parser.parse_args()

    for word in args.words:
        print_related_words(word)


if __name__ == "__main__":
    main()
