from pprint import pprint
from unittest import TestCase
from unittest.mock import patch

from freezegun import freeze_time

from app.decosjoin_service import DecosJoinConnection
from app.field_parsers import to_date
from app.fixtures.response_mock import get_response_mock, post_response_mock
from app.zaaktypes import BBVergunning


@patch(
    "app.crypto.get_encrytion_key",
    lambda: "z4QXWk3bjwFST2HRRVidnn7Se8VFCaHscK39JfODzNs=",
)
@patch(
    "app.test_decosjoin_service.DecosJoinConnection.get_response",
    get_response_mock,
)
@patch("app.helpers.DecosJoinConnection.post_response", post_response_mock)
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

    @patch("app.decosjoin_service.PAGE_SIZE", 10)
    def test_get_zaken(self):
        zaken = self.connection.get_zaken("bsn", "111222333")

        self.assertEqual(len(zaken), 17)
        zaken_from_fixtures = []

        for z in zaken:
            zaken_from_fixtures.append(
                [z["identifier"], z["status"], z["decision"], z["caseType"]]
            )

        zaken_expected = [
            ["Z/20/1234567", "Ontvangen", None, "TVM - RVV - Object"],
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
            ["Z/21/78901234", "Ontvangen", None, "B&B - vergunning"],
            [
                "Z/21/7865356778",
                "Afgehandeld",
                "Verleend",
                "Vakantieverhuur vergunningsaanvraag",
            ],
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
            ["Z/20/2345678.0", "Ontvangen", None, "TVM - RVV - Object"],
        ]

        self.assertEqual(
            sorted(zaken_from_fixtures, key=lambda zaak: zaak[0]),
            sorted(zaken_expected, key=lambda zaak: zaak[0]),
        )

        self.assertEqual(zaken[8].get("identifier"), "Z/21/123123123")

        # Z/20/4567890 is filtered out because of subject1 contents
        self.assert_unknown_identifier(zaken, "Z/20/4567890")

        # Z/20/56789012 is filtered out because of subject1 starts with "*verwijder"
        self.assert_unknown_identifier(zaken, "Z/20/56789012")

        # Z/20/2 is filtered out because of decision "Buiten behandeling"
        self.assert_unknown_identifier(zaken, "Z/20/2")

        # Z/20/2345678.1 is filtered out because of decision "Geannuleerd"
        self.assert_unknown_identifier(zaken, "Z/20/2345678.1")

    @patch("app.decosjoin_service.PAGE_SIZE", 10)
    def test_get_documents(self):
        documents = self.connection.get_documents("ZAAKKEY1", "111222333")
        self.assertEqual(len(documents), 2)

        doc0 = documents[0]
        self.assertEqual(doc0["id"], "D/2")
        self.assertTrue(doc0["url"].startswith("/decosjoin/document/"))

    def test_transform_bb_vergunning(self):
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

        zaak_bb_vergunning = {
            "company": "Haarlem",
            "date6": "2021-05-19T00:00:00",
            "date7": "2021-12-31T00:00:00",
            "document_date": "2021-05-19T00:00:00",
            "mark": "Z/21/78901234",
            "subject1": "B&B vergunning aanvragen - Amstel 1",
            "text10": "Ja",
            "text11": "Geheel",
            "text12": "Online voldaan",
            "text45": "B&B - vergunning",
            "text6": "Amstel 1 1012AA Amsterdam",
            "text7": "Test veld Adres Locatie",
            "text8": "<nietnodig>",
            "title": "Ontvangen",
            "id": "HEXSTRING17",
        }

        zaken_result = self.connection.transform(
            [
                wrap(zaak_bb_vergunning, "HEXSTRING17"),
            ],
            "test-user-id",
        )

        self.assertEqual(len(zaken_result), 1)
        self.assertEqual(zaken_result[0]["caseType"], "B&B - vergunning")
        self.assertEqual(zaken_result[0]["identifier"], "Z/21/78901234")
        self.assertEqual(zaken_result[0]["dateWorkflowActive"], to_date("2021-09-15"))

    def test_get_workflow(self):
        workflow_date = self.connection.get_workflow_date_by_step_title(
            "HEXSTRING17", BBVergunning.date_workflow_active_step_title
        )

        self.assertEqual(workflow_date, to_date("2021-09-15"))

    # def test_get_document_blob(self):
    #     documents = self.connection.get_document_blob('DOCUMENTKEY01')
    #     self.assertEqual(documents['Content-Type'], "application/pdf")
    #     self.assertEqual(documents['file_data'], get_document_blob())
