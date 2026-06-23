"""
Pipeline 'train_finetuned' — fine-tune xlm-roberta-base on labeled Bluesky posts.

Flow:
  get_finetuning_data ──► finetune_xlm_roberta ──► (model saved to disk)
"""

from kedro.pipeline import Node, Pipeline

from .nodes import finetune_xlm_roberta, get_finetuning_data


def create_pipeline(**_kwargs) -> Pipeline:
    return Pipeline(
        [
            Node(
                func=get_finetuning_data,
                inputs=[
                    "params:train_finetuned.min_reliable",
                    "params:train_finetuned.min_misinfo",
                ],
                outputs=["ft_texts", "ft_labels"],
                name="get_finetuning_data_node",
            ),
            Node(
                func=finetune_xlm_roberta,
                inputs=[
                    "ft_texts",
                    "ft_labels",
                    "params:train_finetuned.model_name",
                    "params:train_finetuned.max_length",
                    "params:train_finetuned.batch_size",
                    "params:train_finetuned.num_epochs",
                    "params:train_finetuned.learning_rate",
                    "params:train_finetuned.unfreeze_layers",
                    "params:train_finetuned.model_path",
                ],
                outputs="ft_model_path",
                name="finetune_xlm_roberta_node",
            ),
        ]
    )
