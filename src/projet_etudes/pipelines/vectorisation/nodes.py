import logging
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from pymongo import UpdateOne
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score

from shared.embedding_service import encode as embed
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


def encode_texts(texts: list, embedding_model: str) -> np.ndarray:
    """Encode normalized texts into dense sentence embeddings."""
    matrix = embed(texts, model_name=embedding_model)
    logger.info(f"Embedding matrix shape: {matrix.shape}")
    return matrix


def cluster_posts(embedding_matrix, posts: list, n_clusters: int):
    """KMeans clustering. Returns labels, distance-based scores, and fitted model.

    Cluster orientation is determined by two complementary signals:
      - Posts from reliable sources (source_label == "reliable") anchor the real cluster.
      - Posts from the Misinformation search theme anchor the fake cluster.
    The cluster that scores higher on reliable_rate - misinfo_rate is the real cluster.
    This removes the arbitrary cluster-0=fake assumption.
    """
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    labels = km.fit_predict(embedding_matrix)

    distances = km.transform(embedding_matrix)  # (n_samples, n_clusters)
    d0 = distances[:, 0]
    d1 = distances[:, 1] if n_clusters > 1 else np.zeros_like(d0)

    is_reliable = np.array(
        [p.get("source_label", "unverified") == "reliable" for p in posts]
    )
    is_misinfo = np.array([p.get("category", "") == "Misinformation" for p in posts])

    def _cluster_score(cluster_id):
        mask = labels == cluster_id
        if not mask.any():
            return 0.0
        reliable_rate = is_reliable[mask].mean()
        misinfo_rate = is_misinfo[mask].mean()
        return float(reliable_rate - misinfo_rate)

    scores_c = [_cluster_score(i) for i in range(n_clusters)]
    # The real cluster has the highest reliable_rate - misinfo_rate
    real_cluster = int(np.argmax(scores_c))
    fake_cluster = 1 - real_cluster  # works for n_clusters=2

    logger.info(
        "Cluster orientation scores (reliable_rate - misinfo_rate): "
        + ", ".join(f"cluster-{i}: {s:.3f}" for i, s in enumerate(scores_c))
        + f" → real_cluster={real_cluster}, fake_cluster={fake_cluster}"
    )

    if scores_c[real_cluster] == 0.0:
        logger.warning(
            "No reliable-source or Misinformation posts found to orient clusters. "
            "Defaulting to cluster-0=fake. Re-ingest with source labelling enabled."
        )

    km.fake_cluster_ = fake_cluster

    # Score in [0, 1]: distance to fake centroid as fraction of total — high = likely real
    if fake_cluster == 0:
        raw_scores = d0 / (d0 + d1 + 1e-8)
    else:
        raw_scores = d1 / (d0 + d1 + 1e-8)

    is_real = labels == real_cluster
    logger.info(
        f"Clustered {len(labels)} posts → "
        f"real: {is_real.sum()} (reliable sources: {is_reliable[is_real].sum()}), "
        f"fake: {(~is_real).sum()} (misinformation: {is_misinfo[~is_real].sum()})"
    )
    return labels, raw_scores, km


def save_model_artifacts(km_model, kmeans_path: str):
    """Persist the fitted KMeans model for the API service."""
    Path(kmeans_path).parent.mkdir(parents=True, exist_ok=True)
    with open(kmeans_path, "wb") as f:
        pickle.dump(km_model, f)
    logger.info(f"Saved KMeans model → {kmeans_path}")


def get_reliability_training_data(
    min_reliable: int, min_misinfo: int
) -> tuple[list, list]:
    """Fetch labeled training data from cleaned_posts.

    Reliable sources (source_label='reliable') → label 1 (real news).
    Misinformation category posts               → label 0 (fake news).
    """
    collection = mongo.use_collection("cleaned_posts")

    reliable_posts = list(
        collection.find(
            {
                "source_label": "reliable",
                "normalized_text": {"$exists": True, "$ne": ""},
            },
            {"normalized_text": 1},
        )
    )
    misinfo_posts = list(
        collection.find(
            {
                "category": "Misinformation",
                "normalized_text": {"$exists": True, "$ne": ""},
            },
            {"normalized_text": 1},
        )
    )

    if len(reliable_posts) < min_reliable:
        raise ValueError(
            f"Not enough reliable-source posts to train: found {len(reliable_posts)}, "
            f"need at least {min_reliable}. "
            "Run the ingest_from_bluesky + nlp_transform pipelines first."
        )
    if len(misinfo_posts) < min_misinfo:
        raise ValueError(
            f"Not enough misinformation posts to train: found {len(misinfo_posts)}, "
            f"need at least {min_misinfo}. "
            "Run the ingest_from_bluesky + nlp_transform pipelines first."
        )

    texts = [p["normalized_text"] for p in reliable_posts] + [
        p["normalized_text"] for p in misinfo_posts
    ]
    labels = [1] * len(reliable_posts) + [0] * len(misinfo_posts)

    logger.info(
        f"Reliability training data: {len(reliable_posts)} reliable posts (label=1), "
        f"{len(misinfo_posts)} misinformation posts (label=0)"
    )
    return texts, labels


def train_reliability_classifier(
    texts: list, labels: list, embedding_model: str
) -> LogisticRegression:
    """Encode texts with sentence embeddings then fit LogisticRegression."""
    X = embed(texts, model_name=embedding_model)

    clf = LogisticRegression(
        max_iter=1000, class_weight="balanced", solver="lbfgs", C=1.0
    )
    clf.fit(X, labels)

    cv_scores = cross_val_score(
        clf, X, labels, cv=min(5, len(set(labels))), scoring="roc_auc"
    )
    logger.info(
        f"Reliability classifier trained — "
        f"ROC-AUC CV: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}"
    )
    return clf


def save_reliability_model(classifier, classifier_path: str) -> None:
    """Persist the reliability classifier for the API service."""
    Path(classifier_path).parent.mkdir(parents=True, exist_ok=True)
    with open(classifier_path, "wb") as f:
        pickle.dump(classifier, f)
    logger.info(f"Saved reliability classifier → {classifier_path}")


def save_predictions(posts: list, probs, labels, km_model) -> int:
    """Upsert cluster-based predictions into the classified_posts collection."""
    collection = mongo.use_collection("classified_posts")
    fake_cluster = getattr(km_model, "fake_cluster_", 0)

    updates = [
        UpdateOne(
            {"unique_id": post["unique_id"]},
            {
                "$set": {
                    "unique_id": post["unique_id"],
                    "username": post.get("username"),
                    "category": post.get("category"),
                    "source_label": post.get("source_label", "unverified"),
                    "normalized_text": post.get("normalized_text"),
                    "fake_news_prob": float(prob),
                    "is_real": bool(label != fake_cluster),
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
