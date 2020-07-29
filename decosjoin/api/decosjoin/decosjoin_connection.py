import math
from datetime import datetime, date, time, timedelta

import requests
from dateutil import parser
from flask import make_response
from requests.auth import HTTPBasicAuth

from decosjoin.api.decosjoin.Exception import DecosJoinConnectionError, ParseError
from decosjoin.crypto import encrypt

log_raw = False
page_size = 10


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
                                          headers={"Accept": "application/itemdata"})
        elif method == 'post':
            response = self._post_response(url,
                                           auth=HTTPBasicAuth(self.username, self.password),
                                           headers={"Accept": "application/itemdata"},
                                           json=json)

        if response.status_code == 200:
            json = response.json()
            # print("response\n", json)
            return json
        else:  # TODO: for debugging. Also test this
            # print("status", response.status_code)
            # print(">>", response.content)
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

    def _get_user_keys(self, bsn):
        """ Retrieve the internal ids used for a user. """
        keys = []
        for boek in self.adres_boeken['bsn']:
            url = f"{self.api_url}search/books?properties=false"
            res_json = self._get(url, json=self.search_query(bsn, boek), method='post')
            if res_json['itemDataResultSet']['count'] > 0:
                for item in res_json['itemDataResultSet']['content']:
                    user_key = item['key']
                    keys.append(user_key)

        return keys

    def _get_zaken_for_user(self, user_key, offset=None):
        url = f"{self.api_url}items/{user_key}/folders?select=title,mark,text45,subject1,text9,text11,text12,text13,text6,date6,text7,text10,date7,text8,document_date,date5,processed,dfunction&top={page_size}"
        if offset:
            url += f'&skip={offset}'
        res_json = self._get(url)
        if log_raw:
            from pprint import pprint
            pprint(res_json)
        return res_json

    # def _enrich_with_case_type(self, zaken):
    #     for zaak in zaken:
    #         zaak_key = zaak['key']
    #         url = f"{self.api_url}items/{zaak_key}/casetype"
    #         case_type = self._get(url)
    #         zaak['MA-casetype'] = case_type['description']  # store it on the case itself with MA- prefix
    #         zaak['MA-casestatus'] = case_type['currentStatus']

    def _transform(self, zaken):
        new_zaken = []

        for zaak in zaken:
            f = zaak['fields']

            if f['text45'] == "TVM - RVV - Object":
                fields = [
                    {"name": "status", "from": 'title', "parser": to_string},
                    {"name": "title", "from": 'subject1', "parser": to_string},
                    {"name": "identifier", "from": 'mark', "parser": to_string},
                    {"name": "caseType", "from": 'text45', "parser": to_string},
                    {"name": "dateFrom", "from": 'date6', "parser": to_date},
                    {"name": "dateEndInclusive", "from": 'date7', "parser": to_date},
                    {"name": "timeStart", "from": 'text10', "parser": to_time},
                    {"name": "timeEnd", "from": 'text11', "parser": to_time},  # this is a freeform text field, it can contain ANYTHING
                    {"name": "kenteken", "from": 'text9', "parser": to_string},
                    {"name": "location", "from": 'text6', "parser": to_string},
                    {"name": "dateRequest", "from": "document_date", "parser": to_datetime},
                    {"name": "decision", "from": "dfunction", "parser": to_decision},
                    {"name": "dateDecision", "from": "date5", "parser": to_string},  # datum afhandeling?
                ]

                new_zaak = _get_fields(fields, zaak)

                new_zaak['documents_url'] = f"/api/decosjoin/listdocument/{encrypt(new_zaak['identifier'])}"

                # if end date is not defined, its the same as date start
                if not new_zaak['dateEndInclusive']:
                    new_zaak['dateEndInclusive'] = new_zaak['dateFrom']

                # if date range is within now, it is current
                if _is_current(new_zaak):
                    new_zaak['isActual'] = True
                else:
                    new_zaak['isActual'] = False

                new_zaken.append(new_zaak)

        return new_zaken

    def filter_zaken(self, zaken):
        """ Filter un-parsed cases. """
        zaken = [zaak for zaak in zaken if zaak['caseType'].lower() in ['tvm - rvv - object']]
        zaken = [zaak for zaak in zaken if zaak['title'].lower() not in ['wacht op online betaling', 'wacht op ideal betaling']]

        zaken = [zaak for zaak in zaken if not zaak['title'].lower().startswith("*verwijder")]

        return zaken

    def get_zaken(self, bsn):
        """ Get all zaken for a bsn. """
        zaken = []
        user_keys = self._get_user_keys(bsn)

        for key in user_keys:
            # fetch one
            res_zaken = self._get_zaken_for_user(key)
            max = math.ceil(res_zaken['count'] / page_size) * page_size
            zaken.extend(res_zaken['content'])
            # paginate over the rest (with page sizes)
            for offset in range(page_size, max, page_size):
                res_zaken = self._get_zaken_for_user(key, offset)
                zaken.extend(res_zaken['content'])

        zaken = self._transform(zaken)
        return self.filter_zaken(zaken)

    def list_documents(self, zaak_id):
        url = f"{self.api_url}items/{zaak_id}/DOCUMENTS"
        res_json = self._get(url)

        if log_raw:
            from pprint import pprint
            pprint(res_json)

        fields = [
            {"name": 'fileName', "from": 'subject1', "parser": to_string},
            {"name": 'sequence', "from": 'sequence', "parser": to_int},
            {"name": 'id', "from": 'mark', "parser": to_string},
        ]

        new_docs = []

        for item in res_json['content']:
            f = item['fields']
            if f['itemtype_key'].lower() == 'document':
                document_meta_data = _get_fields(fields, item)
                document_meta_data['downloadUrl'] = f"/api/decosjoin/document/{encrypt(item['key'])}"
                new_docs.append(document_meta_data)

        new_docs.sort(key=lambda x: x['sequence'])

        return new_docs

    def get_document(self, document_id):
        url = f"{self.api_url}items/{document_id}/BLOB/content"

        document_response = self._get_response(
            url,
            auth=HTTPBasicAuth(self.username, self.password),
            headers={"Accept": "application/octet-stream"}
        )

        if log_raw:
            from pprint import pprint
            pprint(document_response.data)
            pprint(document_response.headers)

        return {
            'Content-Type': document_response.headers['Content-Type'],
            'file_data': document_response.data
        }


def _get_fields(fields, zaak):
    result = {}
    for f in fields:
        key = f['name']
        val = zaak['fields'].get(f['from'])
        result[key] = f['parser'](val)

    return result


def _is_current(zaak):
    # date start
    start = to_datetime(zaak['dateFrom'])
    # add time start
    if zaak.get('timeStart'):
        start_time = zaak['timeStart']
        start = start.replace(hour=start_time.hour, minute=start_time.minute, second=start_time.second)

    # date end
    if zaak.get('dateEnd'):
        end = to_datetime(zaak['dateEnd'])
    elif zaak.get('dateEndInclusive'):
        end = to_datetime(zaak['dateEndInclusive'])
        end = (end + timedelta(days=1)) - timedelta(seconds=1)
    else:
        return False

    # add time end
    if zaak.get('timeEnd'):
        end_time = zaak['timeEnd']
        end = end.replace(hour=end_time.hour, minute=end_time.minute, second=end_time.second)
        # end.hour = end_time.hour
        # end.minute = end_time.minute
        # end.second = end_time.second

    # if now between start and end it is current
    now = datetime.now()
    if start < now < end:
        return True
    return False


def to_date(value) -> [datetime, None]:
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


def to_time(value) -> [time, None]:
    # TODO: not done, there is no example data for time from the api
    if not value:
        return None

    if type(value) == time:
        return value

    if type(value) == datetime:
        return value.time()

    if type(value) == str:
        try:
            parsed_value = parser.isoparse(value).time()  # TODO: this doesn't parse times
        except ValueError:
            return None
        return parsed_value

    raise ParseError(f"Unable to parse type({type(value)} '{value}' with to_time")


def to_datetime(value) -> [datetime, None]:
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


def to_decision(value):
    translate_values = [
        "verleend met borden",
        "verleend zonder bebording",
        "verleend zonder borden"
    ]

    if value and value.lower() in translate_values:
        return 'Verleend'

    return value
