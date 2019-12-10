from unittest import TestCase

from decosjoin.api.decosjoin.decosjoin_connection import DecosJoinConnection
from decosjoin.tests.fixtures.response_mock import mock


class ConnectionTests(TestCase):

    def test_get_user_key(self):
        connection = DecosJoinConnection('username', 'password', 'http://localhost', 'hexkey32chars0000000000000000000')

        # set mock
        connection._get_response = mock

        user_key = connection._get_user_key("1234578")
        self.assertEqual(user_key, "32charsstringxxxxxxxxxxxxxxxxxxx")

    def test_get_zaken(self):
        connection = DecosJoinConnection('username', 'password', 'http://localhost', 'hexkey32chars0000000000000000000')

        def mock_get_user_key(bsn):
            return "32charsstringxxxxxxxxxxxxxxxxxxx"

        # set mocks
        connection._get_user_key = mock_get_user_key
        connection._get_response = mock

        zaken = connection.get_zaken("12345678")
        from pprint import pprint
        pprint(zaken)
