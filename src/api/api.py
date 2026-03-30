import logging
import os

import fastapi
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

from shared.gemini_service import GeminiService
from shared.llm_interface import LLMInterface
from shared.metrics import VERDICT_COUNTER

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = fastapi.FastAPI()
Instrumentator().instrument(app).expose(app)

llm_service: LLMInterface = GeminiService(
    model_name="gemini-3-flash-preview",
    api_key=os.environ.get("GEMINI_API_KEY"),
)


class QuestionRequest(BaseModel):
    question: str


@app.post("/ask")
async def ask(request: QuestionRequest):
    answer = llm_service.send_message(request.question)
    VERDICT_COUNTER.labels(verdict=answer.get("verdict", "unknown")).inc()
    return answer


@app.get("/health")
def health():
    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
