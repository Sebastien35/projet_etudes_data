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
        pct = int(round(probability * 100))

        prompt = f"""RULE #1 — LANGUAGE: You MUST write your entire response in the same language as the CLAIM below. If the claim is in French, respond in French. If it is in Spanish, respond in Spanish. Never switch to English.

You are a fact-checker assistant.
A KMeans + Ollama (llama3.2:3b) pipeline assigned {pct}% likelihood of being real information to the following claim.

In 2-3 sentences, explain what signals in the claim support this classification.
Be factual and concise. Do not repeat the percentage.

CLAIM: {claim}

Explanation (in the same language as the CLAIM):"""

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
