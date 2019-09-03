from flask_testing import TestCase

from decosjoin.server import app


class ApiTests(TestCase):
    def create_app(self):
        return app

    def test_status(self):
        response = self.client.get('/status/health')
        self.assert200(response)
        self.assertEqual(response.data, b"OK")

    def test_getvergunningen(self):
        response = self.client.get('/decosjoin/getvergunningen')
        data = response.get_json()
        self.assertEqual(data['status'], "OK")
