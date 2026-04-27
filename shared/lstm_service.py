"""
Singleton service for real-time fake news classification using the trained LSTM.
Loaded lazily on first call to avoid slow startup.
"""

import logging
import pickle
import re
from pathlib import Path

from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences

logger = logging.getLogger(__name__)

_instance = None

MODEL_PATH = "data/06_models/lstm_model.keras"
TOKENIZER_PATH = "data/06_models/lstm_tokenizer.pkl"
MAX_LEN = 200


def _prob_to_verdict(prob: float) -> str:
    if prob >= 0.8:
        return "true"
    if prob >= 0.6:
        return "very likely true"
    if prob >= 0.4:
        return "uncertain"
    if prob >= 0.2:
        return "very likely false"
    return "false"


class LSTMService:
    def __init__(self, model_path: str = MODEL_PATH, tokenizer_path: str = TOKENIZER_PATH, max_len: int = MAX_LEN):
        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"LSTM model not found at {model_path}. "
                "Run: kedro run --pipeline model_training"
            )
        self._model = load_model(model_path)
        with open(tokenizer_path, "rb") as f:
            self._tokenizer = pickle.load(f)
        self._max_len = max_len
        logger.info(f"LSTMService loaded model from {model_path}")

    def _preprocess(self, text: str) -> str:
        text = str(text).lower()
        text = re.sub(r"http\S+|www\S+", "", text)
        text = re.sub(r"[^a-z\s]", "", text)
        return re.sub(r"\s+", " ", text).strip()

    def classify(self, text: str) -> dict:
        cleaned = self._preprocess(text)
        seq = self._tokenizer.texts_to_sequences([cleaned])
        padded = pad_sequences(seq, maxlen=self._max_len, padding="post", truncating="post")
        prob = float(self._model.predict(padded, verbose=0).flatten()[0])
        return {
            "verdict": _prob_to_verdict(prob),
            "probability": round(prob, 4),
            "based_on": "lstm",
        }


def get_lstm_service() -> LSTMService:
    """Return the global LSTMService singleton (lazy-loaded)."""
    global _instance
    if _instance is None:
        _instance = LSTMService()
    return _instance
