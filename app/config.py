import logging
import os
import os.path
from datetime import date, time

from flask.json.provider import DefaultJSONProvider

BASE_PATH = os.path.abspath(os.path.dirname(__file__))

OTAP_ENV = os.getenv("MA_OTAP_ENV")

# Environment determination
IS_PRODUCTION = OTAP_ENV == "production"
IS_ACCEPTANCE = OTAP_ENV == "acceptance"
IS_DEV = OTAP_ENV == "development"
IS_TEST = OTAP_ENV == "test"

IS_TAP = IS_PRODUCTION or IS_ACCEPTANCE or IS_TEST
IS_AP = IS_ACCEPTANCE or IS_PRODUCTION
IS_OT = IS_DEV or IS_TEST
IS_AZ = os.getenv("IS_AZ", False)

# App constants
VERIFY_JWT_SIGNATURE = os.getenv("VERIFY_JWT_SIGNATURE", IS_AP)

DECOS_API_REQUEST_TIMEOUT = 5

# Set-up logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "ERROR").upper()

logging.basicConfig(
    format="%(asctime)s,%(msecs)d %(levelname)-8s [%(pathname)s:%(lineno)d in function %(funcName)s] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=LOG_LEVEL,
)


class UpdatedJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, time):
            return obj.isoformat(timespec="minutes")

        if isinstance(obj, date):
            return obj.isoformat()

        return super().default(obj)


def get_application_insights_connection_string():
    return os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", None)


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


def get_encrytion_key():
    return os.getenv("FERNET_ENCRYPTION_KEY")
