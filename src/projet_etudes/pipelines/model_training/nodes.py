"""
Model-training nodes for the LSTM fake news classifier.

Training data — two separate CSVs (Kaggle "Fake and Real News Dataset" layout):
  - true_news_data  : articles labelled REAL  (True.csv)
  - fake_news_data  : articles labelled FAKE  (Fake.csv)

Both files are expected to contain at least a 'text' column.
'title' is concatenated when present, matching the Kaggle notebook approach.
"""

import logging
import pickle
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import Dense, Dropout, Embedding, LSTM
from tensorflow.keras.models import Sequential
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer

logger = logging.getLogger(__name__)


def load_training_data(
    true_news: pd.DataFrame, fake_news: pd.DataFrame
) -> pd.DataFrame:
    """
    Combine True.csv (label=1) and Fake.csv (label=0) into a single
    labelled DataFrame.  Concatenates title + text when both columns exist,
    matching the Kaggle notebook pre-processing step.
    """
    def _prepare(df: pd.DataFrame, label: int) -> pd.DataFrame:
        df = df.copy()
        if "title" in df.columns and "text" in df.columns:
            df["text"] = df["title"].fillna("") + " " + df["text"].fillna("")
        elif "text" not in df.columns:
            raise ValueError(f"DataFrame for label={label} has no 'text' column")
        df["label"] = label
        return df[["text", "label"]]

    combined = (
        pd.concat([_prepare(true_news, 1), _prepare(fake_news, 0)], ignore_index=True)
        .dropna(subset=["text"])
        .drop_duplicates(subset=["text"])
        .sample(frac=1, random_state=42)  # shuffle
        .reset_index(drop=True)
    )

    logger.info(
        f"Training set: {len(combined)} samples "
        f"(real: {(combined['label'] == 1).sum()}, fake: {(combined['label'] == 0).sum()})"
    )
    return combined


def preprocess_training_data(
    df: pd.DataFrame,
) -> tuple[list, list, list, list]:
    """
    Clean text and produce stratified train / test splits.

    Returns:
        X_train, X_test, y_train, y_test
    """
    URL_PATTERN = re.compile(r"http\S+|www\S+")

    def _clean(text: str) -> str:
        text = str(text).lower()
        text = URL_PATTERN.sub("", text)
        text = re.sub(r"[^a-z\s]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    df = df.copy()
    df["clean_text"] = df["text"].apply(_clean)
    # Drop rows that became empty after cleaning
    df = df[df["clean_text"].str.strip().astype(bool)]

    X_train, X_test, y_train, y_test = train_test_split(
        df["clean_text"].tolist(),
        df["label"].tolist(),
        test_size=0.2,
        random_state=42,
        stratify=df["label"],
    )
    logger.info(f"Train: {len(X_train)} | Test: {len(X_test)}")
    return X_train, X_test, y_train, y_test


def build_tokenizer_and_sequences(
    X_train: list,
    X_test: list,
    vocab_size: int,
    max_len: int,
) -> tuple:
    """
    Fit a Keras Tokenizer on training data and pad both splits.

    Returns:
        X_train_pad, X_test_pad, tokenizer
    """
    tokenizer = Tokenizer(num_words=vocab_size, oov_token="<OOV>")
    tokenizer.fit_on_texts(X_train)

    X_train_pad = pad_sequences(
        tokenizer.texts_to_sequences(X_train),
        maxlen=max_len,
        padding="post",
        truncating="post",
    )
    X_test_pad = pad_sequences(
        tokenizer.texts_to_sequences(X_test),
        maxlen=max_len,
        padding="post",
        truncating="post",
    )

    logger.info(
        f"Vocabulary: {len(tokenizer.word_index)} words, using top {vocab_size}. "
        f"Sequences padded to {max_len}."
    )
    return X_train_pad, X_test_pad, tokenizer


def build_lstm_model(vocab_size: int, max_len: int, embedding_dim: int) -> Sequential:
    """
    LSTM architecture matching the Kaggle notebook:

      Embedding → LSTM(128, return_sequences) → Dropout →
      LSTM(64) → Dropout → Dense(32, relu) → Dense(1, sigmoid)
    """
    model = Sequential(
        [
            Embedding(input_dim=vocab_size, output_dim=embedding_dim, input_length=max_len),
            LSTM(128, return_sequences=True),
            Dropout(0.5),
            LSTM(64),
            Dropout(0.5),
            Dense(32, activation="relu"),
            Dense(1, activation="sigmoid"),
        ]
    )
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    model.summary(print_fn=logger.info)
    return model


def train_lstm(
    X_train_pad,
    y_train: list,
    X_test_pad,
    y_test: list,
    model: Sequential,
    epochs: int,
    batch_size: int,
) -> Sequential:
    """Train the LSTM with early stopping on validation accuracy."""
    early_stop = EarlyStopping(
        monitor="val_accuracy", patience=3, restore_best_weights=True
    )

    history = model.fit(
        X_train_pad,
        np.array(y_train),
        validation_data=(X_test_pad, np.array(y_test)),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=[early_stop],
    )

    val_acc = max(history.history["val_accuracy"])
    logger.info(f"Best val accuracy: {val_acc:.4f}")
    return model


def save_lstm_artifacts(
    model: Sequential,
    tokenizer: Tokenizer,
    model_path: str,
    tokenizer_path: str,
) -> None:
    """Persist Keras model (.keras) and Tokenizer (pickle)."""
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    Path(tokenizer_path).parent.mkdir(parents=True, exist_ok=True)

    model.save(model_path)
    with open(tokenizer_path, "wb") as f:
        pickle.dump(tokenizer, f)

    logger.info(f"Model saved  → {model_path}")
    logger.info(f"Tokenizer saved → {tokenizer_path}")
