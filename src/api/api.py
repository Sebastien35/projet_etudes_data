import logging

import fastapi
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

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


def _reliability_label(probability: float) -> str:
    if probability >= 0.75:
        return "Likely reliable"
    if probability >= 0.50:
        return "Possibly reliable"
    if probability >= 0.25:
        return "Possibly misleading"
    return "Likely misleading"


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
    result["label"] = _reliability_label(prob)
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


@app.get("/health")
def health():
    return "OK"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
