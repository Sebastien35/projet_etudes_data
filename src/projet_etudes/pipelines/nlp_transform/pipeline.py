"""
This is a boilerplate pipeline 'nlp_transform'
generated using Kedro 1.0.0
"""

from kedro.pipeline import Node, Pipeline  # noqa
from .nodes import (
    clean_text,
    classify_emotion,
    get_posts_to_treat,
    lemmatize_text,
    merge_features,
    normalize_text,
    save_to_db,
)  # noqa


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            Node(
                func=get_posts_to_treat,
                inputs=None,
                outputs="raw_posts",
                name="get_posts_to_treat_node",
            ),
            Node(
                func=clean_text,
                inputs="raw_posts",
                outputs="cleaned_posts",
                name="clean_text_node",
            ),
            Node(
                func=normalize_text,
                inputs="cleaned_posts",
                outputs="normalized_posts",
                name="normalize_text_node",
            ),
            # Lemmatization and emotion classification run on the same
            # normalized text in parallel — each adds its own columns.
            Node(
                func=lemmatize_text,
                inputs="normalized_posts",
                outputs="lemmatized_posts",
                name="lemmatize_text_node",
            ),
            Node(
                func=classify_emotion,
                inputs="normalized_posts",
                outputs="emotion_posts",
                name="classify_emotion_node",
            ),
            Node(
                func=merge_features,
                inputs=["lemmatized_posts", "emotion_posts"],
                outputs="featured_posts",
                name="merge_features_node",
            ),
            Node(
                func=save_to_db,
                inputs="featured_posts",
                outputs=None,
                name="save_to_db_node",
            ),
        ]
    )
