from pprint import pprint

import requests
# import json
from requests.auth import HTTPBasicAuth

from decosjoin.api.config import get_decosjoin_username, get_decosjoin_password, get_decosjoin_api_host, get_decosjoin_adres_boek


class DecosJoinConnection:
    def __init__(self):
        self.username = get_decosjoin_username()
        self.password = get_decosjoin_password()

        self.adres_boek = get_decosjoin_adres_boek()

        self._api_host = get_decosjoin_api_host()
        self._api_location = "/decosweb/aspx/api/v1/"
        self.api_url = f"{self._api_host}{self._api_location}"

    def _get(self, url):
        """ Makes request to the decos join api with credentials added. """
        print("Getting", url)
        response = requests.get(url, auth=HTTPBasicAuth(self.username, self.password))
        if response.status_code == 200:
            json = response.json()
            pprint(json)
            return json

    def _get_user_key(self, bsn):
        """ Retrieve the internally used id for a user. """
        url = f"{self.api_url}items/{self.adres_boek}/addresses?filter=num1%20eq%20{bsn}&select=num1"
        res_json = self._get(url)
        user_key = res_json['content'][0]['key']
        return user_key

    def get_zaken(self, bsn):
        """ Get all zaken for a bsn. """
        user_key = self._get_user_key(bsn)
        url = f"{self.api_url}items/{user_key}/folders"
        '/folders?select = mark, text45, subject1, text9, text11, text12, text13, text6, date6, text7, text10, date7,'
        ' text8, document_date, date5, processed, dfunction'
        res_json = self._get(url)
        return res_json
