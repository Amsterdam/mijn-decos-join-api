from cryptography.fernet import Fernet

from decosjoin.config import get_key


def encrypt(plain_text: str) -> str:
    f = Fernet(get_key())
    return f.encrypt(plain_text.encode()).decode()


def decrypt(encrypted: str) -> str:
    f = Fernet(get_key())
    return f.decrypt(encrypted.encode(), ttl=60*60).decode()
