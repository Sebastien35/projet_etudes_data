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

from shared.energy_service import get_energy_logs  # noqa
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
                    "normalized_text": 1,
                },
            )
        )
    )
    if df.empty:
        return df
    df["created_at"] = pd.to_datetime(df["created_at"], format="ISO8601", utc=True)
    return df


def get_classified_posts() -> pd.DataFrame:
    """Fetch posts classified by KMeans clustering (fake/real labels)."""
    collection = mongo.use_collection("classified_posts")
    df = pd.DataFrame(
        list(
            collection.find(
                {},
                {
                    "_id": 0,
                    "username": 1,
                    "category": 1,
                    "is_real": 1,
                    "fake_news_prob": 1,
                    "classified_at": 1,
                },
            )
        )
    )
    if df.empty:
        return df
    df["classified_at"] = pd.to_datetime(df["classified_at"], utc=True)
    df["label"] = df["is_real"].map({True: "Real", False: "Fake"})
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
        "be", "have", "do", "not", "say", "get", "make", "go", "know", "see",
        "use", "would", "could", "should", "the", "a", "an", "is", "it", "in",
        "of", "to", "and", "or", "for", "on", "at", "by", "with", "this",
        "de", "la", "le", "et", "les", "des", "un", "une", "pour", "dans",
        "que", "qui", "sur", "pas", "plus", "ne", "au", "aux",
    }
    counter = Counter()
    for text in df["normalized_text"].dropna():
        counter.update(
            w for w in text.split()
            if w not in BLACKLIST and len(w) > 2 and w.isalpha()
        )
    return pd.DataFrame(counter.most_common(top_k), columns=["keyword", "count"])


def posts_per_hour(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["hour"] = df["created_at"].dt.hour
    return df.groupby("hour").size().reset_index(name="count").sort_values("hour")


def fake_real_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Distribution of fake vs real posts from classified_posts collection."""
    if df.empty or "label" not in df.columns:
        return pd.DataFrame(columns=["label", "count"])
    return (
        df.groupby("label")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )


# ── Energy monitoring ──────────────────────────────────────────────────────

def get_energy_df() -> pd.DataFrame:
    """Load energy logs from MongoDB and return as a DataFrame."""
    logs = get_energy_logs()
    if not logs:
        return pd.DataFrame()
    df = pd.DataFrame(logs)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    # Convert to more readable units
    df["energy_wh"] = df["energy_kwh"] * 1000
    df["cpu_energy_wh"] = df["cpu_energy_kwh"] * 1000
    df["gpu_energy_wh"] = df["gpu_energy_kwh"] * 1000
    df["ram_energy_wh"] = df["ram_energy_kwh"] * 1000
    df["co2_mg"] = df["co2_kg"] * 1_000_000
    return df


def energy_by_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("pipeline_name")
        .agg(
            total_wh=("energy_wh", "sum"),
            total_co2_mg=("co2_mg", "sum"),
            runs=("run_id", "nunique"),
            total_duration_s=("duration_s", "sum"),
        )
        .reset_index()
        .sort_values("total_wh", ascending=False)
    )


def energy_by_node(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["pipeline_name", "node_name"])
        .agg(
            avg_wh=("energy_wh", "mean"),
            total_wh=("energy_wh", "sum"),
            avg_cpu_wh=("cpu_energy_wh", "mean"),
            avg_gpu_wh=("gpu_energy_wh", "mean"),
            avg_ram_wh=("ram_energy_wh", "mean"),
            avg_duration_s=("duration_s", "mean"),
            runs=("run_id", "count"),
        )
        .reset_index()
        .sort_values("total_wh", ascending=False)
    )


def energy_timeline(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["run_id", "pipeline_name", "timestamp"])
        .agg(total_wh=("energy_wh", "sum"), total_co2_mg=("co2_mg", "sum"))
        .reset_index()
        .sort_values("timestamp")
    )
