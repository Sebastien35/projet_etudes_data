"""
DAG: nlp_transform
==================
Cleans and normalises raw Bluesky posts stored in MongoDB and writes the
result to the cleaned_posts collection. Processing is incremental: only posts
whose unique_id is not already in cleaned_posts are processed.

Schedule: None — triggered automatically by dag_ingest_from_bluesky on each
successful run, or manually via the Airflow UI.

Pipeline nodes (sequential, all intermediates are in-memory DataFrames):

  get_posts_to_treat_node  → raw_posts (DataFrame)
        Reads posts from MongoDB whose unique_id is not yet in cleaned_posts.

  clean_text_node          → cleaned_posts* (DataFrame, in-memory Kedro dataset)
        Lowercase; strip URLs, @mentions, #hashtags, emojis, punctuation.
        * Note: the Kedro dataset name "cleaned_posts" is a coincidence with
          the MongoDB collection of the same name. No conflict at runtime.

  normalize_text_node      → normalized_posts (DataFrame)
        NFKD unicode normalisation, ASCII encoding, whitespace collapse.

  save_to_db_node          → (writes to MongoDB collection: cleaned_posts)
        Upserts one document per row into the cleaned_posts collection.

On success: triggers dag_vectorisation so the model is refreshed
immediately after new cleaned data is available.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow.decorators import dag
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

from kedro_operator import KedroOperator

PIPELINE = "nlp_transform"

DEFAULT_ARGS = {
    "owner": "data-team",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=1),
    "email_on_failure": False,
    "email_on_retry": False,
}


@dag(
    dag_id="dag_nlp_transform",
    description="Clean and normalise raw Bluesky posts (incremental, triggered after ingest).",
    schedule=None,  # triggered by dag_ingest_from_bluesky
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["kedro", "nlp", "transform"],
    doc_md=__doc__,
)
def nlp_dag():
    # ── Nodes 1-4 share in-memory DataFrames — single KedroSession ───────────
    nlp = KedroOperator(
        task_id="nlp_transform",
        pipeline_name=PIPELINE,
        pool="default_pool",
    )

    # ── Trigger downstream pipelines in parallel ──────────────────────────────
    trigger_vectorisation = TriggerDagRunOperator(
        task_id="trigger_vectorisation",
        trigger_dag_id="dag_vectorisation",
        wait_for_completion=False,
        reset_dag_run=True,
    )

    trigger_emotion = TriggerDagRunOperator(
        task_id="trigger_emotion_classification",
        trigger_dag_id="dag_emotion_classification",
        wait_for_completion=False,
        reset_dag_run=True,
    )

    # vectorisation and emotion_classification are independent — run both
    nlp >> [trigger_vectorisation, trigger_emotion]


nlp_dag()
