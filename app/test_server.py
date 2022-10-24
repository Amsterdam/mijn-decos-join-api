import time
from unittest.mock import patch

from cryptography.fernet import Fernet, InvalidToken

from app.auth import PROFILE_TYPE_COMMERCIAL, PROFILE_TYPE_PRIVATE, FlaskServerTestCase
from app.crypto import encrypt
from app.fixtures.data import get_document_blob
from app.fixtures.response_mock import (
    get_response_mock,
    post_response_mock,
    post_response_mock_unauthorized,
)
from app.server import app

TESTKEY = "z4QXWk3bjwFST2HRRVidnn7Se8VFCaHscK39JfODzNs="


@patch("app.crypto.get_encrytion_key", lambda: TESTKEY)
@patch("app.helpers.get_decosjoin_api_host", lambda: "http://localhost")
@patch(
    "app.helpers.get_decosjoin_adres_boeken",
    lambda: {
        PROFILE_TYPE_PRIVATE: [
            "hexkey32chars000000000000000BSN1",
            "hexkey32chars000000000000000BSN2",
        ],
        PROFILE_TYPE_COMMERCIAL: ["hexkey32chars0000000000000000KVK"],
    },
)
class ApiTests(FlaskServerTestCase):
    app = app

    def expected_zaak(self):
        return {
            "caseType": "TVM - RVV - Object",
            "dateDecision": None,
            "dateEnd": "2020-06-16",
            "dateRequest": "2020-06-08",
            "dateStart": "2020-06-16",
            "dateWorkflowActive": "2020-06-08",
            "decision": None,
            "description": "SB RVV ontheffing hele stad",
            "id": "HEXSTRING12",
            "identifier": "Z/20/2345678.0",
            "kenteken": None,
            "location": None,
            "status": "Ontvangen",
            "timeEnd": None,
            "timeStart": None,
            "title": "Tijdelijke verkeersmaatregel (TVM-RVV-Object)",
        }

    def client_get(self, location):
        return self.get_secure(location)

    def client_get_kvk(self, location):
        return self.get_secure(location, PROFILE_TYPE_COMMERCIAL)

    def test_status(self):
        response = self.client.get("/status/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(), '{"content":"OK","status":"OK"}\n')

    @patch("app.helpers.DecosJoinConnection.get_response", get_response_mock)
    @patch("app.helpers.DecosJoinConnection.post_response", post_response_mock)
    @patch("app.decosjoin_service.PAGE_SIZE", 10)
    def test_getvergunningen(self):
        response = self.client_get("/decosjoin/getvergunningen")

        self.assertEqual(response.status_code, 200, response.data)
        data = response.get_json()

        self.assertEqual(data["status"], "OK")
        self.assertEqual(len(data["content"]), 18)

        # remove the encrypted url, it is time based
        del data["content"][0]["documentsUrl"]

        self.assertEqual(data["content"][0], self.expected_zaak())

    @patch("app.helpers.DecosJoinConnection.get_response", get_response_mock)
    @patch(
        "app.helpers.DecosJoinConnection.post_response",
        post_response_mock_unauthorized,
    )
    @patch("app.decosjoin_service.PAGE_SIZE", 10)
    def test_getvergunningen_unauthorized(self):
        response = self.client_get("/decosjoin/getvergunningen")

        self.assertEqual(response.status_code, 401, response.data)
        data = response.get_json()

        self.assertEqual(data["status"], "ERROR")
        self.assertEqual(data["message"], "Request error occurred")
        self.assertTrue("content" not in data)

    @patch("app.helpers.DecosJoinConnection.get_response", get_response_mock)
    def test_getvergunningen_no_header(self):
        response = self.client.get("/decosjoin/getvergunningen")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json,
            {"message": "Auth error occurred", "status": "ERROR"},
        )

    @patch("app.helpers.DecosJoinConnection.get_response", get_response_mock)
    @patch("app.decosjoin_service.PAGE_SIZE", 10)
    def test_listdocuments(self):
        response = self.client_get(
            f"/decosjoin/listdocuments/{encrypt('ZAAKKEY1', self.TEST_BSN)}"
        )
        data = response.json["content"]
        self.assertEqual(len(data), 2)
        self.assertTrue(data[0]["url"].startswith("/decosjoin/document/"))

    @patch("app.helpers.DecosJoinConnection.get_response", get_response_mock)
    @patch("app.decosjoin_service.PAGE_SIZE", 10)
    def test_listdocuments_kvk(self):
        response = self.client_get_kvk(
            f"/decosjoin/listdocuments/{encrypt('ZAAKKEY2', self.TEST_KVK)}"
        )
        data = response.json["content"]
        self.assertEqual(len(data), 2)
        self.assertTrue(data[0]["url"].startswith("/decosjoin/document/"))

    @patch("app.helpers.DecosJoinConnection.get_response", get_response_mock)
    def test_listdocuments_unencrypted(self):
        response = self.client_get("/decosjoin/listdocuments/ZAAKKEY1")
        self.assertEqual(response.status_code, 500)
        self.assertRaises(InvalidToken)
        self.assertEqual(
            response.json, {"message": "Server error occurred", "status": "ERROR"}
        )

    @patch("app.helpers.DecosJoinConnection.get_response", get_response_mock)
    def test_listdocuments_expired_token(self):
        f = Fernet(TESTKEY)
        value = f"{self.TEST_BSN}:ZAAKKEY1".encode()
        expired_time = int(time.time()) - (60 * 60 + 2)  # one hour + 2 seconds
        encrypted_token = f.encrypt_at_time(value, expired_time)

        response = self.client_get(f"/decosjoin/listdocuments/{encrypted_token}")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json, {"message": "Server error occurred", "status": "ERROR"}
        )

    @patch("app.helpers.DecosJoinConnection.get_response", get_response_mock)
    def test_get_document_blob(self):
        response = self.client_get(
            f"/decosjoin/document/{encrypt('DOCUMENTKEY01', self.TEST_BSN)}",
        )
        self.assertEqual(response.data, get_document_blob())
        self.assertEqual(response.headers["Content-Type"], "application/pdf")

    @patch("app.helpers.DecosJoinConnection.get_response", get_response_mock)
    def test_get_document_unencrypted(self):
        response = self.client_get("/decosjoin/document/DOCUMENTKEY01")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json, {"message": "Server error occurred", "status": "ERROR"}
        )

    @patch("app.helpers.DecosJoinConnection.get_response", get_response_mock)
    @patch("app.helpers.DecosJoinConnection.post_response", post_response_mock)
    @patch("app.decosjoin_service.PAGE_SIZE", 10)
    def test_get_with_openapi(self):
        response = self.client_get("/decosjoin/getvergunningen")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "OK")
