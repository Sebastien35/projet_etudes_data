import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.mongo import mongo_client


def test_mongo_client():
    conn = mongo_client()
    assert conn is not None
