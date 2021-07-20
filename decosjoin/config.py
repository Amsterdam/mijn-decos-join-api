from datetime import date, time
import os
import os.path

from flask.json import JSONDecoder, JSONEncoder
from tma_saml.exceptions import (
    InvalidBSNException,
    SamlExpiredException,
    SamlVerificationException,
)
from tma_saml.user_type import UserType


BASE_PATH = os.path.abspath(os.path.dirname(__file__))

# Use the Sentry environment
IS_PRODUCTION = os.getenv("SENTRY_ENVIRONMENT") == "production"
IS_ACCEPTANCE = os.getenv("SENTRY_ENVIRONMENT") == "acceptance"
IS_AP = IS_PRODUCTION or IS_ACCEPTANCE


def get_sentry_dsn():
    return os.getenv("SENTRY_DSN", None)


def get_decosjoin_username():
    return os.getenv("DECOS_JOIN_USERNAME")


def get_decosjoin_password():
    return os.getenv("DECOS_JOIN_PASSWORD")


def get_decosjoin_api_host():
    return os.getenv("DECOS_JOIN_API_HOST")


def get_decosjoin_adres_boeken_bsn():
    return os.getenv("DECOS_JOIN_ADRES_BOEKEN_BSN").split(",")


def get_decosjoin_adres_boeken_kvk():
    return os.getenv("DECOS_JOIN_ADRES_BOEKEN_KVK").split(",")


def get_decosjoin_adres_boeken():
    return {
        [UserType.BURGER]: get_decosjoin_adres_boeken_bsn(),
        [UserType.BEDRIJF]: get_decosjoin_adres_boeken_kvk(),
    }


def get_encrytion_key():
    return os.getenv("FERNET_KEY")


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, time):
            return obj.isoformat(timespec="minutes")
        if isinstance(obj, date):
            return obj.isoformat()

        return JSONEncoder.default(self, obj)


TMAException = (SamlVerificationException, InvalidBSNException, SamlExpiredException)
