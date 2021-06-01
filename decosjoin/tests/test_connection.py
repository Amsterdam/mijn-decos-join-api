from datetime import date
from unittest import TestCase
from unittest.mock import patch

from decosjoin.api.decosjoin.decosjoin_connection import DecosJoinConnection
# from decosjoin.tests.fixtures.data import get_document
from decosjoin.tests.fixtures.response_mock import get_response_mock, post_response_mock


@patch("decosjoin.crypto.get_key", lambda: "z4QXWk3bjwFST2HRRVidnn7Se8VFCaHscK39JfODzNs=")
@patch('decosjoin.tests.test_connection.DecosJoinConnection._get_response', get_response_mock)
@patch("decosjoin.server.DecosJoinConnection._post_response", post_response_mock)
class ConnectionTests(TestCase):

    def setUp(self) -> None:
        self.connection = DecosJoinConnection('username', 'password', 'http://localhost', {'bsn': ['hexkey32chars000000000000000BSN1', 'hexkey32chars000000000000000BSN2']})

    def test_get_user_key(self):
        user_key = self.connection._get_user_keys("bsn", "111222333")
        self.assertEqual(user_key, ['32charsstringxxxxxxxxxxxxxxxxxxx', '32charsstringxxxxxxxxxxxxxxxxxx2', '32charsstringxxxxxxxxxxxxxxxxxx3'])

    @patch('decosjoin.api.decosjoin.decosjoin_connection.page_size', 10)
    def test_get_zaken(self):
        zaken = self.connection.get_zaken("bsn", "111222333")
        self.assertEqual(len(zaken), 11)

        self.assertEqual(zaken[0]["identifier"], "Z/21/78901234")
        self.assertEqual(zaken[1]["identifier"], "Z/21/67890123")

        self.assertEqual(zaken[10]["identifier"], "Z/20/1234567")
        self.assertEqual(zaken[9]["identifier"], "Z/20/2345678")
        # Z/20/4567890 is filtered out because of subject1 contents
        # Z/20/56789012 is filtered out because of subject1 starts with "*verwijder"
        # Z/20/2 is filtered out because of decision "Buiten behandeling"

        self.assertEqual(zaken[7]['decision'], 'Verleend')
        self.assertEqual(zaken[7]['dateDecision'], date(2020, 6, 16))

    @patch('decosjoin.api.decosjoin.decosjoin_connection.page_size', 10)
    def test_list_documents(self):
        documents = self.connection.list_documents('ZAAKKEY1', "111222333")
        self.assertEqual(len(documents), 2)
        self.assertEqual(documents[0]['sequence'], 2)
        self.assertEqual(documents[1]['sequence'], 5)

        doc0 = documents[0]
        self.assertEqual(doc0['sequence'], 2)
        self.assertEqual(doc0['id'], 'D/2')
        self.assertTrue(doc0['url'].startswith('/api/decosjoin/document/'))

        # check exclusions
        sequence_numbers = [d['sequence'] for d in documents]
        self.assertEqual([2, 5], sequence_numbers)

        self.assertNotIn(7, sequence_numbers)
        self.assertNotIn(8, sequence_numbers)
        self.assertNotIn(9, sequence_numbers)

    def test_next_april_first(self):
        self.assertEqual(self.connection.next_april_first(date(2021, 3, 1)), date(2021, 4, 1))
        self.assertEqual(self.connection.next_april_first(date(2021, 4, 1)), date(2022, 4, 1))
        self.assertEqual(self.connection.next_april_first(date(2021, 6, 1)), date(2022, 4, 1))

    # def test_get_document(self):
    #     documents = self.connection.get_document('DOCUMENTKEY01')
    #     self.assertEqual(documents['Content-Type'], "application/pdf")
    #     self.assertEqual(documents['file_data'], get_document())
