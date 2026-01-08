import logging
import os
import sys
import pandas as pd
import re
import string
import unicodedata
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
    return list(posts_collection.find({"unique_id": {"$nin": cleaned_posts_ids}}))

def clean_text(df: pd.DataFrame) -> pd.DataFrame:
    
    URL_PATTERN = re.compile(r"http\S+|www\S+")
    MENTION_PATTERN = re.compile(r"@\w+")
    HASHTAG_PATTERN = re.compile(r"#\w+")
    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "]+",
        flags=re.UNICODE
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

def lemmatize_text(df: pd.DataFrame, nlp) -> pd.DataFrame:
    def _lemmatize(text: str) -> list[str]:
        doc = nlp(text)
        return [
            token.lemma_
            for token in doc
            if not token.is_stop and token.is_alpha
        ]

    df = df.copy()
    df["lemmas"] = df["normalized_text"].apply(_lemmatize)
    return df


posts = get_posts_to_treat()

if posts:
    df_posts = pd.DataFrame(posts)
    print("Initial Posts DataFrame:")
    print(df_posts.head())

    df_cleaned = clean_text(df_posts)
    print("Cleaned Posts DataFrame:")
    print(df_cleaned.head())
    df_normalized = normalize_text(df_cleaned)
    print("Normalized Posts DataFrame:")
    print(df_normalized.head())
    df_tokenized = tokenize_text(df_normalized)
    print("Tokenized Posts DataFrame:")
    print(df_tokenized.head())

    nlp = spacy.load("en_core_web_sm")
    df_lemmatized = lemmatize_text(df_tokenized, nlp)
    print("Lemmatized Posts DataFrame:")
    print(df_lemmatized.head())