import fastapi
import os
from shared.llm_interface import LLMInterface
from shared.gemini_service import GeminiService
from pydantic import BaseModel
import json


app = fastapi.FastAPI()
llm_service: LLMInterface = GeminiService(model_name="gemini-3-flash-preview", api_key=os.environ.get("GEMINI_API_KEY"))

class QuestionRequest(BaseModel):
    question: str

@app.post("/ask")
def ask(request: QuestionRequest):
    answer = llm_service.send_message(request.question)
    return {"answer": answer}


@app.route("/health", methods=["GET"])
def health():
    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
