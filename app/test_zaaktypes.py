from datetime import date
from unittest.case import TestCase
from unittest.mock import MagicMock, call

from app.field_parsers import to_date
from app.zaaktypes import (
    BZB,
    BZP,
    AanbiedenDiensten,
    BBVergunning,
    Flyeren,
    NachtwerkOntheffing,
    Omzettingsvergunning,
    TVM_RVV_Object,
    VakantieVerhuurVergunning,
    ZwaarVerkeer,
    Samenvoegingsvergunning,
    Splitsingsvergunning,
    VOBvergunning,
    RVVHeleStad,
    RVVSloterweg,
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
            "processed": False,
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
            "date6": "2021-06-26T00:00:00",
            "date7": "2022-06-26T00:00:00",
            "document_date": "2021-05-18T00:00:00",
            "mark": "Z/21/99012350",
            "text8": ";KN-UW-TS;AAZZ88",
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
        self.assertEqual(zaak_transformed["kenteken"], "KN-UW-TS | AAZZ88")
        self.assertEqual(zaak_transformed["dateStart"], to_date("2021-06-26"))

    def test_BZB(self):
        zaak_source = {
            "date6": "2021-05-26T00:00:00",
            "date7": "2022-05-26T00:00:00",
            "document_date": "2021-05-18T00:00:00",
            "mark": "Z/21/99012349",
            "company": "Uw bedrijfje",
            "text45": "Parkeerontheffingen Blauwe zone bedrijven",
            "title": "Ontvangen",
            "dfunction": "Verleend",
            "num6": "4",
            "id": "zaak-1",
        }
        zaak_transformed = BZB(zaak_source).result()
        self.assertEqual(
            zaak_transformed["caseType"], "Parkeerontheffingen Blauwe zone bedrijven"
        )
        self.assertEqual(zaak_transformed["companyName"], "Uw bedrijfje")
        self.assertEqual(zaak_transformed["dateStart"], to_date("2021-05-26"))
        self.assertEqual(zaak_transformed["numberOfPermits"], 4)

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
        self.assertEqual(zaak_transformed["caseType"], "Flyeren-Sampling")
        self.assertEqual(zaak_transformed["timeStart"], "10:00")
        self.assertEqual(zaak_transformed["timeEnd"], "17:00")
        self.assertEqual(zaak_transformed["dateStart"], to_date("2022-05-21"))
        self.assertEqual(zaak_transformed["dateEnd"], to_date("2022-05-26"))
        self.assertEqual(zaak_transformed["decision"], "Verleend")

    def test_FlyerenNietBetaald(self):
        zaak_source = {
            "mark": "Z/21/99012350",
            "document_date": "2021-05-18T00:00:00",
            "date5": "2022-02-01T00:00:00",
            "text6": "Amstel 1 1012AK AMSTERDAM",
            "date6": "2022-05-21T00:00:00",
            "date7": "2022-05-26T00:00:00",
            "text7": "10:00",
            "text8": "17:00",
            "text11": "Nogniet",
            "text12": "Wacht op online betaling",
            "title": "Ontvangen",
            "dfunction": "Verleend",
            "id": "zaak-1",
        }
        zaak_transformed = Flyeren(zaak_source).result()
        # should not transform because payment is not completed
        self.assertEqual(zaak_transformed, None)

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
        self.assertEqual(zaak_transformed["decision"], "Toegestaan")

    def test_Nachtwerk(self):
        zaak_source = {
            "mark": "Z/22/9901425151",
            "document_date": "2022-05-18T00:00:00",
            "date5": "2022-02-01T00:00:00",
            "text6": "Amstel 1 1012AK AMSTERDAM",
            "date6": "2022-07-21T00:00:00",
            "date7": "2022-07-26T00:00:00",
            "text7": "10:00",
            "text10": "17:00",
            "title": "Ontvangen",
            "dfunction": "Verleend met borden",
            "id": "zaak-1",
        }
        zaak_transformed = NachtwerkOntheffing(zaak_source).result()
        self.assertEqual(
            zaak_transformed["title"],
            "Geluidsontheffing werken in de openbare ruimte (nachtwerkontheffing)",
        )
        self.assertEqual(zaak_transformed["location"], "Amstel 1 1012AK AMSTERDAM")
        self.assertEqual(zaak_transformed["dateStart"], to_date("2022-07-21"))
        self.assertEqual(zaak_transformed["dateEnd"], to_date("2022-07-26"))
        self.assertEqual(zaak_transformed["timeStart"], "10:00")
        self.assertEqual(zaak_transformed["timeEnd"], "17:00")
        self.assertEqual(zaak_transformed["decision"], "Verleend")

        class connection_mock:
            get_workflow = MagicMock(return_value=to_date("2022-06-15"))

        zaken_all = []

        NachtwerkOntheffing.defer_transform(
            zaak_transformed, zaken_all, connection_mock()
        )

        self.assertEqual(zaak_transformed["dateWorkflowActive"], to_date("2022-06-15"))

        connection_mock.get_workflow.assert_called_once_with(
            "zaak-1",
            NachtwerkOntheffing.date_workflow_active_step_title,
        )

    def test_ZwaarVerkeer(self):
        zaak_source = {
            "mark": "Z/22/9901425152",
            "document_date": "2022-05-18T00:00:00",
            "date5": "2022-02-01T00:00:00",
            "date6": "2022-10-21T00:00:00",
            "date7": "2023-10-26T00:00:00",
            "text17": "Routeontheffing brede wegen tm 30 ton",
            "text49": "KN-UW-TS,AAZZ88",
            "title": "Ontvangen",
            "dfunction": "Verleend",
            "id": "zaak-99",
        }

        zaak_transformed = ZwaarVerkeer(zaak_source).result()
        self.assertEqual(
            zaak_transformed["title"],
            "Ontheffing zwaar verkeer",
        )
        self.assertEqual(zaak_transformed["dateStart"], to_date("2022-10-21"))
        self.assertEqual(zaak_transformed["dateEnd"], to_date("2023-10-26"))
        self.assertEqual(
            zaak_transformed["exemptionKind"],
            "Routeontheffing breed opgezette wegen tot en met 30 ton",
        )

        class connection_mock:
            get_workflow = MagicMock(return_value=to_date("2022-10-15"))

        zaken_all = []

        ZwaarVerkeer.defer_transform(zaak_transformed, zaken_all, connection_mock())
        self.assertEqual(zaak_transformed["dateWorkflowActive"], to_date("2022-10-15"))

        connection_mock.get_workflow.assert_called_once_with(
            "zaak-99",
            ZwaarVerkeer.date_workflow_active_step_title,
        )

    def test_Samenvoegingsvergunning(self):
        zaak_source = {
            "mark": "Z/22/9901425263",
            "document_date": "2022-05-18T00:00:00",
            "date5": "2022-02-01T00:00:00",
            "text6": "Amstel 1 1000AB",
            "title": "Ontvangen",
            "dfunction": "Verleend",
            "id": "zaak-100",
        }

        zaak_transformed = Samenvoegingsvergunning(zaak_source).result()
        self.assertEqual(
            zaak_transformed["title"],
            "Vergunning voor samenvoegen van woonruimten",
        )
        self.assertEqual(zaak_transformed["location"], "Amstel 1 1000AB")

        class connection_mock:
            get_workflow = MagicMock(return_value=to_date("2022-10-15"))

        zaken_all = []

        Samenvoegingsvergunning.defer_transform(
            zaak_transformed, zaken_all, connection_mock()
        )
        self.assertEqual(zaak_transformed["dateWorkflowActive"], to_date("2022-10-15"))

        connection_mock.get_workflow.assert_called_once_with(
            "zaak-100",
            Samenvoegingsvergunning.date_workflow_active_step_title,
        )

    def test_Splitsingsvergunning(self):
        zaak_source = {
            "mark": "Z/22/9901425263",
            "document_date": "2022-05-18T00:00:00",
            "date5": "2022-02-01T00:00:00",
            "text6": "Amstel 10 1000AB",
            "title": "Ontvangen",
            "dfunction": "Verleend",
            "id": "zaak-101",
        }

        zaak_transformed = Splitsingsvergunning(zaak_source).result()
        self.assertEqual(
            zaak_transformed["title"],
            "Splitsingsvergunning",
        )
        self.assertEqual(zaak_transformed["location"], "Amstel 10 1000AB")

        class connection_mock:
            get_workflow = MagicMock(return_value=to_date("2022-10-20"))

        zaken_all = []

        Splitsingsvergunning.defer_transform(
            zaak_transformed, zaken_all, connection_mock()
        )
        self.assertEqual(zaak_transformed["dateWorkflowActive"], to_date("2022-10-20"))

        connection_mock.get_workflow.assert_called_once_with(
            "zaak-101",
            Splitsingsvergunning.date_workflow_active_step_title,
        )

    def test_VOB(self):
        zaak_source = {
            "mark": "Z/23/99012462",
            "document_date": "2023-05-18T00:00:00",
            "text6": "Amstel 12 1012AK AMSTERDAM",
            "text9": "Ligplaatsvergunning woonboot",
            "text10": "Sloep",
            "text14": "Sloepie IX",
            "text18": "Nieuwe ligplaats",
            "title": "Ontvangen",
            "dfunction": "Verleend",
            "id": "zaak-145",
        }
        zaak_transformed = VOBvergunning(zaak_source).result()
        self.assertEqual(zaak_transformed["caseType"], "VOB")
        self.assertEqual(
            zaak_transformed["title"],
            "Ligplaatsvergunning",
        )
        self.assertEqual(zaak_transformed["location"], "Amstel 12 1012AK AMSTERDAM")
        self.assertEqual(zaak_transformed["decision"], "Verleend")
        self.assertEqual(
            zaak_transformed["requestKind"], "Ligplaatsvergunning woonboot"
        )
        self.assertEqual(zaak_transformed["reason"], "Nieuwe ligplaats")
        self.assertEqual(zaak_transformed["vesselKind"], "Sloep")
        self.assertEqual(zaak_transformed["vesselName"], "Sloepie IX")

        class connection_mock:
            get_workflow = MagicMock(return_value=to_date("2023-03-13"))

        zaken_all = []

        VOBvergunning.defer_transform(zaak_transformed, zaken_all, connection_mock())
        self.assertEqual(zaak_transformed["dateWorkflowActive"], to_date("2023-03-13"))

        connection_mock.get_workflow.assert_called_once_with(
            "zaak-145",
            VOBvergunning.date_workflow_active_step_title,
        )

    def test_RVVHeleStad(self):
        zaak_source = {
            "mark": "Z/23/11023673",
            "document_date": "2023-04-18T00:00:00",
            "date5": "2023-02-01T00:00:00",
            "date6": "2023-06-21T00:00:00",
            "date7": "2023-12-24T00:00:00",
            "text49": "KN-UW-TS,AAZZ88",
            "title": "Ontvangen",
            "dfunction": "Verleend",
            "id": "zaak-146",
        }
        zaak_transformed = RVVHeleStad(zaak_source).result()
        self.assertEqual(zaak_transformed["caseType"], "RVV - Hele stad")
        self.assertEqual(
            zaak_transformed["title"],
            "RVV-verkeersontheffing",
        )
        self.assertEqual(zaak_transformed["decision"], "Verleend")
        self.assertEqual(
            zaak_transformed["dateDecision"], to_date("2023-02-01T00:00:00")
        )
        self.assertEqual(zaak_transformed["dateStart"], to_date("2023-06-21T00:00:00"))
        self.assertEqual(zaak_transformed["dateEnd"], to_date("2023-12-24T00:00:00"))
        self.assertEqual(zaak_transformed["licensePlates"], "KN-UW-TS | AAZZ88")

        class connection_mock:
            get_workflow = MagicMock(return_value=to_date("2023-04-11"))

        zaken_all = []

        RVVHeleStad.defer_transform(zaak_transformed, zaken_all, connection_mock())
        self.assertEqual(zaak_transformed["dateWorkflowActive"], to_date("2023-04-11"))

        connection_mock.get_workflow.assert_called_once_with(
            "zaak-146",
            RVVHeleStad.date_workflow_active_step_title,
        )

    def test_RVVSlooterweg(self):
        zaak_source = {
            "mark": "Z/23/123123123",
            "document_date": "2023-04-18T00:00:00",
            "date5": "2023-02-01T00:00:00",
            "date6": "2023-06-21T00:00:00",
            "date7": "2023-12-24T00:00:00",
            "text10": "KN-UW-TS, AAZZ88",
            "text15": "LA-TO-RS, BA-BI-BO",
            "title": "Ontvangen",
            "dfunction": "Verleend",
            "id": "zaak-147",
        }
        zaak_transformed = RVVSloterweg(zaak_source).result()
        self.assertEqual(zaak_transformed["caseType"], "Sluipverkeer Slooterweg")
        self.assertEqual(
            zaak_transformed["title"],
            "RVV ontheffing Sloterweg",
        )
        self.assertEqual(zaak_transformed["decision"], "Verleend")
        self.assertEqual(
            zaak_transformed["dateDecision"], to_date("2023-02-01T00:00:00")
        )
        self.assertEqual(zaak_transformed["dateStart"], to_date("2023-06-21T00:00:00"))
        self.assertEqual(zaak_transformed["dateEnd"], to_date("2023-12-24T00:00:00"))
        self.assertEqual(zaak_transformed["licensePlates"], "KN-UW-TS | AAZZ88")
        self.assertEqual(
            zaak_transformed["previousLicensePlates"], "LA-TO-RS | BA-BI-BO"
        )

        class connection_mock:
            get_workflow = MagicMock(return_value=to_date("2023-04-11"))

        zaken_all = []

        RVVSloterweg.defer_transform(zaak_transformed, zaken_all, connection_mock())

        self.assertEqual(zaak_transformed["dateWorkflowActive"], to_date("2023-04-11"))
        self.assertEqual(
            zaak_transformed["dateWorkflowVerleend"], to_date("2023-04-11")
        )

        connection_mock.get_workflow.assert_has_calls(
            [
                call("zaak-147", RVVSloterweg.date_workflow_active_step_title),
                call("zaak-147", RVVSloterweg.date_workflow_verleend_step_title),
            ],
        )
