import os
from unittest import TestCase

from unittest.mock import patch

from decosjoin.config import get_sentry_dsn, get_decosjoin_adres_boeken, get_decosjoin_api_host, get_decosjoin_password, \
    get_decosjoin_username, get_tma_certificate


@patch.dict(os.environ, {
    "TMA_CERTIFICATE": __file__,
    "SENTRY_DSN": "sentry",
    "DECOS_JOIN_USERNAME": "username",
    "DECOS_JOIN_PASSWORD": "password",
    "DECOS_JOIN_API_HOST": "host",
    "DECOS_JOIN_ADRES_BOEKEN_BSN": "address1,address2",
    "DECOS_JOIN_ADRES_BOEKEN_KVK": "address3,address4",
})
class ConfigTests(TestCase):
    def test_config(self):
        self.assertTrue(len(get_tma_certificate()) > 0)
        self.assertEqual(get_decosjoin_username(), "username")
        self.assertEqual(get_decosjoin_password(), "password")
        self.assertEqual(get_decosjoin_api_host(), "host")
        self.assertEqual(get_decosjoin_adres_boeken(), {'bsn': ['address1', 'address2'], 'kvk': ['address3', 'address4']})
        self.assertEqual(get_sentry_dsn(), "sentry")
