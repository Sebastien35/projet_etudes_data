import logging
import time

from dotenv import load_dotenv
from google import genai

from shared.llm_interface import LLMInterface
from shared.metrics import LLM_LATENCY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("shared.gemini_service")

load_dotenv()


class GeminiService(LLMInterface):
    def __init__(self, model_name: str, api_key: str):
        super().__init__(model_name, api_key)
        self.client = genai.Client(api_key=api_key)
        self.model = model_name

    def explain(self, claim: str, verdict: str, probability: float) -> str:
        """
        Ask Gemini to explain why a claim was classified with a given verdict.
        Returns a plain-text explanation (2-3 sentences).
        """
        MIN = 0.5
        is_real = probability >= MIN
        confidence_pct = (
            int(probability * 100) if is_real else int((1 - probability) * 100)
        )
        label = "real news" if is_real else "fake news"

        prompt = f"""You are a fact-checker assistant.
A KMeans + Ollama (llama3.2:3b) pipeline classified the following claim as {label.upper()} with {confidence_pct}% confidence (verdict: "{verdict}").

In 2-3 sentences, explain what signals in the claim support this classification.
Be factual and concise. Do not repeat the verdict label.

CLAIM: {claim}

Explanation:"""

        start = time.perf_counter()
        response = self.client.models.generate_content(
            model=self.model, contents=prompt
        )
        LLM_LATENCY.observe(time.perf_counter() - start)
        logger.info(
            f"Gemini explanation generated in {time.perf_counter() - start:.2f}s"
        )
        return response.text.strip()

    # kept for backward compatibility — not used by the API anymore
    def send_message(self, claim: str) -> dict:
        explanation = self.explain(claim, verdict="uncertain", probability=0.5)
        return {
            "verdict": "uncertain",
            "probability": 0.5,
            "explanation": explanation,
            "based_on": "gemini",
        }
