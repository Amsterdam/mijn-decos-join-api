from datetime import date
from decosjoin.api.decosjoin.field_parsers import to_date, to_datetime
from unittest.case import TestCase

from decosjoin.api.decosjoin.zaaktypes import (BBVergunning, TVM_RVV_Object,
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
            "dateRequest": to_datetime(zaak_source['document_date']),
            "status": "Ontvangen",
            "decision": None,
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
