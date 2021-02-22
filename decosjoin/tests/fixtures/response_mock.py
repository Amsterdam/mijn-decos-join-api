from decosjoin.tests.fixtures.data import get_zaken_response, \
    get_zaken_response_2, get_zaken_response_empty, get_search_addresses_bsn_111222333_response_empty, \
    get_search_addresses_bsn_111222333_response, get_search_addresses_bsn_111222333_response_2, \
    get_zaken_resposne_2_part_2, get_documents_response, get_document, get_blob_response


def get_response_mock(self, *args, **kwargs):
    """ Attempt to get data from mock_get_urls. """
    try:
        res_data = mocked_get_urls[args[0]]
    except KeyError:
        raise Exception("Url not defined %s", args[0])
    return MockedResponse(res_data)


def post_response_mock(self, *args, **kwargs):
    """ Attempt to get data from mock_get_urls. """
    url = args[0]
    body = kwargs['json']
    for item in mocked_post_urls:
        if url == item['url']:
            # Does the body also match?
            if body == item['post_body']:
                return MockedResponse(item['response'])

    # if nothing is found
    raise Exception("Url with body not defined", url, body)


class MockedResponse:
    status_code = 200

    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data

    @property
    def content(self):
        return self.data

    headers = {'Content-Type': 'application/pdf'}


_folder_params = "?select=title,mark,text45,subject1,text9,text11,text12,text13,text6,date6,text7,text10,date7,text8,document_date,date5,processed,dfunction&top=10"
# For readability sake, this is a tuple which is converted into a dict
mocked_get_urls_tuple = (
    (
        f"http://localhost/decosweb/aspx/api/v1/items/32charsstringxxxxxxxxxxxxxxxxxxx/folders{_folder_params}",
        get_zaken_response()
    ),
    (
        f"http://localhost/decosweb/aspx/api/v1/items/32charsstringxxxxxxxxxxxxxxxxxx2/folders{_folder_params}",
        get_zaken_response_2()
    ),
    (
        f"http://localhost/decosweb/aspx/api/v1/items/32charsstringxxxxxxxxxxxxxxxxxx2/folders{_folder_params}&skip=10",
        get_zaken_resposne_2_part_2()
    ),
    (
        f"http://localhost/decosweb/aspx/api/v1/items/32charsstringxxxxxxxxxxxxxxxxxx3/folders{_folder_params}",
        get_zaken_response_empty()
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/ZAAKKEY1/documents?select=subject1,sequence,mark,text39,text40,text41,itemtype_key",
        get_documents_response()
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/BLOBKEY01/content",
        get_document()
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/DOCUMENTKEY01/blobs",
        get_blob_response()
    )
)
mocked_get_urls = dict(mocked_get_urls_tuple)


mocked_post_urls = (
    {
        "url": "http://localhost/decosweb/aspx/api/v1/search/books?properties=false",
        "post_body": {
            'bookKey': 'hexkey32chars000000000000000BSN1',
            'orderBy': 'sequence',
            'skip': 0,
            'take': 50,
            'searchInHierarchyPath': False,
            'searchInPendingItemContainerKeys': False,
            'filterFields': {
                'num1': [
                    {
                        'FilterOperation': 1,
                        'FilterValue': '111222333',
                        'FilterOperator': '='
                    }
                ]
            }
        },
        "response": get_search_addresses_bsn_111222333_response(),
    },
    {
        "url": "http://localhost/decosweb/aspx/api/v1/search/books?properties=false",
        "post_body": {
            'bookKey': 'hexkey32chars000000000000000BSN2',
            'orderBy': 'sequence',
            'skip': 0,
            'take': 50,
            'searchInHierarchyPath': False,
            'searchInPendingItemContainerKeys': False,
            'filterFields': {
                'num1': [
                    {
                        'FilterOperation': 1,
                        'FilterValue': '111222333',
                        'FilterOperator': '='
                    }
                ]
            }
        },
        "response": get_search_addresses_bsn_111222333_response_2(),
    },
    {
        "url": "http://localhost/decosweb/aspx/api/v1/search/books?properties=false",
        "post_body": {
            'bookKey': 'hexkey32chars000000000000000BSN3',
            'orderBy': 'sequence',
            'skip': 0,
            'take': 50,
            'searchInHierarchyPath': False,
            'searchInPendingItemContainerKeys': False,
            'filterFields': {
                'num1': [
                    {
                        'FilterOperation': 1,
                        'FilterValue': '111222333',
                        'FilterOperator': '='
                    }
                ]
            }
        },
        "response": get_search_addresses_bsn_111222333_response_empty(),
    },

)
