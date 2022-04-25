import logging
import os
import os.path
from datetime import date, time
from app.auth import PROFILE_TYPE_COMMERCIAL, PROFILE_TYPE_PRIVATE

from flask.json import JSONEncoder

BASE_PATH = os.path.abspath(os.path.dirname(__file__))

# Use the Sentry environment
IS_PRODUCTION = os.getenv("SENTRY_ENVIRONMENT") == "production"
IS_ACCEPTANCE = os.getenv("SENTRY_ENVIRONMENT") == "acceptance"
IS_AP = IS_PRODUCTION or IS_ACCEPTANCE
IS_DEV = os.getenv("FLASK_ENV") == "development" and not IS_AP

DECOS_API_REQUEST_TIMEOUT = 30

ENABLE_OPENAPI_VALIDATION = os.environ.get("ENABLE_OPENAPI_VALIDATION", not IS_AP)

# Set-up logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "ERROR").upper()

logging.basicConfig(
    format="%(asctime)s,%(msecs)d %(levelname)-8s [%(pathname)s:%(lineno)d in function %(funcName)s] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=LOG_LEVEL,
)


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, time):
            return obj.isoformat(timespec="minutes")
        if isinstance(obj, date):
            return obj.isoformat()

        return JSONEncoder.default(self, obj)


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
        PROFILE_TYPE_PRIVATE: get_decosjoin_adres_boeken_bsn(),
        PROFILE_TYPE_COMMERCIAL: get_decosjoin_adres_boeken_kvk(),
    }


def get_encrytion_key():
    return os.getenv("FERNET_KEY")
