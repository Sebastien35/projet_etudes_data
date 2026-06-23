"""
DAG: train_finetuned
====================
Fine-tunes xlm-roberta-base on labeled Bluesky posts from MongoDB and saves
the model to disk for the API's primary classifier.

Schedule: weekly on Sundays at 02:00 UTC. Can also be triggered manually
from the Airflow UI when new labeled data is available.

Pipeline nodes:
  get_finetuning_data_node      Fetches labeled posts from MongoDB with
                                minimum sample thresholds (reliable + misinfo).
  finetune_xlm_roberta_node     Fine-tunes xlm-roberta-base and saves the
                                model checkpoint to data/06_models/xlm_roberta_finetuned.

Note: first run downloads xlm-roberta-base (~1 GB) from HuggingFace Hub.
Fine-tuning is CPU-only and may take several hours depending on dataset size.
The model path is mounted into the API container via ./data:/app/data so the
API picks up the updated model on next restart.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow.decorators import dag

from kedro_operator import KedroOperator

PIPELINE = "train_finetuned"

DEFAULT_ARGS = {
    "owner": "data-team",
    "depends_on_past": False,
    "retries": 0,
    "execution_timeout": timedelta(hours=12),
    "email_on_failure": False,
    "email_on_retry": False,
}


@dag(
    dag_id="dag_train_finetuned",
    description="Fine-tune XLM-RoBERTa on labeled posts; exports model artefact for the API.",
    schedule="0 2 * * 0",  # weekly Sunday 02:00 UTC (after train_reliability)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["kedro", "train", "xlm-roberta", "finetuned", "ml"],
    doc_md=__doc__,
)
def train_finetuned_dag():
    KedroOperator(
        task_id="train_finetuned",
        pipeline_name=PIPELINE,
        pool="default_pool",
    )


train_finetuned_dag()
