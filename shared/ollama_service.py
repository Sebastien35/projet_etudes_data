import logging
import os
import time

import httpx

from shared.llm_interface import LLMInterface
from shared.metrics import LLM_LATENCY

logger = logging.getLogger("shared.ollama_service")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")


class OllamaService(LLMInterface):
    def __init__(self):
        super().__init__(model_name=OLLAMA_MODEL, api_key=None)
        self._url = f"{OLLAMA_HOST}/api/chat"
        logger.info(f"OllamaService targeting {self._url} with model {self.model_name}")

    async def explain(self, claim: str, verdict: str, probability: float) -> str:
        MIN_PROBABILITY = 0.5
        is_real = probability >= MIN_PROBABILITY
        confidence_pct = (
            int(probability * 100) if is_real else int((1 - probability) * 100)
        )
        label = "real news" if is_real else "fake news"

        system = (
            "You are a machine learning interpretability assistant. "
            "Your sole task is to explain why a text classifier assigned a label to a piece of text, "
            "based purely on observable linguistic and structural features "
            "(e.g. emotional tone, hedging words, sensationalist language, source cues, syntax). "
            "Do NOT comment on the factual truth of the claim. "
            "Do NOT refuse based on the subject matter. "
            "Always respond with exactly 2-3 sentences of technical analysis."
        )
        user = (
            f"A KMeans text classifier labeled the following input as {label.upper()} "
            f'with {confidence_pct}% confidence (verdict: "{verdict}").\n\n'
            "Identify 2-3 linguistic or structural features in the text that likely drove this classification. "
            "Be concise and technical. Do not repeat the verdict.\n\n"
            f"TEXT: {claim}"
        )

        start = time.perf_counter()
        # CPU inference can take 2-3 min on first call (model warm-up + generation)
        async with httpx.AsyncClient(timeout=300.0) as client:
            logger.info(f"Sending request to Ollama ({self.model_name})…")
            response = await client.post(
                self._url,
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()

        elapsed = time.perf_counter() - start
        LLM_LATENCY.observe(elapsed)

        result = data["message"]["content"]
        logger.info(f"Ollama explanation in {elapsed:.2f}s: {result[:80]}…")
        return result.strip()
