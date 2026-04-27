"""
Pipeline 'nlp_transform' — cleans and normalises raw Bluesky posts
for downstream KMeans classification.
"""

from kedro.pipeline import Node, Pipeline

from .nodes import clean_text, get_posts_to_treat, normalize_text, save_to_db


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
                func=save_to_db,
                inputs="normalized_posts",
                outputs=None,
                name="save_to_db_node",
            ),
        ]
    )
