from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from decosjoin.config import get_key


def encrypt(plain_text: str, bsn: Optional[str] = '') -> str:
    f = Fernet(get_key())
    return f.encrypt(f"{bsn}:{plain_text}".encode()).decode()


def decrypt(encrypted: str, match_bsn: Optional[str] = None) -> str:
    f = Fernet(get_key())
    value_bsn = f.decrypt(encrypted.encode(), ttl=60 * 60).decode()
    bsn, value = value_bsn.split(':', maxsplit=1)

    if match_bsn:
        if bsn != match_bsn:
            raise InvalidToken("BSN does not match")

    return value
