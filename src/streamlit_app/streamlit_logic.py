import pandas as pd
import random
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from collections import Counter
from streamlit_color_chart import ColorChart

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../..")

from shared.mongo import mongo_client  # noqa

load_dotenv()

mongo = mongo_client()

# =====================================================
# COLOR PALETTE
# =====================================================
BG_MAIN        = ColorChart.get_bg_main()
BG_SIDEBAR     = ColorChart.get_bg_sidebar()
BG_CARD        = ColorChart.get_bg_card()
ACCENT_PRIMARY = ColorChart.get_accent_primary()
ACCENT_SOFT    = ColorChart.get_accent_soft()
TEXT_MAIN      = ColorChart.get_text_main()
TEXT_MUTED     = ColorChart.get_text_muted()
SUCCESS_COLOR  = ColorChart.get_success_color()
WARNING_COLOR  = ColorChart.get_warning_color()

# =====================================================
# CHAT BOT FUNCTIONS
# =====================================================

def fake_news_model(text: str):
    verdict = random.choice(["FAKE", "REAL", "UNCERTAIN"])

    color = {
        "FAKE": WARNING_COLOR,
        "REAL": SUCCESS_COLOR,
        "UNCERTAIN": ACCENT_SOFT,
    }[verdict]

    explanation = {
        "FAKE": "Linguistic patterns and emotional bias strongly indicate misinformation.",
        "REAL": "Content aligns with verified sources and neutral phrasing.",
        "UNCERTAIN": "Insufficient signals to confidently classify this content.",
    }[verdict]

    return verdict, color, explanation

# =====================================================
# GRAPHES FUNCTIONS
# =====================================================


# Chargement des données
def load_posts():
    return pd.DataFrame({
        "country": ["FR", "US", "US", "DE", "FR", "IT", "FR", "UK"],
        "keyword": ["election", "covid", "election", "war", "covid", "war", "election", "migration"],
        "timestamp": pd.date_range(end=datetime.now(), periods=8, freq="H"),
    })

def get_posts():
    posts_collection = mongo.use_collection("cleaned_posts")
    df = pd.DataFrame(
        list(posts_collection.find({},{"_id": 0,"username": 1,"created_at": 1,"category": 1,"lemmas": 1,}))
    )
    df["created_at"] = pd.to_datetime(df["created_at"], format="ISO8601", utc=True)
    return df

# Top publicateurs par categrorie
def top_users_per_category(df: pd.DataFrame, top_k: int = 10) -> pd.DataFrame:
    df = df.copy()

    # Group by category and username, count posts
    grouped = df.groupby(['category', 'username']).size().reset_index(name='post_count')

    # Sort by category and post_count descending
    grouped = grouped.sort_values(['category', 'post_count'], ascending=[True, False])

    # Take top_k per category
    top_users = grouped.groupby('category').head(top_k).reset_index(drop=True)

    return top_users


# Tendances
def trending_keywords(df: pd.DataFrame, top_k: int = 20) -> pd.DataFrame:
    counter = Counter()

    LEMMAS_BLACKLIST = {"be", "have", "do", "not", "say", "get", "make", "go", "know", "see", "use", "would", "could", "should","de","la","le","et","les","des","un","une","pour","dans","que","qui","sur","pas","plus","ne","au","aux"}

    for lemmas in df["lemmas"]:
        filtered = [
            lemma
            for lemma in lemmas
            if lemma not in LEMMAS_BLACKLIST
            and len(lemma) > 1
            and lemma.isalpha()
        ]
        counter.update(filtered)

    return pd.DataFrame(
        counter.most_common(top_k),
        columns=["keyword", "count"]
    )

# Nb de posts par heure
def posts_per_hour(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["hour"] = df["created_at"].dt.hour

    return (
        df.groupby("hour")
        .size()
        .reset_index(name="count")
        .sort_values("hour")
    )
