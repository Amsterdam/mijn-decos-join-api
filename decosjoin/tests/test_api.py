import time
from unittest.mock import patch

from cryptography.fernet import Fernet
from tma_saml import FlaskServerTMATestCase
from tma_saml.for_tests.cert_and_key import server_crt

from decosjoin.crypto import encrypt
from decosjoin.server import app
from decosjoin.tests.fixtures.data import get_document
from decosjoin.tests.fixtures.response_mock import get_response_mock, post_response_mock


TESTKEY = "z4QXWk3bjwFST2HRRVidnn7Se8VFCaHscK39JfODzNs="


@patch("decosjoin.server.get_tma_certificate", lambda: server_crt)
@patch("decosjoin.crypto.get_key", lambda: TESTKEY)
@patch("decosjoin.server.get_decosjoin_api_host", lambda: "http://localhost")
@patch("decosjoin.server.get_decosjoin_adres_boeken", lambda: {'bsn': ["hexkey32chars000000000000000BSN1", "hexkey32chars000000000000000BSN2"], 'kvk': ['hexkey32chars0000000000000000KVK']})
class ApiTests(FlaskServerTMATestCase):
    TEST_BSN = "111222333"

    def _expected_zaak(self):
        return {
            'caseType': 'TVM - RVV - Object',
            'dateEndInclusive': '2020-06-16',
            'dateFrom': '2020-06-16',
            'dateRequest': '2020-06-08T00:00:00',
            'identifier': 'Z/20/1234567',
            'isActual': False,
            'kenteken': None,
            'location': None,
            'decision': None,
            'dateDecision': None,
            'status': 'Ontvangen',
            'timeEnd': None,
            'timeStart': None,
            'title': 'SB RVV ontheffing hele stad',
            # 'documents_url': '/api/decos/listdocuments/...'
        }

    def _saml_headers(self):
        return self.add_digi_d_headers(self.TEST_BSN)

    def _client_get(self, location):
        return self.client.get(location, headers=self._saml_headers())

    def setUp(self):
        """ Setup app for testing """
        self.client = self.get_tma_test_app(app)

    def test_status(self):
        response = self.client.get("/status/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"OK")

    @patch("decosjoin.server.DecosJoinConnection._get_response", get_response_mock)
    @patch("decosjoin.server.DecosJoinConnection._post_response", post_response_mock)
    def test_getvergunningen(self):
        response = self._client_get("/decosjoin/getvergunningen")
        self.assertEqual(response.status_code, 200, response.data)
        data = response.get_json()
        self.assertEqual(data["status"], "OK")

        self.assertTrue(data["content"][0]["documents_url"].startswith("/api/decosjoin/listdocument/"))

        # remove the encrypted url, it is time based
        del(data["content"][-1]["documents_url"])

        self.assertEqual(data["content"][-1], self._expected_zaak())

    @patch("decosjoin.server.DecosJoinConnection._get_response", get_response_mock)
    def test_getvergunningen_no_header(self):
        response = self.client.get("/decosjoin/getvergunningen")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'message': 'Missing SAML token', 'status': 'ERROR'})

    @patch("decosjoin.server.DecosJoinConnection._get_response", get_response_mock)
    def test_listdocuments(self):
        response = self._client_get(f"/decosjoin/listdocuments/{encrypt('ZAAKKEY1')}")
        data = response.json['content']
        self.assertEqual(data[0]['fileName'], "Training voorbeelddocument.docx")
        self.assertTrue(data[0]['downloadUrl'].startswith("/api/decosjoin/document/"))

    @patch("decosjoin.server.DecosJoinConnection._get_response", get_response_mock)
    def test_listdocuments_unencrypted(self):
        response = self._client_get("/decosjoin/listdocuments/ZAAKKEY1")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'message': 'decryption zaak ID invalid', 'status': 'ERROR'})

    @patch("decosjoin.server.DecosJoinConnection._get_response", get_response_mock)
    def test_listdocuments_expired_token(self):
        f = Fernet(TESTKEY)
        value = "ZAAKKEY1".encode()
        expired_time = int(time.time()) - (60 * 60 + 2)  # one hour + 2 seconds
        encrypted_token = f.encrypt_at_time(value, expired_time)

        response = self._client_get(f"/decosjoin/listdocuments/{encrypted_token}")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'message': 'decryption zaak ID invalid', 'status': 'ERROR'})

    @patch("decosjoin.server.DecosJoinConnection._get_response", get_response_mock)
    def test_get_document(self):
        response = self.client.get(f"/decosjoin/document/{encrypt('DOCUMENTKEY01')}", headers=self._saml_headers())
        self.assertEqual(response.data, get_document())
        self.assertEqual(response.headers['Content-Type'], 'application/pdf')

    @patch("decosjoin.server.DecosJoinConnection._get_response", get_response_mock)
    def test_get_document_unencrypted(self):
        response = self.client.get("/decosjoin/document/DOCUMENTKEY01", headers=self._saml_headers())
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'message': 'decryption zaak ID invalid', 'status': 'ERROR'})
