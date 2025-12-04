import logging
import os
import sys
from datetime import datetime

from atproto import Client
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../../..")
from shared.mongo import mongo_client  # noqa

load_dotenv()

mongo = mongo_client()


def get_client() -> Client:
    """Authenticate and return a Bluesky client."""
    BSKY_PWD = os.getenv("BSKY_APP_PASSWORD")
    BSKY_USERNAME = os.getenv("BSKY_USERNAME")

    if not BSKY_PWD or not BSKY_USERNAME:
        raise ValueError(
            "BSKY_PWD and BSKY_USERNAME must be set in environment variables"
        )

    client = Client()
    client.login(BSKY_USERNAME, BSKY_PWD)
    return client


def validate_handle(client: Client, username: str) -> bool:
    """Check if the Bluesky handle exists."""
    try:
        client.app.bsky.actor.get_profile({"actor": username})
        return True
    except Exception:
        return False


def format_posts(client: Client, username: str, category: str, limit: int = 10) -> list:
    """
    Fetch posts from a Bluesky user and return formatted post objects.
    
    Returns list of dicts containing:
    - username
    - text
    - created_at
    - category
    """
    response = client.app.bsky.feed.get_author_feed(
        params={"actor": username, "limit": limit}
    )
    existing_posts = mongo.use_collection("posts").distinct("unique_id")

    formatted_posts = []

    for item in response.feed:
        unique_id = f"{username}_{item.post.record.created_at}"
        if unique_id in existing_posts:
            continue
        
        post = item.post
        record = post.record

        text = getattr(record, "text", None)
        created_at = getattr(record, "created_at", None)

        if text and created_at:
            formatted_posts.append(
                {
                    "username": username,
                    "text": text,
                    "created_at": created_at,
                    "category": category,
                }
            )

    return formatted_posts


def save_posts_to_db(posts: list) -> int:
    """Save posts to MongoDB and return count."""
    for post in posts:
        save_to_db = {
            "text": post["text"],
            "username": post["username"],
            "created_at": post["created_at"],
            "unique_id": f"{post['username']}_{post['created_at']}",
            "utc_saved_at": datetime.now(),
            "category": post["category"],
        }
        conn = mongo.use_collection("posts")
        conn.insert_one(save_to_db)
    
    return len(posts)


def fetch_from_trusted_sources() -> list:
    """Fetch posts from trusted news and topic sources."""

    client = get_client()

    data_sources = {
        "news": [
            "apnews.bsky.social",
            "axios.com",
            "washingtonpost.com",
            "theguardian.com",
            "nytimes.com",
            "bbc.com",
            "abcnews.bsky.social",
            "bloomberg.bsky.social",
            "skynews.com",
            "aljazeera.com",
        ],
        "tech": [
            "techcrunch.com",
            "verge.bsky.social",
            "wired.com",
            "arstechnica.com",
        ],
        "science": [
            "noaa.bsky.social",
            "nasa.gov",
            "esa.int",
            "nature.com",
        ],
        "fact_checking": [
            "politifact.com",
            "snopes.com",
            "fullfact.org",
            "leadstories.com",
            "factcheck.org",
        ],
    }

    untrusted = []
    data = []
    
    for category, sources in data_sources.items():
        for source in sources:
            if not validate_handle(client, source):
                untrusted.append(source)
                continue
            posts = format_posts(client, source, category, limit=5)
            data.extend(posts)

    logger.info(f"Fetched {len(data)} posts from trusted sources.")
    if untrusted:
        logger.warning(f"Untrusted sources: {untrusted}")
    
    return data