import requests
from requests.auth import HTTPBasicAuth

from decosjoin.api.decosjoin.Exception import DecosJoinConnectionError


class DecosJoinConnection:
    def __init__(self, username, password, api_host, adres_boeken):
        self.username = username
        self.password = password
        self.adres_boeken = adres_boeken
        self._api_host = api_host
        self._api_location = "/decosweb/aspx/api/v1/"
        self.api_url = f"{self._api_host}{self._api_location}"

    def _get_response(self, *args, **kwargs):
        """ Easy to get_response_mock intermediate function. """
        return requests.get(*args, **kwargs)

    def _get(self, url):
        """ Makes a request to the decos join api with HTTP basic auth credentials added. """
        print("\n------\nGetting\n", url, "\n")
        response = self._get_response(url,
                                      auth=HTTPBasicAuth(self.username, self.password),
                                      headers={
                                          "Accept": "application/itemdata",
                                      })
        if response.status_code == 200:
            json = response.json()
            print("response\n", json)
            return json
        else:  # TODO: for debugging. Also test this
            print("status", response.status_code)
            print(">>", response.content)
            raise DecosJoinConnectionError(response.status_code)

    def _get_user_keys(self, bsn):
        """ Retrieve the internal ids used for a user. """
        keys = []
        for boek in self.adres_boeken['bsn']:
            url = f"{self.api_url}items/{boek}/addresses?filter=num1%20eq%20{bsn}&select=num1"
            res_json = self._get(url)
            if res_json['count'] > 0:
                user_key = res_json['content'][0]['key']
                keys.append(user_key)

        return keys

    def _get_zaken_for_user(self, user_key):
        url = f"{self.api_url}items/{user_key}/folders?select=title,mark,text45,subject1,text9,text11,text12,text13,text6,date6,text7,text10,date7,text8,document_date,date5,processed,dfunction"
        res_json = self._get(url)
        return res_json

    def _transform(self, zaken):
        new_zaken = []
        for zaak in zaken:
            # copy fields
            f = zaak['fields']
            new_zaak = {}
            if f['text45'] == "TVM - RVV - Object":
                new_zaak = {
                    "status": f['title'],  # this makes soooo much sense /s
                    "title": f['subject1'],
                    "mark": f['mark'],
                    "zaakType": f['text45'],
                    "datumVan": f['date6'],
                    "datumTotenmet": f['date7'],
                    # "tijdVan": f['text10'],  # not coming back
                    "tijdTot": f['text11'],  # or is it text13?
                    "kenteken": f['text9'],
                }
            new_zaken.append(new_zaak)
        return new_zaken

    def filter_zaken(self, zaken):
        return [zaak for zaak in zaken if zaak['fields']['text45'] in ['TVM - RVV - Object']]

    def get_zaken(self, bsn):
        """ Get all zaken for a bsn. """
        zaken = []
        user_keys = self._get_user_keys(bsn)
        # if not user_keys:
        #     return []
        for key in user_keys:
            res_zaken = self._get_zaken_for_user(key)
            key_zaken = self.filter_zaken(res_zaken['content'])
            zaken.extend(key_zaken)

        zaken

        return self._transform(zaken)
