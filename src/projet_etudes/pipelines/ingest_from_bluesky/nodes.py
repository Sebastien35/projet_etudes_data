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
    bsky_pwd = os.getenv("BSKY_APP_PASSWORD")
    bsky_username = os.getenv("BSKY_USERNAME")

    if not bsky_pwd or not bsky_username:
        raise ValueError(
            "bsky_pwd and bsky_username must be set in environment variables"
        )

    client = Client()
    client.login(bsky_username, bsky_pwd)
    return client


def validate_handle(client: Client, username: str) -> bool:
    """Check if the Bluesky handle exists."""
    try:
        client.app.bsky.actor.get_profile({"actor": username})
        return True
    except Exception:
        return False


def is_reliable_source(handle: str, reliable_domains: list) -> bool:
    """Return True if the handle belongs to a trusted news outlet or gov agency.

    Matches exact domain handles (e.g. reuters.com) and subdomains
    (e.g. journalist.reuters.com), but not prefix matches (fakereuters.com).
    """
    h = handle.lower()
    return any(h == domain or h.endswith("." + domain) for domain in reliable_domains)


def format_posts(
    client: Client,
    username: str,
    category: str,
    reliable_domains: list,
    limit: int = 10,
) -> list:
    """Fetch posts from a Bluesky user and return formatted post objects."""
    response = client.app.bsky.feed.get_author_feed(
        params={"actor": username, "limit": limit}
    )
    existing_posts = mongo.use_collection("posts").distinct("unique_id")
    source_label = (
        "reliable" if is_reliable_source(username, reliable_domains) else "unverified"
    )

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
                    "source_label": source_label,
                }
            )

    return formatted_posts


def save_posts_to_db(posts: list) -> int:
    """Save posts to MongoDB and return count."""
    conn = mongo.use_collection("posts")
    save = []
    for post in posts:
        save.append(
            {
                "text": post["text"],
                "username": post["username"],
                "created_at": post["created_at"],
                "unique_id": f"{post['username']}_{post['created_at']}",
                "utc_saved_at": datetime.now(),
                "category": post["category"],
                "source_label": post.get("source_label", "unverified"),
            }
        )
    conn.insert_many(save)
    return len(posts)


def fetch_from_reliable_accounts(
    reliable_accounts: list, reliable_domains: list, limit_per_account: int
) -> list:
    """Fetch recent posts from known reliable Bluesky handles and label them reliable."""
    client = get_client()
    data = []
    for handle in reliable_accounts:
        if not validate_handle(client, handle):
            logger.warning(f"Reliable account not found on Bluesky, skipping: {handle}")
            continue
        try:
            posts = format_posts(
                client, handle, "Reliable", reliable_domains, limit=limit_per_account
            )
            data.extend(posts)
            logger.info(f"Fetched {len(posts)} posts from reliable account: {handle}")
        except Exception as e:
            logger.error(f"Error fetching from reliable account '{handle}': {e}")
    logger.info(f"Fetched {len(data)} reliable-source posts total")
    return data


def fetch_from_keywords(reliable_domains: list) -> list:
    """Fetch posts by trending keywords and label them by source reliability."""
    client = get_client()

    themes = {
        "Discover": ["news", "world news", "science", "technology", "research"],
        "Trending": ["breaking news", "urgent", "live updates", "alert"],
        "Hot Topics": ["politics", "election", "climate", "crisis", "economy", "AI"],
        "Misinformation": [
            "fact check",
            "debunked",
            "misinformation",
            "conspiracy",
            "hoax",
        ],
    }

    existing_posts = set(mongo.use_collection("posts").distinct("unique_id"))
    seen_uris: set[str] = set()
    data = []
    reliable_count = 0

    for category, keywords in themes.items():
        for word in keywords:
            try:
                response = client.app.bsky.feed.search_posts(
                    params={"q": word, "limit": 25, "lang": "en"}
                )
                for item in response.posts:
                    uri = item.uri
                    if uri in seen_uris:
                        continue
                    seen_uris.add(uri)

                    username = item.author.handle
                    record = item.record
                    text = getattr(record, "text", None)
                    created_at = getattr(record, "created_at", None)

                    if not text or not created_at:
                        continue

                    unique_id = f"{username}_{created_at}"
                    if unique_id in existing_posts:
                        continue
                    existing_posts.add(unique_id)

                    source_label = (
                        "reliable"
                        if is_reliable_source(username, reliable_domains)
                        else "unverified"
                    )
                    if source_label == "reliable":
                        reliable_count += 1

                    data.append(
                        {
                            "username": username,
                            "text": text,
                            "created_at": created_at,
                            "category": category,
                            "source_label": source_label,
                        }
                    )
            except Exception as e:
                logger.error(f"Error fetching posts for keyword '{word}': {e}")

    logger.info(
        f"Fetched {len(data)} posts — {reliable_count} from reliable sources, "
        f"{len(data) - reliable_count} unverified."
    )
    return data
