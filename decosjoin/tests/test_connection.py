from unittest import TestCase
from unittest.mock import patch

from decosjoin.api.decosjoin.decosjoin_connection import DecosJoinConnection
from decosjoin.tests.fixtures.response_mock import get_response_mock, post_response_mock
from freezegun import freeze_time


@patch(
    "decosjoin.crypto.get_encrytion_key",
    lambda: "z4QXWk3bjwFST2HRRVidnn7Se8VFCaHscK39JfODzNs=",
)
@patch(
    "decosjoin.tests.test_connection.DecosJoinConnection.get_response",
    get_response_mock,
)
@patch("decosjoin.server.DecosJoinConnection.post_response", post_response_mock)
@freeze_time("2021-07-05")
class ConnectionTests(TestCase):
    def setUp(self) -> None:
        self.connection = DecosJoinConnection(
            "username",
            "password",
            "http://localhost",
            {
                "bsn": [
                    "hexkey32chars000000000000000BSN1",
                    "hexkey32chars000000000000000BSN2",
                ]
            },
        )

    def test_get_user_key(self):
        user_key = self.connection.get_user_keys("bsn", "111222333")
        self.assertEqual(
            user_key,
            [
                "32charsstringxxxxxxxxxxxxxxxxxxx",
                "32charsstringxxxxxxxxxxxxxxxxxx2",
                "32charsstringxxxxxxxxxxxxxxxxxx3",
            ],
        )

    def assert_unknown_identifier(self, zaken, identifier):
        self.assertEqual(
            [zaak["identifier"] for zaak in zaken if zaak["identifier"] == identifier],
            [],
        )

    @patch("decosjoin.api.decosjoin.decosjoin_connection.PAGE_SIZE", 10)
    def test_get_zaken(self):
        zaken = self.connection.get_zaken("bsn", "111222333")

        self.assertEqual(len(zaken), 20)
        zaken_from_fixtures = []

        for z in zaken:
            zaken_from_fixtures.append(
                [z["identifier"], z["status"], z["decision"], z["caseType"]]
            )

        zaken_expected = [
            [
                "Z/21/99012350",
                "Ontvangen",
                "Verleend",
                "Parkeerontheffingen Blauwe zone particulieren",
            ],
            [
                "Z/21/99012349",
                "Ontvangen",
                "Verleend",
                "Parkeerontheffingen Blauwe zone bedrijven",
            ],
            ["Z/21/99012348", "Ontvangen", None, "Omzettingsvergunning"],
            ["Z/21/99012347", "Ontvangen", None, "GPK"],
            ["Z/21/99012346", "Ontvangen", None, "GPP"],
            ["Z/21/99012345", "Ontvangen", None, "E-RVV - TVM"],
            ["Z/21/89012345", "Ontvangen", None, "Vakantieverhuur"],
            ["Z/21/78901234", "Ontvangen", None, "B&B - vergunning"],
            [
                "Z/21/7865356778",
                "Afgehandeld",
                "Verleend",
                "Vakantieverhuur vergunningsaanvraag",
            ],
            ["Z/21/67890123", "Ontvangen", None, "Vakantieverhuur"],
            [
                "Z/21/123123123",
                "Afgehandeld",
                "Ingetrokken",
                "Vakantieverhuur vergunningsaanvraag",
            ],
            ["Z/20/9", "Ontvangen", "Verleend", "TVM - RVV - Object"],
            ["Z/20/2345678.6", "Ontvangen", None, "TVM - RVV - Object"],
            ["Z/20/2345678.5", "Ontvangen", "Verleend", "TVM - RVV - Object"],
            ["Z/20/2345678.4", "Ontvangen", None, "TVM - RVV - Object"],
            ["Z/20/2345678.3", "Ontvangen", None, "TVM - RVV - Object"],
            ["Z/20/2345678.2", "Ontvangen", None, "TVM - RVV - Object"],
            ["Z/20/2345678.1", "Ontvangen", None, "TVM - RVV - Object"],
            ["Z/20/2345678.0", "Ontvangen", None, "TVM - RVV - Object"],
            ["Z/20/1234567", "Ontvangen", None, "TVM - RVV - Object"],
        ]

        self.assertEqual(zaken_from_fixtures, zaken_expected)

        # Z/21/90123456 "vakantieverhuur" is filtered out because it is replaced by Z/21/89012345 "vakantieverhuur afmelding"
        self.assert_unknown_identifier(zaken, "Z/21/90123456")

        # Z/20/4567890 is filtered out because of subject1 contents
        self.assert_unknown_identifier(zaken, "Z/20/4567890")

        # Z/20/56789012 is filtered out because of subject1 starts with "*verwijder"
        self.assert_unknown_identifier(zaken, "Z/20/56789012")

        # Z/20/2 is filtered out because of decision "Buiten behandeling"
        self.assert_unknown_identifier(zaken, "Z/20/2")

    @patch("decosjoin.api.decosjoin.decosjoin_connection.PAGE_SIZE", 10)
    def test_get_documents(self):
        documents = self.connection.get_documents("ZAAKKEY1", "111222333")
        self.assertEqual(len(documents), 2)
        self.assertEqual(documents[0]["sequence"], 2)
        self.assertEqual(documents[1]["sequence"], 5)

        doc0 = documents[0]
        self.assertEqual(doc0["sequence"], 2)
        self.assertEqual(doc0["id"], "D/2")
        self.assertTrue(doc0["url"].startswith("/api/decosjoin/document/"))

        # check exclusions
        sequence_numbers = [d["sequence"] for d in documents]
        self.assertEqual([2, 5], sequence_numbers)

        self.assertNotIn(7, sequence_numbers)
        self.assertNotIn(8, sequence_numbers)
        self.assertNotIn(9, sequence_numbers)

    def test_transform(self):
        def wrap(zaak, key):
            return {
                "key": key,
                "fields": zaak,
                "links": [
                    {
                        "href": """https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/{key}""",
                        "rel": "self",
                    }
                ],
            }

        zaak_vakantieverhuur = {
            "date6": "2021-06-18T00:00:00",
            "date7": "2021-06-21T00:00:00",
            "document_date": "2021-04-28T00:00:00",
            "mark": "Z/21/67890123",
            "subject1": "Melding Amstel 1  - V Achternaam",
            "text11": "Nvt",
            "text12": "Geen kosten",
            "text45": "Vakantieverhuur",
            "text6": "Amstel 1 1012AA Amsterdam",
            "text7": "Z/11/123456",
            "title": "Ontvangen",
        }

        zaak_vakantieverhuur_afmelding = {
            "company": "Moes",
            "date6": "2021-06-18T00:00:00",
            "date7": "2021-06-21T00:00:00",
            "document_date": "2021-05-10T00:00:00",
            "mark": "Z/21/89012345",
            "subject1": "Melding Amstel 1  - V Achternaam",
            "text11": "Nvt",
            "text45": "Vakantieverhuur afmelding",
            "text6": "Amstel 1 1012AA Amsterdam",
            "title": "Ontvangen",
        }

        zaken_result = self.connection.transform(
            [
                wrap(zaak_vakantieverhuur, "zaak1"),
                wrap(zaak_vakantieverhuur_afmelding, "zaak2"),
            ],
            "test-user-id",
        )

        self.assertEqual(len(zaken_result), 1)
        self.assertEqual(zaken_result[0]["caseType"], "Vakantieverhuur")
        self.assertEqual(zaken_result[0]["identifier"], "Z/21/89012345")
        self.assert_unknown_identifier(zaken_result, "Z/21/67890123")
        self.assertTrue("documentsUrl" in zaken_result[0])

    # def test_get_document_blob(self):
    #     documents = self.connection.get_document_blob('DOCUMENTKEY01')
    #     self.assertEqual(documents['Content-Type'], "application/pdf")
    #     self.assertEqual(documents['file_data'], get_document_blob())
