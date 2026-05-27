import logging

logger = logging.getLogger(__name__)

_instance = None
MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"


class EmotionInferenceService:
    def __init__(self):
        from transformers import pipeline as hf_pipeline

        logger.info(f"[emotion-rt] Loading model {MODEL_NAME} …")
        self._classifier = hf_pipeline(
            "text-classification",
            model=MODEL_NAME,
            top_k=None,
            truncation=True,
            max_length=128,
            device=-1,
        )
        logger.info("[emotion-rt] Model ready.")

    def classify(self, text: str) -> list[dict]:
        """Return all emotion scores sorted by confidence descending."""
        predictions = self._classifier([text])[0]
        return sorted(
            [
                {"emotion": p["label"].lower(), "score": round(p["score"], 4)}
                for p in predictions
            ],
            key=lambda x: x["score"],
            reverse=True,
        )


def get_emotion_inference_service() -> EmotionInferenceService:
    global _instance
    if _instance is None:
        _instance = EmotionInferenceService()
    return _instance
