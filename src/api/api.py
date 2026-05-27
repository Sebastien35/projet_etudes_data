import logging

import fastapi
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

from shared.emotion_inference_service import get_emotion_inference_service
from shared.kmeans_service import get_kmeans_service
from shared.metrics import VERDICT_COUNTER
from shared.ollama_service import OllamaService
from shared.reliability_service import get_reliability_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = fastapi.FastAPI()
Instrumentator().instrument(app).expose(app)

ollama_service = OllamaService()


class QuestionRequest(BaseModel):
    question: str


class EmotionRequest(BaseModel):
    text: str


class ProbabilityScoreModel:
    """Modèle de seuils pour les scores de probabilité (Évite les magic values)."""
    likely: float = 0.60    # Seuil pour la couleur de succès (Anciennement 0.6)
    probable: float = 0.40  # Seuil pour la couleur d'avertissement (Anciennement 0.4)
    possible: float = 0.20

@app.post("/ask")
async def ask(request: QuestionRequest):
    # 1. Reliability classifier — primary scorer (supervised, trained on trusted outlets)
    try:
        result = get_reliability_service().classify(request.question)
    except FileNotFoundError:
        logger.warning(
            "Reliability model not found — falling back to KMeans. "
            "Run: kedro run --pipeline train_reliability"
        )
        result = get_kmeans_service().classify(request.question)

    prob = result["probability"]
    result["label"] =   "true" if prob >= ProbabilityScoreModel.likely else (
        "very likely true" if prob >= ProbabilityScoreModel.probable else (
            "uncertain" if prob >= ProbabilityScoreModel.possible else (
                "very likely false" if prob > 0 else "false"
            )
        )
    )
    result["score_pct"] = int(round(prob * 100))

    # 2. Ollama — natural language explanation (best-effort)
    try:
        result["explanation"] = await ollama_service.explain(
            claim=request.question,
            verdict=result["verdict"],
            probability=prob,
        )
    except Exception as e:
        logger.warning(f"Ollama explanation failed: {e}")
        result["explanation"] = ""

    VERDICT_COUNTER.labels(verdict=result["label"]).inc()
    return result


@app.post("/emotion")
async def analyze_emotion(request: EmotionRequest):
    try:
        scores = get_emotion_inference_service().classify(request.text)
        return {"emotions": scores}
    except Exception as e:
        logger.warning(f"Emotion analysis failed: {e}")
        raise fastapi.HTTPException(status_code=500, detail="Emotion analysis unavailable")


@app.get("/health")
def health():
    return "OK"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
