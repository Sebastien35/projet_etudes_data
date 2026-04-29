"""
This is a boilerplate pipeline 'ingest_from_bluesky'
generated using Kedro 1.0.0
"""

from kedro.pipeline import Node, Pipeline  # noqa

from .nodes import fetch_from_keywords, save_posts_to_db


def create_pipeline(**_kwargs) -> Pipeline:
    return Pipeline(
        [
            Node(
                func=fetch_from_keywords,
                inputs=None,
                outputs="posts",
                name="fetch_from_keywords_node",
            ),
            Node(
                func=save_posts_to_db,
                inputs="posts",
                outputs=None,
                name="save_posts_to_db_node",
            ),
        ]
    )
