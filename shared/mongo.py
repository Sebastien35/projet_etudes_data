import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()


class mongo_client:
    def __init__(self):
        MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
        if not MONGO_CONNECTION_STRING:
            raise ValueError(
                "MONGO_CONNECTION_STRING must be set in environment variables"
            )
        self.mongo_client = MongoClient(MONGO_CONNECTION_STRING)
        self.db = self.mongo_client["bluesky_db"]

    def use_collection(self, collection_name: str):
        return self.db[collection_name]

    def get_client(self):
        return self.mongo_client
