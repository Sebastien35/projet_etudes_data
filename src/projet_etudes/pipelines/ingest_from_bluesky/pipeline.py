"""
This is a boilerplate pipeline 'ingest_from_bluesky'
generated using Kedro 1.0.0
"""

from kedro.pipeline import Node, Pipeline  # noqa

from .nodes import fetch_from_keywords, fetch_from_reliable_accounts, save_posts_to_db


def create_pipeline(**_kwargs) -> Pipeline:
    return Pipeline(
        [
            Node(
                func=fetch_from_reliable_accounts,
                inputs=[
                    "params:ingest_from_bluesky.reliable_accounts",
                    "params:ingest_from_bluesky.reliable_domains",
                    "params:ingest_from_bluesky.limit_per_reliable_account",
                ],
                outputs="reliable_posts",
                name="fetch_from_reliable_accounts_node",
            ),
            Node(
                func=fetch_from_keywords,
                inputs="params:ingest_from_bluesky.reliable_domains",
                outputs="keyword_posts",
                name="fetch_from_keywords_node",
            ),
            Node(
                func=lambda a, b: a + b,
                inputs=["reliable_posts", "keyword_posts"],
                outputs="posts",
                name="merge_posts_node",
            ),
            Node(
                func=save_posts_to_db,
                inputs="posts",
                outputs=None,
                name="save_posts_to_db_node",
            ),
        ]
    )
