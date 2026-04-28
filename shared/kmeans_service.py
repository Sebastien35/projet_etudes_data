"""
Singleton service for real-time fake news classification using the trained KMeans model.
Loaded lazily on first call to avoid slow startup.
"""

import logging
import pickle
import re
import string
import unicodedata
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

_instance = None

VECTORIZER_PATH = "data/06_models/tfidf_vectorizer.pkl"
KMEANS_PATH = "data/06_models/kmeans_model.pkl"


def _score_to_verdict(score: float) -> str:
    if score >= 0.8:
        return "true"
    if score >= 0.6:
        return "very likely true"
    if score >= 0.4:
        return "uncertain"
    if score >= 0.2:
        return "very likely false"
    return "false"


class KMeansService:
    def __init__(self, vectorizer_path: str = VECTORIZER_PATH, kmeans_path: str = KMEANS_PATH):
        if not Path(vectorizer_path).exists():
            raise FileNotFoundError(
                f"TF-IDF vectorizer not found at {vectorizer_path}. "
                "Run: kedro run --pipeline vectorisation"
            )
        if not Path(kmeans_path).exists():
            raise FileNotFoundError(
                f"KMeans model not found at {kmeans_path}. "
                "Run: kedro run --pipeline vectorisation"
            )
        with open(vectorizer_path, "rb") as f:
            self._vectorizer = pickle.load(f)
        with open(kmeans_path, "rb") as f:
            self._km = pickle.load(f)
        logger.info(f"KMeansService loaded from {vectorizer_path} + {kmeans_path}")

    def _preprocess(self, text: str) -> str:
        text = str(text).lower()
        text = re.sub(r"http\S+|www\S+", "", text)
        text = re.sub(r"@\w+", "", text)
        text = re.sub(r"#\w+", "", text)
        text = re.sub(
            "[\U0001f600-\U0001f64f\U0001f300-\U0001f5ff"
            "\U0001f680-\U0001f6ff\U0001f1e0-\U0001f1ff]+",
            "",
            text,
            flags=re.UNICODE,
        )
        text = text.translate(str.maketrans("", "", string.punctuation))
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("utf-8")
        return re.sub(r"\s+", " ", text).strip()

    def classify(self, text: str) -> dict:
        cleaned = self._preprocess(text)
        vec = self._vectorizer.transform([cleaned])

        if vec.nnz == 0:
            # No vocabulary overlap with training data — distances are constant
            return {
                "verdict": "uncertain",
                "probability": 0.5,
                "based_on": "kmeans",
                "cluster": -1,
            }

        label = int(self._km.predict(vec)[0])

        distances = self._km.transform(vec)[0]
        d0, d1 = distances[0], distances[1] if len(distances) > 1 else 0.0
        score = float(d0 / (d0 + d1 + 1e-8))

        return {
            "verdict": _score_to_verdict(score),
            "probability": round(score, 4),
            "based_on": "kmeans",
            "cluster": label,
        }


def get_kmeans_service() -> KMeansService:
    """Return the global KMeansService singleton (lazy-loaded)."""
    global _instance
    if _instance is None:
        _instance = KMeansService()
    return _instance
