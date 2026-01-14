from shared.llm_interface import LLMInterface
from google import genai
from dotenv import load_dotenv
import os
from shared.rag import Rag

load_dotenv()


def is_context_sufficient(context_chunks, min_chars=300):
    """
    Simple heuristic to decide if RAG context is meaningful.
    """
    if not context_chunks:
        return False
    total_chars = sum(len(c) for c in context_chunks)
    return total_chars >= min_chars


class GeminiService(LLMInterface):
    def __init__(self, model_name: str, api_key: str):
        super().__init__(model_name, api_key)
        self.client = genai.Client(api_key=api_key)
        self.rag = Rag()
        self.model = model_name

    # -----------------------
    # PROMPTS
    # -----------------------

    def build_strict_rag_prompt(self, question, context_chunks):
        context = "\n\n".join(f"- {chunk}" for chunk in context_chunks)

        return f"""
You are an assistant that answers questions using ONLY the provided context.
Do NOT use outside knowledge.
If the answer is not explicitly present in the context, reply exactly:

"I don't know based on the provided data."

Context:
{context}

Question:
{question}

Answer:
"""

    def build_fallback_prompt(self, question):
        return f"""
The internal data source was not sufficient to answer the question.
Answer using general knowledge from reliable news sources.
Be factual, cautious, and avoid speculation.

Question:
{question}

Answer:
"""

    # -----------------------
    # MAIN ENTRY POINT
    # -----------------------

    def send_message(self, question: str) -> str:
        # 1️⃣ Retrieve RAG context
        context_chunks = self.rag.retrieve_context(
            question,
            top_k_docs=5
        )

        # 2️⃣ Decide which mode to use
        if is_context_sufficient(context_chunks):
            prompt = self.build_strict_rag_prompt(question, context_chunks)
        else:
            prompt = self.build_fallback_prompt(question)

        # 3️⃣ Call Gemini
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )

        return response.text
