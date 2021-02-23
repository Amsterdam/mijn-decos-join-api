from datetime import date
from unittest import TestCase
from unittest.mock import patch

from decosjoin.api.decosjoin.decosjoin_connection import DecosJoinConnection
from decosjoin.tests.fixtures.data import get_document
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

    def test_get_zaken(self):
        zaken = self.connection.get_zaken("bsn", "111222333")
        self.assertEqual(zaken[8]["identifier"], "Z/20/1234567")
        self.assertEqual(zaken[7]["identifier"], "Z/20/2345678")
        # Z/20/4567890 is filtered out because of subject1 contents
        # Z/20/56789012 is filtered out because of subject1 starts with "*verwijder"
        # Z/20/2 is filtered out because of decision "Buiten behandeling"

        self.assertEqual(len(zaken), 9)

        self.assertEqual(zaken[5]['decision'], 'Verleend')
        self.assertEqual(zaken[5]['dateDecision'], date(2020, 6, 16))

    def test_list_documents(self):
        documents = self.connection.list_documents('ZAAKKEY1', "111222333")
        self.assertEqual(len(documents), 6)
        self.assertEqual(documents[0]['sequence'], 1)
        self.assertEqual(documents[1]['sequence'], 2)


        doc0 = documents[0]
        self.assertEqual(doc0['title'], 'Training voorbeelddocument.docx')
        self.assertEqual(doc0['sequence'], 1)
        self.assertEqual(doc0['id'], 'D/1')
        self.assertTrue(doc0['url'].startswith('/api/decosjoin/document/'))

        # check exclusions
        sequence_numbers = [d['sequence'] for d in documents]
        self.assertEqual([1, 2, 3, 4, 5, 6], sequence_numbers)

        self.assertNotIn(7, sequence_numbers)
        self.assertNotIn(8, sequence_numbers)
        self.assertNotIn(9, sequence_numbers)

    def test_get_document(self):
        documents = self.connection.get_document('DOCUMENTKEY01')
        self.assertEqual(documents['Content-Type'], "application/pdf")
        self.assertEqual(documents['file_data'], get_document())
