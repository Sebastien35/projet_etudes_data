"""
Singleton service for real-time fake news classification using the trained KMeans model.
Loaded lazily on first call to avoid slow startup.
"""

import logging
import math
import pickle
from pathlib import Path

from shared.embedding_service import encode

logger = logging.getLogger(__name__)

_instance = None

KMEANS_PATH = "data/06_models/kmeans_model.pkl"


def _score_to_verdict(score: float) -> str:
    return f"{int(round(score * 100))}% real"


class KMeansService:
    def __init__(self, kmeans_path: str = KMEANS_PATH):
        if not Path(kmeans_path).exists():
            raise FileNotFoundError(
                f"KMeans model not found at {kmeans_path}. "
                "Run: kedro run --pipeline vectorisation"
            )
        with open(kmeans_path, "rb") as f:
            self._km = pickle.load(f)
        logger.info(f"KMeansService loaded from {kmeans_path}")

    def classify(self, text: str) -> dict:
        vec = encode([text])  # shape (1, embedding_dim)

        label = int(self._km.predict(vec)[0])
        distances = self._km.transform(vec)[0]
        d0, d1 = distances[0], distances[1] if len(distances) > 1 else 0.0

        fake_cluster = getattr(self._km, "fake_cluster_", 0)

        closer = d0 if label == fake_cluster else d1
        farther = d1 if label == fake_cluster else d0
        relative_margin = (farther - closer) / (closer + 1e-8)
        confidence = 1.0 / (1.0 + math.exp(-relative_margin * 20.0))

        score = (1.0 - confidence) if label == fake_cluster else confidence

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
