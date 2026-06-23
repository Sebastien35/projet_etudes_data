"""
Singleton service for reliability scoring using the supervised LogisticRegression model.
Returns a probability in [0, 1] — high = reliable (real news), low = unreliable (fake news).
Trained on trusted-outlet posts (label=1) vs misinformation posts (label=0).
Features: MiniLM sentence embeddings + 5 stylometric features.
"""

import logging
import pickle
from pathlib import Path

import numpy as np

from shared.embedding_service import encode, extract_style_features

logger = logging.getLogger(__name__)

_instance = None

CLASSIFIER_PATH = "data/06_models/reliability_classifier.pkl"


class ReliabilityService:
    def __init__(self, classifier_path: str = CLASSIFIER_PATH):
        if not Path(classifier_path).exists():
            raise FileNotFoundError(
                f"Reliability classifier not found at {classifier_path}. "
                "Run: kedro run --pipeline train_reliability"
            )
        with open(classifier_path, "rb") as f:
            self._clf = pickle.load(f)
        logger.info(f"ReliabilityService loaded from {classifier_path}")

    def classify(self, text: str) -> dict:
        emb = encode([text])
        style = np.array([extract_style_features(text)], dtype=float)
        X = np.hstack([emb, style])
        prob_real = float(self._clf.predict_proba(X)[0][1])
        verdict = f"{int(round(prob_real * 100))}% real"

        return {
            "verdict": verdict,
            "probability": round(prob_real, 4),
            "based_on": "reliability_classifier",
        }


def get_reliability_service() -> ReliabilityService:
    """Return the global ReliabilityService singleton (lazy-loaded)."""
    global _instance
    if _instance is None:
        _instance = ReliabilityService()
    return _instance
