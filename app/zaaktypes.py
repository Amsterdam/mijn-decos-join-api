import re
from datetime import date

from app.config import IS_PRODUCTION
from app.field_parsers import (
    get_fields,
    get_translation,
    to_date,
    to_int,
    to_string,
    to_string_if_exists,
    to_time,
    to_bool,
    to_bool_if_exists,
)


def static(method):
    return method.__func__


class Zaak:
    enabled = True
    zaak_source = None

    zaak_type = None
    title = None
    zaak = None

    status_translations = []
    decision_translations = []
    parse_fields = []

    def __init__(self, zaak_source: dict):
        self.zaak_source = zaak_source

        if not self.has_valid_source_data():
            return
        self.transform()
        self.after_transform()

    def transform(self):
        # Data that's present in every Zaak
        self.zaak = {
            "id": self.zaak_source["id"],
            "caseType": self.zaak_type,
            "title": self.to_title(),
            "identifier": self.to_identifier(),
            "dateRequest": self.to_date_request(),
            "dateWorkflowActive": self.to_date_request(),
            "status": self.to_status(),
            "decision": self.to_decision(),
            "dateDecision": self.to_date_decision(),
            "description": self.to_description(),
            "processed": self.to_processed(),
        }

        # Arbitrary data for individual Zaken
        self.zaak.update(get_fields(self.parse_fields, self.zaak_source))

    def after_transform(self):
        """Post transformation"""

    defer_transform = None  # Should be @staticmethod if defined
    # @staticmethod
    # def defer_transform(self, zaak_deferred, decosjoin_service):
    #     return zaak_deferred

    def to_title(self):
        """Returns the title we want to give to the particular case"""
        return self.title

    def to_identifier(self):  # Zaak kenmerk
        return to_string_if_exists(self.zaak_source, "mark")

    def to_date_request(self):  # Startdatum zaak
        return to_date(to_string_if_exists(self.zaak_source, "document_date"))

    def to_status(self) -> str:
        status_source = to_string_if_exists(self.zaak_source, "title")
        return get_translation(status_source, self.status_translations, True)

    def to_decision(self) -> str:  # Resultaat (besluit)
        decision_source = to_string_if_exists(self.zaak_source, "dfunction")
        return get_translation(decision_source, self.decision_translations, True)

    def to_date_decision(self) -> str:  # Datum afhandeling
        return to_date(to_string_if_exists(self.zaak_source, "date5"))

    def to_description(self) -> str:
        return to_string_if_exists(self.zaak_source, "subject1")

    def to_processed(self):
        return to_bool_if_exists(self.zaak_source, "processed")

    def result(self):
        return self.zaak

    def type(self):
        return self.zaak_type

    def has_valid_source_data(self):
        return True

    def has_valid_payment_status(self):
        payment_status = to_string_if_exists(self.zaak_source, "text11")
        payment_method = to_string_if_exists(self.zaak_source, "text12")

        if payment_status == "Nogniet" and payment_method == "Wacht op online betaling":
            return False

        return True


#######################
# Zaak configurations #
#######################


class TVM_RVV_Object(Zaak):
    zaak_type = "TVM - RVV - Object"
    title = "Tijdelijke verkeersmaatregel (TVM-RVV-Object)"

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
        if not self.zaak["dateEnd"]:
            self.zaak["dateEnd"] = self.zaak["dateStart"]

    def to_decision(self):
        value = super().to_decision()

        translate_values = [
            "verleend met borden",
            "verleend zonder bebording",
            "verleend zonder borden",
        ]

        if value and value.lower() in translate_values:
            return "Verleend"

        return value

    def has_valid_source_data(self):
        return super().has_valid_payment_status()


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
        return date(case_date.year + 1, 4, 1)

    parse_fields = [
        {"name": "location", "from": "text6", "parser": to_string},
        {
            "name": "dateStart",
            "from": "document_date",
            "parser": to_date,
        },  # same as dateRequest
        # Custom decision + status transformations based on business logic
        {
            "name": "status",
            "from": "title",
            "parser": static(to_vakantie_verhuur_vergunning_status),
        },
        {
            "name": "decision",
            "from": "dfunction",
            "parser": static(to_vakantie_verhuur_vergunning_decision),
        },
    ]

    def after_transform(self):
        # The validity of this case runs from april 1st until the next. set the end date to the next april the 1st
        self.zaak["dateEnd"] = self.next_april_first(self.zaak["dateRequest"])


class BBVergunning(Zaak):
    zaak_type = "B&B - vergunning"
    title = "Vergunning bed & breakfast"

    date_workflow_active_step_title = "B&B - vergunning - Behandelen"

    @staticmethod
    def to_transition_agreement(value) -> bool:
        if value and value.lower() == "verleend met overgangsrecht":
            return True
        return False

    @staticmethod
    def defer_transform(zaak_deferred, decosjoin_service):
        date_workflow_active = decosjoin_service.get_workflow(
            zaak_deferred["id"], BBVergunning.date_workflow_active_step_title
        )
        zaak_deferred["dateWorkflowActive"] = date_workflow_active
        return zaak_deferred

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
        {"name": "dateStart", "from": "date6", "parser": to_date},  # Datum van
        {"name": "dateEnd", "from": "date7", "parser": to_date},  # Datum tot en met
        {"name": "requester", "from": "company", "parser": to_string},
        {"name": "owner", "from": "text25", "parser": to_string},
        {
            "name": "hasTransitionAgreement",
            "from": "dfunction",
            "parser": static(to_transition_agreement),
        },  # need this for tip mijn-33
    ]


class GPP(Zaak):
    # !!!!!!!!!!!!!
    enabled = True
    # !!!!!!!!!!!!!

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
        {"name": "kenteken", "from": "text7", "parser": to_string},
        {"name": "location", "from": "text8", "parser": to_string},
    ]


class GPK(Zaak):
    # !!!!!!!!!!!!!
    enabled = True
    # !!!!!!!!!!!!!

    zaak_type = "GPK"
    title = "Europese gehandicaptenparkeerkaart (GPK)"

    decision_translations = [
        ["Ingetrokken", "Ingetrokken"],
        ["Ingetrokken i.v.m. overlijden of verhuizing", "Ingetrokken"],
        ["Ingetrokken verleende GPK wegens overlijden", "Ingetrokken"],
        ["Niet verleend", "Niet verleend"],
        ["Nog niet bekend", "", False],
        ["Verleend", "Verleend"],
        [
            "Verleend Bestuurder met GPP (niet verleend passagier)",
            "Verleend Bestuurder, niet verleend Passagier",
        ],
        [
            "Verleend Bestuurder, niet verleend Passagier",
            "Verleend Bestuurder, niet verleend Passagier",
        ],
        # Decos cuts of the field at 50 chars, we sadly have to anticipate on this
        [
            "Verleend Bestuurder met GPP (niet verleend passagi",
            "Verleend Bestuurder, niet verleend Passagier",
        ],
        ["Verleend met GPP", "Verleend"],
        [
            "Verleend Passagier met GPP (niet verleend Bestuurder)",
            "Verleend Passagier, niet verleend Bestuurder",
        ],
        # Decos cuts of the field at 50 chars, we sadly have to anticipate on this
        [
            "Verleend Passagier met GPP (niet verleend Bestuurd",
            "Verleend Passagier, niet verleend Bestuurder",
        ],
        [
            "Verleend Passagier, niet verleend Bestuurder",
            "Verleend Passagier, niet verleend Bestuurder",
        ],
        ["Verleend vervangend GPK", "Verleend"],
    ]

    parse_fields = [
        {"name": "cardNumber", "from": "num3", "parser": to_int},  # kaartnummer
        {"name": "cardtype", "from": "text7", "parser": to_string},
        {"name": "dateEnd", "from": "date7", "parser": to_date},  # vervaldatum
    ]


class EvenementMelding(Zaak):
    # !!!!!!!!!!!!!
    enabled = True
    # !!!!!!!!!!!!!

    zaak_type = "Evenement melding"
    title = "Evenement melding"

    parse_fields = [
        {"name": "dateStart", "from": "date6", "parser": to_date},  # Op   <datum> ?
        {"name": "dateEnd", "from": "date7", "parser": to_date},
        {"name": "location", "from": "text6", "parser": to_string},
        {"name": "timeStart", "from": "text7", "parser": to_time},  # Van   <tijd>
        {"name": "timeEnd", "from": "text8", "parser": to_time},  # Tot    <tijd>
    ]

    decision_translations = [
        ["Ingetrokken", "Ingetrokken"],
        ["Niet verleend", "Niet toegestaan"],
        ["Verleend", "Toegestaan"],
        ["Nog niet  bekend", "", False],
        ["Nog niet bekend", "", False],
        ["Verleend", "Verleend"],
        ["Verleend (Bijzonder/Bewaren)", "Verleend"],
        ["Verleend zonder borden", "Verleend"],
    ]


class EvenementVergunning(Zaak):
    # !!!!!!!!!!!!!
    enabled = True
    # !!!!!!!!!!!!!

    zaak_type = "Evenement vergunning"
    title = "Evenement vergunning"

    parse_fields = [
        {"name": "dateStart", "from": "date6", "parser": to_date},  # Datum van
        {"name": "dateEnd", "from": "date7", "parser": to_date},  # Datum tot en met
        {"name": "location", "from": "text6", "parser": to_string},
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
    # !!!!!!!!!!!!!
    enabled = True
    # !!!!!!!!!!!!!

    zaak_type = "Omzettingsvergunning"
    title = "Vergunning voor kamerverhuur (omzettingsvergunning)"
    date_workflow_active_step_title = "Omzettingsvergunning - Behandelen"

    @staticmethod
    def defer_transform(zaak_deferred, decosjoin_service):
        date_workflow_active = decosjoin_service.get_workflow(
            zaak_deferred["id"], Omzettingsvergunning.date_workflow_active_step_title
        )
        zaak_deferred["dateWorkflowActive"] = date_workflow_active
        return zaak_deferred

    parse_fields = [
        {"name": "location", "from": "text6", "parser": to_string},
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
    # !!!!!!!!!!!!!
    enabled = True
    # !!!!!!!!!!!!!

    zaak_type = "E-RVV - TVM"
    title = "e-RVV (Gratis verkeersontheffing voor elektrisch goederenvervoer)"

    parse_fields = [
        {"name": "location", "from": "text6", "parser": to_string},
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


class BZP(Zaak):
    # !!!!!!!!!!!!!
    enabled = True
    # !!!!!!!!!!!!!

    zaak_type = "Parkeerontheffingen Blauwe zone particulieren"
    title = "Parkeerontheffingen Blauwe zone particulieren"

    @staticmethod
    def to_kenteken(value) -> bool:
        if not value:
            return None

        value = re.sub("[^0-9a-zA-Z-]+", " ", value)
        value = re.sub(" +", " ", value.strip())
        value = re.sub(" ", " | ", value.upper())

        return value

    parse_fields = [
        {"name": "dateStart", "from": "date6", "parser": to_date},  # Datum van
        {"name": "dateEnd", "from": "date7", "parser": to_date},  # Datum tot en met
        {"name": "kenteken", "from": "text8", "parser": static(to_kenteken)},
    ]

    decision_translations = [
        ["Ingetrokken", "Ingetrokken"],
        ["Niet verleend", "Niet verleend"],
        ["Verleend", "Verleend"],
    ]

    def has_valid_source_data(self):
        return super().has_valid_payment_status()


class BZB(Zaak):
    # !!!!!!!!!!!!!
    enabled = True
    # !!!!!!!!!!!!!

    zaak_type = "Parkeerontheffingen Blauwe zone bedrijven"
    title = "Parkeerontheffingen Blauwe zone bedrijven"

    parse_fields = [
        {"name": "dateStart", "from": "date6", "parser": to_date},  # Datum van
        {"name": "dateEnd", "from": "date7", "parser": to_date},  # Datum tot en met
        {"name": "companyName", "from": "company", "parser": to_string},
        {"name": "numberOfPermits", "from": "num6", "parser": to_int},
    ]

    decision_translations = [
        ["Ingetrokken", "Ingetrokken"],
        ["Niet verleend", "Niet verleend"],
        ["Verleend", "Verleend"],
    ]


class Flyeren(Zaak):
    # !!!!!!!!!!!!!
    enabled = True
    # !!!!!!!!!!!!!

    zaak_type = "Flyeren-Sampling"
    title = "Verspreiden reclamemateriaal (sampling)"

    parse_fields = [
        {"name": "location", "from": "text6", "parser": to_string},  # Locatie
        {"name": "dateStart", "from": "date6", "parser": to_date},  # Datum van
        {"name": "dateEnd", "from": "date7", "parser": to_date},  # Datum tot en met
        {"name": "timeStart", "from": "text7", "parser": to_time},  # Start tijd
        {"name": "timeEnd", "from": "text8", "parser": to_time},  # Eind tijd
    ]

    decision_translations = [
        ["Ingetrokken", "Ingetrokken"],
        ["Niet verleend", "Niet verleend"],
        ["Verleend", "Verleend"],
    ]

    def has_valid_source_data(self):
        return super().has_valid_payment_status()


class AanbiedenDiensten(Zaak):
    # !!!!!!!!!!!!!
    enabled = True
    # !!!!!!!!!!!!!

    zaak_type = "Aanbieden van diensten"
    title = "Aanbieden van diensten"

    parse_fields = [
        {"name": "location", "from": "text6", "parser": to_string},  # Locatie
        {"name": "dateStart", "from": "date6", "parser": to_date},  # Datum van
        {"name": "dateEnd", "from": "date7", "parser": to_date},  # Datum tot
    ]

    decision_translations = [
        ["Ingetrokken", "Ingetrokken"],
        ["Niet verleend", "Niet toegestaan"],
        ["Verleend", "Toegestaan"],
    ]


class NachtwerkOntheffing(Zaak):
    # !!!!!!!!!!!!!
    enabled = True
    # !!!!!!!!!!!!!

    zaak_type = "Nachtwerkontheffing"
    title = "Geluidsontheffing werken in de openbare ruimte (nachtwerkontheffing)"
    date_workflow_active_step_title = "Nachtwerkontheffing - Behandelen"

    @staticmethod
    def defer_transform(zaak_deferred, decosjoin_service):
        date_workflow_active = decosjoin_service.get_workflow(
            zaak_deferred["id"], NachtwerkOntheffing.date_workflow_active_step_title
        )
        zaak_deferred["dateWorkflowActive"] = date_workflow_active
        return zaak_deferred

    parse_fields = [
        {"name": "location", "from": "text6", "parser": to_string},  # Locatie
        {"name": "dateStart", "from": "date6", "parser": to_date},  # Datum van
        {"name": "dateEnd", "from": "date7", "parser": to_date},  # Datum tot
        {"name": "timeStart", "from": "text7", "parser": to_time},  # Start tijd
        {"name": "timeEnd", "from": "text10", "parser": to_time},  # Eind tijd
    ]

    decision_translations = [
        ["Ingetrokken", "Ingetrokken"],
        ["Niet verleend", "Niet verleend"],
        ["Verleend met borden", "Verleend"],
        ["Verleend zonder borden", "Verleend"],
    ]

    def has_valid_source_data(self):
        return super().has_valid_payment_status()


class ZwaarVerkeer(Zaak):
    # !!!!!!!!!!!!!
    enabled = True
    # !!!!!!!!!!!!!

    zaak_type = "Zwaar verkeer"
    title = "Ontheffing zwaar verkeer"
    date_workflow_active_step_title = "Zwaar verkeer - Behandelen"

    @staticmethod
    def defer_transform(zaak_deferred, decosjoin_service):
        date_workflow_active = decosjoin_service.get_workflow(
            zaak_deferred["id"], ZwaarVerkeer.date_workflow_active_step_title
        )
        zaak_deferred["dateWorkflowActive"] = date_workflow_active
        return zaak_deferred

    def to_kind(kind_source) -> str:
        if not kind_source:
            return None
        return get_translation(kind_source, ZwaarVerkeer.kind_translations, True)

    parse_fields = [
        {
            "name": "exemptionKind",
            "from": "text17",
            "parser": to_kind,
        },  # Soort ontheffing
        {
            "name": "licensePlates",
            "from": "text49",
            "parser": BZP.to_kenteken,
        },  # Kentekens
        {"name": "dateStart", "from": "date6", "parser": to_date},  # Van
        {"name": "dateEnd", "from": "date7", "parser": to_date},  # Tot en met
    ]

    kind_translations = [
        [
            "Jaarontheffing bijzonder",
            "Jaarontheffing hele zone voor bijzondere voertuigen",
        ],
        ["Jaarontheffing gewicht", "Jaarontheffing hele zone met gewichtsverklaring"],
        [
            "Jaarontheffing gewicht bijzonder",
            "Jaarontheffing hele zone voor bijzondere voertuigen met gewichtsverklaring",
        ],
        [
            "Jaarontheffing gewicht en ondeelbaar",
            "Jaarontheffing hele zone met gewichtsverklaring en verklaring ondeelbare lading",
        ],
        [
            "Jaarontheffing ondeelbaar",
            "Jaarontheffing hele zone met verklaring ondeelbare lading",
        ],
        [
            "Routeontheffing bijzonder boven 30 ton",
            "Routeontheffing bijzondere voertuig boven 30 ton",
        ],
        [
            "Routeontheffing brede wegen boven 30 ton",
            "Routeontheffing breed opgezette wegen boven 30 ton",
        ],
        [
            "Routeontheffing brede wegen tm 30 ton",
            "Routeontheffing breed opgezette wegen tot en met 30 ton",
        ],
        [
            "Routeontheffing culturele instelling",
            "Routeontheffing pilot culturele instelling",
        ],
        [
            "Routeontheffing ondeelbaar boven 30 ton",
            "Routeontheffing boven 30 ton met verklaring ondeelbare lading",
        ],
        ["Zwaar verkeer", "Ontheffing zwaar verkeer"],
        ["Dagontheffing", "Dagontheffing hele zone"],
        ["Jaarontheffing", "Jaarontheffing hele zone"],
    ]

    decision_translations = [
        ["Ingetrokken", "Ingetrokken"],
        ["Niet verleend", "Afgewezen"],
        ["Verleend", "Toegekend"],
    ]

    def has_valid_source_data(self):
        return super().has_valid_payment_status()


class Samenvoegingsvergunning(Zaak):
    # !!!!!!!!!!!!!
    enabled = True
    # !!!!!!!!!!!!!

    zaak_type = "Samenvoegingsvergunning"
    title = "Vergunning voor samenvoegen van woonruimten"
    date_workflow_active_step_title = (
        "Samenvoegingsvergunning - Beoordelen en besluiten"
    )

    @staticmethod
    def defer_transform(zaak_deferred, decosjoin_service):
        date_workflow_active = decosjoin_service.get_workflow(
            zaak_deferred["id"], Samenvoegingsvergunning.date_workflow_active_step_title
        )
        zaak_deferred["dateWorkflowActive"] = date_workflow_active
        return zaak_deferred

    parse_fields = [
        {"name": "location", "from": "text6", "parser": to_string},  # Locatie
    ]


class Onttrekkingsvergunning(Zaak):
    # !!!!!!!!!!!!!
    enabled = True
    # !!!!!!!!!!!!!

    zaak_type = "Onttrekkingsvergunning voor ander gebruik"
    title = "Onttrekkingsvergunning voor ander gebruik"
    date_workflow_active_step_title = (
        "Onttrekkingsvergunning voor ander gebruik - Beoordelen en besluiten"
    )

    @staticmethod
    def defer_transform(zaak_deferred, decosjoin_service):
        date_workflow_active = decosjoin_service.get_workflow(
            zaak_deferred["id"], Onttrekkingsvergunning.date_workflow_active_step_title
        )
        zaak_deferred["dateWorkflowActive"] = date_workflow_active
        return zaak_deferred

    parse_fields = [
        {"name": "location", "from": "text6", "parser": to_string},  # Locatie
    ]


class OnttrekkingsvergunningSloop(Zaak):
    # !!!!!!!!!!!!!
    enabled = True
    # !!!!!!!!!!!!!

    zaak_type = "Onttrekkingsvergunning voor sloop"
    title = "Onttrekkingsvergunning voor sloop"
    date_workflow_active_step_title = (
        "Onttrekkingsvergunning voor sloop - Beoordelen en besluiten"
    )

    @staticmethod
    def defer_transform(zaak_deferred, decosjoin_service):
        date_workflow_active = decosjoin_service.get_workflow(
            zaak_deferred["id"],
            OnttrekkingsvergunningSloop.date_workflow_active_step_title,
        )
        zaak_deferred["dateWorkflowActive"] = date_workflow_active
        return zaak_deferred

    parse_fields = [
        {"name": "location", "from": "text6", "parser": to_string},  # Locatie
    ]


class VormenVanWoonruimte(Zaak):
    # !!!!!!!!!!!!!
    enabled = True
    # !!!!!!!!!!!!!

    zaak_type = "Woningvormingsvergunning"
    title = "Vergunning voor woningvorming"
    date_workflow_active_step_title = (
        "Woningvormingsvergunning - Beoordelen en besluiten"
    )

    @staticmethod
    def defer_transform(zaak_deferred, decosjoin_service):
        date_workflow_active = decosjoin_service.get_workflow(
            zaak_deferred["id"], VormenVanWoonruimte.date_workflow_active_step_title
        )
        zaak_deferred["dateWorkflowActive"] = date_workflow_active
        return zaak_deferred

    parse_fields = [
        {"name": "location", "from": "text6", "parser": to_string},  # Locatie
    ]


class Splitsingsvergunning(Zaak):
    # !!!!!!!!!!!!!
    enabled = True
    # !!!!!!!!!!!!!

    zaak_type = "Splitsingsvergunning"
    title = "Splitsingsvergunning"
    date_workflow_active_step_title = "Splitsingsvergunning - Behandelen"

    @staticmethod
    def defer_transform(zaak_deferred, decosjoin_service):
        date_workflow_active = decosjoin_service.get_workflow(
            zaak_deferred["id"], Splitsingsvergunning.date_workflow_active_step_title
        )
        zaak_deferred["dateWorkflowActive"] = date_workflow_active
        return zaak_deferred

    parse_fields = [
        {"name": "location", "from": "text6", "parser": to_string},  # Locatie
    ]


class VOBvergunning(Zaak):
    # !!!!!!!!!!!!!
    enabled = True
    # !!!!!!!!!!!!!

    zaak_type = "VOB"
    title = "Ligplaatsvergunning"
    date_workflow_active_step_title = "VOB - Beoordelen en besluiten"

    @staticmethod
    def defer_transform(zaak_deferred, decosjoin_service):
        date_workflow_active = decosjoin_service.get_workflow(
            zaak_deferred["id"], VOBvergunning.date_workflow_active_step_title
        )
        zaak_deferred["dateWorkflowActive"] = date_workflow_active
        return zaak_deferred

    parse_fields = [
        {"name": "requestKind", "from": "text9", "parser": to_string},  # Soort aanvraag
        {"name": "reason", "from": "text18", "parser": to_string},  # Reden
        {"name": "location", "from": "text6", "parser": to_string},  # Locatie
        {"name": "vesselKind", "from": "text10", "parser": to_string},  # Soort vaartuig
        {"name": "vesselName", "from": "text14", "parser": to_string},  # Naam vaartuig
    ]


class ExploitatieHorecabedrijf(Zaak):
    # !!!!!!!!!!!!!
    enabled = True
    # !!!!!!!!!!!!!

    zaak_type = "Horeca vergunning exploitatie Horecabedrijf"
    title = "Horeca vergunning exploitatie Horecabedrijf"

    date_workflow_active_step_title = (
        "Horeca vergunning exploitatie Horecabedrijf - In behandeling nemen"
    )

    @staticmethod
    def defer_transform(zaak_deferred, decosjoin_service):
        date_workflow_active = decosjoin_service.get_workflow(
            zaak_deferred["id"],
            ExploitatieHorecabedrijf.date_workflow_active_step_title,
        )
        zaak_deferred["dateWorkflowActive"] = date_workflow_active
        return zaak_deferred

    parse_fields = [
        {"name": "dateEnd", "from": "date2", "parser": to_date},  # Eind datum
        {
            "name": "dateStart",
            "from": "date6",
            "parser": to_date,
        },  # Begindatum vergunning
        {"name": "location", "from": "text6", "parser": to_string},  # Locatie
    ]


class RVVHeleStad(Zaak):
    # !!!!!!!!!!!!!
    enabled = not IS_PRODUCTION
    # !!!!!!!!!!!!!

    zaak_type = "RVV - Hele stad"
    title = "RVV-verkeersontheffing"

    date_workflow_active_step_title = (
        "Status bijwerken en notificatie verzenden - In behandeling"
    )

    @staticmethod
    def defer_transform(zaak_deferred, decosjoin_service):
        date_workflow_active = decosjoin_service.get_workflow(
            zaak_deferred["id"], RVVHeleStad.date_workflow_active_step_title
        )
        zaak_deferred["dateWorkflowActive"] = date_workflow_active
        return zaak_deferred

    parse_fields = [
        {
            "name": "dateStart",
            "from": "date6",
            "parser": to_date,
        },  # Begindatum vergunning
        {"name": "dateEnd", "from": "date7", "parser": to_date},  # Einddatum vergunning
        {
            "name": "licensePlates",
            "from": "text49",
            "parser": BZP.to_kenteken,
        },  # Kentekens
    ]

    def has_valid_source_data(self):
        return super().has_valid_payment_status()


class RVVSloterweg(Zaak):
    # !!!!!!!!!!!!!
    enabled = not IS_PRODUCTION
    # !!!!!!!!!!!!!

    zaak_type = "RVV Sloterweg"
    title = "RVV ontheffing Sloterweg"

    date_workflow_active_step_title = "Behandelen"
    date_workflow_verleend_step_title = "Status naar actief"

    # status_translations = []

    decision_translations = [
        ["Verleend", "Verleend"],
        ["Ingetrokken door gemeente", "Ingetrokken"],
        ["Verlopen", "Verlopen"],
    ]

    @staticmethod
    def defer_transform(zaak_deferred, decosjoin_service):
        date_workflow_active = decosjoin_service.get_workflow(
            zaak_deferred["id"], RVVSloterweg.date_workflow_active_step_title
        )
        zaak_deferred["dateWorkflowActive"] = date_workflow_active

        date_workflow_verleend = decosjoin_service.get_workflow(
            zaak_deferred["id"], RVVSloterweg.date_workflow_verleend_step_title
        )
        zaak_deferred["dateWorkflowVerleend"] = date_workflow_verleend

        if date_workflow_verleend is not None:
            zaak_deferred['processed'] = True
            # if the workflow verleend has run but there is no decision then its actually Verleend.
            # this decision (verleend) is not set by decos eventhough the actual permit is granted
            if zaak_deferred['decision'] is None: 
                zaak_deferred['decision'] = 'Verleend'

        zaak_deferred['title'] = f"RVV ontheffing Sloterweg ({zaak_deferred['licensePlates']})"

        return zaak_deferred

    parse_fields = [
        {
            "name": "requestType",
            "from": "text8",
            "parser": to_string,
        },  # Gebied
        {
            "name": "area",
            "from": "text7",
            "parser": to_string,
        },  # Gebied
        {
            "name": "dateStart",
            "from": "date6",
            "parser": to_date,
        },  # Begindatum vergunning
        {"name": "dateEnd", "from": "date7", "parser": to_date},  # Einddatum vergunning
        {
            "name": "licensePlates",
            "from": "text10",
            "parser": BZP.to_kenteken,
        },  # Kentekens
        {
            "name": "previousLicensePlates",
            "from": "text15",
            "parser": BZP.to_kenteken,
        },  # Vorige Kentekens
    ]


class Eigenparkeerplaats(Zaak):
    # !!!!!!!!!!!!!
    enabled = not IS_PRODUCTION
    # !!!!!!!!!!!!!

    zaak_type = "Eigen parkeerplaats"
    title = "Eigen parkeerplaats"

    date_workflow_active_step_title = "Status bijwerken en notificatie verzenden - In behandeling"

    @staticmethod
    def defer_transform(zaak_deferred, decosjoin_service):
        date_workflow_active = decosjoin_service.get_workflow(
            zaak_deferred["id"], Eigenparkeerplaats.date_workflow_active_step_title
        )
        zaak_deferred["dateWorkflowActive"] = date_workflow_active

        return zaak_deferred

    def to_requesttype(self):
        type_map = {
            "isNewRequest": "Nieuwe aanvraag",
            "isCarsharingpermit": "Autodeelbedrijf",
            "isLicensePlateChange": "Kentekenwijziging",
            "isRelocation": "Verhuizing",
            "isExtension": "Verlenging",
        }

        for key in type_map.keys():
            if self.zaak[key] is not None:
                return type_map[key]

        return None

    def after_transform(self):
        locations = []
        if self.zaak["streetLocation1"] is not None:
            locations.append({
                "type": self.zaak["locationkindLocation1"],
                "street": self.zaak["streetLocation1"],
                "houseNumber": self.zaak["housenumberLocation1"],
                "fiscalNumber": self.zaak["fiscalnumberLocation1"],
                "url": self.zaak["urlLocation1"]
            })

        if self.zaak["streetLocation2"] is not None:
            locations.append({
                "type": self.zaak["locationkindLocation2"],
                "street": self.zaak["streetLocation2"],
                "houseNumber": self.zaak["housenumberLocation2"],
                "fiscalNumber": self.zaak["fiscalnumberLocation2"],
                "url": self.zaak["urlLocation2"]
            })

        self.zaak["locations"] = locations
        self.zaak["requestType"] = self.to_requesttype()

        # removed duplicate keys
        for key in ["locationkindLocation1", "streetLocation1", "housenumberLocation1", "fiscalnumberLocation1", "locationkindLocation2", "streetLocation2", "housenumberLocation2", "fiscalnumberLocation2", "urlLocation1", "urlLocation2"]:
            self.zaak.pop(key, None)

    parse_fields = [
        {
            "name": "isNewRequest",
            "from": "bol9",
            "parser": to_bool,
        },
        {
            "name": "isExtension",
            "from": "bol7",
            "parser": to_bool,
        },
        {
            "name": "isLicensePlateChange",
            "from": "bol10",
            "parser": to_bool,
        },
        {
            "name": "isRelocation",
            "from": "bol11",
            "parser": to_bool,
        },
        {
            "name": "isCarsharingpermit",
            "from": "bol8",
            "parser": to_bool,
        },
        {
            "name": "streetLocation1",
            "from": "text25",
            "parser": to_string,
        },
        {
            "name": "housenumberLocation1",
            "from": "num14",
            "parser": to_int,
        },
        {
            "name": "locationkindLocation1",
            "from": "text17",
            "parser": to_string,
        },
        {
            "name": "fiscalnumberLocation1",
            "from": "text18",
            "parser": to_string,
        },
        {
            "name": "urlLocation1",
            "from": "text19",
            "parser": to_string,
        },
        {
            "name": "streetLocation2",
            "from": "text15",
            "parser": to_string,
        },
        {
            "name": "housenumberLocation2",
            "from": "num15",
            "parser": to_int,
        },
        {
            "name": "locationkindLocation2",
            "from": "text20",
            "parser": to_string,
        },
        {
            "name": "fiscalnumberLocation2",
            "from": "text21",
            "parser": to_string,
        },
        {
            "name": "urlLocation2",
            "from": "text22",
            "parser": to_string,
        },
        {
            "name": "licensePlates",
            "from": "text13",
            "parser": BZP.to_kenteken,
        },
        {
            "name": "previousLicensePlates",
            "from": "text14",
            "parser": BZP.to_kenteken,
        },
        {
            "name": "dateStart",
            "from": "date6",
            "parser": to_date,
        },
        {
            "name": "dateEnd",
            "from": "date8",
            "parser": to_date,
        },
    ]

    def has_valid_source_data(self):
        not_before = to_date("2023-08-08")
        creation_date = to_date(self.zaak_source["document_date"])

        return creation_date >= not_before and super().has_valid_payment_status()


class EigenparkeerplaatsOpheffen(Zaak):
    # !!!!!!!!!!!!!
    enabled = not IS_PRODUCTION
    # !!!!!!!!!!!!!

    zaak_type = "Eigen parkeerplaats opheffen"
    title = "Eigen parkeerplaats opheffen"

    date_workflow_active_step_title = "Status bijwerken en notificatie verzenden - In behandeling"

    @staticmethod
    def defer_transform(zaak_deferred, decosjoin_service):
        date_workflow_active = decosjoin_service.get_workflow(
            zaak_deferred["id"], EigenparkeerplaatsOpheffen.date_workflow_active_step_title
        )
        zaak_deferred["dateWorkflowActive"] = date_workflow_active
        return zaak_deferred

    def after_transform(self):
        location = {
            "type": self.zaak["locationType"],
            "street": self.zaak["street"],
            "houseNumber": self.zaak["houseNumber"],
            "fiscalNumber": self.zaak["fiscalNumber"],
            "url": self.zaak["locationUrl"]
        }

        self.zaak["location"] = location

        # removed duplicate keys
        for key in ["locationType", "street", "houseNumber", "fiscalNumber", "locationUrl"]:
            self.zaak.pop(key, None)

    parse_fields = [
        {
            "name": "isCarsharingpermit",
            "from": "bol8",
            "parser": to_bool,
        },
        {
            "name": "street",
            "from": "text25",
            "parser": to_string,
        },
        {
            "name": "houseNumber",
            "from": "num14",
            "parser": to_int,
        },
        {
            "name": "locationType",
            "from": "text17",
            "parser": to_string,
        },
        {
            "name": "fiscalNumber",
            "from": "text18",
            "parser": to_string,
        },
        {
            "name": "locationUrl",
            "from": "text19",
            "parser": to_string,
        },
        {
            "name": "dateEnd",
            "from": "date8",
            "parser": to_date,
        },
    ]

    def has_valid_source_data(self):
        not_before = to_date("2023-08-08")
        creation_date = to_date(self.zaak_source["document_date"])

        return creation_date >= not_before and super().has_valid_payment_status()


# A dict with all enabled Zaken
zaken_index = {
    getattr(cls, "zaak_type"): cls for cls in Zaak.__subclasses__() if cls.enabled
}
