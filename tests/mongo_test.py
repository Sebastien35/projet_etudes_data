import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.mongo import mongo_client


def test_mongo_client_raises_without_connection_string(monkeypatch):
    monkeypatch.delenv("MONGO_CONNECTION_STRING", raising=False)
    with pytest.raises(ValueError, match="MONGO_CONNECTION_STRING"):
        mongo_client()
