import logging
import os
import sys
from collections import Counter

import pandas as pd
import requests
from dotenv import load_dotenv
from streamlit_color_chart import ColorChart
from streamlit_config import StreamlitConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../..")

from shared.mongo import mongo_client  # noqa

load_dotenv()

mongo = mongo_client()


def send_message_api(message: str) -> dict:
    url = StreamlitConfig().api_url + "ask"
    try:
        response = requests.post(url, json={"question": message}, timeout=120)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"API error: {e}")
        return {
            "verdict": "error",
            "color": ColorChart.DANGER_COLOR,
            "explanation": "Could not reach the API.",
            "probability": None,
            "based_on": "error",
        }

    verdict = data.get("verdict", "uncertain")
    return {
        "verdict": verdict,
        "color": ColorChart.verdict_color(verdict),
        "explanation": data.get("explanation", ""),
        "probability": data.get("probability"),
        "based_on": data.get("based_on", "unknown"),
    }


def get_posts() -> pd.DataFrame:
    collection = mongo.use_collection("cleaned_posts")
    df = pd.DataFrame(
        list(
            collection.find(
                {},
                {
                    "_id": 0,
                    "username": 1,
                    "created_at": 1,
                    "category": 1,
                    "lemmas": 1,
                    "emotion": 1,
                },
            )
        )
    )
    if df.empty:
        return df
    df["created_at"] = pd.to_datetime(df["created_at"], format="ISO8601", utc=True)
    return df


def top_users_per_category(df: pd.DataFrame, top_k: int = 10) -> pd.DataFrame:
    grouped = (
        df.groupby(["category", "username"])
        .size()
        .reset_index(name="post_count")
        .sort_values(["category", "post_count"], ascending=[True, False])
    )
    return grouped.groupby("category").head(top_k).reset_index(drop=True)


def trending_keywords(df: pd.DataFrame, top_k: int = 20) -> pd.DataFrame:
    BLACKLIST = {
        "be",
        "have",
        "do",
        "not",
        "say",
        "get",
        "make",
        "go",
        "know",
        "see",
        "use",
        "would",
        "could",
        "should",
        "de",
        "la",
        "le",
        "et",
        "les",
        "des",
        "un",
        "une",
        "pour",
        "dans",
        "que",
        "qui",
        "sur",
        "pas",
        "plus",
        "ne",
        "au",
        "aux",
    }
    counter = Counter()
    for lemmas in df["lemmas"]:
        counter.update(
            w for w in lemmas if w not in BLACKLIST and len(w) > 1 and w.isalpha()
        )
    return pd.DataFrame(counter.most_common(top_k), columns=["keyword", "count"])


def posts_per_hour(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["hour"] = df["created_at"].dt.hour
    return df.groupby("hour").size().reset_index(name="count").sort_values("hour")


def emotion_distribution(df: pd.DataFrame) -> pd.DataFrame:
    if "emotion" not in df.columns:
        return pd.DataFrame(columns=["emotion", "count"])
    return (
        df[df["emotion"].notna()]
        .groupby("emotion")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )
