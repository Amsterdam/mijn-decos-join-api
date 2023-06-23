from flask import Flask, g
import os
from unittest import TestCase

from unittest.mock import patch
from app.auth import PROFILE_TYPE_COMMERCIAL, PROFILE_TYPE_PRIVATE

from app.config import (
    get_sentry_dsn,
    get_decosjoin_adres_boeken,
    get_decosjoin_api_host,
    get_decosjoin_password,
    get_decosjoin_username,
    get_encrytion_key,
)


test_app = Flask(__name__)


@patch.dict(
    os.environ,
    {
        "SENTRY_DSN": "sentry",
        "DECOS_JOIN_USERNAME": "username",
        "DECOS_JOIN_PASSWORD": "password",
        "DECOS_JOIN_API_HOST": "host",
        "DECOS_JOIN_ADRES_BOEKEN_BSN": "address1,address2",
        "DECOS_JOIN_ADRES_BOEKEN_KVK": "address3,address4",
        "FERNET_ENCRYPTION_KEY": "z4QXWk3bjwFST2HRRVidnn7Se8VFCaHscK39JfODzNs=",
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
        self.assertEqual(
            get_encrytion_key(), "z4QXWk3bjwFST2HRRVidnn7Se8VFCaHscK39JfODzNs="
        )
