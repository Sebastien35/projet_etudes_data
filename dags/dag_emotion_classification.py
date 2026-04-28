"""
DAG: emotion_classification
============================
Classifies the emotion of each cleaned Bluesky post using a pre-trained
BERT-based model (j-hartmann/emotion-english-distilroberta-base —
DistilRoBERTa fine-tuned on Ekman's 7 emotions).

Emotions: anger · disgust · fear · joy · neutral · sadness · surprise

Schedule: None — triggered by dag_nlp_transform after each successful run,
or manually via the Airflow UI.

Pipeline nodes (sequential, all intermediates in-memory):
  get_posts_for_emotion_node    Incremental fetch from cleaned_posts;
                                excludes unique_ids already in emotion_posts.
  classify_emotions_bert_node   Batch inference with HuggingFace transformers
                                (batch_size=16, max_length=128, CPU).
  save_emotion_results_node     Bulk upsert into MongoDB emotion_posts.

First run downloads the model (~300 MB) to ~/.cache/huggingface/hub/.
Subsequent runs reuse the local cache. Mount a named volume on
/home/airflow/.cache/huggingface to persist the cache across restarts.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow.decorators import dag

from kedro_operator import KedroOperator

PIPELINE = "emotion_classification"

DEFAULT_ARGS = {
    "owner": "data-team",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
    # First inference can be slow on CPU (model download + warm-up)
    "execution_timeout": timedelta(hours=3),
    "email_on_failure": False,
    "email_on_retry": False,
}


@dag(
    dag_id="dag_emotion_classification",
    description="BERT emotion classification of Bluesky posts (triggered after nlp_transform).",
    schedule=None,  # triggered by dag_nlp_transform
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["kedro", "emotion", "bert", "nlp"],
    doc_md=__doc__,
)
def emotion_dag():
    KedroOperator(
        task_id="emotion_classification",
        pipeline_name=PIPELINE,
        pool="default_pool",
    )


emotion_dag()
