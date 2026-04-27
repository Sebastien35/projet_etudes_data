"""
TF-IDF based RAG for context retrieval.
Replaced the previous SentenceTransformer implementation.
"""

import logging

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class Rag:
    def __init__(self, filepath="data/06_models/rag_vectors.joblib"):
        data = joblib.load(filepath)
        self.docs = data["docs"]
        self._vectorizer = TfidfVectorizer()
        self._matrix = self._vectorizer.fit_transform(self.docs)
        logger.info(f"RAG index built: {len(self.docs)} docs")

    def retrieve_context(self, query: str, top_k_docs: int = 5) -> list[str]:
        query_vec = self._vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self._matrix).flatten()
        best_indices = sims.argsort()[-top_k_docs:][::-1]
        return [self.docs[idx] for idx in best_indices if sims[idx] > 0]
