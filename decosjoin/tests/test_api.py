from unittest.mock import patch

from tma_saml import FlaskServerTMATestCase
from tma_saml.for_tests.cert_and_key import server_crt

from decosjoin.server import app
from decosjoin.tests.fixtures.response_mock import get_response_mock


@patch("decosjoin.server.get_tma_certificate", lambda: server_crt)
@patch("decosjoin.server.get_decosjoin_api_host", lambda: "http://localhost")
@patch("decosjoin.server.get_decosjoin_adres_boeken", lambda: {'bsn': ["hexkey32chars000000000000000BSN1", "hexkey32chars000000000000000BSN2"], 'kvk': ['hexkey32chars0000000000000000KVK']})
class ApiTests(FlaskServerTMATestCase):
    TEST_BSN = "111222333"

    def _expected(self):
        return {
            'caseType': 'TVM - RVV - Object',
            'dateEndInclusive': '2020-06-16',
            'dateFrom': '2020-06-16',
            'dateRequest': '2020-06-08T00:00:00',
            'identifier': 'Z/20/1234567',
            'isActual': False,
            'kenteken': None,
            'location': None,
            'outcome': None,
            'outcomeDate': None,
            'status': 'Ontvangen',
            'timeEnd': None,
            'timeStart': None,
            'title': 'SB RVV ontheffing hele stad',
        }

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
        self.assertEqual(data["status"], "OK")
        self.assertEqual(data["content"][0], self._expected())

    @patch("decosjoin.server.DecosJoinConnection._get_response", get_response_mock)
    def test_getvergunningen_no_header(self):
        response = self.client.get("/decosjoin/getvergunningen")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'message': 'Missing SAML token', 'status': 'ERROR'})
