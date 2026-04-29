import logging
import os
import re
import string
import sys
import unicodedata

import pandas as pd
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
    url_pattern = re.compile(r"http\S+|www\S+")
    mention_pattern = re.compile(r"@\w+")
    hashtag_pattern = re.compile(r"#\w+")
    emoji_pattern = re.compile(
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
        text = url_pattern.sub("", text)
        text = mention_pattern.sub("", text)
        text = hashtag_pattern.sub("", text)
        text = emoji_pattern.sub("", text)
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


def save_to_db(df: pd.DataFrame) -> int:
    cleaned_posts_collection = mongo.use_collection("cleaned_posts")
    records = df.to_dict(orient="records")
    for record in records:
        cleaned_posts_collection.insert_one(
            {
                "username": record["username"],
                "created_at": record["created_at"],
                "unique_id": record["unique_id"],
                "utc_saved_at": pd.Timestamp.now(),
                "category": record["category"],
                "normalized_text": record["normalized_text"],
            }
        )
    return len(records)
