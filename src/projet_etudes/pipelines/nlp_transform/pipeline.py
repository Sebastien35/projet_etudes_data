"""
This is a boilerplate pipeline 'nlp_transform'
generated using Kedro 1.0.0
"""

from kedro.pipeline import Node, Pipeline  # noqa
from .nodes import (
    clean_text,
    get_posts_to_treat,
    lemmatize_text,
    normalize_text,
    tokenize_text,
    save_to_db
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
            Node(
                func=tokenize_text,
                inputs="normalized_posts",
                outputs="tokenized_posts",
                name="tokenize_text_node",
            ),
            Node(
                func=lemmatize_text,
                inputs="tokenized_posts",
                outputs="lemmatized_posts",
                name="lemmatize_text_node",
            ),
            Node(
                func=save_to_db,
                inputs="lemmatized_posts",
                outputs=None,
                name="save_to_db_node",
            ),
        ]
    )