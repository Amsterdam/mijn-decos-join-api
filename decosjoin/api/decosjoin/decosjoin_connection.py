import requests
from requests.auth import HTTPBasicAuth

from decosjoin.api.decosjoin.Exception import DecosJoinConnectionError


class DecosJoinConnection:
    def __init__(self, username, password, api_host, adres_boek):
        self.username = username
        self.password = password

        self.adres_boek = adres_boek

        self._api_host = api_host
        self._api_location = "/decosweb/aspx/api/v1/"
        self.api_url = f"{self._api_host}{self._api_location}"

    def _get_response(self, *args, **kwargs):
        """ Easy to mock intermediate function. """
        return requests.get(*args, **kwargs)

    def _get(self, url):
        """ Makes a request to the decos join api with HTTP basic auth credentials added. """
        print("Getting", url)
        response = self._get_response(url,
                                      auth=HTTPBasicAuth(self.username, self.password),
                                      headers={
                                          "Accept": "application/itemdata",
                                      })
        if response.status_code == 200:
            json = response.json()
            return json
        else:  # TODO: for debugging. Also test this
            print("status", response.status_code)
            print(">>", response.content)
            raise DecosJoinConnectionError(response.status_code)

    def _get_user_key(self, bsn):
        """ Retrieve the internally used id for a user. """
        url = f"{self.api_url}items/{self.adres_boek}/addresses?filter=num1%20eq%20{bsn}&select=num1"
        res_json = self._get(url)
        user_key = res_json['content'][0]['key']
        return user_key

    def get_zaken(self, bsn):
        """ Get all zaken for a bsn. """
        user_key = self._get_user_key(bsn)
        url = f"{self.api_url}items/{user_key}/folders?select=mark,text45,subject1,text9,text11,text12,text13,text6,date6,text7,text10,date7,text8,document_date,date5,processed,dfunction"
        res_json = self._get(url)
        return res_json
