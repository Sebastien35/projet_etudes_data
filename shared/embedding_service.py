import logging
import os

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.getenv(
    "EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2"
)

_model = None
_model_name = None

class ProbabilityScoreModel:
    """Modèle de seuils pour les scores de probabilité (Évite les magic values)."""
    likely: float = 0.60    # Seuil pour la couleur de succès (Anciennement 0.6)
    probable: float = 0.40  # Seuil pour la couleur d'avertissement (Anciennement 0.4)
    possible: float = 0.20


def get_embedding_model(model_name: str = DEFAULT_MODEL):
    global _model, _model_name
    if _model is None or _model_name != model_name:

        logger.info(f"Loading SentenceTransformer: {model_name}")
        _model = SentenceTransformer(model_name)
        _model_name = model_name
    return _model


def encode(texts: list[str], model_name: str = DEFAULT_MODEL) -> np.ndarray:
    """Return L2-normalised sentence embeddings for a list of texts."""
    return get_embedding_model(model_name).encode(
        texts,
        show_progress_bar=False,
        normalize_embeddings=True,
        batch_size=64,
    )
