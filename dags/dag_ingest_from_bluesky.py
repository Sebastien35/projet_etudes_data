"""
DAG: ingest_from_bluesky
========================
Fetches posts from the Bluesky API and stores them raw in MongoDB (collection: posts).

Schedule: every hour at :05 to avoid top-of-hour load spikes.

Pipeline nodes (sequential — intermediate dataset is in-memory):
  fetch_from_keywords_node  Search Bluesky by themed keywords (4 themes × N keywords,
                            25 posts/query, lang=en). Deduplicates against existing posts.
  save_posts_to_db_node     Bulk-inserts new posts into MongoDB.

On success: triggers dag_nlp_transform so the cleaning step
runs immediately after fresh data arrives.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from kedro_operator import KedroOperator

from airflow.decorators import dag
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

PIPELINE = "ingest_from_bluesky"

DEFAULT_ARGS = {
    "owner": "data-team",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "execution_timeout": timedelta(minutes=30),
    "email_on_failure": False,
    "email_on_retry": False,
}


@dag(
    dag_id="dag_ingest_from_bluesky",
    description="Fetch Bluesky posts by keywords and persist them to MongoDB.",
    schedule="5 * * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["kedro", "ingest", "bluesky"],
    doc_md=__doc__,
)
def ingest_dag():
    # ── Node 1: fetch from Bluesky API ────────────────────────────────────────
    # ── Node 2: save to MongoDB                                               -
    # Both nodes share an in-memory dataset (`posts` list), so they must run
    # inside the same KedroSession. The pipeline runs them sequentially.
    ingest = KedroOperator(
        task_id="ingest_from_bluesky",
        pipeline_name=PIPELINE,
        pool="default_pool",
    )

    # ── Trigger downstream NLP pipeline ───────────────────────────────────────
    trigger_nlp = TriggerDagRunOperator(
        task_id="trigger_nlp_transform",
        trigger_dag_id="dag_nlp_transform",
        wait_for_completion=False,  # fire-and-forget — nlp runs in its own DAG run
        reset_dag_run=True,
    )

    ingest >> trigger_nlp


ingest_dag()
