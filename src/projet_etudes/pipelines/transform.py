import os
import requests
from atproto import Client
from dotenv import load_dotenv
from pymongo import MongoClient
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../..')
from shared.mongo import mongo_client # noqa

load_dotenv()

mongo = mongo_client()

def get_posts_to_treat():
    posts_collection = mongo.use_collection("posts")
    cleaned_posts_collection = mongo.use_collection("cleaned_posts")
    cleaned_posts_ids = cleaned_posts_collection.distinct("unique_id")
    return list(posts_collection.find({"unique_id": {"$nin": cleaned_posts_ids}}))

logging.info("Starting transformation pipeline...")
posts = get_posts_to_treat()
logging.info(f"Found {len(posts)} posts to transform.")

for post in posts:
    text = post['text']

    transformed_text = text.lower()
    transformed_text = ' '.join(word for word in transformed_text.split() if not word.startswith('http'))
    # Remove Emojis
    transformed_text = transformed_text.encode('ascii', 'ignore').decode('ascii')

    cleaned_post = {
        'username': post['username'],
        'created_at': post['created_at'],
        'unique_id': post['unique_id'],
        'text': transformed_text
    }

    conn = mongo.use_collection("cleaned_posts")
    conn.insert_one(cleaned_post)