import concurrent.futures
import math
from pprint import pprint

import requests
from requests import PreparedRequest
from requests.auth import HTTPBasicAuth

from app.auth import PROFILE_TYPE_COMMERCIAL, PROFILE_TYPE_PRIVATE
from app.config import (
    DECOS_API_REQUEST_TIMEOUT,
    get_decosjoin_adres_boeken_bsn,
    get_decosjoin_adres_boeken_kvk,
)
from app.crypto import encrypt
from app.field_parsers import (
    get_fields,
    to_date,
    to_int,
    to_string,
    to_string_or_empty_string,
)
from app.zaaktypes import zaken_index

LOG_RAW = False
PAGE_SIZE = 60

SELECT_FIELDS = ",".join(
    [
        "title",
        "mark",
        "text45",
        "subject1",
        "bol10",
        "company",
        "date1",
        "date2",
        "date5",
        "date6",
        "date7",
        "dfunction",
        "document_date",
        "num3",
        "num6",
        "text6",
        "text7",
        "text8",
        "text9",
        "text10",
        "text11",
        "text12",
        "text13",
        "text14",
        "text15",
        "text17",
        "text18",
        "text20",
        "text25",
        "text49",
        "processed",
        "sequence",
    ]
)


def get_decosjoin_adres_boeken():
    return {
        PROFILE_TYPE_PRIVATE: get_decosjoin_adres_boeken_bsn(),
        PROFILE_TYPE_COMMERCIAL: get_decosjoin_adres_boeken_kvk(),
    }


class DecosJoinConnection:
    def __init__(self, username, password, api_host, adres_boeken=None):
        self.username = username
        self.password = password
        self.adres_boeken = (
            adres_boeken if adres_boeken else get_decosjoin_adres_boeken()
        )
        self.api_host = api_host
        self.api_location = "/decosweb/aspx/api/v1/"
        self.api_url = f"{self.api_host}{self.api_location}"

    def get_response(self, *args, **kwargs):
        """Easy to mock intermediate function."""
        return requests.get(*args, **kwargs)

    def post_response(self, *args, **kwargs):
        """Easy to mock intermediate function."""
        return requests.post(*args, **kwargs)

    def request(self, url, method="get", json=None):
        """Makes a request to the decos join api with HTTP basic auth credentials added."""
        if method == "get":
            response = self.get_response(
                url,
                auth=HTTPBasicAuth(self.username, self.password),
                headers={"Accept": "application/itemdata"},
                timeout=DECOS_API_REQUEST_TIMEOUT,
            )
        elif method == "post":
            response = self.post_response(
                url,
                auth=HTTPBasicAuth(self.username, self.password),
                headers={"Accept": "application/itemdata"},
                json=json,
                timeout=DECOS_API_REQUEST_TIMEOUT,
            )
        else:
            raise RuntimeError("Method needs to be GET or POST")

        if LOG_RAW:
            print("\nstatus", response.status_code, url)
            print("\npost", json)
            print(">>", response.content)

        if response.status_code == 200:
            json = response.json()
            return json
        else:
            response.raise_for_status()

    def get_search_query_json(self, bsn: str, book_key: str):
        return {
            "bookKey": book_key,
            "orderBy": "sequence",
            "skip": 0,
            "take": 50,
            "searchInHierarchyPath": False,
            "searchInPendingItemContainerKeys": False,
            "filterFields": {
                "num1": [
                    {"FilterOperation": 1, "FilterValue": bsn, "FilterOperator": "="}
                ]
            },
        }

    def get_user_keys(self, profile_type, user_identifier):
        """Retrieve the internal ids used for a user."""
        keys = []

        adres_boeken = self.adres_boeken[profile_type]

        def get_key(boek):
            keys = []
            url = f"{self.api_url}search/books?properties=false"

            res_json = self.request(
                url,
                json=self.get_search_query_json(user_identifier, boek),
                method="post",
            )

            if res_json["itemDataResultSet"]["count"] > 0:
                for item in res_json["itemDataResultSet"]["content"]:
                    user_key = item["key"]
                    keys.append(user_key)

            return keys

        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            results = executor.map(
                get_key, adres_boeken, timeout=DECOS_API_REQUEST_TIMEOUT
            )

        for result in results:
            keys.extend(result)

        return keys

    @staticmethod
    def is_list_match(zaak, key, test_list) -> bool:
        value = zaak[key] if key in zaak else None
        if value is None:
            return False
        value = value.lower()
        return value in test_list

    def transform(self, zaken_source, user_identifier):  # noqa: C901
        new_zaken = []
        deferred_zaken = []

        zaken_source_sorted = sorted(
            zaken_source, key=lambda zaak: zaak["fields"]["mark"]
        )

        for zaak_source in zaken_source_sorted:
            source_fields = zaak_source["fields"]

            # Cannot reliably determine the zaaktype of this zaak
            if "text45" not in source_fields:
                continue

            source_fields.update({"id": zaak_source["key"]})

            zaak_type = source_fields["text45"]

            # Zaak is defined
            if zaak_type not in zaken_index:
                continue

            Zaak = zaken_index[zaak_type]
            new_zaak = Zaak(source_fields).result()

            if new_zaak is None:
                continue

            # These matching conditions are used to prevent these items from being included in the returned list of zaken
            if self.is_list_match(
                new_zaak,
                "description",
                ["wacht op online betaling", "wacht op ideal betaling"],
            ):
                continue

            if self.is_list_match(
                new_zaak,
                "decision",
                ["buiten behandeling", "geannuleerd", "geen aanvraag of dubbel"],
            ):
                continue

            if new_zaak["description"] and new_zaak["description"].lower().startswith(
                "*verwijder"
            ):
                continue

            # This url can be used to retrieve matching document attachments for this particular zaak
            new_zaak[
                "documentsUrl"
            ] = f"/decosjoin/listdocuments/{encrypt(zaak_source['key'], user_identifier)}"

            if Zaak.defer_transform:
                deferred_zaken.append([new_zaak, Zaak])
            else:
                new_zaken.append(new_zaak)

        deferred_zaken.sort(key=lambda x: x[0].get("caseType"))

        # In parallel
        # Makes it possible to defer adding the zaak to the zaken response for example to:
        # - Adding dateWorkflowActive by querying other Api's
        def perform_deferred_transform(zaak_tuple):
            [deferred_zaak, Zaak_cls] = zaak_tuple
            return Zaak_cls.defer_transform(
                zaak_deferred=deferred_zaak,
                decosjoin_service=self,
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            results = executor.map(
                perform_deferred_transform,
                deferred_zaken,
                timeout=DECOS_API_REQUEST_TIMEOUT,
            )

        for result in results:
            new_zaken.append(result)

        return new_zaken

    def get_page(self, url, offset=None):
        """Get a single page for url. When offset is provided add that to the url."""
        if offset:
            url += f"&skip={offset}"
        res_json = self.request(url)
        if LOG_RAW:
            from pprint import pprint

            print("request:", url)
            pprint(res_json)
        return res_json

    def get_all_pages(self, url):
        """Get 'content' from all pages for the provided url"""

        req = PreparedRequest()
        req.prepare_url(url, {"top": PAGE_SIZE})  # append top get param
        url = req.url

        items = []
        # fetch one page to get the first part of the data and item count
        res = self.get_page(url)

        end = math.ceil(res["count"] / PAGE_SIZE) * PAGE_SIZE
        items.extend(res["content"])

        for offset in range(PAGE_SIZE, end, PAGE_SIZE):
            res = self.get_page(url, offset)
            items.extend(res["content"])

        return items

    def get_zaken(self, profile_type, user_identifier):
        zaken_source = []
        user_keys = self.get_user_keys(profile_type, user_identifier)

        def fetch_zaken(key):
            url = f"{self.api_url}items/{key}/folders?select={SELECT_FIELDS}"
            zaken = self.get_all_pages(url)
            return zaken

        # execute in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            results = executor.map(
                fetch_zaken, user_keys, timeout=DECOS_API_REQUEST_TIMEOUT
            )

        for result in results:
            zaken_source.extend(result)

        zaken = self.transform(zaken_source, user_identifier)
        return zaken

    def get_document_data(self, document_id: str):
        res_json = self.request(f"{self.api_url}items/{document_id}/blob?select=bol10")

        content = res_json["content"]
        if content:
            for i in content[::-1]:
                is_pdf = i["fields"].get("bol10", False)
                if is_pdf:
                    return {"is_pdf": is_pdf, "doc_key": i["key"]}
        return {
            "is_pdf": False,
        }

    def get_documents(self, zaak_id, identifier):
        url = f"{self.api_url}items/{zaak_id}/documents?select=subject1,sequence,mark,text39,text40,text41,itemtype_key"

        res = self.get_all_pages(url)

        if LOG_RAW:
            print("Documents list")
            pprint(res)

        parse_fields = [
            {"name": "title", "from": "text41", "parser": to_string_or_empty_string},
            {"name": "id", "from": "mark", "parser": to_string},
            {"name": "sequence", "from": "sequence", "parser": to_int},
            {"name": "text39", "from": "text39", "parser": to_string_or_empty_string},
            {"name": "text40", "from": "text40", "parser": to_string_or_empty_string},
            {"name": "text41", "from": "text41", "parser": to_string_or_empty_string},
        ]

        new_docs = []

        for item in res:
            document_source = item["fields"]
            if document_source["itemtype_key"].lower() == "document":
                document_meta_data = get_fields(parse_fields, document_source)

                if (
                    document_meta_data["text39"].lower() == "definitief"
                    and document_meta_data["text40"].lower()
                    in ["openbaar", "beperkt openbaar"]
                    and document_meta_data["text41"].lower() != "nvt"
                ):
                    doc_data = self.get_document_data(item["key"])

                    if doc_data["is_pdf"]:
                        document_meta_data[
                            "url"
                        ] = f"/decosjoin/document/{encrypt(doc_data['doc_key'], identifier)}"

                        del document_meta_data["text39"]
                        del document_meta_data["text40"]
                        del document_meta_data["text41"]

                        new_docs.append(document_meta_data)

        new_docs.sort(key=lambda x: x["sequence"])

        for doc in new_docs:
            del doc["sequence"]

        return new_docs

    def get_document_blob(self, document_id):
        url_blob_content = f"{self.api_url}items/{document_id}/content"

        document_response = self.get_response(
            url_blob_content,
            auth=HTTPBasicAuth(self.username, self.password),
            headers={"Accept": "application/octet-stream"},
        )

        if LOG_RAW:
            pprint(document_response.content)
            pprint(document_response.headers)

        return {
            "Content-Type": document_response.headers["Content-Type"],
            "file_data": document_response.content,
        }

    def get_workflow(self, zaak_id: str, step_title: str):
        all_workflows_response = self.request(
            f"{self.api_url}items/{zaak_id}/workflows"
        )

        if all_workflows_response and all_workflows_response["count"] > 0:
            # Take last workflow key

            if LOG_RAW:
                print("\n\nAll workflows")
                pprint(all_workflows_response)
                print("====\n\n")

            worflow_key = all_workflows_response["content"][-1]["key"]
            single_workflow_url = f"{self.api_url}items/{worflow_key}/workflowlinkinstances?properties=false&fetchParents=false&oDataQuery.select=mark,date1,date2,text7,sequence&oDataQuery.orderBy=sequence"
            single_workflow_response = self.request(single_workflow_url)

            if not single_workflow_response["content"]:
                return None

            date_in_behandeling = None

            for workflow_step in single_workflow_response["content"]:
                if (
                    "text7" in workflow_step["fields"]
                    and workflow_step["fields"]["text7"] == step_title
                ):
                    date_in_behandeling = to_date(workflow_step["fields"]["date1"])

            return date_in_behandeling

        return None
