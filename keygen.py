import logging

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def generate_key():
    """Generate a new Fernet key and save it to a file."""
    key = Fernet.generate_key()
    logger.info(key)


generate_key()
