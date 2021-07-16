import logging
import math
import re
from datetime import datetime, date, time
from typing import Union

import requests
from dateutil import parser
from requests import PreparedRequest
from requests.auth import HTTPBasicAuth

from decosjoin.api.decosjoin.Exception import DecosJoinConnectionError, ParseError
from decosjoin.crypto import encrypt

log_raw = False
page_size = 30

ALLOWED_ZAAKTYPES = [
    'tvm - rvv - object',
    'vakantieverhuur',
    'vakantieverhuur vergunningsaanvraag',
    'b&b - vergunning',
    'gpp',
    'gpk',
    'omzettingsvergunning',
    'e-rvv - tvm',
    # 'evenement melding',
    # 'evenement vergunning',
]


SELECT_FIELDS = ','.join([
    'title',
    'mark',
    'text45',
    'subject1',
    'bol10',
    'company',
    'date5',
    'date6',
    'date7',
    'dfunction',
    'document_date',
    'text6',
    'text7',
    'text8',
    'text9',
    'text10',
    'text11',
    'text12',
    'text13',
    'text20',
    'text25',
])


class DecosJoinConnection:
    def __init__(self, username, password, api_host, adres_boeken):
        self.username = username
        self.password = password
        self.adres_boeken = adres_boeken
        self.api_host = api_host
        self.api_location = "/decosweb/aspx/api/v1/"
        self.api_url = f"{self.api_host}{self.api_location}"

    def get_response(self, *args, **kwargs):
        """ Easy to mock intermediate function. """
        return requests.get(*args, **kwargs)

    def post_response(self, *args, **kwargs):
        """ Easy to mock intermediate function. """
        return requests.post(*args, **kwargs)

    def request(self, url, method='get', json=None):
        """ Makes a request to the decos join api with HTTP basic auth credentials added. """
        if method == 'get':
            response = self.get_response(url,
                                         auth=HTTPBasicAuth(self.username, self.password),
                                         headers={"Accept": "application/itemdata"},
                                         timeout=9)
        elif method == 'post':
            response = self.post_response(url,
                                          auth=HTTPBasicAuth(self.username, self.password),
                                          headers={"Accept": "application/itemdata"},
                                          json=json,
                                          timeout=9)
        else:
            raise RuntimeError("Method needs to be GET or POST")

        if log_raw:
            print("\nstatus", response.status_code, url)
            print("\npost", json)
            print(">>", response.content)

        if response.status_code == 200:
            json = response.json()
            # print("response\n", json)
            return json
        else:
            raise DecosJoinConnectionError(response.status_code)

    def search_query(self, bsn: str, book_key: str):
        return {
            "bookKey": book_key,
            "orderBy": "sequence",
            "skip": 0,
            "take": 50,
            "searchInHierarchyPath": False,
            "searchInPendingItemContainerKeys": False,
            "filterFields": {
                "num1": [
                    {
                        "FilterOperation": 1,
                        "FilterValue": bsn,
                        "FilterOperator": "="
                    }
                ]
            }
        }

    def get_user_keys(self, kind, identifier):
        """ Retrieve the internal ids used for a user. """
        keys = []

        adres_boeken = self.adres_boeken[kind]

        for boek in adres_boeken:
            url = f"{self.api_url}search/books?properties=false"
            res_json = self.request(url, json=self.search_query(identifier, boek), method='post')
            if res_json['itemDataResultSet']['count'] > 0:
                for item in res_json['itemDataResultSet']['content']:
                    user_key = item['key']
                    keys.append(user_key)

        return keys

    def transform(self, zaken, user_identifier):  # noqa: C901
        new_zaken = []
        deferred_zaken = []

        for zaak in zaken:
            f = zaak['fields']

            # Cannot reliably determine the zaaktype of this zaak
            if 'text45' not in f:
                continue

            zaak_type = f['text45']

            if zaak_type == "TVM - RVV - Object":
                fields = [
                    {"name": "status", "from": "title", "parser": to_string},
                    {"name": "title", "from": "text45", "parser": to_title},
                    {"name": "description", "from": "subject1", "parser": to_string},
                    {"name": "identifier", "from": "mark", "parser": to_string},
                    {"name": "caseType", "from": "text45", "parser": to_string},
                    {"name": "dateStart", "from": "date6", "parser": to_date},
                    {"name": "dateEnd", "from": "date7", "parser": to_date},
                    {"name": "timeStart", "from": "text10", "parser": to_time},
                    {"name": "timeEnd", "from": "text13", "parser": to_time},
                    {"name": "kenteken", "from": "text9", "parser": to_string},
                    {"name": "location", "from": "text6", "parser": to_string},
                    {"name": "dateRequest", "from": "document_date", "parser": to_date},
                    {"name": "decision", "from": "dfunction", "parser": to_decision},
                    {"name": "dateDecision", "from": "date5", "parser": to_date},  # datum afhandeling?
                ]

                new_zaak = get_fields(fields, zaak)

                # if end date is not defined, its the same as date start
                if not new_zaak['dateEnd']:
                    new_zaak['dateEnd'] = new_zaak['dateStart']

            elif zaak_type == 'Vakantieverhuur vergunningsaanvraag':
                fields = [
                    {"name": "caseType", "from": "text45", "parser": to_string},
                    {"name": "title", "from": "text45", "parser": to_title},
                    {"name": "identifier", "from": 'mark', "parser": to_string},
                    {"name": "dateRequest", "from": "document_date", "parser": to_date},
                    {"name": "dateDecision", "from": "date5", "parser": to_datetime},  # Datum afhandeling
                    {"name": "location", "from": "text6", "parser": to_string},
                    {"name": "status", "from": "title", "parser": to_vakantie_verhuur_vergunning_status},
                    {"name": "decision", "from": "dfunction", "parser": to_vakantie_verhuur_vergunning_decision},
                    {"name": "dateStart", "from": "document_date", "parser": to_date},  # same as dateRequest
                    # dateEnd is set programmatically  Datum tot
                ]
                new_zaak = get_fields(fields, zaak)

                # The validity of this case runs from april 1st until the next. set the end date to the next april the 1st
                new_zaak['dateEnd'] = self.next_april_first(new_zaak['dateRequest'])

            elif zaak_type == 'Vakantieverhuur':
                fields = [
                    {"name": "caseType", "from": "text45", "parser": to_string},
                    {"name": "title", "from": "text45", "parser": to_title},
                    {"name": "identifier", "from": 'mark', "parser": to_string},
                    {"name": "dateRequest", "from": "document_date", "parser": to_date},
                    {"name": "dateDecision", "from": "date5", "parser": to_datetime},  # Datum afhandeling
                    {"name": "dateStart", "from": 'date6', "parser": to_date},  # Start verhuur
                    {"name": "dateEnd", "from": 'date7', "parser": to_date},  # Einde verhuur
                    {"name": "location", "from": "text6", "parser": to_string},
                ]
                new_zaak = get_fields(fields, zaak)

                if new_zaak['dateEnd'] and new_zaak['dateEnd'] <= date.today():
                    new_zaak['title'] = 'Afgelopen verhuur'

            elif zaak_type == 'Vakantieverhuur afmelding':
                fields = [
                    {"name": "caseType", "from": "text45", "parser": to_string},
                    {"name": "title", "from": "text45", "parser": to_title},
                    {"name": "identifier", "from": 'mark', "parser": to_string},
                    {"name": "dateRequest", "from": "document_date", "parser": to_date},
                    {"name": "dateStart", "from": 'date6', "parser": to_date},  # Start verhuur
                    {"name": "dateEnd", "from": 'date7', "parser": to_date},  # Einde verhuur
                ]

                new_zaak = get_fields(fields, zaak)
                deferred_zaken.append(new_zaak)
                continue  # do not follow normal new_zaak procedure

            elif zaak_type == 'B&B - vergunning':
                fields = [
                    {"name": "caseType", "from": "text45", "parser": to_string},
                    {"name": "dateRequest", "from": "document_date", "parser": to_date},  # Startdatum zaak
                    {"name": "decision", "from": "dfunction", "parser": to_string},
                    {"name": "location", "from": "text6", "parser": to_string},
                    {"name": "title", "from": "text45", "parser": to_title},
                    {"name": "description", "from": "subject1", "parser": to_string},
                    {"name": "identifier", "from": "mark", "parser": to_string},
                    {"name": "dateDecision", "from": "date5", "parser": to_datetime},  # Datum afhandeling
                    {"name": "dateStart", "from": 'date6', "parser": to_date},  # Datum van
                    {"name": "dateEnd", "from": 'date7', "parser": to_date},  # Datum tot en met
                    {"name": "status", "from": "title", "parser": to_string},
                    {"name": "requester", "from": "company", "parser": to_string},
                    {"name": "owner", "from": "text25", "parser": to_string},
                    {"name": "hasTransitionAgreement", "from": "dfunction", "parser": to_transition_agreement}  # need this for tip mijn-33
                ]
                new_zaak = get_fields(fields, zaak)
                decision_translations = [
                    ["Verleend met overgangsrecht", "Verleend"],
                    ["Verleend zonder overgangsrecht", "Verleend"],
                    ["Geweigerd", "Geweigerd"],
                    ["Geweigerd met overgangsrecht", "Geweigerd"],
                    ["Geweigerd op basis van Quotum", "Geweigerd"],
                    ["Ingetrokken", "Ingetrokken"],
                ]

                status_translations = [
                    ["Publicatie aanvraag", "Ontvangen"],
                    ["Ontvangen", "Ontvangen"],
                    ["Volledigheidstoets uitvoeren", "Ontvangen"],
                    ["Behandelen aanvraag", "In behandeling"],
                    ["Huisbezoek", "In behandeling"],
                    ["Beoordelen en besluiten", "In behandeling"],
                    ["Afgehandeld", "Afgehandeld"],
                ]
                new_zaak['decision'] = get_translation(new_zaak['decision'], decision_translations)
                new_zaak['status'] = get_translation(new_zaak['status'], status_translations)

            elif zaak_type == 'GPP':
                fields = [
                    {"name": "caseType", "from": "text45", "parser": to_string},
                    {"name": "title", "from": "text45", "parser": to_title},
                    {"name": "identifier", "from": "mark", "parser": to_string},
                    {"name": "dateDecision", "from": "date5", "parser": to_datetime},  # Datum afhandeling
                    {"name": "dateRequest", "from": "document_date", "parser": to_string},
                    {"name": "decision", "from": "dfunction", "parser": to_string},
                    {"name": "kenteken", "from": "text7", "parser": to_string},
                    {"name": "location", "from": "text8", "parser": to_string},
                    {"name": "status", "from": "title", "parser": to_string},
                ]
                new_zaak = get_fields(fields, zaak)
                translations = [
                    ["Buiten behandeling", "Buiten behandeling", False],
                    ["Ingetrokken", "Ingetrokken"],
                    ["Ingetrokken i.v.m. overlijden of verhuizing", "Ingetrokken"],
                    ["Niet verleend", "Niet verleend"],
                    ["Nog niet bekend", "", False],
                    ["Verleend", "Verleend"],
                ]
                new_zaak['decision'] = get_translation(new_zaak['decision'], translations)

            elif zaak_type == 'GPK':
                fields = [
                    {"name": "caseType", "from": "text45", "parser": to_string},
                    {"name": "title", "from": "text45", "parser": to_title},
                    {"name": "identifier", "from": "mark", "parser": to_string},
                    {"name": "decision", "from": "dfunction", "parser": to_string},
                    {"name": "dateDecision", "from": "date5", "parser": to_datetime},  # Datum afhandeling
                    {"name": "cardNumber", "from": "num3", "parser": to_string},  # kaartnummer
                    {"name": "dateRequest", "from": "document_date", "parser": to_date},
                    {"name": "cardtype", "from": "text7", "parser": to_string},
                    {"name": "dateEnd", "from": "date7", "parser": to_date},  # vervaldatum
                ]
                new_zaak = get_fields(fields, zaak)

                # Copied from RD
                translations = [
                    ["Buiten behandeling", "Buiten behandeling", False],
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
                new_zaak['decision'] = get_translation(new_zaak['decision'], translations)

            # elif zaak_type == 'Evenement melding':
            #     fields = [
            #         {"name": "caseType", "from": "text45", "parser": to_string},
            #         {"name": "identifier", "from": "mark", "parser": to_string},
            #         {"name": "dateDecision", "from": "date5", "parser": to_datetime},  # Datum afhandeling
            #         {"name": "dateRequest", "from": "document_date", "parser": to_string},
            #         {"name": "dateStart", "from": "date6", "parser": to_date},  # Op   <datum> ?
            #         {"name": "location", "from": "text8", "parser": to_string},
            #         {"name": "timeStart", "from": "text7", "parser": to_time},  # Van   <tijd>
            #         {"name": "timeEnd", "from": "text8", "parser": to_time},  # Tot    <tijd>
            #         {"name": "decision", "from": "dfunction", "parser": to_string},
            #     ]
            #     new_zaak = get_fields(fields, zaak)
            #     translations = [
            #         ["Ingetrokken", "Ingetrokken"],
            #         ["Buiten behandeling", "Buiten behandeling", False],
            #         ["Niet verleend", "Geweigerd"],
            #         ["Verleend", "Gemeld"],
            #         ["Nog niet  bekend", "", False],
            #         ["Nog niet bekend", "", False],
            #         ["Verleend", "Verleend"],
            #         ["Verleend (Bijzonder/Bewaren)", "Verleend"],
            #         ["Verleend zonder borden", "Verleend"],
            #     ]
            #     new_zaak['decision'] = get_translation(new_zaak['decision'], translations)
            #
            # elif zaak_type == 'Evenement vergunning':
            #     fields = [
            #         {"name": "caseType", "from": "text45", "parser": to_string},
            #         {"name": "identifier", "from": "mark", "parser": to_string},
            #         {"name": "dateDecision", "from": "date5", "parser": to_datetime},  # Datum afhandeling
            #         {"name": "dateRequest", "from": "document_date", "parser": to_datetime},
            #         {"name": "title", "from": "text45", "parser": to_title},
            #         {"name": "dateStart", "from": "date6", "parser": to_date},  # Datum van
            #         {"name": "dateEnd", "from": "date7", "parser": to_date},  # Datum tot en met
            #         {"name": "location", "from": "text8", "parser": to_string},
            #         {"name": "timeStart", "from": "text7", "parser": to_time},
            #         {"name": "timeEnd", "from": "text8", "parser": to_time},  # tijd tot
            #     ]
            #     new_zaak = get_fields(fields, zaak)
            #
            #     translations = [
            #         ["Afgebroken (Ingetrokken)", "Afgebroken (Ingetrokken)"],
            #         ["Buiten behandeling", "Buiten behandeling", False],
            #         ["Geweigerd", "Geweigerd"],
            #         ["Nog niet  bekend", "", False],
            #         ["Nog niet  bekend", "", False],
            #         ["Nog niet bekend", "", False],
            #         ["Verleend", "Verleend"],
            #         ["Verleend (Bijzonder/Bewaren)", "Verleend"],
            #         ["Verleend zonder borden", "Verleend"],
            #     ]
            #     new_zaak['decision'] = get_translation(new_zaak['decision'], translations)

            elif zaak_type == 'Omzettingsvergunning':
                fields = [
                    {"name": "caseType", "from": "text45", "parser": to_string},
                    {"name": "title", "from": "text45", "parser": to_title},
                    {"name": "identifier", "from": "mark", "parser": to_string},
                    {"name": "dateRequest", "from": "document_date", "parser": to_datetime},
                    {"name": "dateDecision", "from": "date5", "parser": to_datetime},  # Datum afhandeling
                    {"name": "location", "from": "text8", "parser": to_string},
                    {"name": "description", "from": "subject1", "parser": to_string},
                    {"name": "decision", "from": "dfunction", "parser": to_string},
                ]
                new_zaak = get_fields(fields, zaak)
                translations = [
                    ["Buiten behandeling", "Buiten behandeling", False],
                    ["Geweigerd", "Geweigerd"],
                    ["Ingetrokken door gemeente", "Ingetrokken door gemeente"],
                    ["Ingetrokken op eigen verzoek", "Ingetrokken op eigen verzoek"],
                    ["Nog niet bekend", "", False],
                    ["Van rechtswege verleend", "Verleend"],
                    ["Vergunningvrij", "Vergunningvrij"],
                    ["Verleend", "Verleend"],
                    ["Verleend zonder borden", "Verleend"],
                ]
                new_zaak['decision'] = get_translation(new_zaak['decision'], translations)

            elif zaak_type == 'E-RVV - TVM':
                fields = [
                    {"name": "caseType", "from": "text45", "parser": to_string},
                    {"name": "identifier", "from": "mark", "parser": to_string},
                    {"name": "dateRequest", "from": "document_date", "parser": to_string},
                    {"name": "dateDecision", "from": "date5", "parser": to_datetime},  # Datum afhandeling
                    {"name": "title", "from": "text45", "parser": to_title},
                    {"name": "description", "from": "subject1", "parser": to_string},
                    {"name": "location", "from": "text8", "parser": to_string},
                    {"name": "status", "from": "title", "parser": to_string},
                    {"name": "dateStart", "from": "date6", "parser": to_date},  # Datum van
                    {"name": "dateEnd", "from": "date7", "parser": to_date},  # Datum tot en met
                    {"name": "timeStart", "from": "text10", "parser": to_time},
                    {"name": "timeEnd", "from": "text13", "parser": to_time},  # tijd tot
                    {"name": "decision", "from": "dfunction", "parser": to_string},
                ]
                new_zaak = get_fields(fields, zaak)
                translations = [
                    ["Buiten behandeling", "Buiten behandeling", False],
                    ["Ingetrokken", "Ingetrokken"],
                    ["Niet verleend", "Niet verleend"],
                    ["Nog niet bekend", "", False],
                    ["Verleend met borden", "Verleend"],
                    ["Verleend met borden en Fietsenrekken verwijderen", "Verleend"],
                    ["Verleend met Fietsenrekken verwijderen", "Verleend"],
                    ["Verleend zonder bebording", "Verleend"],
                    ["Verleend zonder borden", "Verleend"],
                ]
                new_zaak['decision'] = get_translation(new_zaak['decision'], translations)

            else:
                # zaak does not match one of the known ones
                continue

            # These matching conditions are used to prevent these items from being included in the returned list of zaken
            if self.is_list_match(new_zaak, 'description', ['wacht op online betaling', 'wacht op ideal betaling']):
                continue
            if self.is_list_match(new_zaak, 'decision', ['buiten behandeling']):
                continue
            if 'description' in new_zaak and new_zaak['description'] and new_zaak['description'].lower().startswith("*verwijder"):
                continue

            # This url can be used to retrieve matching document attachments for this particular zaak
            new_zaak['documentsUrl'] = f"/api/decosjoin/listdocuments/{encrypt(zaak['key'], user_identifier)}"

            new_zaken.append(new_zaak)

        # Matching start/end dates for Vakantieverhuur afmelding and transforming the geplande verhuur to afgemelde verhuur
        for defferred_zaak in deferred_zaken:
            if defferred_zaak['caseType'] == 'Vakantieverhuur afmelding':
                # update the existing registration
                for new_zaak in new_zaken:
                    if new_zaak['caseType'] == 'Vakantieverhuur' and new_zaak['dateStart'] == defferred_zaak['dateStart'] and new_zaak['dateEnd'] == defferred_zaak['dateEnd']:
                        new_zaak['dateDescision'] = defferred_zaak['dateRequest']
                        new_zaak['title'] = defferred_zaak['title']
                        new_zaak['identifier'] = defferred_zaak['identifier']

        return new_zaken

    def next_april_first(self, case_date: date):
        if case_date < date(case_date.year, 4, 1):
            return date(case_date.year, 4, 1)
        else:
            return date(case_date.year + 1, 4, 1)

    def is_list_match(self, zaak, key, test_list):
        value = zaak[key] if key in zaak else None
        if value is None:
            return False
        value = value.lower()
        return value in test_list

    def filter_zaken(self, zaken):
        """ Filter un-parsed cases. """
        zaken = [zaak for zaak in zaken if zaak['caseType'].lower() in ALLOWED_ZAAKTYPES]

        return zaken

    def get_page(self, url, offset=None):
        """ Get a single page for url. When offset is provided add that to the url. """
        if offset:
            url += f'&skip={offset}'
        res_json = self.request(url)
        if log_raw:
            from pprint import pprint
            print("request:", url)
            pprint(res_json)
        return res_json

    def get_all_pages(self, url):
        """ Get 'content' from all pages for the provided url """

        req = PreparedRequest()
        req.prepare_url(url, {"top": page_size})  # append top get param
        url = req.url

        items = []
        # fetch one page to get the first part of the data and item count
        res = self.get_page(url)

        end = math.ceil(res['count'] / page_size) * page_size
        items.extend(res['content'])

        for offset in range(page_size, end, page_size):
            res = self.get_page(url, offset)
            items.extend(res['content'])

        return items

    def get_zaken(self, kind, identifier):
        """ Get all zaken for a kind ['bsn' or 'kvk']. """
        zaken = []
        user_keys = self.get_user_keys(kind, identifier)

        for key in user_keys:
            url = f"{self.api_url}items/{key}/folders?select={SELECT_FIELDS}"
            zaken.extend(self.get_all_pages(url))

        zaken = self.transform(zaken, identifier)
        return sorted(self.filter_zaken(zaken), key=lambda x: x['identifier'], reverse=True)

    def get_document_data(self, doc_id: str):
        res_json = self.request(f"{self.api_url}items/{doc_id}/blob?select=bol10")

        content = res_json['content']
        if content:
            for i in content[::-1]:
                is_pdf = i['fields'].get('bol10', False)
                if is_pdf:
                    return {
                        'is_pdf': is_pdf,
                        'doc_key': i['key']
                    }
        return {
            'is_pdf': False,
        }

    def list_documents(self, zaak_id, identifier):
        url = f"{self.api_url}items/{zaak_id}/documents?select=subject1,sequence,mark,text39,text40,text41,itemtype_key"

        res = self.get_all_pages(url)

        if log_raw:
            from pprint import pprint
            print("Documents list")
            pprint(res)

        fields = [
            {"name": 'title', "from": 'text41', "parser": to_string},
            {"name": 'sequence', "from": 'sequence', "parser": to_int},
            {"name": 'id', "from": 'mark', "parser": to_string},
            {"name": "text39", "from": "text39", "parser": to_string_or_empty_string},
            {"name": "text40", "from": "text40", "parser": to_string_or_empty_string},
            {"name": "text41", "from": "text41", "parser": to_string_or_empty_string},
        ]

        new_docs = []

        for item in res:
            f = item['fields']
            if f['itemtype_key'].lower() == 'document':
                document_meta_data = get_fields(fields, item)

                if document_meta_data['text39'].lower() == "definitief" \
                        and document_meta_data['text40'].lower() in ["openbaar", "beperkt openbaar"] \
                        and document_meta_data['text41'].lower() != 'nvt':

                    doc_data = self.get_document_data(item['key'])

                    if doc_data['is_pdf']:
                        document_meta_data['url'] = f"/api/decosjoin/document/{encrypt(doc_data['doc_key'], identifier)}"

                        del(document_meta_data['text39'])
                        del(document_meta_data['text40'])
                        del(document_meta_data['text41'])
                        new_docs.append(document_meta_data)

        new_docs.sort(key=lambda x: x['sequence'])

        return new_docs

    def get_document(self, document_id):
        url_blob_content = f"{self.api_url}items/{document_id}/content"

        document_response = self.get_response(
            url_blob_content,
            auth=HTTPBasicAuth(self.username, self.password),
            headers={"Accept": "application/octet-stream"}
        )

        if log_raw:
            from pprint import pprint
            pprint(document_response.content)
            pprint(document_response.headers)

        return {
            'Content-Type': document_response.headers['Content-Type'],
            'file_data': document_response.content
        }


def get_translation(value: str, translations: list, fallbackToOriginalValue: bool = False):
    """ Accepts a 2d list with 3 items. [ ["from", "to" "show"], ... ] """
    if value is None:
        return value

    value = value.lower()

    # Find a translation
    for i in translations:
        if i[0].lower() == value:
            if len(i) == 3 and i[2] is False:  # Explicitly use None
                return None
            return i[1]

    # Return the original value if not found
    return value if fallbackToOriginalValue else None


def get_fields(fields, zaak):
    result = {}
    for f in fields:
        key = f['name']
        val = zaak['fields'].get(f['from'])
        result[key] = f['parser'](val)

    return result


def to_date(value) -> Union[date, None]:
    if not value:
        return None

    if type(value) == date:
        return value

    if type(value) == datetime:
        return value.date()

    if type(value) == str:
        parsed_value = parser.isoparse(value).date()
        return parsed_value

    raise ParseError(f"Unable to parse type({type(value)} with to_date")


def to_time(value) -> Union[str, None]:
    if not value:
        return None

    if type(value) == time:
        return f'{value.hour:02}:{value.minute:02}'

    if type(value) == datetime:
        return to_time(value.time())

    if type(value) == str:
        time_pattern = r'([0-9]{2})[\.:]([0-9]{2})'
        matches = re.match(time_pattern, value)
        if matches:
            hour = int(matches.group(1))
            minute = int(matches.group(2))

            if (0 <= hour <= 23 and 0 <= minute <= 59) or (hour == 24 and minute == 00):
                return f'{hour:02}:{minute:02}'
            logging.error(f"Error parsing time, value: {value}")
            return None

    return None


def to_datetime(value) -> Union[datetime, None]:
    if not value:
        return None

    if type(value) == date:
        return datetime(value.year, value.month, value.day)

    if type(value) == datetime:
        return value

    if type(value) == str:
        parsed_value = parser.isoparse(value)
        return parsed_value

    raise ParseError(f"Unable to parse type({type(value)} with to_datetime")


def to_int(value):
    if value == 0:
        return 0
    if not value:
        return None
    return int(value)


def to_string(value):
    if not value:
        return None
    return str(value).strip()


def to_string_or_empty_string(value):
    if not value:
        return ''
    return str(value).strip()


def to_bool(value):
    return bool(value)


def to_decision(value):
    translate_values = [
        "verleend met borden",
        "verleend zonder bebording",
        "verleend zonder borden"
    ]

    if value and value.lower() in translate_values:
        return 'Verleend'

    return value


def to_title(value):
    translations = [
        ["TVM - RVV - Object", "Tijdelijke verkeersmaatregel"],
        ["GPP", "Vaste parkeerplaats voor gehandicapten (GPP)"],
        ["GPK", "Europse gehandicaptenparkeerkaart (GPK)"],
        ["Omzettingsvergunning", "Vergunning voor kamerverhuur"],
        ["E-RVV - TVM", "e-RVV (Gratis verkeersontheffing voor elektrisch goederenvervoer)"],
        ["Vakantieverhuur afmelding", "Geannuleerde verhuur"],
        ["Vakantieverhuur", "Geplande verhuur"],
        ["B&B - vergunning", "Vergunning bed & breakfast"],
        ["Vakantieverhuur vergunningsaanvraag", "Vergunning vakantieverhuur"],
    ]
    if not value:
        return None
    return get_translation(value, translations)


def to_transition_agreement(value):
    if value and value.lower() == "verleend met overgangsrecht":
        return True
    return False


def to_vakantie_verhuur_vergunning_status(value):
    # Vakantieverhuur vergunningen worden direct verleend (en dus voor Mijn Amsterdam afgehandeld)
    return "Afgehandeld"


def to_vakantie_verhuur_vergunning_decision(value):
    # Vakantieverhuur vergunningen worden na betaling direct verleend en per mail toegekend zonder dat de juiste status in Decos wordt gezet.
    # Later, na controle, wordt mogelijk de vergunning weer ingetrokken. Geplande/Afgemelde Verhuur is een uizondering in relatie tot de reguliere statusbeschrijvingen
    # daar "Verleend" een resultaat is en geen status.
    if value and "ingetrokken" in value.lower():
        return "Ingetrokken"

    return "Verleend"
