"""
This is a boilerplate pipeline 'vectorisation'
generated using Kedro 1.0.0
"""

from kedro.pipeline import Node, Pipeline  # noqa
from .nodes import (
    get_cleaned_posts,
    vectorise,
    clusterize,
    save_rag_pkl,
    save_rag_joblib,
)


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            Node(
                func=get_cleaned_posts,
                inputs=None,
                outputs="primary_cleaned_posts",  # Unique name
                name="get_cleaned_posts_from_mongo",
            ),
            Node(
                func=vectorise,
                inputs="primary_cleaned_posts",  # Match input
                outputs="tfidf_matrix",
                name="vectorise",
            ),
            Node(
                func=clusterize,
                inputs="tfidf_matrix",
                outputs="clusters",
                name="clusterize",
            ),
            Node(
                func=save_rag_pkl,
                inputs=["clusters", "tfidf_matrix", "primary_cleaned_posts"],
                outputs="rag_vectors_jsonl",  # Catalog entry
                name="save_rag_json",
            ),
            Node(
                func=save_rag_joblib,
                inputs=["clusters", "tfidf_matrix", "primary_cleaned_posts"],
                outputs="rag_vectors_joblib",  # Catalog entry
                name="save_rag_joblib",
            ),
        ]
    )
