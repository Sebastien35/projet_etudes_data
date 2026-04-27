"""
Pipeline 'vectorisation' — KMeans-based clustering on cleaned posts.

Flow:
  get_cleaned_posts ──► vectorize_texts ──► cluster_posts ──► save_predictions
                                                         └───► save_model_artifacts
"""

from kedro.pipeline import Node, Pipeline

from .nodes import (
    cluster_posts,
    get_cleaned_posts,
    save_model_artifacts,
    save_predictions,
    vectorize_texts,
)


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            Node(
                func=get_cleaned_posts,
                inputs=None,
                outputs=["texts", "posts_"],
                name="get_cleaned_posts_node",
            ),
            Node(
                func=vectorize_texts,
                inputs=["texts", "params:vectorisation.max_features"],
                outputs=["tfidf_matrix", "tfidf_vectorizer"],
                name="vectorize_texts_node",
            ),
            Node(
                func=cluster_posts,
                inputs=["tfidf_matrix", "params:vectorisation.n_clusters"],
                outputs=["labels", "probs", "km_model"],
                name="cluster_posts_node",
            ),
            Node(
                func=save_model_artifacts,
                inputs=[
                    "tfidf_vectorizer",
                    "km_model",
                    "params:vectorisation.vectorizer_path",
                    "params:vectorisation.kmeans_path",
                ],
                outputs=None,
                name="save_model_artifacts_node",
            ),
            Node(
                func=save_predictions,
                inputs=["posts_", "probs", "labels"],
                outputs=None,
                name="save_predictions_node",
            ),
        ]
    )
