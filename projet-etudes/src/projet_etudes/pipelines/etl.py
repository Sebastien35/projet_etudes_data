import os

from atproto import Client
from dotenv import load_dotenv

load_dotenv()


BSKY_PWD = os.getenv('BSKY_APP_PASSWORD')
BSKY_USERNAME = os.getenv('BSKY_USERNAME')

if( not BSKY_PWD or not BSKY_USERNAME):
    raise ValueError("BSKY_PWD and BSKY_USERNAME must be set in environment variables")

client = Client()
client.login(BSKY_USERNAME, BSKY_PWD)




