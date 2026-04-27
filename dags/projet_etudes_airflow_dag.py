from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from kedro.framework.project import configure_project
from kedro.framework.session import KedroSession

from airflow import DAG
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults


class KedroOperator(BaseOperator):
    @apply_defaults
    def __init__(
        self,
        package_name: str,
        pipeline_name: str,
        project_path: str | Path,
        env: str,
        conf_source: str,
        node_name: str | list[str] | None = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.package_name = package_name
        self.pipeline_name = pipeline_name
        self.node_name = node_name
        self.project_path = project_path
        self.env = env
        self.conf_source = conf_source

    def execute(self, context):
        configure_project(self.package_name)
        with KedroSession.create(
            self.project_path, env=self.env, conf_source=self.conf_source
        ) as session:
            if isinstance(self.node_name, str):
                self.node_name = [self.node_name]
            session.run(self.pipeline_name, node_names=self.node_name)


# ── Shared settings ────────────────────────────────────────────────────────

PROJECT_PATH = Path(__file__).parent.parent  # /opt/airflow inside the container
PACKAGE_NAME = "projet_etudes"
ENV = "airflow"
CONF_SOURCE = str(PROJECT_PATH / "conf")

DEFAULT_ARGS = dict(
    owner="airflow",
    depends_on_past=False,
    email_on_failure=False,
    email_on_retry=False,
    retries=1,
    retry_delay=timedelta(minutes=5),
)


def kedro_task(dag: DAG, task_id: str, pipeline_name: str) -> KedroOperator:
    """Create a KedroOperator task that runs an entire pipeline in one session."""
    return KedroOperator(
        task_id=task_id,
        package_name=PACKAGE_NAME,
        pipeline_name=pipeline_name,
        project_path=PROJECT_PATH,
        env=ENV,
        conf_source=CONF_SOURCE,
        dag=dag,
    )


# ── DAG 1: ingest_from_bluesky ─────────────────────────────────────────────
# Fetches posts from the Bluesky API and saves them to MongoDB.
# Runs hourly so the dataset stays fresh.

with DAG(
    dag_id="ingest_from_bluesky",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@hourly",
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["kedro", "ingest"],
) as ingest_dag:
    kedro_task(ingest_dag, "ingest_from_bluesky", "ingest_from_bluesky")


# ── DAG 2: nlp_transform ───────────────────────────────────────────────────
# Cleans, lemmatizes, and emotion-classifies posts from MongoDB.
# Processes only posts not yet in cleaned_posts (incremental).
# Runs hourly, in step with ingestion.

with DAG(
    dag_id="nlp_transform",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@hourly",
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["kedro", "nlp"],
) as nlp_dag:
    kedro_task(nlp_dag, "nlp_transform", "nlp_transform")


# ── DAG 3: vectorisation ───────────────────────────────────────────────────
# Encodes cleaned posts with SBERT, clusters them, and persists
# embeddings to MongoDB and the RAG joblib file.
# Re-runs daily since clustering is computed over the full corpus.

with DAG(
    dag_id="vectorisation",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["kedro", "vectorisation"],
) as vectorisation_dag:
    kedro_task(vectorisation_dag, "vectorisation", "vectorisation")


# ── DAG 4: full_pipeline ───────────────────────────────────────────────────
# Runs all three pipelines end-to-end in the correct order.
# Useful for bootstrapping the system from scratch or for daily full runs.

with DAG(
    dag_id="full_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["kedro", "full"],
) as full_dag:
    ingest = kedro_task(full_dag, "ingest_from_bluesky", "ingest_from_bluesky")
    nlp = kedro_task(full_dag, "nlp_transform", "nlp_transform")
    vectorise = kedro_task(full_dag, "vectorisation", "vectorisation")

    ingest >> nlp >> vectorise
