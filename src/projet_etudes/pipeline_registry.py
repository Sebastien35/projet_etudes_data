"""Project pipelines."""

from kedro.pipeline import Pipeline

from projet_etudes.pipelines.ingest_from_bluesky.pipeline import (
    create_pipeline as ingest_pipeline,
)
from projet_etudes.pipelines.model_training.pipeline import (
    create_pipeline as model_training_pipeline,
)
from projet_etudes.pipelines.nlp_transform.pipeline import (
    create_pipeline as nlp_pipeline,
)
from projet_etudes.pipelines.vectorisation.pipeline import (
    create_pipeline as vectorisation_pipeline,
)


def register_pipelines() -> dict[str, Pipeline]:
    """Register the project's pipelines."""
    pipelines = {
        "ingest_from_bluesky": ingest_pipeline(),
        "nlp_transform": nlp_pipeline(),
        "model_training": model_training_pipeline(),
        "vectorisation": vectorisation_pipeline(),
    }
    # __default__ excludes model_training — that's a one-off training step
    pipelines["__default__"] = (
        pipelines["ingest_from_bluesky"]
        + pipelines["nlp_transform"]
        + pipelines["vectorisation"]
    )
    return pipelines
