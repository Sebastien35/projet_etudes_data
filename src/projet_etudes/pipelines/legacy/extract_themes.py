import os
import sys
from datetime import datetime

from atproto import Client
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../..")
import logging

from shared.mongo import mongo_client  # noqa

load_dotenv()

mongo = mongo_client()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_client() -> Client:
    bsky_pwd = os.getenv("BSKY_APP_PASSWORD")
    bsky_username = os.getenv("BSKY_USERNAME")

    if not bsky_pwd or not bsky_username:
        raise ValueError(
            "bsky_pwd and bsky_username must be set in environment variables"
        )

    client = Client()
    client.login(bsky_username, bsky_pwd)

    return client


def format_posts(client: Client, username: str, category: str, limit: int = 10):
    """
    Récupère les posts d'un utilisateur Bluesky
    et renvoie une liste d'objets contenant :
    - username
    - text
    - created_at
    """
    response = client.app.bsky.feed.get_author_feed(
        params={"actor": username, "limit": limit}
    )
    existing_posts = mongo.use_collection("posts").distinct("unique_id")

    formatted_posts = []

    # 🔹 la réponse est un objet avec un attribut .feed (une liste)
    for item in response.feed:
        if f"{username}_{item.post.record.created_at}" in existing_posts:
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


client: Client = get_client()


def validate_handle(client: Client, username: str) -> bool:
    """Check if the Bluesky handle exists."""
    try:
        client.app.bsky.actor.get_profile({"actor": username})
        return True
    except Exception:
        return False


untrusted = []
data = []

# Mots clés
# Discover : news, world, science, tech
# Trending : breaking, urgent, live
# Hot Topics : politics, election, covid, crisis

themes = {}
themes["Discover"] = ["news", "world", "science", "tech"]
themes["Trending"] = ["breaking", "urgent", "live"]
themes["Hot Topics"] = ["politics", "election", "covid", "crisis"]


def fetch_posts_by_keyword():
    for category, keywords in themes.items():
        for word in keywords:
            try:
                search = {"q": word, "limit": 5}
                response = client.app.bsky.feed.search_posts(params=search)
                for item in response.posts:
                    username = item.author.handle
                    posts = format_posts(client, username, category, limit=2)
                    data.extend(posts)
            except Exception as e:
                logger.info(f"Error fetching posts for keyword '{word}': {e}")
    return data


data = fetch_posts_by_keyword()
for post in data:
    save_to_db = {
        "text": post["text"],
        "username": post["username"],
        "created_at": post["created_at"],
        "unique_id": f"{post['username']}_{post['created_at']}",
        "utc_saved_at": datetime.now(),
        "category": post["category"],
    }

    conn = mongo.use_collection(post["category"])
    conn.insert_one(save_to_db)
