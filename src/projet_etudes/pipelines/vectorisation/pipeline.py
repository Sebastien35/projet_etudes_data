"""
Pipeline 'vectorisation' — KMeans clustering + supervised reliability classifier.

Flow:
  get_cleaned_posts ──► encode_texts ──► cluster_posts ──► save_predictions
                                                      └───► save_model_artifacts

  get_reliability_training_data ──► train_reliability_classifier ──► save_reliability_model
"""

from kedro.pipeline import Node, Pipeline

from .nodes import (
    cluster_posts,
    encode_texts,
    get_cleaned_posts,
    get_reliability_training_data,
    save_model_artifacts,
    save_predictions,
    save_reliability_model,
    train_reliability_classifier,
)

_KMEANS_NODES = [
    Node(
        func=get_cleaned_posts,
        inputs=None,
        outputs=["texts", "posts_"],
        name="get_cleaned_posts_node",
    ),
    Node(
        func=encode_texts,
        inputs=["texts", "posts_", "params:vectorisation.embedding_model"],
        outputs="embedding_matrix",
        name="encode_texts_node",
    ),
    Node(
        func=cluster_posts,
        inputs=["embedding_matrix", "posts_", "params:vectorisation.n_clusters"],
        outputs=["labels", "probs", "km_model"],
        name="cluster_posts_node",
    ),
    Node(
        func=save_model_artifacts,
        inputs=[
            "km_model",
            "params:vectorisation.kmeans_path",
        ],
        outputs=None,
        name="save_model_artifacts_node",
    ),
    Node(
        func=save_predictions,
        inputs=["posts_", "probs", "labels", "km_model"],
        outputs=None,
        name="save_predictions_node",
    ),
]

_RELIABILITY_NODES = [
    Node(
        func=get_reliability_training_data,
        inputs=[
            "params:vectorisation.reliability_min_reliable",
            "params:vectorisation.reliability_min_misinfo",
        ],
        outputs=["reliability_texts", "reliability_labels", "reliability_style"],
        name="get_reliability_training_data_node",
    ),
    Node(
        func=train_reliability_classifier,
        inputs=[
            "reliability_texts",
            "reliability_labels",
            "params:vectorisation.embedding_model",
            "reliability_style",
        ],
        outputs="reliability_clf",
        name="train_reliability_classifier_node",
    ),
    Node(
        func=save_reliability_model,
        inputs=[
            "reliability_clf",
            "params:vectorisation.reliability_classifier_path",
        ],
        outputs=None,
        name="save_reliability_model_node",
    ),
]


def create_reliability_pipeline(**_kwargs) -> Pipeline:
    return Pipeline(_RELIABILITY_NODES)


def create_pipeline(**_kwargs) -> Pipeline:
    return Pipeline(_KMEANS_NODES + _RELIABILITY_NODES)
