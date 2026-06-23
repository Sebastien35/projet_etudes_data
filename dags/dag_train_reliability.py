"""
DAG: train_reliability
======================
Trains the supervised reliability classifier (embedding + LogReg) on labeled
posts from MongoDB and exports the model artefact for the API.

Schedule: triggered by dag_vectorisation after each run, AND as a weekly
safety net on Sundays at 01:00 UTC.

Pipeline nodes:
  get_reliability_training_data_node   Fetches labeled posts from MongoDB
                                       (reliable vs misinfo) with minimum
                                       sample thresholds.
  train_reliability_classifier_node    Embeds texts and fits a LogReg
                                       classifier on the embeddings.
  save_reliability_model_node          Persists the model artefact to disk
                                       (mounted into the API container).
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow.decorators import dag

from kedro_operator import KedroOperator

PIPELINE = "train_reliability"

DEFAULT_ARGS = {
    "owner": "data-team",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
    "execution_timeout": timedelta(hours=2),
    "email_on_failure": False,
    "email_on_retry": False,
}


@dag(
    dag_id="dag_train_reliability",
    description="Train reliability classifier (embedding + LogReg); exports artefact for the API.",
    schedule="0 1 * * 0",  # weekly Sunday 01:00 UTC; also triggered after dag_vectorisation
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["kedro", "train", "reliability", "ml"],
    doc_md=__doc__,
)
def train_reliability_dag():
    KedroOperator(
        task_id="train_reliability",
        pipeline_name=PIPELINE,
        pool="default_pool",
    )


train_reliability_dag()
