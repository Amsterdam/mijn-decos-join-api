from decosjoin.tests.fixtures.data import get_addresses_bsn_111222333_response_empty, \
    get_addresses_bsn_111222333_response, get_zaken_response


def get_response_mock(self, *args, **kwargs):
    """ Attempt to get data from mock_urls. """
    try:
        res_data = mocked_urls[args[0]]
    except KeyError:
        raise Exception("Url not defined %s", args[0])
    return MockedResponse(res_data)


class MockedResponse:
    status_code = 200

    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


# For readability sake, this is a tuple which is converted into a dict
mocked_urls_tuple = (
    (
        "http://localhost/decosweb/aspx/api/v1/items/hexkey32chars000000000000000BSN1/addresses?filter=num1%20eq%20111222333&select=num1",
        get_addresses_bsn_111222333_response_empty()
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/hexkey32chars000000000000000BSN2/addresses?filter=num1%20eq%20111222333&select=num1",
        get_addresses_bsn_111222333_response()
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/32charsstringxxxxxxxxxxxxxxxxxxx/folders?select=title,mark,text45,subject1,text9,text11,text12,text13,text6,date6,text7,text10,date7,text8,document_date,date5,processed,dfunction",
        get_zaken_response()
    )
)
mocked_urls = dict(mocked_urls_tuple)
