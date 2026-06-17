"""Project pipelines."""

from kedro.pipeline import Pipeline

from projet_etudes.pipelines.emotion_classification.pipeline import (
    create_pipeline as emotion_pipeline,
)
from projet_etudes.pipelines.ingest_from_bluesky.pipeline import (
    create_pipeline as ingest_pipeline,
)
from projet_etudes.pipelines.nlp_transform.pipeline import (
    create_pipeline as nlp_pipeline,
)
from projet_etudes.pipelines.train_finetuned.pipeline import (
    create_pipeline as finetuned_pipeline,
)
from projet_etudes.pipelines.vectorisation.pipeline import (
    create_pipeline as vectorisation_pipeline,
)
from projet_etudes.pipelines.vectorisation.pipeline import create_reliability_pipeline


def register_pipelines() -> dict[str, Pipeline]:
    """Register the project's pipelines."""
    pipelines = {
        "ingest_from_bluesky": ingest_pipeline(),
        "nlp_transform": nlp_pipeline(),
        "vectorisation": vectorisation_pipeline(),
        "train_reliability": create_reliability_pipeline(),
        "emotion_classification": emotion_pipeline(),
        "train_finetuned": finetuned_pipeline(),
    }
    pipelines["__default__"] = (
        pipelines["ingest_from_bluesky"]
        + pipelines["nlp_transform"]
        + pipelines["vectorisation"]
        + pipelines["emotion_classification"]
    )
    return pipelines
