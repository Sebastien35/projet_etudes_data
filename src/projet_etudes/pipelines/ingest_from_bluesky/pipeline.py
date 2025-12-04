"""
This is a boilerplate pipeline 'ingest_from_bluesky'
generated using Kedro 1.0.0
"""

from kedro.pipeline import Node, Pipeline  # noqa
from .nodes import get_client, fetch_from_trusted_sources, save_posts_to_db  # noqa


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            Node(
                func=fetch_from_trusted_sources,
                inputs=None,
                outputs="posts",
                name="fetch_from_trusted_sources_node",
            ),
            Node(
                func=save_posts_to_db,
                inputs="posts",
                outputs=None,
                name="save_posts_to_db_node",
            ),
        ]
    )
