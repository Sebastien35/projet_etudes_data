import sys
import os
import joblib
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../../..")


class Rag:
    def __init__(self, filepath="data/06_models/rag_vectors.joblib"):  # pylint: disable=too-few-public-methods
        data = joblib.load(filepath)

        self.vectorizer = data["vectorizer"]  # fitted TF‑IDF
        self.docs = data["docs"]  # list[str]
        self.tfidf_matrix = data["tfidf_matrix"]  # 2D array
        self.clusters = data["clusters"]  # array[int]

    def retrieve_context(self, query, top_k_docs=5):
        """Retrieves the top k docs most similar to the query."""
        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        best_indices = sims.argsort()[-top_k_docs:][::-1]
        results = []
        for idx in best_indices:
            if sims[idx] > 0:
                results.append(self.docs[idx])
        return results
