import os

from atproto import Client
from dotenv import load_dotenv

load_dotenv()




def get_client():
    BSKY_PWD = os.getenv('BSKY_APP_PASSWORD')
    BSKY_USERNAME = os.getenv('BSKY_USERNAME')

    if( not BSKY_PWD or not BSKY_USERNAME):
        raise ValueError("BSKY_PWD and BSKY_USERNAME must be set in environment variables")

    client = Client()
    client.login(BSKY_USERNAME, BSKY_PWD)

    return client


def get_data(client: Client, BSKY_USERNAME: str):
    """Fetch data from Bluesky API."""
    # Example: Fetch the user's profile information
    profile = client.get_profile(BSKY_USERNAME)
    return profile

client = get_client()
data = get_data(client, os.getenv('BSKY_USERNAME'))
print(data)




