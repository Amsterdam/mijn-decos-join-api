from unittest import TestCase

from decosjoin.api.decosjoin.decosjoin_connection import DecosJoinConnection
from decosjoin.tests.fixtures.data import get_bsn_lookup_response, get_GPP_zaken_response, get_GGP_casetype_response, \
    get_GPK_casetype_response


class MockedResponse:
    status_code = 200

    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


# For readability sake, this is a tuple which is converted into a dict
mocked_urls_tuple = (
    (
        "http://localhost/decosweb/aspx/api/v1/items/hexkey32chars0000000000000000000/addresses?filter=num1%20eq%201234578&select=num1",
        get_bsn_lookup_response()
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/32charsstringxxxxxxxxxxxxxxxxxxx/folders?select=mark,text45,subject1,text9,text11,text12,text13,text6,date6,text7,text10,date7,text8,document_date,date5,processed,dfunction",
        get_GPP_zaken_response()
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/HEXSTRINGITEM1/casetype",
        get_GGP_casetype_response()
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/HEXSTRINGITEM2/casetype",
        get_GPK_casetype_response()
    )
)
mocked_urls = dict(mocked_urls_tuple)


def get_mock_call(data):
    def mock(*args, **kwargs):
        """ Attempt to get data from mock_urls. """
        try:
            res_data = mocked_urls[args[0]]
        except KeyError:
            raise Exception("Url not defined %s", args[0])
        return MockedResponse(res_data)
    return mock


class ConnectionTests(TestCase):

    def test_get_user_key(self):
        connection = DecosJoinConnection('username', 'password', 'http://localhost', 'hexkey32chars0000000000000000000')

        # set mock
        connection._get_response = get_mock_call(get_bsn_lookup_response())

        user_key = connection._get_user_key("1234578")
        self.assertEqual(user_key, "32charsstringxxxxxxxxxxxxxxxxxxx")

    def test_get_zaken(self):
        connection = DecosJoinConnection('username', 'password', 'http://localhost', 'hexkey32chars0000000000000000000')

        def mock_get_user_key(bsn):
            return "32charsstringxxxxxxxxxxxxxxxxxxx"

        # set mocks
        connection._get_user_key = mock_get_user_key
        connection._get_response = get_mock_call(get_GPP_zaken_response())

        zaken = connection.get_zaken("12345678")
        from pprint import pprint
        pprint(zaken)
