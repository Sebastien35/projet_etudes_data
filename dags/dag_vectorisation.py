"""
DAG: vectorisation
==================
Vectorises cleaned Bluesky posts with TF-IDF, clusters them with KMeans (k=2),
persists predictions to MongoDB and exports model artefacts for the API.

Schedule: triggered by dag_nlp_transform after each NLP run, AND as a daily
safety net at 03:00 UTC to ensure artefacts are always up to date.

Key parameters (conf/base/parameters_vectorisation.yml):
  n_clusters:   2
  max_features: 5000
  vectorizer_path: data/06_models/tfidf_vectorizer.pkl
  kmeans_path:     data/06_models/kmeans_model.pkl

Pipeline nodes and their exact dependency graph:

  get_cleaned_posts_node  ──► texts   ──► vectorize_texts_node ──► tfidf_matrix ──► cluster_posts_node
        │                                         │                                        │
        │ posts_                                  │ tfidf_vectorizer                       │ labels, probs, km_model
        │                                         └────────────────────────────────────────┤
        │                                                                                  │
        │                                                                         save_model_artifacts_node
        │                                                                         (tfidf_vectorizer + km_model → pkl)
        │
        └──── posts_ ────┐
                         │                     cluster_posts_node
                    probs, labels ◄────────────────────┘
                         │
                  save_predictions_node
                  (posts_ + probs + labels → classified_posts)

All intermediate datasets (texts, posts_, tfidf_matrix, tfidf_vectorizer,
labels, probs, km_model) are in-memory Kedro MemoryDatasets — not persisted
in catalog.yml. The full pipeline therefore runs inside a single KedroSession.
Node-level Airflow tasks would require adding these intermediates to catalog.yml.

The exported pkl files are mounted into the `api` container via the
./data:/app/data Docker volume, so the FastAPI service picks up the
updated model on next cold start.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow.decorators import dag

from kedro_operator import KedroOperator

PIPELINE = "vectorisation"

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
    dag_id="dag_vectorisation",
    description="TF-IDF + KMeans clustering on cleaned posts; exports model artefacts for the API.",
    schedule="0 3 * * *",  # daily safety-net at 03:00 UTC; also triggered after nlp_transform
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["kedro", "vectorisation", "ml", "kmeans"],
    doc_md=__doc__,
)
def vectorisation_dag():
    # ── All 5 nodes run inside a single KedroSession ──────────────────────────
    # Kedro handles the internal fan-out (save_model_artifacts + save_predictions
    # both receive outputs of cluster_posts and run concurrently within the session).
    KedroOperator(
        task_id="vectorisation",
        pipeline_name=PIPELINE,
        pool="default_pool",
    )


vectorisation_dag()
