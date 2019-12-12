from unittest import TestCase
from unittest.mock import patch

from decosjoin.api.decosjoin.decosjoin_connection import DecosJoinConnection
from decosjoin.tests.fixtures.response_mock import get_response_mock


@patch('decosjoin.tests.test_connection.DecosJoinConnection._get_response', get_response_mock)
class ConnectionTests(TestCase):

    def test_get_user_key(self):
        connection = DecosJoinConnection('username', 'password', 'http://localhost', 'hexkey32chars0000000000000000000')

        user_key = connection._get_user_key("111222333")
        self.assertEqual(user_key, "32charsstringxxxxxxxxxxxxxxxxxxx")

    def test_get_zaken(self):
        connection = DecosJoinConnection('username', 'password', 'http://localhost', 'hexkey32chars0000000000000000000')

        # def mock_get_user_key(bsn):
        #     return "32charsstringxxxxxxxxxxxxxxxxxxx"

        # set mocks
        # connection._get_user_key = mock_get_user_key

        zaken = connection.get_zaken("111222333")
        from pprint import pprint
        pprint(zaken)
