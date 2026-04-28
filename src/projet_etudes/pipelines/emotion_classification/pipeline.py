"""
Pipeline 'emotion_classification'
==================================
Classifies the emotion of each cleaned Bluesky post using a pre-trained
BERT-based model (DistilRoBERTa fine-tuned on Ekman's 7 emotions).

Flow:
  get_posts_for_emotion ──► classify_emotions_bert ──► save_emotion_results

All intermediates are in-memory; the full pipeline runs inside a single
KedroSession. Processing is incremental: only posts whose unique_id is
not already in the emotion_posts collection are classified.
"""

from kedro.pipeline import Node, Pipeline

from .nodes import classify_emotions_bert, get_posts_for_emotion, save_emotion_results


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            Node(
                func=get_posts_for_emotion,
                inputs=None,
                outputs=["emotion_texts", "emotion_posts_input"],
                name="get_posts_for_emotion_node",
            ),
            Node(
                func=classify_emotions_bert,
                inputs=[
                    "emotion_texts",
                    "emotion_posts_input",
                    "params:emotion_classification.model_name",
                    "params:emotion_classification.max_length",
                    "params:emotion_classification.batch_size",
                ],
                outputs="emotion_results",
                name="classify_emotions_bert_node",
            ),
            Node(
                func=save_emotion_results,
                inputs="emotion_results",
                outputs=None,
                name="save_emotion_results_node",
            ),
        ]
    )
