import logging
import time

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from shared.llm_interface import LLMInterface
from shared.metrics import LLM_LATENCY

logger = logging.getLogger("shared.claude_service")


class ClaudeService(LLMInterface):
    def __init__(self):
        super().__init__(model_name="claude-opus-4-6", api_key=None)

    async def explain(self, claim: str, verdict: str, probability: float) -> str:
        MIN = 0.5
        is_real = probability >= MIN
        confidence_pct = (
            int(probability * 100) if is_real else int((1 - probability) * 100)
        )
        label = "real news" if is_real else "fake news"

        prompt = (
            f"A KMeans clustering model classified the following claim as {label.upper()} "
            f'with {confidence_pct}% confidence (verdict: "{verdict}").\n\n'
            "In 2-3 sentences, explain what signals in the claim support this "
            "classification. Be factual and do not repeat the verdict label.\n\n"
            f"CLAIM: {claim}"
        )

        start = time.perf_counter()
        result = ""

        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(max_turns=1),
        ):
            if isinstance(message, ResultMessage):
                result = message.result

        LLM_LATENCY.observe(time.perf_counter() - start)
        logger.info(f"Claude explanation in {time.perf_counter() - start:.2f}s")
        return result.strip()
