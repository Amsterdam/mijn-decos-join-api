import os
from unittest import TestCase
from unittest.mock import patch

from cryptography.fernet import Fernet
from flask import Flask, g

from app.auth import PROFILE_TYPE_COMMERCIAL, PROFILE_TYPE_PRIVATE
from app.config import (
    get_decosjoin_api_host,
    get_decosjoin_password,
    get_decosjoin_username,
    get_encrytion_key,
    get_sentry_dsn,
)
from app.decosjoin_service import get_decosjoin_adres_boeken

test_app = Flask(__name__)

FERNET_KEY = str(Fernet.generate_key())


@patch.dict(
    os.environ,
    {
        "SENTRY_DSN": "sentry",
        "DECOS_JOIN_USERNAME": "username",
        "DECOS_JOIN_PASSWORD": "password",
        "DECOS_JOIN_API_HOST": "host",
        "DECOS_JOIN_ADRES_BOEKEN_BSN": "address1,address2",
        "DECOS_JOIN_ADRES_BOEKEN_KVK": "address3,address4",
        "FERNET_ENCRYPTION_KEY": FERNET_KEY,
    },
)
class ConfigTests(TestCase):
    def test_config(self):
        self.assertEqual(get_decosjoin_username(), "username")
        self.assertEqual(get_decosjoin_password(), "password")
        self.assertEqual(get_decosjoin_api_host(), "host")
        self.assertEqual(
            get_decosjoin_adres_boeken(),
            {
                PROFILE_TYPE_PRIVATE: ["address1", "address2"],
                PROFILE_TYPE_COMMERCIAL: ["address3", "address4"],
            },
        )
        self.assertEqual(get_sentry_dsn(), "sentry")
        self.assertEqual(get_encrytion_key(), FERNET_KEY)
