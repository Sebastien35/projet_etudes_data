from shared.llm_interface import LLMInterface
from google import genai
from dotenv import load_dotenv
import os
from shared.rag import Rag
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('shared.gemini_service')

load_dotenv()


def is_context_sufficient(context_chunks, min_chars=300):
    if not context_chunks:
        return False
    return sum(len(c) for c in context_chunks) >= min_chars


class GeminiService(LLMInterface):
    def __init__(self, model_name: str, api_key: str):
        super().__init__(model_name, api_key)
        self.client = genai.Client(api_key=api_key)
        self.rag = Rag()
        self.model = model_name

    # -----------------------
    # PROMPTS
    # -----------------------

    def build_factcheck_rag_prompt(self, claim, context_chunks):
        context = "\n\n".join(f"- {chunk}" for chunk in context_chunks)

        return f"""
You are a professional fact-checker.

Evaluate the following CLAIM using ONLY the CONTEXT below.
Do not use outside knowledge.

If the context does not provide enough evidence, mark the verdict as "uncertain".

Return your answer STRICTLY as valid JSON with this schema:
{{
  "verdict": one of ["true", "very likely true", "uncertain", "very likely false", "false"],
  "probability": number between 0 and 1,
  "explanation": short factual justification,
  "based_on": "rag"
}}

Context:
{context}

CLAIM:
{claim}

JSON:
"""

    def build_factcheck_fallback_prompt(self, claim):
        return f"""
You are a professional fact-checker.

The internal dataset was insufficient.
Evaluate the following CLAIM using general, widely accepted information.
Be cautious and conservative in your judgment.

Return your answer STRICTLY as valid JSON with this schema:
{{
  "verdict": one of ["true", "very likely true", "uncertain", "very likely false", "false"],
  "probability": number between 0 and 1,
  "explanation": short factual justification,
  "based_on": "general_knowledge"
}}

CLAIM:
{claim}

JSON:
"""

    # -----------------------
    # MAIN ENTRY POINT
    # -----------------------

    def send_message(self, claim: str) -> dict:
        context_chunks = self.rag.retrieve_context(
            claim,
            top_k_docs=5
        )

        if is_context_sufficient(context_chunks):
            prompt = self.build_factcheck_rag_prompt(claim, context_chunks)
        else:
            prompt = self.build_factcheck_fallback_prompt(claim)

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )

        # Ensure valid JSON output
        try:
            logger.info(f"LLM response: {response.text}")
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {
                "verdict": "uncertain",
                "probability": 0.0,
                "explanation": "Model returned invalid output.",
                "based_on": "error"
            }
