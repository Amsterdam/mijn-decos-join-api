from datetime import date
from unittest import TestCase
from unittest.mock import patch
from freezegun import freeze_time

from decosjoin.api.decosjoin.decosjoin_connection import DecosJoinConnection, get_translation, to_transition_agreement
from decosjoin.tests.fixtures.response_mock import get_response_mock, post_response_mock


@patch("decosjoin.crypto.get_encrytion_key", lambda: "z4QXWk3bjwFST2HRRVidnn7Se8VFCaHscK39JfODzNs=")
@patch('decosjoin.tests.test_connection.DecosJoinConnection.get_response', get_response_mock)
@patch("decosjoin.server.DecosJoinConnection.post_response", post_response_mock)
@freeze_time("2021-07-05")
class ConnectionTests(TestCase):

    def setUp(self) -> None:
        self.connection = DecosJoinConnection('username', 'password', 'http://localhost', {'bsn': ['hexkey32chars000000000000000BSN1', 'hexkey32chars000000000000000BSN2']})

    def test_get_user_key(self):
        user_key = self.connection.get_user_keys("bsn", "111222333")
        self.assertEqual(user_key, ['32charsstringxxxxxxxxxxxxxxxxxxx', '32charsstringxxxxxxxxxxxxxxxxxx2', '32charsstringxxxxxxxxxxxxxxxxxx3'])

    def assert_unknown_identifier(self, zaken, identifier):
        self.assertEqual([zaak['identifier'] for zaak in zaken if zaak['identifier'] == identifier], [])

    @patch('decosjoin.api.decosjoin.decosjoin_connection.page_size', 10)
    def test_get_zaken(self):
        zaken = self.connection.get_zaken("bsn", "111222333")
        self.assertEqual(len(zaken), 18)

        self.assertEqual(zaken[5]["identifier"], "Z/21/78901234")
        self.assertEqual(zaken[5]["title"], "Vergunning bed & breakfast")

        # Vakantie verhuur vergunningsaanvraag
        self.assertEqual(zaken[6]["identifier"], "Z/21/7865356778")
        self.assertEqual(zaken[6]["title"], "Vergunning vakantieverhuur")
        self.assertEqual(zaken[6]["status"], "Afgehandeld")
        self.assertEqual(zaken[6]["decision"], "Verleend")

        self.assertEqual(zaken[8]["identifier"], "Z/21/123123123")
        self.assertEqual(zaken[8]["title"], "Vergunning vakantieverhuur")
        self.assertEqual(zaken[8]["status"], "Afgehandeld")
        self.assertEqual(zaken[8]["decision"], "Ingetrokken")

        # Vakantieverhuur melding
        self.assertEqual(zaken[7]["identifier"], "Z/21/67890123")
        self.assertEqual(zaken[7]["title"], 'Geplande verhuur')

        # Z/21/90123456 "vakantieverhuur" is filtered out because it is replaced by Z/21/89012345 "vakantieverhuur afmelding"
        self.assert_unknown_identifier(zaken, 'Z/21/90123456')

        self.assertEqual(zaken[4]["identifier"], "Z/21/89012345")
        self.assertEqual(zaken[4]["title"], 'Geannuleerde verhuur')

        # TVM - RVV
        self.assertEqual(zaken[17]["identifier"], "Z/20/1234567")
        self.assertEqual(zaken[16]["identifier"], "Z/20/2345678")

        # Z/20/4567890 is filtered out because of subject1 contents
        self.assert_unknown_identifier(zaken, 'Z/20/4567890')

        # Z/20/56789012 is filtered out because of subject1 starts with "*verwijder"
        self.assert_unknown_identifier(zaken, 'Z/20/56789012')

        # Z/20/2 is filtered out because of decision "Buiten behandeling"
        self.assert_unknown_identifier(zaken, 'Z/20/2')

        self.assertEqual(zaken[14]['decision'], 'Verleend')
        self.assertEqual(zaken[14]['dateDecision'], date(2020, 6, 16))

    @ patch('decosjoin.api.decosjoin.decosjoin_connection.page_size', 10)
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

    def test_get_translations(self):
        translations = [
            ["a", "1Aa", True],
            ["b", "2Aa", False],
            ["C", "3Aa", True],
            ["D", "4Aa", False],
        ]
        self.assertEqual(get_translation("a", translations), "1Aa")
        self.assertEqual(get_translation("A", translations), "1Aa")
        self.assertIsNone(get_translation("b", translations))
        self.assertEqual(get_translation("c", translations), "3Aa")
        self.assertIsNone(get_translation("d", translations))
        self.assertIsNone(get_translation("Nope", translations))

    def test_to_transition_agreement(self):
        self.assertEqual(to_transition_agreement('Verleend met overgangsrecht'), True)
        self.assertEqual(to_transition_agreement('Verleend zonder overgangsrecht'), False)
        self.assertEqual(to_transition_agreement('abc'), False)

    # def test_get_document(self):
    #     documents = self.connection.get_document('DOCUMENTKEY01')
    #     self.assertEqual(documents['Content-Type'], "application/pdf")
    #     self.assertEqual(documents['file_data'], get_document())
