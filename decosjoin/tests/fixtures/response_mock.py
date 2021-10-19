import json
from decosjoin.tests.fixtures.data import (
    get_blob_response,
    get_blob_response_no_pdf,
    get_blobs_response,
    get_document2_response,
    get_document_blob,
    get_document_response,
    get_documents_response,
    get_search_addresses_bsn_111222333_response,
    get_search_addresses_bsn_111222333_response_2,
    get_search_addresses_bsn_111222333_response_empty,
    get_zaken_response,
    get_zaken_response_2,
    get_zaken_response_2_part_2,
    get_zaken_response_2_part_3,
    get_zaken_response_empty,
    get_all_workflows_response,
    get_single_workflow_response,
)
from requests import Response


class MockedResponse(Response):
    def __init__(
        self,
        url="http://example.com",
        headers={"Content-Type": "application/json"},
        status_code=200,
        reason="Success",
        _content=None,
        json_=None,
        encoding="UTF-8",
    ):
        self.url = url
        self.headers = headers

        if json_ and headers["Content-Type"] == "application/json":
            self._content = json.dumps(json_).encode(encoding)
        elif isinstance(_content, bytes):
            self._content = _content
        elif isinstance(_content, str):
            self._content = _content.encode(encoding) if _content else None
        else:
            self._content = None

        self.status_code = status_code
        self.reason = reason
        self.encoding = encoding


def get_response_mock(self, *args, **kwargs):
    """Attempt to get data from mock_get_urls."""

    url = args[0]
    headers = {"Content-Type": "application/json"}

    if url in mocked_get_urls:
        if isinstance(mocked_get_urls[url], tuple):
            (res_data, headers) = mocked_get_urls[url]
        else:
            res_data = mocked_get_urls[url]
    else:
        raise Exception("Url not defined %s", url)

    if isinstance(res_data, dict):
        return MockedResponse(json_=res_data, headers=headers)

    return MockedResponse(_content=res_data, headers=headers)


def post_response_mock(self, *args, **kwargs):
    """Attempt to get data from mock_get_urls."""
    url = args[0]
    body = kwargs["json"]
    for item in mocked_post_urls:
        if url == item["url"]:
            # Does the body also match?
            if body == item["post_body"]:
                status_code = item.get("status_code", 200)
                return MockedResponse(
                    json_=item["response"],
                    status_code=status_code,
                    url=item["url"],
                    reason=item.get("reason", "Success"),
                )

    # if nothing is found
    raise Exception("Url with body not defined", url, body)


def post_response_mock_unauthorized(self, *args, **kwargs):
    return post_response_mock(
        self, mocked_post_urls[-1]["url"], json=mocked_post_urls[-1]["post_body"]
    )


_folder_params = "?select=title,mark,text45,subject1,bol10,company,date5,date6,date7,dfunction,document_date,num3,text6,text7,text8,text9,text10,text11,text12,text13,text20,text25&top=10"
# For readability sake, this is a tuple which is converted into a dict
mocked_get_urls_tuple = (
    (
        f"http://localhost/decosweb/aspx/api/v1/items/32charsstringxxxxxxxxxxxxxxxxxxx/folders{_folder_params}",
        get_zaken_response(),
    ),
    (
        f"http://localhost/decosweb/aspx/api/v1/items/32charsstringxxxxxxxxxxxxxxxxxx2/folders{_folder_params}",
        get_zaken_response_2(),
    ),
    (
        f"http://localhost/decosweb/aspx/api/v1/items/32charsstringxxxxxxxxxxxxxxxxxx2/folders{_folder_params}&skip=10",
        get_zaken_response_2_part_2(),
    ),
    (
        f"http://localhost/decosweb/aspx/api/v1/items/32charsstringxxxxxxxxxxxxxxxxxx2/folders{_folder_params}&skip=20",
        get_zaken_response_2_part_3(),
    ),
    (
        f"http://localhost/decosweb/aspx/api/v1/items/32charsstringxxxxxxxxxxxxxxxxxx3/folders{_folder_params}",
        get_zaken_response_empty(),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/ZAAKKEY1/documents?select=subject1,sequence,mark,text39,text40,text41,itemtype_key&top=10",
        get_documents_response(),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/ZAAKKEY2/documents?select=subject1,sequence,mark,text39,text40,text41,itemtype_key&top=10",
        get_documents_response(),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/DOCUMENTKEY01/content",
        (get_document_blob(), {"Content-Type": "application/pdf"}),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/DOCUMENTKEY01/blobs",
        get_blobs_response(),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/DOCUMENTKEY01/blob?select=bol10",
        get_blob_response_no_pdf(),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/DOCUMENTKEY02/blob?select=bol10",
        get_blob_response(),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/DOCUMENTKEY05/blob?select=bol10",
        get_blob_response_no_pdf(),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/DOCUMENTKEY06/blob?select=bol10",
        get_blob_response(),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/DOCUMENTKEY07/blob?select=bol10",
        get_blob_response_no_pdf(),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/DOCUMENTKEY08/blob?select=bol10",
        get_blob_response_no_pdf(),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/DOCUMENTKEY01",
        get_document_response(),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/DOCUMENTKEY02",
        get_document2_response(),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/DOCUMENTKEY03",
        get_document2_response(),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/DOCUMENTKEY04",
        get_document2_response(),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/DOCUMENTKEY05",
        get_document_response(),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/DOCUMENTKEY06",
        get_document2_response(),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/DOCUMENTKEY07",
        get_document2_response(),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/DOCUMENTKEY08",
        get_document2_response(),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/DOCUMENTKEY09",
        get_document2_response(),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/HEXSTRING17/workflows",
        get_all_workflows_response(),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/HEXSTRING23/workflows",
        get_all_workflows_response("omzettingsvergunning"),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/HEXSTRING_ALL_WORKFLOWS_RESPONSE/workflowlinkinstances?properties=false&fetchParents=false&oDataQuery.select=mark,date1,date2,text7,sequence&oDataQuery.orderBy=sequence",
        get_single_workflow_response(),
    ),
    (
        "http://localhost/decosweb/aspx/api/v1/items/HEXSTRING_ALL_WORKFLOWS_RESPONSE_OMZETTINGSVERGUNNING/workflowlinkinstances?properties=false&fetchParents=false&oDataQuery.select=mark,date1,date2,text7,sequence&oDataQuery.orderBy=sequence",
        get_single_workflow_response("omzettingsvergunning"),
    ),
)
mocked_get_urls = dict(mocked_get_urls_tuple)


mocked_post_urls = (
    {
        "url": "http://localhost/decosweb/aspx/api/v1/search/books?properties=false",
        "post_body": {
            "bookKey": "hexkey32chars000000000000000BSN1",
            "orderBy": "sequence",
            "skip": 0,
            "take": 50,
            "searchInHierarchyPath": False,
            "searchInPendingItemContainerKeys": False,
            "filterFields": {
                "num1": [
                    {
                        "FilterOperation": 1,
                        "FilterValue": "111222333",
                        "FilterOperator": "=",
                    }
                ]
            },
        },
        "response": get_search_addresses_bsn_111222333_response(),
    },
    {
        "url": "http://localhost/decosweb/aspx/api/v1/search/books?properties=false",
        "post_body": {
            "bookKey": "hexkey32chars000000000000000BSN2",
            "orderBy": "sequence",
            "skip": 0,
            "take": 50,
            "searchInHierarchyPath": False,
            "searchInPendingItemContainerKeys": False,
            "filterFields": {
                "num1": [
                    {
                        "FilterOperation": 1,
                        "FilterValue": "111222333",
                        "FilterOperator": "=",
                    }
                ]
            },
        },
        "response": get_search_addresses_bsn_111222333_response_2(),
    },
    {
        "url": "http://localhost/decosweb/aspx/api/v1/search/books?properties=false",
        "post_body": {
            "bookKey": "hexkey32chars000000000000000BSN3",
            "orderBy": "sequence",
            "skip": 0,
            "take": 50,
            "searchInHierarchyPath": False,
            "searchInPendingItemContainerKeys": False,
            "filterFields": {
                "num1": [
                    {
                        "FilterOperation": 1,
                        "FilterValue": "111222333",
                        "FilterOperator": "=",
                    }
                ]
            },
        },
        "response": get_search_addresses_bsn_111222333_response_empty(),
    },
    {
        "url": "http://localhost/decosweb/aspx/api/v1/search/books?properties=false",
        "post_body": {
            "bookKey": "hexkey32chars000000000000000BSN4",
            "orderBy": "sequence",
            "skip": 0,
            "take": 50,
            "searchInHierarchyPath": False,
            "searchInPendingItemContainerKeys": False,
            "filterFields": {
                "num1": [
                    {
                        "FilterOperation": 1,
                        "FilterValue": "111222333",
                        "FilterOperator": "=",
                    }
                ]
            },
        },
        "response": None,
        "status_code": 401,
        "reason": "Unauthorized",
    },
)
