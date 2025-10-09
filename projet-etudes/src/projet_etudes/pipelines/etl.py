import os

from atproto import Client
from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()

def get_mongo_conn():
    MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
    mongo_client = MongoClient(MONGO_CONNECTION_STRING)
    db = mongo_client["bluesky_db"]
    posts_collection = db["posts"]  # This will use or create the 'posts' collection
    return posts_collection


def get_client():
    BSKY_PWD = os.getenv('BSKY_APP_PASSWORD')
    BSKY_USERNAME = os.getenv('BSKY_USERNAME')

    if( not BSKY_PWD or not BSKY_USERNAME):
        raise ValueError("BSKY_PWD and BSKY_USERNAME must be set in environment variables")

    client = Client()
    client.login(BSKY_USERNAME, BSKY_PWD)

    return client


def get_post_texts(client: Client, username: str, limit: int = 10):
    """Fetch post texts from a Bluesky user."""
    feed = client.app.bsky.feed.get_author_feed({
        'actor': username,
        'limit': limit
    })
    return [item['post']['record']['text'] for item in feed['feed']]

client = get_client()
data = get_post_texts(client, 'gtconway.bsky.social', limit=5)

for post in data:
    save_to_db = {'text': post}
    conn = get_mongo_conn()
    conn.insert_one(save_to_db)

