import time
from unittest.mock import patch

from cryptography.fernet import Fernet, InvalidToken
from requests.models import Response
from tma_saml import FlaskServerTMATestCase, UserType
from tma_saml.for_tests.cert_and_key import server_crt

from app.crypto import encrypt
from app.server import app
from tests.fixtures.data import get_document_blob

from tests.fixtures.response_mock import (
    get_response_mock,
    post_response_mock,
    post_response_mock_unauthorized,
)

TESTKEY = "z4QXWk3bjwFST2HRRVidnn7Se8VFCaHscK39JfODzNs="


@patch("app.helpers.get_tma_certificate", lambda: server_crt)
@patch("app.crypto.get_encrytion_key", lambda: TESTKEY)
@patch("app.helpers.get_decosjoin_api_host", lambda: "http://localhost")
@patch(
    "app.helpers.get_decosjoin_adres_boeken",
    lambda: {
        UserType.BURGER: [
            "hexkey32chars000000000000000BSN1",
            "hexkey32chars000000000000000BSN2",
        ],
        UserType.BEDRIJF: ["hexkey32chars0000000000000000KVK"],
    },
)
class ApiTests(FlaskServerTMATestCase):
    TEST_BSN = "111222333"
    TEST_KVK = "90001354"  # test kvk taken from kvk website

    def expected_zaak(self):
        return {
            "id": "HEXSTRING01",
            "caseType": "TVM - RVV - Object",
            "dateEnd": "2021-04-28",
            "dateStart": "2021-04-27",
            "dateRequest": "2021-04-16",
            "dateWorkflowActive": "2021-04-16",
            "identifier": "Z/20/1234567",
            "kenteken": None,
            "location": "Amstel 1 1000AB",
            "decision": None,
            "dateDecision": None,
            "status": "Ontvangen",
            "description": "Test MA MIJN-3031",
            "timeEnd": "16:00",
            "timeStart": "10:00",
            "title": "Tijdelijke verkeersmaatregel (TVM-RVV-Object)",
            # 'documentsUrl': '/api/decos/listdocuments/...'
        }

    def saml_headers(self):
        return self.add_digi_d_headers(self.TEST_BSN)

    def saml_headers_kvk(self):
        return self.add_e_herkenning_headers(self.TEST_KVK)

    def client_get(self, location):
        return self.client.get(location, headers=self.saml_headers())

    def client_get_kvk(self, location):
        return self.client.get(location, headers=self.saml_headers_kvk())

    def setUp(self):
        """Setup app for testing"""
        self.client = self.get_tma_test_app(app)
        self.maxDiff = None

    def test_status(self):
        response = self.client.get("/status/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(), '"OK"')

    @patch("app.helpers.DecosJoinConnection.get_response", get_response_mock)
    @patch("app.helpers.DecosJoinConnection.post_response", post_response_mock)
    @patch("app.decosjoin_service.PAGE_SIZE", 10)
    def test_getvergunningen(self):
        response = self.client_get("/decosjoin/getvergunningen")

        self.assertEqual(response.status_code, 200, response.data)
        data = response.get_json()

        self.assertEqual(data["status"], "OK")
        self.assertEqual(len(data["content"]), 20)

        # remove the encrypted url, it is time based
        del data["content"][-1]["documentsUrl"]

        self.assertEqual(data["content"][-1], self.expected_zaak())

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
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json,
            {"message": "TMA error occurred", "status": "ERROR"},
        )

    @patch("app.helpers.DecosJoinConnection.get_response", get_response_mock)
    @patch("app.decosjoin_service.PAGE_SIZE", 10)
    def test_listdocuments(self):
        response = self.client_get(
            f"/decosjoin/listdocuments/{encrypt('ZAAKKEY1', self.TEST_BSN)}"
        )
        data = response.json["content"]
        self.assertEqual(len(data), 2)
        self.assertTrue(data[0]["url"].startswith("/api/decosjoin/document/"))

    @patch("app.helpers.DecosJoinConnection.get_response", get_response_mock)
    @patch("app.decosjoin_service.PAGE_SIZE", 10)
    def test_listdocuments_kvk(self):
        response = self.client_get_kvk(
            f"/decosjoin/listdocuments/{encrypt('ZAAKKEY2', self.TEST_KVK)}"
        )
        data = response.json["content"]
        self.assertEqual(len(data), 2)
        self.assertTrue(data[0]["url"].startswith("/api/decosjoin/document/"))

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
