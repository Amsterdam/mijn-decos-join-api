from datetime import date
from unittest.case import TestCase
from unittest.mock import MagicMock

from freezegun import freeze_time

from app.field_parsers import to_date
from app.zaaktypes import (
    BZB,
    BZP,
    BBVergunning,
    Omzettingsvergunning,
    TVM_RVV_Object,
    VakantieVerhuur,
    VakantieVerhuurAfmelding,
    VakantieVerhuurVergunning,
    Flyeren,
    AanbiedenDiensten,
)


class ZaaktypesTest(TestCase):
    def test_next_april_first(self):
        self.assertEqual(
            VakantieVerhuurVergunning.next_april_first(date(2021, 3, 1)),
            date(2022, 4, 1),
        )
        self.assertEqual(
            VakantieVerhuurVergunning.next_april_first(date(2021, 4, 1)),
            date(2022, 4, 1),
        )
        self.assertEqual(
            VakantieVerhuurVergunning.next_april_first(date(2021, 6, 1)),
            date(2022, 4, 1),
        )
        self.assertEqual(
            VakantieVerhuurVergunning.next_april_first(date(2022, 3, 17)),
            date(2023, 4, 1),
        )

    def test_to_transition_agreement(self):
        self.assertEqual(
            BBVergunning.to_transition_agreement("Verleend met overgangsrecht"), True
        )
        self.assertEqual(
            BBVergunning.to_transition_agreement("Verleend zonder overgangsrecht"),
            False,
        )
        self.assertEqual(BBVergunning.to_transition_agreement("abc"), False)

    def test_TVM_RVV_Object(self):
        zaak_source = {
            "title": "Ontvangen",
            "mark": "Z/20/1234567",
            "text45": "TVM - RVV - Object",
            "subject1": "Test beschrijving",
            "text11": "Nogniet",
            "text12": "Er is iets misgegaan, controleer online betaling!",
            "text13": "16:00",
            "text6": "Amstel 1 1000AB",
            "date6": "2021-04-27T00:00:00",
            "text7": "TEST MA Decos",
            "text10": "10:00",
            "date7": "2021-04-28T00:00:00",
            "document_date": "2021-04-16T00:00:00",
            "id": "zaak-1",
        }

        zaak_transformed = {
            "id": "zaak-1",
            "caseType": "TVM - RVV - Object",
            "title": "Tijdelijke verkeersmaatregel (TVM-RVV-Object)",
            "identifier": "Z/20/1234567",
            "dateRequest": to_date(zaak_source["document_date"]),
            "dateWorkflowActive": to_date(zaak_source["document_date"]),
            "status": "Ontvangen",
            "decision": None,
            "dateDecision": None,
            "description": "Test beschrijving",
            "kenteken": None,
            "location": "Amstel 1 1000AB",
            "timeEnd": "16:00",
            "timeStart": "10:00",
            "dateStart": to_date(zaak_source["date6"]),
            "dateEnd": to_date(zaak_source["date7"]),
        }

        self.assertEqual(TVM_RVV_Object(zaak_source).zaak, zaak_transformed)

    def test_VakantieVerhuurVergunning(self):
        zaak_source = {
            "text45": "Vakantieverhuur vergunningsaanvraag",
            "mark": "Z/21/7865356778",
            "document_date": "2021-05-19T00:00:00",
            "date5": "2021-05-19T00:00:00",
            "text6": "Amstel 1 1012AA Amsterdam",
            "title": "Ontvangen",
            "dfunction": None,
            "id": "zaak-1",
        }
        zaak_transformed = VakantieVerhuurVergunning(zaak_source).result()
        self.assertEqual(zaak_transformed["status"], "Afgehandeld")
        self.assertEqual(zaak_transformed["decision"], "Verleend")

        zaak_source = {
            "text45": "Vakantieverhuur vergunningsaanvraag",
            "mark": "Z/21/123123123",
            "document_date": "2020-05-20T00:00:00",
            "date5": "2020-05-20T00:00:00",
            "text6": "Amstel 1 1012AA Amsterdam",
            "title": "Afgehandeld",
            "dfunction": "Ingetrokken",
            "id": "zaak-1",
        }
        zaak_transformed = VakantieVerhuurVergunning(zaak_source).result()
        self.assertEqual(zaak_transformed["status"], "Afgehandeld")
        self.assertEqual(zaak_transformed["decision"], "Ingetrokken")

    @freeze_time("2021-07-15")
    def test_VakantieVerhuur(self):
        zaak_source = {
            "date6": "2021-07-05T00:00:00",
            "date7": "2021-07-06T00:00:00",
            "document_date": "2021-04-28T00:00:00",
            "mark": "Z/21/67890123",
            "subject1": "Melding Amstel 1  - V Achternaam",
            "text11": "Nvt",
            "text12": "Geen kosten",
            "text45": "Vakantieverhuur",
            "text6": "Amstel 1 1012AA Amsterdam",
            "text7": "Z/11/123456",
            "title": "Ontvangen",
            "id": "zaak-1",
        }
        zaak_transformed = VakantieVerhuur(zaak_source).result()

        self.assertEqual(zaak_transformed["caseType"], "Vakantieverhuur")
        self.assertEqual(zaak_transformed["title"], "Afgelopen verhuur")
        self.assertEqual(zaak_transformed["decision"], None)
        self.assertEqual(zaak_transformed["dateStart"], to_date("2021-07-05"))
        self.assertEqual(zaak_transformed["dateEnd"], to_date("2021-07-06"))
        self.assertEqual(zaak_transformed["dateRequest"], to_date("2021-04-28"))

        zaak_source["date6"] = "2021-07-25T00:00:00"
        zaak_source["date7"] = "2021-07-30T00:00:00"

        zaak_transformed = VakantieVerhuur(zaak_source).result()

        self.assertEqual(zaak_transformed["title"], "Geplande verhuur")
        self.assertEqual(zaak_transformed["dateStart"], to_date("2021-07-25"))
        self.assertEqual(zaak_transformed["dateEnd"], to_date("2021-07-30"))

    def test_VakantieVerhuurAfmelding(self):
        zaak_source = {
            "company": "Moes",
            "date6": "2021-06-18T00:00:00",
            "date7": "2021-06-21T00:00:00",
            "document_date": "2021-06-04T00:00:00",
            "mark": "Z/21/89012345",
            "subject1": "Melding Amstel 1  - R  Moes",
            "text11": "Nvt",
            "text45": "Vakantieverhuur afmelding",
            "text6": "Amstel 1 1012AK",
            "title": "Ontvangen",
            "id": "zaak-1",
        }
        zaak_transformed = VakantieVerhuurAfmelding(zaak_source).result()
        self.assertEqual(zaak_transformed["title"], "Geannuleerde verhuur")
        self.assertEqual(zaak_transformed["caseType"], "Vakantieverhuur afmelding")

    def test_BBVergunning(self):
        zaak_source = {
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
            "id": "zaak-1",
        }
        zaak_transformed = BBVergunning(zaak_source).result()
        self.assertEqual(zaak_transformed["title"], "Vergunning bed & breakfast")
        self.assertEqual(zaak_transformed["caseType"], "B&B - vergunning")

    # def test_GPP(self):
    #     self.assertEqual()

    # def test_GPK(self):
    #     self.assertEqual()

    # def test_EvenementMelding(self):
    #     self.assertEqual()

    # def test_EvenementVergunning(self):
    #     self.assertEqual()

    def test_Omzettingsvergunning(self):
        zaak_source = {
            "id": "zaak-omzettingsvergunning-1",
            "company": "Achternaam",
            "date6": "2021-06-02T00:00:00",
            "document_date": "2021-05-19T00:00:00",
            "mark": "Z/21/99012348",
            "subject1": "Omzettingsvergunning aanvragen",
            "text11": "Geheel",
            "text12": "Online voldaan",
            "text45": "Omzettingsvergunning",
            "text6": "Amstel 1 1012AK AMSTERDAM",
            "text7": "Amstel",
            "title": "Ontvangen",
        }
        zaak_transformed = Omzettingsvergunning(zaak_source).result()
        self.assertEqual(
            zaak_transformed["caseType"],
            "Omzettingsvergunning",
        )
        self.assertEqual(
            zaak_transformed["title"],
            "Vergunning voor kamerverhuur (omzettingsvergunning)",
        )

        class connection_mock:
            get_workflow = MagicMock(return_value=to_date("2021-10-15"))

        zaken_all = []

        Omzettingsvergunning.defer_transform(
            zaak_transformed, zaken_all, connection_mock()
        )

        self.assertEqual(zaak_transformed["dateWorkflowActive"], to_date("2021-10-15"))

        connection_mock.get_workflow.assert_called_once_with(
            "zaak-omzettingsvergunning-1",
            Omzettingsvergunning.date_workflow_active_step_title,
        )

    # def test_ERVV_TVM(self):
    #     self.assertEqual()

    def test_BZP(self):
        zaak_source = {
            "company": "Achternaam",
            "date6": "2021-06-26T00:00:00",
            "date7": "2022-06-26T00:00:00",
            "document_date": "2021-05-18T00:00:00",
            "mark": "Z/21/99012350",
            "text8": "KN-UW-TS",
            "text45": "Parkeerontheffingen Blauwe zone particulieren",
            "title": "Ontvangen",
            "dfunction": "Verleend",
            "id": "zaak-1",
        }
        zaak_transformed = BZP(zaak_source).result()
        self.assertEqual(
            zaak_transformed["caseType"],
            "Parkeerontheffingen Blauwe zone particulieren",
        )
        self.assertEqual(zaak_transformed["kenteken"], "KN-UW-TS")
        self.assertEqual(zaak_transformed["dateStart"], to_date("2021-06-26"))

    def test_BZB(self):
        zaak_source = {
            "company": "Achternaam",
            "date6": "2021-05-26T00:00:00",
            "date7": "2022-05-26T00:00:00",
            "document_date": "2021-05-18T00:00:00",
            "mark": "Z/21/99012349",
            "text8": "Uw bedrijfje",
            "text45": "Parkeerontheffingen Blauwe zone bedrijven",
            "title": "Ontvangen",
            "dfunction": "Verleend",
            "id": "zaak-1",
        }
        zaak_transformed = BZB(zaak_source).result()
        self.assertEqual(
            zaak_transformed["caseType"], "Parkeerontheffingen Blauwe zone bedrijven"
        )
        self.assertEqual(zaak_transformed["companyName"], "Uw bedrijfje")
        self.assertEqual(zaak_transformed["dateStart"], to_date("2021-05-26"))

    def test_Flyeren(self):
        zaak_source = {
            "mark": "Z/21/99012350",
            "document_date": "2021-05-18T00:00:00",
            "date5": "2022-02-01T00:00:00",
            "text6": "Amstel 1 1012AK AMSTERDAM",
            "date6": "2022-05-21T00:00:00",
            "date7": "2022-05-26T00:00:00",
            "text7": "10:00",
            "text8": "17:00",
            "title": "Ontvangen",
            "dfunction": "Verleend",
            "id": "zaak-1",
        }
        zaak_transformed = Flyeren(zaak_source).result()
        self.assertEqual(
            zaak_transformed["caseType"], "Verspreiden reclamemateriaal (sampling)"
        )
        self.assertEqual(zaak_transformed["timeStart"], "10:00")
        self.assertEqual(zaak_transformed["timeEnd"], "17:00")
        self.assertEqual(zaak_transformed["dateStart"], to_date("2022-05-21"))
        self.assertEqual(zaak_transformed["dateEnd"], to_date("2022-05-26"))

    def test_Diensten(self):
        zaak_source = {
            "mark": "Z/21/99012451",
            "document_date": "2021-05-18T00:00:00",
            "date5": "2022-02-01T00:00:00",
            "text6": "Amstel 12 1012AK AMSTERDAM",
            "date6": "2022-04-21T00:00:00",
            "date7": "2022-04-26T00:00:00",
            "title": "Ontvangen",
            "dfunction": "Verleend",
            "id": "zaak-1",
        }
        zaak_transformed = AanbiedenDiensten(zaak_source).result()
        self.assertEqual(zaak_transformed["caseType"], "Aanbieden van diensten")
        self.assertEqual(zaak_transformed["location"], "Amstel 12 1012AK AMSTERDAM")
        self.assertEqual(zaak_transformed["dateStart"], to_date("2022-04-21"))
        self.assertEqual(zaak_transformed["dateEnd"], to_date("2022-04-26"))