import logging
import pickle
from pathlib import Path

import joblib
import numpy as np
from pymongo import UpdateOne
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from shared.mongo import mongo_client

logger = logging.getLogger(__name__)
mongo = mongo_client()


def get_cleaned_posts():
    collection = mongo.use_collection("cleaned_posts")
    raw_posts = list(collection.find())

    filtered_posts = []
    docs = []

    for p in raw_posts:
        lemmas = p.get("lemmas")

        if lemmas:
            filtered_posts.append(p)
            docs.append(" ".join(lemmas))

    logger.info(f"Loaded {len(docs)} documents for clustering")

    return docs, filtered_posts


SBERT_MODEL_NAME = "all-MiniLM-L6-v2"


def vectorize_docs(docs):
    """Encode docs with a sentence-transformer. Returns (embeddings, model_name)."""
    model = SentenceTransformer(SBERT_MODEL_NAME)
    embeddings = model.encode(docs, show_progress_bar=True, convert_to_numpy=True)
    logger.info(f"Encoded {len(docs)} docs → shape {embeddings.shape}")
    return embeddings, SBERT_MODEL_NAME


def find_best_k(embeddings, k_range=range(2, 11)):
    """Auto-select k via silhouette."""
    best_score, best_k = -1, 2
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        if len(np.unique(labels)) > 1:
            score = silhouette_score(embeddings, labels)
            if score > best_score:
                best_score, best_k = score, k
    logger.info(f"Best k: {best_k} (silhouette: {best_score:.4f})")
    return best_k


def clusterize(embeddings):
    """KMeans clustering."""
    n_clusters = find_best_k(embeddings)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(embeddings)
    logger.info(f"Clusters: {np.bincount(clusters)}")
    return clusters


def save_clusters_to_mongo(posts, clusters):
    """Update cleaned_posts with cluster labels."""
    collection = mongo.use_collection("cleaned_posts")

    updates = []

    for post, cluster in zip(posts, clusters):
        updates.append(
            UpdateOne(
                {"unique_id": post["unique_id"]}, {"$set": {"cluster": int(cluster)}}
            )
        )

    if updates:
        collection.bulk_write(updates, ordered=False)
        logger.info(f"Updated {len(updates)} posts with clusters")

    return len(updates)


def save_rag_pkl(docs, tfidf_df, clusters, filepath="data/06_models/rag_vectors.pkl"):
    """Export for RAG."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    data = {
        "docs": docs,
        "tfidf_columns": tfidf_df.columns.tolist(),
        "tfidf_matrix": tfidf_df.to_numpy(),
        "clusters": clusters.astype(int),
    }
    with open(filepath, "wb") as f:
        pickle.dump(data, f)
    logger.info(f"Saved RAG data: {filepath}")
    return filepath


def save_rag_joblib(
    docs, embeddings, clusters, model_name, filepath="data/06_models/rag_vectors.joblib"
):
    """Export for RAG using joblib."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    data = {
        "docs": docs,  # list[str] - lemmatized docs
        "model_name": model_name,  # SentenceTransformer model name
        "embeddings": embeddings,  # NumPy array (n_docs, embedding_dim)
        "clusters": clusters.astype(int),
    }

    joblib.dump(data, filepath, compress=3)
    logger.info(
        f"Saved RAG data ({len(docs)} docs, shape {embeddings.shape}): {filepath}"
    )
    return filepath


def save_vectorized_posts(
    posts, embeddings, clusters, collection_name="vectorized_posts"
):
    """Save posts + sentence embeddings + clusters to Mongo."""
    collection = mongo.use_collection(collection_name)

    if not (len(posts) == len(embeddings) == len(clusters)):
        logger.error(
            f"Mismatch → posts={len(posts)}, embeddings={len(embeddings)}, clusters={len(clusters)}"
        )
        raise ValueError("Mismatch posts / embeddings / clusters")

    updates = []
    for i, post in enumerate(posts):
        updates.append(
            UpdateOne(
                {"unique_id": post["unique_id"]},
                {
                    "$set": {
                        "unique_id": post["unique_id"],
                        "username": post.get("username"),
                        "normalized_text": post.get("normalized_text"),
                        "lemmas": post.get("lemmas"),
                        "emotion": post.get("emotion"),
                        "cluster": int(clusters[i]),
                        "embedding": embeddings[i].tolist(),
                    }
                },
                upsert=True,
            )
        )

    if updates:
        result = collection.bulk_write(updates, ordered=False)
        logger.info(
            f"Upserted {len(updates)} vectorized posts (matched: {result.matched_count}, modified: {result.modified_count})"
        )

    return len(updates)
