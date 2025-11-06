from cryptography.fernet import Fernet

def generate_key():
    """Generate a new Fernet key and save it to a file."""
    key = Fernet.generate_key()
    print(key)

generate_key()