import logging
import os
import re
import string
import sys
import unicodedata

import nltk
import pandas as pd
from dotenv import load_dotenv
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from transformers import pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../../..")
from shared.mongo import mongo_client  # noqa

load_dotenv()


mongo = mongo_client()

EMOTION_MODEL_NAME = "nateraw/bert-base-uncased-emotion"
_emotion_classifier = None


def get_emotion_classifier():
    global _emotion_classifier
    if _emotion_classifier is None:
        logger.info("Loading emotion classifier model...")
        _emotion_classifier = pipeline(
            "text-classification", model=EMOTION_MODEL_NAME, return_all_scores=True
        )
    return _emotion_classifier


def get_posts_to_treat():
    posts_collection = mongo.use_collection("posts")
    cleaned_posts_collection = mongo.use_collection("cleaned_posts")
    cleaned_posts_ids = cleaned_posts_collection.distinct("unique_id")
    df = pd.DataFrame(
        list(posts_collection.find({"unique_id": {"$nin": cleaned_posts_ids}}))
    )
    return df


def clean_text(df: pd.DataFrame) -> pd.DataFrame:
    URL_PATTERN = re.compile(r"http\S+|www\S+")
    MENTION_PATTERN = re.compile(r"@\w+")
    HASHTAG_PATTERN = re.compile(r"#\w+")
    EMOJI_PATTERN = re.compile(
        "["
        "\U0001f600-\U0001f64f"
        "\U0001f300-\U0001f5ff"
        "\U0001f680-\U0001f6ff"
        "\U0001f1e0-\U0001f1ff"
        "]+",
        flags=re.UNICODE,
    )

    def _clean(text: str) -> str:
        text = text.lower()
        text = URL_PATTERN.sub("", text)
        text = MENTION_PATTERN.sub("", text)
        text = HASHTAG_PATTERN.sub("", text)
        text = EMOJI_PATTERN.sub("", text)
        text = text.translate(str.maketrans("", "", string.punctuation))
        return text

    df = df.copy()
    df["clean_text"] = df["text"].apply(_clean)
    return df


def normalize_text(df: pd.DataFrame) -> pd.DataFrame:
    def _normalize(text: str) -> str:
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("utf-8")
        text = re.sub(r"\s+", " ", text).strip()
        return text

    df = df.copy()
    if "clean_text" not in df.columns:
        raise ValueError("Column 'clean_text' missing")
    df["normalized_text"] = df["clean_text"].apply(_normalize)
    return df


def lemmatize_text(df: pd.DataFrame) -> pd.DataFrame:
    nltk.download("wordnet", quiet=True)
    nltk.download("stopwords", quiet=True)
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words("english"))

    def _lemmatize(text: str) -> list[str]:
        return [
            lemmatizer.lemmatize(token)
            for token in text.split()
            if token.isalpha() and token.lower() not in stop_words
        ]

    df = df.copy()
    if "normalized_text" not in df.columns:
        raise ValueError("Column 'normalized_text' missing")
    df["lemmas"] = df["normalized_text"].apply(_lemmatize)
    return df


def classify_emotion(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "normalized_text" not in df.columns:
        raise ValueError("Column 'normalized_text' missing")

    def _predict_emotion(text: str):
        if not isinstance(text, str) or not text.strip():
            return {"emotion": None, "score": None, "all_scores": []}
        try:
            raw = get_emotion_classifier()(text, return_all_scores=True)
            # Toujours récupérer une liste de dicts
            if isinstance(raw, list) and len(raw) > 0:
                scores = raw[0] if isinstance(raw[0], list) else [raw[0]]
            elif isinstance(raw, dict):
                scores = [raw]
            else:
                scores = []

            if scores:
                best = max(scores, key=lambda x: x["score"])
                return {
                    "emotion": best["label"],
                    "score": best["score"],
                    "all_scores": scores,
                }
            return {"emotion": None, "score": None, "all_scores": []}

        except Exception as e:
            logger.warning(f"Emotion classification failed: {e}")
            return {"emotion": None, "score": None, "all_scores": []}

    preds = df["normalized_text"].apply(_predict_emotion)
    df["emotion"] = preds.apply(lambda x: x["emotion"])
    df["emotion_score"] = preds.apply(lambda x: x["score"])
    df["emotion_all_scores"] = preds.apply(lambda x: x["all_scores"])
    return df


def merge_features(
    lemmatized_df: pd.DataFrame, emotion_df: pd.DataFrame
) -> pd.DataFrame:
    emotion_cols = emotion_df[
        ["unique_id", "emotion", "emotion_score", "emotion_all_scores"]
    ]
    return lemmatized_df.merge(emotion_cols, on="unique_id", how="left")


def save_to_db(df: pd.DataFrame) -> int:
    cleaned_posts_collection = mongo.use_collection("cleaned_posts")
    records = df.to_dict(orient="records")
    for record in records:
        save_to_db = {
            "username": record["username"],
            "created_at": record["created_at"],
            "unique_id": record["unique_id"],
            "utc_saved_at": pd.Timestamp.now(),
            "category": record["category"],
            "normalized_text": record["normalized_text"],
            "lemmas": record["lemmas"],
            "emotion": record.get("emotion"),
            "emotion_score": record.get("emotion_score"),
            "emotion_all_scores": record.get("emotion_all_scores"),
        }
        cleaned_posts_collection.insert_one(save_to_db)
    return len(records)
