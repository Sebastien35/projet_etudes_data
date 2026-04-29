import logging
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from pymongo import UpdateOne
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from shared.mongo import mongo_client

logger = logging.getLogger(__name__)
mongo = mongo_client()


def get_cleaned_posts():
    """Fetch posts that have been normalised but not yet classified."""
    cleaned_collection = mongo.use_collection("cleaned_posts")
    classified_ids = set(mongo.use_collection("classified_posts").distinct("unique_id"))

    raw_posts = list(
        cleaned_collection.find({"normalized_text": {"$exists": True, "$ne": ""}})
    )
    posts = [p for p in raw_posts if p["unique_id"] not in classified_ids]
    texts = [p["normalized_text"] for p in posts]

    logger.info(f"Loaded {len(posts)} unclassified posts for inference")
    return texts, posts


def vectorize_texts(texts: list, max_features: int):
    """TF-IDF vectorize normalized texts. Returns matrix and fitted vectorizer."""
    vectorizer = TfidfVectorizer(max_features=max_features, sublinear_tf=True)
    matrix = vectorizer.fit_transform(texts)
    logger.info(f"TF-IDF matrix shape: {matrix.shape}")
    return matrix, vectorizer


def cluster_posts(tfidf_matrix, n_clusters: int):
    """KMeans clustering. Returns labels, distance-based scores, and fitted model.

    Cluster 1 is treated as 'real', cluster 0 as 'fake' (arbitrary convention).
    The score represents how strongly a post belongs to cluster 1 (real),
    derived from the ratio of distances to each centroid.
    """
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    labels = km.fit_predict(tfidf_matrix)

    distances = km.transform(tfidf_matrix)  # (n_samples, n_clusters)
    d0 = distances[:, 0]
    d1 = distances[:, 1] if n_clusters > 1 else np.zeros_like(d0)
    scores = d0 / (d0 + d1 + 1e-8)

    real_count = int((labels == 1).sum())
    fake_count = len(labels) - real_count
    logger.info(
        f"Clustered {len(labels)} posts → cluster-1 (real): {real_count}, cluster-0 (fake): {fake_count}"
    )
    return labels, scores, km


def save_model_artifacts(vectorizer, km_model, vectorizer_path: str, kmeans_path: str):
    """Persist the fitted TF-IDF vectorizer and KMeans model for the API service."""
    Path(vectorizer_path).parent.mkdir(parents=True, exist_ok=True)
    with open(vectorizer_path, "wb") as f:
        pickle.dump(vectorizer, f)
    with open(kmeans_path, "wb") as f:
        pickle.dump(km_model, f)
    logger.info(f"Saved TF-IDF vectorizer → {vectorizer_path}")
    logger.info(f"Saved KMeans model → {kmeans_path}")


def save_predictions(posts: list, probs, labels) -> int:
    """Upsert cluster-based predictions into the classified_posts collection."""
    collection = mongo.use_collection("classified_posts")

    updates = [
        UpdateOne(
            {"unique_id": post["unique_id"]},
            {
                "$set": {
                    "unique_id": post["unique_id"],
                    "username": post.get("username"),
                    "category": post.get("category"),
                    "normalized_text": post.get("normalized_text"),
                    "fake_news_prob": float(prob),
                    "is_real": bool(label == 1),
                    "cluster": int(label),
                    "classified_at": pd.Timestamp.now(),
                }
            },
            upsert=True,
        )
        for post, prob, label in zip(posts, probs, labels)
    ]

    if updates:
        result = collection.bulk_write(updates, ordered=False)
        logger.info(
            f"Upserted {len(updates)} predictions "
            f"(matched: {result.matched_count}, modified: {result.modified_count})"
        )

    return len(updates)
