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
        pct = int(round(probability * 100))
        tone = "reliable" if pct >= 50 else "potentially misleading"

        system = (
            "RULE #1 — LANGUAGE: Detect the language of the TEXT and write your entire response in that exact language. "
            "Never default to English if the text is in another language. "
            "You are a media literacy assistant helping everyday readers understand why a piece of text "
            "reads as credible or suspicious. "
            "Base your explanation only on observable features of the writing: tone, word choice, "
            "emotional language, hedging, sensationalism, structure. "
            "Do NOT judge whether the claim is factually true or false. "
            "Do NOT refuse based on the topic. "
            "Write exactly 2-3 short sentences. Use plain language — no technical terms."
        )
        user = (
            f"This text was rated {pct}% likely to be real information — it reads as {tone}.\n\n"
            "In 2-3 sentences, explain what features of the writing style led to this rating. "
            "Focus on tone, word choice, and how the information is presented. "
            "Do not repeat the score. "
            "IMPORTANT: respond in the same language as the TEXT below.\n\n"
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
