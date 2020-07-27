from unittest import TestCase
from unittest.mock import patch

from decosjoin.api.decosjoin.decosjoin_connection import DecosJoinConnection
from decosjoin.tests.fixtures.response_mock import get_response_mock, post_response_mock


@patch('decosjoin.tests.test_connection.DecosJoinConnection._get_response', get_response_mock)
@patch("decosjoin.server.DecosJoinConnection._post_response", post_response_mock)
class ConnectionTests(TestCase):

    def setUp(self) -> None:
        self.connection = DecosJoinConnection('username', 'password', 'http://localhost', {'bsn': ['hexkey32chars000000000000000BSN1', 'hexkey32chars000000000000000BSN2']})

    def test_get_user_key(self):
        user_key = self.connection._get_user_keys("111222333")
        self.assertEqual(user_key, ['32charsstringxxxxxxxxxxxxxxxxxxx', '32charsstringxxxxxxxxxxxxxxxxxx2', '32charsstringxxxxxxxxxxxxxxxxxx3'])

    def test_get_zaken(self):
        zaken = self.connection.get_zaken("111222333")
        self.assertEqual(zaken[0]["identifier"], "Z/20/1234567")
        self.assertEqual(zaken[1]["identifier"], "Z/20/2345678")
        # Z/20/4567890 is filtered out because of subject1 contents
        # Z/20/56789012 is filtered out because of subject1 starts with "*verwijder"
        self.assertEqual(len(zaken), 9)

    def test_get_documents(self):
        documents = self.connection.get_documents('', 'ZAAKKEY1')
        print(documents)
