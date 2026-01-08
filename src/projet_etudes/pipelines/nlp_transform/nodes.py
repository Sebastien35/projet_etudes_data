import logging
import os
import re
import string
import sys
import unicodedata

import pandas as pd
import spacy
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../../..")
from shared.mongo import mongo_client  # noqa

load_dotenv()

mongo = mongo_client()


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
    df["normalized_text"] = df["clean_text"].apply(_normalize)
    return df


def tokenize_text(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["tokens"] = df["normalized_text"].apply(lambda x: x.split(" "))
    return df


def lemmatize_text(df: pd.DataFrame) -> pd.DataFrame:
    nlp = spacy.load("en_core_web_sm")

    def _lemmatize(text: str) -> list[str]:
        doc = nlp(text)
        return [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]

    df = df.copy()
    df["lemmas"] = df["normalized_text"].apply(_lemmatize)
    return df


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
            "tokens": record["tokens"],
            "lemmas": record["lemmas"],
        }
        cleaned_posts_collection.insert_one(save_to_db)
    return len(records)
