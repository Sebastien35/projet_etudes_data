"""
Pipeline 'model_training' — LSTM fake news classifier training.

Expected catalog entries:
  true_news_data  →  data/01_raw/True.csv   (real articles)
  fake_news_data  →  data/01_raw/Fake.csv   (fake articles)

Download from: https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset

Run once before 'vectorisation':
  kedro run --pipeline model_training
"""

from kedro.pipeline import Node, Pipeline

from .nodes import (
    build_lstm_model,
    build_tokenizer_and_sequences,
    load_training_data,
    preprocess_training_data,
    save_lstm_artifacts,
    train_lstm,
)


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            Node(
                func=load_training_data,
                inputs=["true_news_data", "fake_news_data"],
                outputs="training_df",
                name="load_training_data_node",
            ),
            Node(
                func=preprocess_training_data,
                inputs="training_df",
                outputs=["X_train", "X_test", "y_train", "y_test"],
                name="preprocess_training_data_node",
            ),
            Node(
                func=build_tokenizer_and_sequences,
                inputs=[
                    "X_train",
                    "X_test",
                    "params:model_training.vocab_size",
                    "params:model_training.max_len",
                ],
                outputs=["X_train_pad", "X_test_pad", "tokenizer"],
                name="build_tokenizer_node",
            ),
            # Can run in parallel with build_tokenizer_node
            Node(
                func=build_lstm_model,
                inputs=[
                    "params:model_training.vocab_size",
                    "params:model_training.max_len",
                    "params:model_training.embedding_dim",
                ],
                outputs="lstm_model",
                name="build_lstm_model_node",
            ),
            Node(
                func=train_lstm,
                inputs=[
                    "X_train_pad",
                    "y_train",
                    "X_test_pad",
                    "y_test",
                    "lstm_model",
                    "params:model_training.epochs",
                    "params:model_training.batch_size",
                ],
                outputs="trained_lstm_model",
                name="train_lstm_node",
            ),
            Node(
                func=save_lstm_artifacts,
                inputs=[
                    "trained_lstm_model",
                    "tokenizer",
                    "params:model_training.model_path",
                    "params:model_training.tokenizer_path",
                ],
                outputs=None,
                name="save_lstm_artifacts_node",
            ),
        ]
    )
