from atproto import Client
from dotenv import load_dotenv
from pymongo import MongoClient

import os
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../..')
from shared.mongo import mongo_client # noqa
load_dotenv()

mongo = mongo_client()

def get_client():
    BSKY_PWD = os.getenv('BSKY_APP_PASSWORD')
    BSKY_USERNAME = os.getenv('BSKY_USERNAME')

    if( not BSKY_PWD or not BSKY_USERNAME):
        raise ValueError("BSKY_PWD and BSKY_USERNAME must be set in environment variables")

    client = Client()
    client.login(BSKY_USERNAME, BSKY_PWD)

    return client



def format_posts(client: Client, username: str, limit: int = 10):
    """
    Récupère les posts d'un utilisateur Bluesky
    et renvoie une liste d'objets contenant :
    - username
    - text
    - created_at
    """
    response = client.app.bsky.feed.get_author_feed(params={
        'actor': username,
        'limit': limit
    })
    existing_posts = mongo.use_collection("posts").distinct("unique_id")

    formatted_posts = []

    # 🔹 la réponse est un objet avec un attribut .feed (une liste)
    for item in response.feed:
        if(f"{username}_{item.post.record.created_at}" in existing_posts):
            continue
        post = item.post
        record = post.record

        text = getattr(record, 'text', None)
        created_at = getattr(record, 'created_at', None)

        if text and created_at:
            formatted_posts.append({
                "username": username,
                "text": text,
                "created_at": created_at
            })

    return formatted_posts


client = get_client()
trusted_data_sources = [
    # --- Major News ---
    'apnews.bsky.social',
    'axios.com',
    'washingtonpost.com',
    'theguardian.com',
    'nytimes.com',
    'bbc.com',
    'abcnews.bsky.social',
    'bloomberg.bsky.social',
    'skynews.com',
    'aljazeera.com',

    # --- Tech & Science ---
    'techcrunch.com',
    'verge.bsky.social',
    'wired.com',
    'arstechnica.com',
    'noaa.bsky.social',        # active US weather data source
    'nasa.gov',                # NASA now uses its web domain instead of .bsky.social
    'esa.int',                 # European Space Agency
    'nature.com',

    # --- Fact-Checking ---
    'politifact.com',
    'snopes.com',
    'fullfact.org',
    'leadstories.com',
    'factcheck.org'
]
def validate_handle(client, username):
    """Check if the Bluesky handle exists."""
    try:
        profile = client.app.bsky.actor.get_profile({'actor': username})
        return True
    except Exception:
        return False
untrusted = []
data = []
for source in trusted_data_sources:
    if not validate_handle(client, source):
        untrusted.append(source)
        continue
    posts = format_posts(client, source, limit=5)
    data.extend(posts)

print(f"Fetched {len(data)} posts from trusted sources.")
print(f"Untrusted sources: {untrusted}")

for post in data:
    save_to_db = {
        'text': post['text'], 
        'username': post['username'],
        'created_at': post['created_at'],
        'unique_id': f"{post['username']}_{post['created_at']}",
        'utc_saved_at': datetime.now()
    }

    conn = mongo.use_collection("posts")
    conn.insert_one(save_to_db)


