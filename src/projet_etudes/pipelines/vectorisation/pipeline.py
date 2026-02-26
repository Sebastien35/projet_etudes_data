from kedro.pipeline import node, pipeline
from .nodes import (
    get_cleaned_posts,
    vectorize_docs,
    clusterize,
    save_clusters_to_mongo,
    save_rag_joblib,
    save_vectorized_posts,
)


def create_pipeline(**kwargs):
    return pipeline(
        [
            node(get_cleaned_posts, None, ["docs", "posts_"]),
            node(vectorize_docs, "docs", ["tfidf_df", "vectorizer"]),  # Both outputs
            node(clusterize, "tfidf_df", "clusters"),
            node(save_clusters_to_mongo, ["posts_", "clusters"], None),  # Uses posts
            node(save_rag_joblib, ["docs", "tfidf_df", "clusters", "vectorizer"], None),
            node(save_vectorized_posts, ["posts_", "tfidf_df", "clusters"], None),
        ]
    )


def register_pipelines():
    return {"vectorize_cluster": create_pipeline()}
