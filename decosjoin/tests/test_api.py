from unittest.mock import patch

from tma_saml import FlaskServerTMATestCase
from tma_saml.for_tests.cert_and_key import server_crt

from decosjoin.server import app
from decosjoin.tests.fixtures.response_mock import get_response_mock


@patch("decosjoin.server.get_tma_certificate", lambda: server_crt)
@patch("decosjoin.server.get_decosjoin_api_host", lambda: "http://localhost")
@patch("decosjoin.server.get_decosjoin_adres_boek", lambda: "hexkey32chars0000000000000000000")
class ApiTests(FlaskServerTMATestCase):
    TEST_BSN = "111222333"

    def setUp(self):
        """ Setup app for testing """
        self.client = self.get_tma_test_app(app)

    def test_status(self):
        response = self.client.get("/status/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"OK")

    @patch("decosjoin.server.DecosJoinConnection._get_response", get_response_mock)
    def test_getvergunningen(self):
        SAML_HEADERS = self.add_digi_d_headers(self.TEST_BSN)

        response = self.client.get("/decosjoin/getvergunningen", headers=SAML_HEADERS)
        self.assertEqual(response.status_code, 200, response.data)
        data = response.get_json()
        from pprint import pprint
        pprint(data)
        self.assertEqual(data["status"], "OK")
        self.assertEqual(data["content"][0]["mark"], "Z/17/123456")
        self.assertEqual(data["content"][0]["caseType"], "GPP")
        # TODO: check fields

        # from pprint import pprint
        # pprint(data)

    @patch("decosjoin.server.DecosJoinConnection._get_response", get_response_mock)
    def test_getvergunningen_no_header(self):
        response = self.client.get("/decosjoin/getvergunningen")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'message': 'Missing SAML token', 'status': 'ERROR'})
