"""
Singleton service for fake news scoring using the fine-tuned xlm-roberta-base model.
Primary classifier — more accurate than the embedding+LogReg approach when trained data exists.
Returns a probability in [0, 1] — high = reliable (real news), low = unreliable (fake news).
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_instance = None
_load_failed = False

MODEL_PATH = "data/06_models/xlm_roberta_finetuned"


class FinetunedService:
    def __init__(self, model_path: str = MODEL_PATH):
        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"Fine-tuned model not found at {model_path}. "
                "Run: kedro run --pipeline train_finetuned"
            )

        # Imported here to avoid loading torch at API startup when model doesn't exist
        import torch  # noqa: PLC0415
        from transformers import (  # noqa: PLC0415
            AutoModelForSequenceClassification,
            AutoTokenizer,
        )

        try:
            self._tokenizer = AutoTokenizer.from_pretrained(model_path)
            self._model = AutoModelForSequenceClassification.from_pretrained(model_path)
        except Exception as e:
            raise FileNotFoundError(
                f"Fine-tuned model at {model_path} failed to load: {e}"
            ) from e
        self._model.eval()
        self._torch = torch
        logger.info(f"FinetunedService loaded from {model_path}")

    def classify(self, text: str) -> dict:
        inputs = self._tokenizer(
            text, return_tensors="pt", truncation=True, max_length=128, padding=True
        )
        with self._torch.no_grad():
            logits = self._model(**inputs).logits
        probs = self._torch.softmax(logits, dim=-1)[0]
        prob_real = float(probs[1])

        return {
            "verdict": f"{int(round(prob_real * 100))}% real",
            "probability": round(prob_real, 4),
            "based_on": "xlm_roberta_finetuned",
        }


def get_finetuned_service() -> FinetunedService:
    """Return the global FinetunedService singleton (lazy-loaded)."""
    global _instance, _load_failed
    if _load_failed:
        raise FileNotFoundError(
            "Fine-tuned model unavailable (failed to load at startup)."
        )
    if _instance is None:
        try:
            _instance = FinetunedService()
        except FileNotFoundError:
            _load_failed = True
            raise
    return _instance
