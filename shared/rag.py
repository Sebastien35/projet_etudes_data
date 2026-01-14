import joblib
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import sys,os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../../..")
class Rag:
    def __init__(self, filepath="data/06-models/rag_vectors.joblib"):
        data = joblib.load(filepath)

        self.vectorizer = data["vectorizer"]       # fitted TF‑IDF
        self.docs = data["docs"]                   # list[str]
        self.tfidf_matrix = data["tfidf_matrix"]   # 2D array
        self.clusters = data["clusters"]           # array[int]

    def retrieve_context(self, query, top_k_docs=5):
        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        best_idx = np.argmax(sims)
        cluster_id = self.clusters[best_idx]
        cluster_docs = [
            doc for doc, c in zip(self.docs, self.clusters) if c == cluster_id
        ]

        return cluster_docs[:top_k_docs]
