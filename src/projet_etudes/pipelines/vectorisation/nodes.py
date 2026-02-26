import logging
import pickle
import joblib
from pathlib import Path
import numpy as np
import pandas as pd
from pymongo import UpdateOne
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
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


def vectorize_docs(docs):
    """Return tfidf_df AND fitted vectorizer."""
    vectorizer = TfidfVectorizer(
        max_features=2000,
        min_df=3,
        max_df=0.8,
        ngram_range=(1, 2),
        stop_words="english",
    )
    tfidf_matrix = vectorizer.fit_transform(docs)
    tfidf_df = pd.DataFrame(
        tfidf_matrix.toarray(), columns=vectorizer.get_feature_names_out()
    )
    return tfidf_df, vectorizer  # RETURN BOTH


def find_best_k(tfidf_matrix, k_range=range(2, 11)):
    """Auto-select k via silhouette."""
    best_score, best_k = -1, 2
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(tfidf_matrix)
        if len(np.unique(labels)) > 1:
            score = silhouette_score(tfidf_matrix, labels)
            if score > best_score:
                best_score, best_k = score, k
    logger.info(f"Best k: {best_k} (silhouette: {best_score:.4f})")
    return best_k


def clusterize(tfidf_matrix):
    """KMeans clustering."""
    n_clusters = find_best_k(tfidf_matrix)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(tfidf_matrix)
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
    docs, tfidf_df, clusters, vectorizer, filepath="data/06_models/rag_vectors.joblib"
):
    """Export for RAG using joblib (better for large NumPy arrays)."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    data = {
        "docs": docs,  # list[str] - lemmatized docs
        "tfidf_columns": tfidf_df.columns.tolist(),
        "vectorizer": vectorizer,  # TfidfVectorizer
        "tfidf_matrix": tfidf_df.to_numpy(),  # NumPy array - efficient with joblib
        "clusters": clusters.astype(int),  # cluster labels
    }

    joblib.dump(data, filepath, compress=3)
    logger.info(f"Saved RAG data ({len(docs)} docs): {filepath}")
    return filepath


from pymongo import UpdateOne


def save_vectorized_posts(
    posts, tfidf_df, clusters, collection_name="vectorized_posts"
):
    """
    Save posts + TF-IDF vectors + clusters + vectorizer to Mongo.

    Args:
        posts: list[dict] from cleaned_posts
        tfidf_df: pd.DataFrame (TF-IDF matrix)
        clusters: np.array[int] cluster labels
        vectorizer: fitted TfidfVectorizer
    """
    collection = mongo.use_collection(collection_name)
    vectors = tfidf_df.to_numpy()

    if not (len(posts) == len(vectors) == len(clusters)):
        logger.error(
            f"Mismatch → posts={len(posts)}, vectors={len(vectors)}, clusters={len(clusters)}"
        )
        raise ValueError("Mismatch posts / vectors / clusters")

    updates = []
    for i in range(len(posts)):
        post = posts[i]

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
                        "tfidf_vector": vectors[i].tolist(),  # dense vector
                        "tfidf_columns": tfidf_df.columns.tolist(),  # vocab
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
