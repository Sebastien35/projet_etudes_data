import joblib
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class Rag:
    def __init__(self, filepath="data/06_models/rag_vectors.joblib"):
        data = joblib.load(filepath)

        self.model = SentenceTransformer(data["model_name"])
        self.docs = data["docs"]          # list[str]
        self.embeddings = data["embeddings"]  # (n_docs, embedding_dim)
        self.clusters = data["clusters"]  # array[int]

    def retrieve_context(self, query: str, top_k_docs: int = 5) -> list[str]:
        """Return the top-k docs most semantically similar to the query."""
        query_vec = self.model.encode([query], convert_to_numpy=True)
        sims = cosine_similarity(query_vec, self.embeddings).flatten()
        best_indices = sims.argsort()[-top_k_docs:][::-1]
        return [self.docs[idx] for idx in best_indices if sims[idx] > 0]
