import os

import requests
from atproto import Client
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

class mongo_client():
    def __init__(self):
        MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
        if not MONGO_CONNECTION_STRING:
            raise ValueError("MONGO_CONNECTION_STRING must be set in environment variables")
        self.mongo_client = MongoClient(MONGO_CONNECTION_STRING)
        self.db = self.mongo_client["bluesky_db"]
        self.collections = {
            "posts": self.db["posts"],  # This will use or create the 'posts' collection
            "cleaned_posts": self.db["cleaned_posts"]  # This will use or create the 'cleaned_posts' collection
        }
    
    def use_collection(self, collection_name: str):
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} does not exist.")
        return self.collections[collection_name]

    def get_client(self):
        return self.mongo_client