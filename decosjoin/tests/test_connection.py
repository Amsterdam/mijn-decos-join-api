from unittest import TestCase

from decosjoin.api.decosjoin.decosjoin_connection import DecosJoinConnection
from decosjoin.tests.fixtures.data import get_bsn_lookup_response_as_dict, get_zaken_response_as_dict


class MockedResponse:
    status_code = 200

    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


def get_mock_call(data):
    def mock(*args, **kwargs):
        return MockedResponse(data)
    return mock


class ConnectionTests(TestCase):

    def test_get_user_key(self):
        connection = DecosJoinConnection('username', 'password', 'http://host', 'hexkey32chars0000000000000000000')

        # set mock
        connection._get_response = get_mock_call(get_bsn_lookup_response_as_dict())

        user_key = connection._get_user_key("1234578")
        self.assertEqual(user_key, "32charsstringxxxxxxxxxxxxxxxxxxx")

    def test_get_zaken(self):
        connection = DecosJoinConnection('username', 'password', 'http://host', 'hexkey32chars0000000000000000000')

        def mock_get_user_key(bsn):
            return "32charsstringxxxxxxxxxxxxxxxxxxx"

        # set mocks
        connection._get_user_key = mock_get_user_key
        connection._get_response = get_mock_call(get_zaken_response_as_dict())

        zaken = connection.get_zaken("12345678")
        self.assertEqual(zaken['count'], 4)
