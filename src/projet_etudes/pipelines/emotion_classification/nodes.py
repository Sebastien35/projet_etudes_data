import logging
import os
import sys

import pandas as pd
from pymongo import UpdateOne

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../../..")
from shared.mongo import mongo_client  # noqa

logger = logging.getLogger(__name__)
mongo = mongo_client()


def get_posts_for_emotion() -> tuple[list[str], list[dict]]:
    """Fetch cleaned posts not yet emotion-classified (incremental)."""
    all_posts = list(
        mongo.use_collection("cleaned_posts").find(
            {"normalized_text": {"$exists": True, "$ne": ""}},
            {"_id": 0, "unique_id": 1, "username": 1, "category": 1, "normalized_text": 1},
        )
    )
    classified_ids = set(
        mongo.use_collection("emotion_posts").distinct("unique_id")
    )
    posts = [p for p in all_posts if p["unique_id"] not in classified_ids]
    texts = [p["normalized_text"] for p in posts]
    logger.info(f"[emotion] {len(posts)} posts to classify ({len(classified_ids)} already done)")
    return texts, posts


def classify_emotions_bert(
    texts: list[str],
    posts: list[dict],
    model_name: str,
    max_length: int,
    batch_size: int,
) -> list[dict]:
    """
    Run a BERT-based emotion classifier on normalized post texts.

    Uses `j-hartmann/emotion-english-distilroberta-base` by default — a
    DistilRoBERTa model fine-tuned on 6 datasets covering Ekman's 7 emotions:
    anger, disgust, fear, joy, neutral, sadness, surprise.

    Returns a list of result dicts ready for MongoDB upsert.
    """
    if not texts:
        logger.info("[emotion] No new posts to classify, skipping inference.")
        return []

    # Import here so the module is importable without torch installed
    # (e.g. in the Streamlit container which only reads from MongoDB)
    from transformers import pipeline as hf_pipeline  # noqa

    logger.info(f"[emotion] Loading model {model_name} …")
    classifier = hf_pipeline(
        "text-classification",
        model=model_name,
        top_k=1,
        truncation=True,
        max_length=max_length,
        device=-1,  # CPU — change to 0 for CUDA
    )
    logger.info(f"[emotion] Model loaded. Classifying {len(texts)} posts in batches of {batch_size} …")

    results = []
    for start in range(0, len(texts), batch_size):
        batch_texts = texts[start : start + batch_size]
        batch_posts = posts[start : start + batch_size]
        batch_preds = classifier(batch_texts)

        for post, pred in zip(batch_posts, batch_preds):
            top = pred[0]
            results.append(
                {
                    "unique_id":       post["unique_id"],
                    "username":        post.get("username"),
                    "category":        post.get("category"),
                    "normalized_text": post.get("normalized_text"),
                    "emotion":         top["label"].lower(),
                    "emotion_score":   round(float(top["score"]), 4),
                }
            )

        logger.info(f"[emotion] {min(start + batch_size, len(texts))}/{len(texts)} done")

    return results


def save_emotion_results(results: list[dict]) -> int:
    """Upsert emotion predictions into the `emotion_posts` MongoDB collection."""
    if not results:
        logger.info("[emotion] Nothing to save.")
        return 0

    collection = mongo.use_collection("emotion_posts")
    now = pd.Timestamp.now(tz="UTC")
    updates = [
        UpdateOne(
            {"unique_id": r["unique_id"]},
            {"$set": {**r, "classified_at": now}},
            upsert=True,
        )
        for r in results
    ]
    res = collection.bulk_write(updates, ordered=False)
    logger.info(
        f"[emotion] Upserted {len(updates)} docs "
        f"(matched: {res.matched_count}, modified: {res.modified_count})"
    )
    return len(updates)
