"""Shared KedroOperator used by all project DAGs."""

from __future__ import annotations

from pathlib import Path

from airflow.models import BaseOperator
from kedro.framework.project import configure_project
from kedro.framework.session import KedroSession

# Paths are resolved relative to the repo root mounted at /opt/airflow inside the container.
PROJECT_PATH = Path(__file__).parent.parent
PACKAGE_NAME = "projet_etudes"
ENV = "airflow"
CONF_SOURCE = str(PROJECT_PATH / "conf")


class KedroOperator(BaseOperator):
    """Execute a Kedro pipeline (or a subset of nodes) inside an AirflowSession."""

    def __init__(
        self,
        pipeline_name: str,
        node_names: list[str] | None = None,
        project_path: Path = PROJECT_PATH,
        package_name: str = PACKAGE_NAME,
        env: str = ENV,
        conf_source: str = CONF_SOURCE,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.pipeline_name = pipeline_name
        self.node_names = node_names
        self.project_path = project_path
        self.package_name = package_name
        self.env = env
        self.conf_source = conf_source

    def execute(self, context) -> None:
        configure_project(self.package_name)
        with KedroSession.create(
            self.project_path,
            env=self.env,
            conf_source=self.conf_source,
        ) as session:
            session.run(self.pipeline_name, node_names=self.node_names)
