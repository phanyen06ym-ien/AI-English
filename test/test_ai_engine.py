from __future__ import annotations

import unittest

from ai.pipeline import AIEngine


class FakeDetector:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail

    def detect(self, frame):
        if self.should_fail:
            raise RuntimeError("detector failed")
        return [
            {
                "class_name": "laptop",
                "confidence": 0.93,
                "box": (1, 2, 30, 40),
            }
        ]


def fake_classifier(word: str) -> dict:
    return {
        "english": word,
        "vietnamese": "May tinh xach tay",
        "category": "Technology",
        "level": "Medium",
        "source": "lookup",
    }


def fake_related_words(word: str, n: int) -> list[dict]:
    return [
        {
            "english": "mouse",
            "vietnamese": "Chuot may tinh",
            "category": "Technology",
            "level": "Medium",
            "distance": 0.2,
        }
    ][:n]


def fake_cluster_words(word: str) -> list[dict]:
    return [
        {
            "english": "keyboard",
            "vietnamese": "Ban phim",
            "category": "Technology",
            "level": "Medium",
            "cluster": 0,
        }
    ]


def fake_vocabulary() -> dict:
    return {
        "laptop": {
            "english": "laptop",
            "vietnamese": "May tinh xach tay",
            "category": "Technology",
            "level": "Medium",
        }
    }


def build_engine(detector=None) -> AIEngine:
    return AIEngine(
        detector=detector or FakeDetector(),
        classifier=fake_classifier,
        related_words_provider=fake_related_words,
        cluster_words_provider=fake_cluster_words,
        vocabulary_provider=fake_vocabulary,
    )


def failing_related_words(word: str, n: int) -> list[dict]:
    raise AssertionError("KNN should not run")


def failing_cluster_words(word: str) -> list[dict]:
    raise AssertionError("KMeans should not run")


class AIEngineTest(unittest.TestCase):
    def test_detect_objects(self) -> None:
        engine = build_engine()

        objects, elapsed_ms = engine.detect_objects(frame=object())

        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0].class_name, "laptop")
        self.assertEqual(objects[0].box, (1, 2, 30, 40))
        self.assertGreaterEqual(elapsed_ms, 0.0)

    def test_related_words(self) -> None:
        engine = build_engine()

        words = engine.get_related_words("laptop", n=3)

        self.assertEqual(len(words), 1)
        self.assertEqual(words[0].english, "mouse")
        self.assertEqual(words[0].category, "Technology")

    def test_cluster_words(self) -> None:
        engine = build_engine()

        words = engine.get_cluster_words("laptop")

        self.assertEqual(len(words), 1)
        self.assertEqual(words[0].english, "keyboard")
        self.assertEqual(words[0].cluster, 0)

    def test_pipeline_success_and_timing(self) -> None:
        engine = build_engine()

        result = engine.analyze_frame(frame=object())

        self.assertTrue(result.success)
        self.assertEqual(result.error_code, None)
        self.assertEqual(result.detections[0].english, "laptop")
        self.assertEqual(result.related_words[0].english, "mouse")
        self.assertEqual(result.cluster_words[0].english, "keyboard")
        self.assertGreaterEqual(result.timing.yolo_ms, 0.0)
        self.assertGreaterEqual(result.timing.vocabulary_ms, 0.0)
        self.assertGreaterEqual(result.timing.knn_ms, 0.0)
        self.assertGreaterEqual(result.timing.kmeans_ms, 0.0)
        self.assertGreaterEqual(result.timing.pipeline_ms, 0.0)

    def test_pipeline_can_skip_learning_steps(self) -> None:
        engine = AIEngine(
            detector=FakeDetector(),
            classifier=fake_classifier,
            related_words_provider=failing_related_words,
            cluster_words_provider=failing_cluster_words,
            vocabulary_provider=fake_vocabulary,
        )

        result = engine.analyze_frame(
            frame=object(),
            include_learning=False,
        )

        self.assertTrue(result.success)
        self.assertEqual(len(result.detections), 1)
        self.assertEqual(result.related_words, [])
        self.assertEqual(result.cluster_words, [])

    def test_pipeline_error_handling(self) -> None:
        engine = build_engine(FakeDetector(should_fail=True))

        with self.assertLogs("ai.pipeline", level="ERROR"):
            result = engine.analyze_frame(frame=object())

        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "AI_PIPELINE_ERROR")
        self.assertIn("detector failed", result.message)
        self.assertIsNotNone(result.exception)

    def test_regression_output_matches_old_formatting(self) -> None:
        engine = build_engine()

        result = engine.analyze_frame(frame=object())
        detection = result.detections_as_dicts()[0]

        self.assertEqual(
            detection,
            {
                "english": "laptop",
                "vietnamese": "May tinh xach tay",
                "category": "Technology",
                "level": "Medium",
                "confidence": 0.93,
                "text": (
                    "laptop - May tinh xach tay "
                    "[Technology - Medium] (0.93)"
                ),
                "box": (1, 2, 30, 40),
            },
        )


if __name__ == "__main__":
    unittest.main()
