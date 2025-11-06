from __future__ import annotations

import logging
import sys
import time
from pprint import pprint
#from ../../src/projet_etudes/pipelines/extract.py import get_posts

import pendulum

# Importing operators
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import (
    PythonOperator,
    PythonVirtualenvOperator,
)
from airflow.sdk import DAG

log = logging.getLogger(__name__)

import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
PYTHON_BIN = os.path.join(PROJECT_ROOT, "venv", "bin", "python")
EXTRACT_SCRIPT = os.path.join(PROJECT_ROOT, "src", "projet_etudes", "pipelines", "extract.py")

with DAG(
    dag_id="run_get_posts",
    schedule="*/3 * * * *",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    tags=["extract", "posts"],
) as dag:
    # [START howto_operator_python]
    def print_context(ds=None, **kwargs):
        log.info("Lancement de l'extraction des posts Bluesky \n")

    call_python = PythonOperator(task_id="call_ETL", python_callable=print_context)
    # [END howto_operator_python]

    # [START howto_operator_bash]
    call_bash = BashOperator(
        task_id="call_bash",
        bash_command=f"echo 'Lancement extraction Bluesky'; {PYTHON_BIN} {EXTRACT_SCRIPT}",
    )
    # [END howto_operator_bash]

