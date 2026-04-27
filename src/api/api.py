import logging
import os

import fastapi
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

from shared.claude_service import ClaudeService
from shared.kmeans_service import get_kmeans_service
from shared.metrics import VERDICT_COUNTER

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = fastapi.FastAPI()
Instrumentator().instrument(app).expose(app)

claude_service = ClaudeService()


class QuestionRequest(BaseModel):
    question: str


@app.post("/ask")
async def ask(request: QuestionRequest):
    # 1. KMeans — primary classifier
    result = get_kmeans_service().classify(request.question)

    # 2. Claude — natural language explanation (best-effort)
    try:
        result["explanation"] = await claude_service.explain(
            claim=request.question,
            verdict=result["verdict"],
            probability=result["probability"],
        )
    except Exception as e:
        logger.warning(f"Claude explanation failed: {e}")
        result["explanation"] = ""

    VERDICT_COUNTER.labels(verdict=result["verdict"]).inc()
    return result


@app.get("/health")
def health():
    return "OK"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
