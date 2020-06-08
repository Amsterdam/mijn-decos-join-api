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
        for boek in self.adres_boeken:
            url = f"{self.api_url}items/{boek}/addresses?filter=num1%20eq%20{bsn}&select=num1"
            res_json = self._get(url)
            print(res_json)
            if res_json['count'] == 0:
                continue
            user_key = res_json['content'][0]['key']
            return user_key

    def _get_zaken_for_user(self, user_key):
        url = f"{self.api_url}items/{user_key}/folders?select=title,mark,text45,subject1,text9,text11,text12,text13,text6,date6,text7,text10,date7,text8,document_date,date5,processed,dfunction"
        res_json = self._get(url)
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
            print('z', zaak)
            # copy fields
            new_zaak = {key: zaak['fields'][key] for key in zaak['fields'] if key in ['mark', 'date5', 'date6', 'date7']}
            # new_zaak['caseType'] = zaak['MA-casetype']
            # new_zaak['caseStatus'] = zaak['MA-casestatus']
            new_zaken.append(new_zaak)
        return new_zaken

    def get_zaken(self, bsn):
        """ Get all zaken for a bsn. """
        print("----- get zaken", bsn)
        user_key = self._get_user_key(bsn)
        if user_key is None:
            return []
        res_zaken = self._get_zaken_for_user(user_key)
        # self._enrich_with_case_type(res_zaken['content'])
        return self._transform(res_zaken['content'])
