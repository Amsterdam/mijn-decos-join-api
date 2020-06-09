from unittest import TestCase
from unittest.mock import patch

from decosjoin.api.decosjoin.decosjoin_connection import DecosJoinConnection
from decosjoin.tests.fixtures.response_mock import get_response_mock


@patch('decosjoin.tests.test_connection.DecosJoinConnection._get_response', get_response_mock)
class ConnectionTests(TestCase):

    def setUp(self) -> None:
        self.connection = DecosJoinConnection('username', 'password', 'http://localhost', {'bsn':['hexkey32chars000000000000000BSN1', 'hexkey32chars000000000000000BSN2']})

    def test_get_user_key(self):
        user_key = self.connection._get_user_key("111222333")
        self.assertEqual(user_key, "32charsstringxxxxxxxxxxxxxxxxxxx")

    def test_get_zaken(self):
        zaken = self.connection.get_zaken("111222333")
        self.assertEqual(zaken[0]["mark"], "Z/20/1234567")
        # self.assertEqual(zaken[0]["caseType"], "GPP")

    # def test_get_zaken_user2(self):
    #     zaken = self.connection.get_zaken("234567890")
    #     self.assertEqual(zaken[0]["mark"], "Z/17/123456")
    #     self.assertEqual(zaken[0]["caseType"], "GPP")
