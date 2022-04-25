from flask import Flask, g
from tma_saml.user_type import UserType
from app.helpers import get_tma_certificate
import os
from unittest import TestCase

from unittest.mock import patch

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
        "TMA_CERTIFICATE": __file__,
        "SENTRY_DSN": "sentry",
        "DECOS_JOIN_USERNAME": "username",
        "DECOS_JOIN_PASSWORD": "password",
        "DECOS_JOIN_API_HOST": "host",
        "DECOS_JOIN_ADRES_BOEKEN_BSN": "address1,address2",
        "DECOS_JOIN_ADRES_BOEKEN_KVK": "address3,address4",
        "FERNET_KEY": "z4QXWk3bjwFST2HRRVidnn7Se8VFCaHscK39JfODzNs=",
    },
)
class ConfigTests(TestCase):
    def test_config(self):

        with test_app.app_context():
            self.assertTrue(len(get_tma_certificate()) > 0)

            g.tma_certificate = "test123"

            self.assertEqual(get_tma_certificate(), "test123")

        self.assertEqual(get_decosjoin_username(), "username")
        self.assertEqual(get_decosjoin_password(), "password")
        self.assertEqual(get_decosjoin_api_host(), "host")
        self.assertEqual(
            get_decosjoin_adres_boeken(),
            {
                UserType.BURGER: ["address1", "address2"],
                UserType.BEDRIJF: ["address3", "address4"],
            },
        )
        self.assertEqual(get_sentry_dsn(), "sentry")
        self.assertEqual(
            get_encrytion_key(), "z4QXWk3bjwFST2HRRVidnn7Se8VFCaHscK39JfODzNs="
        )
