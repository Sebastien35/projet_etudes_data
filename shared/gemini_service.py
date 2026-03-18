from shared.llm_interface import LLMInterface
from google import genai
from dotenv import load_dotenv
import os
from shared.rag import Rag
import json
import logging
import re


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('shared.gemini_service')


load_dotenv()


def is_context_sufficient(context_chunks, min_chars=300):
    if not context_chunks:
        return False
    return sum(len(c) for c in context_chunks) >= min_chars


def extract_json_from_response(text: str) -> dict:
    """
    Extract JSON from LLM response that may be wrapped in markdown code blocks.
    Handles ```json ... ``` and plain JSON.
    """
    if not text:
        raise ValueError("Empty response text")
    
    # Remove common markdown wrappers like ```json ... ```
    cleaned = re.sub(r'^```(?:json)?\s*\n?', '', text, flags=re.MULTILINE)
    cleaned = re.sub(r'\n?```$', '', cleaned, flags=re.MULTILINE)
    cleaned = cleaned.strip()
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Failed to parse JSON after markdown cleanup: {e.msg}", 
            e.doc, 
            e.pos
        )


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

now answer the question in JSON:
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

        # Ensure valid JSON output with markdown extraction
        try:
            logger.info(f"LLM response: {response.text}")
            parsed_response = extract_json_from_response(response.text)
            return parsed_response
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {response.text[:500]}... Error: {str(e)}")
            return {
                "verdict": "uncertain",
                "probability": 0.0,
                "explanation": "Model returned invalid output.",
                "based_on": "error"
            }
