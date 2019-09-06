from unittest.mock import patch

from tma_saml import FlaskServerTMATestCase
from tma_saml.for_tests.cert_and_key import server_crt

from decosjoin.server import app
from decosjoin.tests.fixtures.data import get_zaken_response_as_dict


class ApiTests(FlaskServerTMATestCase):
    TEST_BSN = '111222333'

    def setUp(self):
        """ Setup app for testing """
        self.client = self.get_tma_test_app(app)

    def test_status(self):
        response = self.client.get('/status/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"OK")

    @patch('decosjoin.server.DecosJoinConnection.get_zaken', autospec=True)
    @patch('decosjoin.server.get_tma_certificate', lambda: server_crt)
    def test_getvergunningen(self, getzaken_mock):
        getzaken_mock.return_value = get_zaken_response_as_dict()

        SAML_HEADERS = self.add_digi_d_headers(self.TEST_BSN)
        response = self.client.get('/decosjoin/getvergunningen', headers=SAML_HEADERS)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], "OK")
        self.assertEqual(data['count'], 4)
        self.assertEqual(data['content'][0]['key'], "zaak1xxxxxxxxxxxxxxxxxxxxxxxxxxx")
        # TODO: check fields

        # from pprint import pprint
        # pprint(data)

    @patch('decosjoin.server.DecosJoinConnection.get_zaken', autospec=True)
    @patch('decosjoin.server.get_tma_certificate', lambda: server_crt)
    def test_getvergunningen_no_header(self, getzaken_mock):
        getzaken_mock.return_value = get_zaken_response_as_dict()

        response = self.client.get('/decosjoin/getvergunningen')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, b'Missing SAML token')
