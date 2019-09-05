import json


def get_bsn_lookup_response():
    return bsn_lookup_response_json


def get_bsn_lookup_response_as_dict():
    return json.loads(get_bsn_lookup_response())


# Copied from a response. But formatted and anonymized
bsn_lookup_response_json = """{
    "content": [
        {
            "fields": {
                "identifier": 123456789.0
            },
            "key": "32charsstringxxxxxxxxxxxxxxxxxxx",
            "links": [
                {
                    "href": "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/32charsstringxxxxxxxxxxxxxxxxxxx",
                    "rel": "self"
                }
            ]
        }
    ],
    "count": 1,
    "links": [
        {
            "href": "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/itemprofiles/another32charsxxxxxxxxxxxxxxxxxx/list",
            "rel": "itemprofile"
        }
    ]
}"""


def get_zaken_response():
    return zaken_response


def get_zaken_response_as_dict():
    return json.loads(get_zaken_response())


# Copied from a response. But formatted and anonymized
zaken_response = """{
    "content": [
        {
            "fields": {
                "documentDate": "2019-01-01T00:00:00",
                "isProcessed": true,
                "mark": "Z/19/123456",
                "subject": "Trambaan ontheffing verleend"
            },
            "key": "zaak1xxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "links": [
                {
                    "href": "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/zaak1xxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    "rel": "self"
                }
            ]
        },
        {
            "fields": {
                "documentDate": "2019-02-01T00:00:00",
                "isProcessed": false,
                "mark": "Z/19/234567",
                "subject": "TBO raamkaart"
            },
            "key": "zaak2xxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "links": [
                {
                    "href": "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/zaak2xxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    "rel": "self"
                }
            ]
        },
        {
            "fields": {
                "documentDate": "2017-04-01T00:00:00",
                "mark": "Z/19/345678",
                "subject": "C123456789-00001"
            },
            "key": "zaak3xxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "links": [
                {
                    "href": "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/zaak3xxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    "rel": "self"
                }
            ]
        },
        {
            "fields": {
                "documentDate": "2019-03-01T00:00:00",
                "isProcessed": false,
                "mark": "Z/19/456789"
            },
            "key": "zaak4xxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "links": [
                {
                    "href": "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/zaak4xxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    "rel": "self"
                }
            ]
        }
    ],
    "count": 4,
    "links": [
        {
            "href": "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/itemprofiles/another32charsxxxxxxxxxxxxxxxxxx/list",
            "rel": "itemprofile"
        }
    ]
}"""
