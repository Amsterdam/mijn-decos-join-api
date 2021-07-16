
from datetime import date

from decosjoin.api.decosjoin.field_parsers import (get_fields, get_translation,
                                                   to_date, to_datetime,
                                                   to_string,
                                                   to_string_if_exists,
                                                   to_time)


class Zaak:
    zaak_source = None

    zaak_type = None
    title = None
    zaak = None

    status_translations = []
    decision_translations = []
    parse_fields = []

    def __init__(self, zaak_source: dict):
        self.zaak_source = zaak_source

        self.transform()
        self.after_transform()

    def transform(self):
        # Data that's present in every Zaak
        self.zaak = {
            "caseType": self.zaak_type,
            "title": self.to_title(),
            "identifier": self.to_identifier(),
            "dateRequest": self.to_date_request(),
            "status": self.to_status(),
            "decision": self.to_decision(),
            "description": self.to_description(),
        }

        # Arbitrary data for particualar Zaken
        self.zaak.update(get_fields(self.parse_fields, self.zaak_source))

    # def before_transform(self, zaak_source):
    #     """ Pre transformation """

    def after_transform(self):
        """ Post transformation """

    def to_title(self):
        """ Returns the title we want to give to the particular case """
        return self.title

    def to_identifier(self):
        return to_string_if_exists(self.zaak_source, 'mark')

    def to_date_request(self):
        return to_datetime(to_string_if_exists(self.zaak_source, 'document_date'))

    def to_status(self) -> str:
        status_source = to_string_if_exists(self.zaak_source, 'title')
        return get_translation(status_source, self.status_translations, True)

    def to_decision(self) -> str:
        decision_source = to_string_if_exists(self.zaak_source, 'dfunction')
        return get_translation(decision_source, self.decision_translations)

    def to_date_decision(self) -> str:
        return to_datetime(to_string_if_exists(self.zaak_source, 'date5'))

    def to_description(self) -> str:
        return to_string_if_exists(self.zaak_source, 'subject1')

    def result(self):
        return self.zaak

    def type(self):
        return self.zaak_type


class TVM_RVV_Object(Zaak):

    def to_decision(self):
        value = super().to_decision()

        translate_values = [
            "verleend met borden",
            "verleend zonder bebording",
            "verleend zonder borden"
        ]

        if value and value.lower() in translate_values:
            return 'Verleend'

        return value

    zaak_type = "TVM - RVV - Object"
    title = "Tijdelijke verkeersmaatregel"

    parse_fields = [
        {"name": "dateStart", "from": "date6", "parser": to_date},
        {"name": "dateEnd", "from": "date7", "parser": to_date},
        {"name": "timeStart", "from": "text10", "parser": to_time},
        {"name": "timeEnd", "from": "text13", "parser": to_time},
        {"name": "kenteken", "from": "text9", "parser": to_string},
        {"name": "location", "from": "text6", "parser": to_string},
    ]

    def after_transform(self):
        # if end date is not defined, its the same as date start
        if not self.zaak['dateEnd']:
            self.zaak['dateEnd'] = self.zaak['dateStart']


class VakantieVerhuurVergunning(Zaak):
    zaak_type = "Vakantieverhuur vergunningsaanvraag"
    title = "Vergunning vakantieverhuur"

    @staticmethod
    def to_vakantie_verhuur_vergunning_status(value):
        # Vakantieverhuur vergunningen worden direct verleend (en dus voor Mijn Amsterdam afgehandeld)
        return "Afgehandeld"

    @staticmethod
    def to_vakantie_verhuur_vergunning_decision(value):
        # Vakantieverhuur vergunningen worden na betaling direct verleend en per mail toegekend zonder dat de juiste status in Decos wordt gezet.
        # Later, na controle, wordt mogelijk de vergunning weer ingetrokken. Geplande/Afgemelde Verhuur is een uizondering in relatie tot de reguliere statusbeschrijvingen
        # daar "Verleend" een resultaat is en geen status.
        if value and "ingetrokken" in value.lower():
            return "Ingetrokken"

        return "Verleend"

    @staticmethod
    def next_april_first(case_date: date) -> date:
        if case_date < date(case_date.year, 4, 1):
            return date(case_date.year, 4, 1)
        else:
            return date(case_date.year + 1, 4, 1)

    parse_fields = [
        {"name": "location", "from": "text6", "parser": to_string},
        {"name": "dateStart", "from": "document_date", "parser": to_date},  # same as dateRequest

        # Custom decision + status transformations based on business logic
        {"name": "status", "from": "title", "parser": to_vakantie_verhuur_vergunning_status},
        {"name": "decision", "from": "dfunction", "parser": to_vakantie_verhuur_vergunning_decision},
    ]

    def after_transform(self, zaak):
        # The validity of this case runs from april 1st until the next. set the end date to the next april the 1st
        zaak['dateEnd'] = self.next_april_first(zaak['dateRequest'])


class VakantieVerhuur(Zaak):
    zaak_type = "Vakantieverhuur"
    title = "Geplande verhuur"

    parse_fields = [
        {"name": "dateStart", "from": 'date6', "parser": to_date},  # Start verhuur
        {"name": "dateEnd", "from": 'date7', "parser": to_date},  # Einde verhuur
        {"name": "location", "from": "text6", "parser": to_string},
    ]

    def after_transform(self):
        if self.zaak['dateEnd'] and self.zaak['dateEnd'] <= date.today():
            self.zaak['title'] = 'Afgelopen verhuur'


class VakantieVerhuurAfmelding(Zaak):
    zaak_type = "Vakantieverhuur afmelding"
    title = "Geannuleerde verhuur"

    parse_fields = [
        {"name": "dateStart", "from": 'date6', "parser": to_date},  # Start verhuur
        {"name": "dateEnd", "from": 'date7', "parser": to_date},  # Einde verhuur
    ]


class BBVergunning(Zaak):
    zaak_type = "B&B - vergunning"
    title = "Vergunning bed & breakfast"

    @staticmethod
    def to_transition_agreement(value) -> bool:
        if value and value.lower() == "verleend met overgangsrecht":
            return True
        return False

    status_translations = [
        ["Publicatie aanvraag", "Ontvangen"],
        ["Ontvangen", "Ontvangen"],
        ["Volledigheidstoets uitvoeren", "Ontvangen"],
        ["Behandelen aanvraag", "In behandeling"],
        ["Huisbezoek", "In behandeling"],
        ["Beoordelen en besluiten", "In behandeling"],
        ["Afgehandeld", "Afgehandeld"],
    ]

    decision_translations = [
        ["Verleend met overgangsrecht", "Verleend"],
        ["Verleend zonder overgangsrecht", "Verleend"],
        ["Geweigerd", "Geweigerd"],
        ["Geweigerd met overgangsrecht", "Geweigerd"],
        ["Geweigerd op basis van Quotum", "Geweigerd"],
        ["Ingetrokken", "Ingetrokken"],
    ]

    parse_fields = [
        # Startdatum zaak
        {"name": "location", "from": "text6", "parser": to_string},
        {"name": "dateStart", "from": 'date6', "parser": to_date},  # Datum van
        {"name": "dateEnd", "from": 'date7', "parser": to_date},  # Datum tot en met
        {"name": "requester", "from": "company", "parser": to_string},
        {"name": "owner", "from": "text25", "parser": to_string},
        {"name": "hasTransitionAgreement", "from": "dfunction", "parser": to_transition_agreement}  # need this for tip mijn-33
    ]


class GPP(Zaak):
    zaak_type = "GPP"
    title = "Vaste parkeerplaats voor gehandicapten (GPP)"

    decision_translations = [
        ["Ingetrokken", "Ingetrokken"],
        ["Ingetrokken i.v.m. overlijden of verhuizing", "Ingetrokken"],
        ["Niet verleend", "Niet verleend"],
        ["Nog niet bekend", "", False],
        ["Verleend", "Verleend"],
    ]

    parse_fields = [
        {"name": "dateRequest", "from": "document_date", "parser": to_string},
        {"name": "kenteken", "from": "text7", "parser": to_string},
        {"name": "location", "from": "text8", "parser": to_string},
    ]


class GPK(Zaak):
    zaak_type = "GPK"
    title = "Europse gehandicaptenparkeerkaart (GPK)"

    decision_translations = [
        ["Ingetrokken", "Ingetrokken"],
        ["Ingetrokken i.v.m. overlijden of verhuizing", "Ingetrokken"],
        ["Ingetrokken verleende GPK wegens overlijden", "Ingetrokken"],
        ["Niet verleend", "Niet verleend"],
        ["Nog niet bekend", "", False],
        ["Verleend", "Verleend"],
        ["Verleend Bestuurder met GPP (niet verleend passagier)", "Verleend Bestuurder, niet verleend Passagier"],
        ["Verleend Bestuurder, niet verleend Passagier", "Verleend Bestuurder, niet verleend Passagier"],
        ["Verleend met GPP", "Verleend"],
        ["Verleend Passagier met GPP (niet verleend Bestuurder)", "Verleend Passagier, niet verleend Bestuurder"],
        ["Verleend Passagier, niet verleend Bestuurder", "Verleend Passagier, niet verleend Bestuurder"],
        ["Verleend vervangend GPK", "Verleend"],
    ]

    parse_fields = [
        {"name": "cardNumber", "from": "num3", "parser": to_string},  # kaartnummer
        {"name": "cardtype", "from": "text7", "parser": to_string},
        {"name": "dateEnd", "from": "date7", "parser": to_date},  # vervaldatum
    ]


class EvenementMelding(Zaak):
    zaak_type = "Evenement melding"
    title = "Evenement melding"

    parse_fields = [
        {"name": "dateRequest", "from": "document_date", "parser": to_string},
        {"name": "dateStart", "from": "date6", "parser": to_date},  # Op   <datum> ?
        {"name": "location", "from": "text8", "parser": to_string},
        {"name": "timeStart", "from": "text7", "parser": to_time},  # Van   <tijd>
        {"name": "timeEnd", "from": "text8", "parser": to_time},  # Tot    <tijd>
    ]

    decision_translations = [
        ["Ingetrokken", "Ingetrokken"],
        ["Niet verleend", "Geweigerd"],
        ["Verleend", "Gemeld"],
        ["Nog niet  bekend", "", False],
        ["Nog niet bekend", "", False],
        ["Verleend", "Verleend"],
        ["Verleend (Bijzonder/Bewaren)", "Verleend"],
        ["Verleend zonder borden", "Verleend"],
    ]


class EvenementVergunning(Zaak):
    zaak_type = "Evenement vergunning"
    title = "Evenement vergunning"

    parse_fields = [
        {"name": "dateRequest", "from": "document_date", "parser": to_datetime},
        {"name": "dateStart", "from": "date6", "parser": to_date},  # Datum van
        {"name": "dateEnd", "from": "date7", "parser": to_date},  # Datum tot en met
        {"name": "location", "from": "text8", "parser": to_string},
        {"name": "timeStart", "from": "text7", "parser": to_time},
        {"name": "timeEnd", "from": "text8", "parser": to_time},  # tijd tot
    ]

    decision_translations = [
        ["Afgebroken (Ingetrokken)", "Afgebroken (Ingetrokken)"],
        ["Geweigerd", "Geweigerd"],
        ["Nog niet  bekend", "", False],
        ["Nog niet  bekend", "", False],
        ["Nog niet bekend", "", False],
        ["Verleend", "Verleend"],
        ["Verleend (Bijzonder/Bewaren)", "Verleend"],
        ["Verleend zonder borden", "Verleend"],
    ]


class Omzettingsvergunning(Zaak):
    zaak_type = "Omzettingsvergunning"
    title = "Vergunning voor kamerverhuur"

    parse_fields = [
        {"name": "dateRequest", "from": "document_date", "parser": to_datetime},
        {"name": "location", "from": "text8", "parser": to_string},
    ]

    decision_translations = [
        ["Geweigerd", "Geweigerd"],
        ["Ingetrokken door gemeente", "Ingetrokken door gemeente"],
        ["Ingetrokken op eigen verzoek", "Ingetrokken op eigen verzoek"],
        ["Nog niet bekend", "", False],
        ["Van rechtswege verleend", "Verleend"],
        ["Vergunningvrij", "Vergunningvrij"],
        ["Verleend", "Verleend"],
        ["Verleend zonder borden", "Verleend"],
    ]


class ERVV_TVM(Zaak):
    zaak_type = "E-RVV - TVM"
    title = "e-RVV (Gratis verkeersontheffing voor elektrisch goederenvervoer)"

    parse_fields = [
        {"name": "dateRequest", "from": "document_date", "parser": to_string},
        {"name": "location", "from": "text8", "parser": to_string},
        {"name": "dateStart", "from": "date6", "parser": to_date},  # Datum van
        {"name": "dateEnd", "from": "date7", "parser": to_date},  # Datum tot en met
        {"name": "timeStart", "from": "text10", "parser": to_time},
        {"name": "timeEnd", "from": "text13", "parser": to_time},  # tijd tot
    ]

    decision_translations = [
        ["Ingetrokken", "Ingetrokken"],
        ["Niet verleend", "Niet verleend"],
        ["Nog niet bekend", "", False],
        ["Verleend met borden", "Verleend"],
        ["Verleend met borden en Fietsenrekken verwijderen", "Verleend"],
        ["Verleend met Fietsenrekken verwijderen", "Verleend"],
        ["Verleend zonder bebording", "Verleend"],
        ["Verleend zonder borden", "Verleend"],
    ]


zaken_index = {
    'tvm - rvv - object': [TVM_RVV_Object, True],
    'vakantieverhuur': [VakantieVerhuur, True],
    'vakantieverhuur vergunningsaanvraag': [VakantieVerhuurVergunning, True],
    'b&b - vergunning': [BBVergunning, True],
    'gpp': [GPP, True],
    'gpk': [GPK, True],
    'omzettingsvergunning': [Omzettingsvergunning, True],
    'e-rvv - tvm': [ERVV_TVM, True],
    'evenement melding': [EvenementMelding, False],
    'evenement vergunning': [EvenementVergunning, False],
}