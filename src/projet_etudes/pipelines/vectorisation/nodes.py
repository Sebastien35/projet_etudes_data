import logging
import os
import pickle
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../../..")
from shared.mongo import mongo_client  # noqa


load_dotenv()
mongo = mongo_client()


def get_cleaned_posts():
    mongo.use_collection("cleaned_posts")
    lemmas = [p["lemmas"] for p in mongo.db.cleaned_posts.find()]
    docs = [" ".join(lemma_list) for lemma_list in lemmas]
    return docs


def vectorise(docs):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(docs)
    df = pd.DataFrame(
        tfidf_matrix.toarray(), columns=vectorizer.get_feature_names_out()
    )
    return df


def find_best_k(tfidf_matrix, k_range=range(2, 11)):
    """Auto-selects k via max silhouette score."""
    best_score = -1
    best_k = 2
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(tfidf_matrix)
        if len(np.unique(labels)) > 1:  # Valid
            score = silhouette_score(tfidf_matrix, labels)
            if score > best_score:
                best_score, best_k = score, k
    logger.info(f"Best k: {best_k} (silhouette: {best_score:.4f})")
    return best_k


def clusterize(tfidf_matrix):
    """Returns cluster labels only (1D array for dataset)."""
    n_clusters = find_best_k(tfidf_matrix)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(tfidf_matrix)
    logger.info(
        f"Clustered into {len(np.unique(clusters))} groups: {np.bincount(clusters)}"
    )
    return clusters


def save_rag_pkl(clusters, tfidf_df, docs, filepath="data/06-models/rag_vectors.pkl"):
    """Save docs, TF-IDF vectors and clusters in a single PKL."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    data = {
        "docs": docs,  # list[str]
        "tfidf_columns": tfidf_df.columns.tolist(),
        "tfidf_matrix": tfidf_df.to_numpy(),  # 2D array
        "clusters": clusters.astype(int),  # 1D array
    }

    with open(filepath, "wb") as f:
        pickle.dump(data, f)

    logger.info(f"Saved {len(docs)} vectorized docs to {filepath}")
    return filepath


def save_rag_joblib(
    clusters, tfidf_df, docs, filepath="data/06-models/rag_vectors.joblib"
):
    """Save docs, TF-IDF vectors and clusters using joblib for better handling of large NumPy arrays."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    data = {
        "docs": docs,  # list[str]
        "tfidf_columns": tfidf_df.columns.tolist(),
        "tfidf_matrix": tfidf_df.to_numpy(),  # 2D array
        "clusters": clusters.astype(int),  # 1D array
    }

    joblib.dump(
        data, filepath, compress=3
    )  # compress=3 balances speed and size [web:11][web:12]

    logger.info(f"Saved {len(docs)} vectorized docs to {filepath}")
    return filepath
