from datetime import date
from unittest.case import TestCase

from decosjoin.api.decosjoin.field_parsers import to_date
from decosjoin.api.decosjoin.zaaktypes import (BBVergunning, BZB, BZP, TVM_RVV_Object,
                                               VakantieVerhuurVergunning)


class ZaaktypesTest(TestCase):

    def test_next_april_first(self):
        self.assertEqual(VakantieVerhuurVergunning.next_april_first(date(2021, 3, 1)), date(2021, 4, 1))
        self.assertEqual(VakantieVerhuurVergunning.next_april_first(date(2021, 4, 1)), date(2022, 4, 1))
        self.assertEqual(VakantieVerhuurVergunning.next_april_first(date(2021, 6, 1)), date(2022, 4, 1))

    def test_to_transition_agreement(self):
        self.assertEqual(BBVergunning.to_transition_agreement('Verleend met overgangsrecht'), True)
        self.assertEqual(BBVergunning.to_transition_agreement('Verleend zonder overgangsrecht'), False)
        self.assertEqual(BBVergunning.to_transition_agreement('abc'), False)

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
            "document_date": "2021-04-16T00:00:00"
        }

        zaak_transformed = {
            "caseType": "TVM - RVV - Object",
            "title": "Tijdelijke verkeersmaatregel",
            "identifier": "Z/20/1234567",
            "dateRequest": to_date(zaak_source['document_date']),
            "status": "Ontvangen",
            "decision": None,
            "dateDecision": None,
            "description": "Test beschrijving",
            "kenteken": None,
            "location": "Amstel 1 1000AB",
            "timeEnd": "16:00",
            "timeStart": "10:00",
            "dateStart": to_date(zaak_source['date6']),
            "dateEnd": to_date(zaak_source['date7']),
        }

        self.assertEqual(TVM_RVV_Object(zaak_source).zaak, zaak_transformed)

    # def test_VakantieVerhuurVergunning(self):
    #     self.assertEqual()

    # def test_VakantieVerhuur(self):
    #     self.assertEqual()

    # def test_VakantieVerhuurAfmelding(self):
    #     self.assertEqual()

    # def test_BBVergunning(self):
    #     self.assertEqual()

    # def test_GPP(self):
    #     self.assertEqual()

    # def test_GPK(self):
    #     self.assertEqual()

    # def test_EvenementMelding(self):
    #     self.assertEqual()

    # def test_EvenementVergunning(self):
    #     self.assertEqual()

    # def test_Omzettingsvergunning(self):
    #     self.assertEqual()

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
            "dfunction": "Verleend"
        }
        zaak_transformed = BZP(zaak_source).result()
        self.assertEqual(zaak_transformed["caseType"], "Parkeerontheffingen Blauwe zone particulieren")
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
            "dfunction": "Verleend"
        }
        zaak_transformed = BZB(zaak_source).result()
        self.assertEqual(zaak_transformed["caseType"], "Parkeerontheffingen Blauwe zone bedrijven")
        self.assertEqual(zaak_transformed["companyName"], "Uw bedrijfje")
        self.assertEqual(zaak_transformed["dateStart"], to_date("2021-05-26"))
