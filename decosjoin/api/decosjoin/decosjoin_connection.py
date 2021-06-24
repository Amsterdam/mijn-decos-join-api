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


select_fields = ','.join([
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
        self._api_host = api_host
        self._api_location = "/decosweb/aspx/api/v1/"
        self.api_url = f"{self._api_host}{self._api_location}"

    def _get_response(self, *args, **kwargs):
        """ Easy to mock intermediate function. """
        return requests.get(*args, **kwargs)

    def _post_response(self, *args, **kwargs):
        """ Easy to mock intermediate function. """
        return requests.post(*args, **kwargs)

    def _get(self, url, method='get', json=None):
        """ Makes a request to the decos join api with HTTP basic auth credentials added. """
        if method == 'get':
            response = self._get_response(url,
                                          auth=HTTPBasicAuth(self.username, self.password),
                                          headers={"Accept": "application/itemdata"},
                                          timeout=9)
        elif method == 'post':
            response = self._post_response(url,
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

    def _get_user_keys(self, kind, identifier):
        """ Retrieve the internal ids used for a user. """
        keys = []

        adres_boeken = self.adres_boeken[kind]

        for boek in adres_boeken:
            url = f"{self.api_url}search/books?properties=false"
            res_json = self._get(url, json=self.search_query(identifier, boek), method='post')
            if res_json['itemDataResultSet']['count'] > 0:
                for item in res_json['itemDataResultSet']['content']:
                    user_key = item['key']
                    keys.append(user_key)

        return keys

    def _transform(self, zaken, user_identifier):  # noqa: C901
        new_zaken = []
        deferred_zaken = []

        for zaak in zaken:
            f = zaak['fields']

            if f['text45'] == "TVM - RVV - Object":
                fields = [
                    {"name": "status", "from": "title", "parser": to_string},
                    {"name": "title", "from": "subject1", "parser": to_string},
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

                new_zaak = _get_fields(fields, zaak)

                new_zaak['documentsUrl'] = f"/api/decosjoin/listdocuments/{encrypt(zaak['key'], user_identifier)}"

                # if end date is not defined, its the same as date start
                if not new_zaak['dateEnd']:
                    new_zaak['dateEnd'] = new_zaak['dateStart']

                if not self._deny_list_filter(new_zaak['title'], ['wacht op online betaling', 'wacht op ideal betaling']):
                    continue
                if not self._deny_list_filter(new_zaak['decision'], ['buiten behandeling']):
                    continue
                if new_zaak['title'].lower().startswith("*verwijder"):
                    continue

            elif f['text45'] == 'Vakantieverhuur vergunningsaanvraag':
                fields = [
                    {"name": "caseType", "from": "text45", "parser": to_string},
                    {"name": "identifier", "from": 'mark', "parser": to_string},
                    {"name": "dateRequest", "from": "document_date", "parser": to_date},
                    {"name": "dateDecision", "from": "date5", "parser": to_datetime},  # Datum afhandeling
                    {"name": "location", "from": "text6", "parser": to_string},
                    {"name": "status", "from": "title", "parser": to_vakantie_verhuur_vergunning_status},
                    {"name": "decision", "from": "dfunction", "parser": to_vakantie_verhuur_vergunning_decision},
                    {"name": "dateStart", "from": "document_date", "parser": to_date},  # same as dateRequest
                    # dateEnd is set programmatically  Datum tot
                ]
                new_zaak = _get_fields(fields, zaak)

                # The validity of this case runs from april 1st until the next. set the end date to the next april the 1st
                new_zaak['dateEnd'] = self.next_april_first(new_zaak['dateRequest'])

            elif f['text45'] == 'Vakantieverhuur':
                fields = [
                    {"name": "caseType", "from": "text45", "parser": to_string},
                    {"name": "identifier", "from": 'mark', "parser": to_string},
                    {"name": "dateRequest", "from": "document_date", "parser": to_date},
                    {"name": "dateDecision", "from": "date5", "parser": to_datetime},  # Datum afhandeling
                    {"name": "dateStart", "from": 'date6', "parser": to_date},  # Start verhuur
                    {"name": "dateEnd", "from": 'date7', "parser": to_date},  # Einde verhuur
                    {"name": "location", "from": "text6", "parser": to_string},
                    # cancelled: true/false
                    # dateCancelled: date(time)?
                ]
                new_zaak = _get_fields(fields, zaak)
                new_zaak['cancelled'] = False
                new_zaak['dateCancelled'] = None
                new_zaak['duration'] = 0

                if new_zaak['dateStart'] and new_zaak['dateEnd']:
                    new_zaak['duration'] = (new_zaak['dateEnd'] - new_zaak['dateStart']).days

            elif f['text45'] == 'Vakantieverhuur afmelding':
                fields = [
                    {"name": "caseType", "from": "text45", "parser": to_string},
                    {"name": "identifier", "from": 'mark', "parser": to_string},
                    {"name": "dateRequest", "from": "document_date", "parser": to_date},
                    {"name": "dateStart", "from": 'date6', "parser": to_date},  # Start verhuur
                    {"name": "dateEnd", "from": 'date7', "parser": to_date},  # Einde verhuur
                ]

                new_zaak = _get_fields(fields, zaak)
                deferred_zaken.append(new_zaak)
                continue  # do not follow normal new_zaak procedure

            elif f['text45'] == 'B&B - vergunning':
                fields = [
                    {"name": "caseType", "from": "text45", "parser": to_string},
                    {"name": "dateRequest", "from": "document_date", "parser": to_date},  # Startdatum zaak
                    {"name": "decision", "from": "dfunction", "parser": to_string},
                    {"name": "location", "from": "text6", "parser": to_string},
                    {"name": "title", "from": "subject1", "parser": to_string},
                    {"name": "identifier", "from": "mark", "parser": to_string},
                    {"name": "dateDecision", "from": "date5", "parser": to_datetime},  # Datum afhandeling
                    {"name": "dateStart", "from": 'date6', "parser": to_date},  # Datum van
                    {"name": "dateEnd", "from": 'date7', "parser": to_date},  # Datum tot en met
                    {"name": "status", "from": "title", "parser": to_string},
                    {"name": "requester", "from": "company", "parser": to_string},
                    {"name": "owner", "from": "text25", "parser": to_string},
                    {"name": "hasTransitionAgreement", "from": "dfunction", "parser": to_transition_agreement}  # need this for tip mijn-33
                ]
                new_zaak = _get_fields(fields, zaak)
                decision_translations = [
                    ["Verleend met overgangsrecht", "Verleend", True],
                    ["Verleend zonder overgangsrecht", "Verleend", True],
                    ["Geweigerd met overgangsrecht", "Geweigerd", True],
                    ["Geweigerd op basis van Quotum", "Geweigerd", True],
                    ["Ingetrokken", "Ingetrokken", True],
                ]

                status_translations = [
                    ["Ontvangen", "Ontvangen", True],
                    ["Volledigheidstoets uitvoeren", "Ontvangen", True],
                    ["Behandelen aanvraag", "In behandeling", True],
                    ["Huisbezoek", "In behandeling", True],
                    ["Beoordelen en besluiten", "In behandeling", True],
                    ["Afgehandeld", "Afgehandeld", True],
                ]
                new_zaak['decision'] = _get_translation(new_zaak['decision'], decision_translations)
                new_zaak['status'] = _get_translation(new_zaak['status'], status_translations)

            elif f['text45'] == 'GPP':
                fields = [
                    {"name": "caseType", "from": "text45", "parser": to_string},
                    {"name": "identifier", "from": "mark", "parser": to_string},
                    {"name": "dateDecision", "from": "date5", "parser": to_datetime},  # Datum afhandeling
                    {"name": "dateRequest", "from": "document_date", "parser": to_string},
                    {"name": "decision", "from": "dfunction", "parser": to_string},
                    {"name": "kenteken", "from": "text7", "parser": to_string},
                    {"name": "location", "from": "text8", "parser": to_string},
                    {"name": "status", "from": "title", "parser": to_string},
                ]
                new_zaak = _get_fields(fields, zaak)
                translations = [
                    ["Buiten behandeling", "Buiten behandeling", False],
                    ["Ingetrokken", "Ingetrokken", True],
                    ["Ingetrokken i.v.m. overlijden of verhuizing", "Ingetrokken", True],
                    ["Niet verleend", "Niet verleend", True],
                    ["Nog niet bekend", "", False],
                    ["Verleend", "Verleend", True],
                ]
                new_zaak['decision'] = _get_translation(new_zaak['decision'], translations)

            elif f['text45'] == 'GPK':
                fields = [
                    {"name": "caseType", "from": "text45", "parser": to_string},
                    {"name": "identifier", "from": "mark", "parser": to_string},
                    {"name": "decision", "from": "dfunction", "parser": to_string},
                    {"name": "dateDecision", "from": "date5", "parser": to_datetime},  # Datum afhandeling
                    {"name": "cardNumber", "from": "num3", "parser": to_string},  # kaartnummer
                    {"name": "dateRequest", "from": "document_date", "parser": to_date},
                    {"name": "cardtype", "from": "text7", "parser": to_string},
                    {"name": "dateEnd", "from": "date7", "parser": to_date},  # vervaldatum
                ]
                new_zaak = _get_fields(fields, zaak)

                # Copied from RD
                translations = [
                    ["Buiten behandeling", "Buiten behandeling", False],
                    ["Ingetrokken", "Ingetrokken", True],
                    ["Ingetrokken i.v.m. overlijden of verhuizing", "Ingetrokken", True],
                    ["Ingetrokken verleende GPK wegens overlijden", "Ingetrokken", True],
                    ["Niet verleend", "Niet verleend", True],
                    ["Nog niet bekend", "", False],
                    ["Verleend", "Verleend", True],
                    ["Verleend Bestuurder met GPP (niet verleend passagier)", "Verleend Bestuurder, niet verleend Passagier", True],
                    ["Verleend Bestuurder, niet verleend Passagier", "Verleend Bestuurder, niet verleend Passagier", True],
                    ["Verleend met GPP", "Verleend", True],
                    ["Verleend Passagier met GPP (niet verleend Bestuurder)", "Verleend Passagier, niet verleend Bestuurder", True],
                    ["Verleend Passagier, niet verleend Bestuurder", "Verleend Passagier, niet verleend Bestuurder", True],
                    ["Verleend vervangend GPK", "Verleend", True],
                ]
                new_zaak['decision'] = _get_translation(new_zaak['decision'], translations)

            # elif f['text45'] == 'Evenement melding':
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
            #     new_zaak = _get_fields(fields, zaak)
            #     translations = [
            #         ["Ingetrokken", "Ingetrokken", True],
            #         ["Buiten behandeling", "Buiten behandeling", False],
            #         ["Niet verleend", "Geweigerd", True],
            #         ["Verleend", "Gemeld", True],
            #         ["Nog niet  bekend", "", False],
            #         ["Nog niet bekend", "", False],
            #         ["Verleend", "Verleend", True],
            #         ["Verleend (Bijzonder/Bewaren)", "Verleend", True],
            #         ["Verleend zonder borden", "Verleend", True],
            #     ]
            #     new_zaak['decision'] = _get_translation(new_zaak['decision'], translations)
            #
            # elif f['text45'] == 'Evenement vergunning':
            #     fields = [
            #         {"name": "caseType", "from": "text45", "parser": to_string},
            #         {"name": "identifier", "from": "mark", "parser": to_string},
            #         {"name": "dateDecision", "from": "date5", "parser": to_datetime},  # Datum afhandeling
            #         {"name": "dateRequest", "from": "document_date", "parser": to_datetime},
            #         {"name": "title", "from": "subject1", "parser": to_string},
            #         {"name": "dateStart", "from": "date6", "parser": to_date},  # Datum van
            #         {"name": "dateEnd", "from": "date7", "parser": to_date},  # Datum tot en met
            #         {"name": "location", "from": "text8", "parser": to_string},
            #         {"name": "timeStart", "from": "text7", "parser": to_time},
            #         {"name": "timeEnd", "from": "text8", "parser": to_time},  # tijd tot
            #     ]
            #     new_zaak = _get_fields(fields, zaak)
            #
            #     translations = [
            #         ["Afgebroken (Ingetrokken)", "Afgebroken (Ingetrokken)", True],
            #         ["Buiten behandeling", "Buiten behandeling", False],
            #         ["Geweigerd", "Geweigerd", True],
            #         ["Nog niet  bekend", "", False],
            #         ["Nog niet  bekend", "", False],
            #         ["Nog niet bekend", "", False],
            #         ["Verleend", "Verleend", True],
            #         ["Verleend (Bijzonder/Bewaren)", "Verleend", True],
            #         ["Verleend zonder borden", "Verleend", True],
            #     ]
            #     new_zaak['decision'] = _get_translation(new_zaak['decision'], translations)

            elif f['text45'] == 'Omzettingsvergunning':
                fields = [
                    {"name": "caseType", "from": "text45", "parser": to_string},
                    {"name": "identifier", "from": "mark", "parser": to_string},
                    {"name": "dateRequest", "from": "document_date", "parser": to_datetime},
                    {"name": "dateDecision", "from": "date5", "parser": to_datetime},  # Datum afhandeling
                    {"name": "location", "from": "text8", "parser": to_string},
                    {"name": "title", "from": "subject1", "parser": to_string},
                    {"name": "decision", "from": "dfunction", "parser": to_string},
                ]
                new_zaak = _get_fields(fields, zaak)
                translations = [
                    ["Buiten behandeling", "Buiten behandeling", False],
                    ["Geweigerd", "Geweigerd", True],
                    ["Ingetrokken door gemeente", "Ingetrokken door gemeente", True],
                    ["Ingetrokken op eigen verzoek", "Ingetrokken op eigen verzoek", True],
                    ["Nog niet bekend", "", False],
                    ["Van rechtswege verleend", "Verleend", True],
                    ["Vergunningvrij", "Vergunningvrij", True],
                    ["Verleend", "Verleend", True],
                    ["Verleend zonder borden", "Verleend", True],
                ]
                new_zaak['decision'] = _get_translation(new_zaak['decision'], translations)

            elif f['text45'] == 'E-RVV - TVM':
                fields = [
                    {"name": "caseType", "from": "text45", "parser": to_string},
                    {"name": "identifier", "from": "mark", "parser": to_string},
                    {"name": "dateRequest", "from": "document_date", "parser": to_string},
                    {"name": "dateDecision", "from": "date5", "parser": to_datetime},  # Datum afhandeling
                    {"name": "title", "from": "subject1", "parser": to_string},
                    {"name": "location", "from": "text8", "parser": to_string},
                    {"name": "status", "from": "title", "parser": to_string},
                    {"name": "dateStart", "from": "date6", "parser": to_date},  # Datum van
                    {"name": "dateEnd", "from": "date7", "parser": to_date},  # Datum tot en met
                    {"name": "timeStart", "from": "text10", "parser": to_time},
                    {"name": "timeEnd", "from": "text13", "parser": to_time},  # tijd tot
                    {"name": "decision", "from": "dfunction", "parser": to_string},
                ]
                new_zaak = _get_fields(fields, zaak)
                translations = [
                    ["Buiten behandeling", "Buiten behandeling", False],
                    ["Ingetrokken", "Ingetrokken", True],
                    ["Niet verleend", "Niet verleend", True],
                    ["Nog niet bekend", "", False],
                    ["Verleend met borden", "Verleend", True],
                    ["Verleend met borden en Fietsenrekken verwijderen", "Verleend", True],
                    ["Verleend met Fietsenrekken verwijderen", "Verleend", True],
                    ["Verleend zonder bebording", "Verleend", True],
                    ["Verleend zonder borden", "Verleend", True],
                ]
                new_zaak['decision'] = _get_translation(new_zaak['decision'], translations)

            else:
                # zaak does not match one of the known ones
                continue

            new_zaken.append(new_zaak)

        for defferred_zaak in deferred_zaken:
            if defferred_zaak['caseType'] == 'Vakantieverhuur afmelding':
                # update the existing registration
                for new_zaak in new_zaken:
                    if new_zaak['caseType'] == 'Vakantieverhuur':
                        if (new_zaak['dateStart'] == defferred_zaak['dateStart']) and (new_zaak['dateEnd'] == defferred_zaak['dateEnd']):
                            new_zaak['cancelled'] = True
                            new_zaak['dateCancelled'] = defferred_zaak['dateRequest']

        return new_zaken

    def next_april_first(self, case_date: date):
        if case_date < date(case_date.year, 4, 1):
            return date(case_date.year, 4, 1)
        else:
            return date(case_date.year + 1, 4, 1)

    def _deny_list_filter(self, value, deny_list):
        if value is None:
            return True
        value = value.lower()
        return value not in deny_list

    def filter_zaken(self, zaken):
        """ Filter un-parsed cases. """
        zaken = [zaak for zaak in zaken if zaak['caseType'].lower() in ALLOWED_ZAAKTYPES]

        return zaken

    def _get_page(self, url, offset=None):
        """ Get a single page for url. When offset is provided add that to the url. """
        if offset:
            url += f'&skip={offset}'
        res_json = self._get(url)
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
        res = self._get_page(url)

        end = math.ceil(res['count'] / page_size) * page_size
        items.extend(res['content'])

        for offset in range(page_size, end, page_size):
            res = self._get_page(url, offset)
            items.extend(res['content'])

        return items

    def get_zaken(self, kind, identifier):
        """ Get all zaken for a kind ['bsn' or 'kvk']. """
        zaken = []
        user_keys = self._get_user_keys(kind, identifier)

        for key in user_keys:
            url = f"{self.api_url}items/{key}/folders?select={select_fields}"
            zaken.extend(self.get_all_pages(url))

        zaken = self._transform(zaken, identifier)
        return sorted(self.filter_zaken(zaken), key=lambda x: x['identifier'], reverse=True)

    def get_document_data(self, doc_id: str):
        res_json = self._get(f"{self.api_url}items/{doc_id}/blob?select=bol10")

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
                document_meta_data = _get_fields(fields, item)

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

        document_response = self._get_response(
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


def _get_translation(value: str, translations: list):
    """ Accepts a 2d list with 3 items. [ ["from", "to" "show"], ... ] """
    if value is None:
        return value
    value = value.lower()
    for i in translations:
        if i[0].lower() == value:
            if not i[2]:  # show in frontend
                return None
            return i[1]
    return None


def _get_fields(fields, zaak):
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


def to_transition_agreement(value):
    if not value:
        return False
    if value.lower() == "verleend met overgangsrecht":
        return True


def to_vakantie_verhuur_vergunning_status(value):
    # Vakantieverhuur vergunningen worden direct verleend (en dus voor Mijn Amsterdam afgehandeld)
    return "Afgehandeld"


def to_vakantie_verhuur_vergunning_decision(value):
    # Vakantieverhuur vergunningen worden na betaling direct verleend en per mail toegekend zonder dat de juiste status in Decos wordt gezet.
    # Later, na controle, wordt mogelijk de vergunning weer ingetrokken
    if value and "ingetrokken" in value.lower():
        return "Ingetrokken"

    return "Verleend"
