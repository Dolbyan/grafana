import unittest
from unittest.mock import patch, MagicMock
from app import app, REQUEST_COUNT, ERROR_RATE, PASS_RATE, REQUEST_LATENCY, REGISTRY

class TestCrud(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

        with app.app_context():
            REQUEST_COUNT._value.set(0)
            ERROR_RATE._value.set(0)
            PASS_RATE._value.set(0)


    def test_latency_endpoint(self):
        response = self.app.get('/latency')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Latency endpoint', response.data)
        self.assertEqual(REQUEST_COUNT._value.get(), 1)


    def test_error_endpoint(self):
        response = self.app.get("/get")
        self.assertEqual(response.status_code, 500)
        self.assertIn(b"Database error occurred", response.data)
        self.assertEqual(REQUEST_COUNT._value.get(), 1)
        self.assertEqual(ERROR_RATE._value.get(), 1)

    def test_timeout_endpoint(self):
        response = self.app.get('/timeout')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'End after 2sec', response.data)
        self.assertEqual(REQUEST_COUNT._value.get(), 1)
        self.assertEqual(PASS_RATE._value.get(), 1)
    def test_timeout5_endpoint(self):
        response = self.app.get('/timeout5')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'End after 5sec', response.data)
        self.assertEqual(REQUEST_COUNT._value.get(), 1)
        self.assertEqual(PASS_RATE._value.get(), 1)

    def test_mstimeout_endpoint(self):
        response = self.app.get('/mstimeout')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'End after 20ms', response.data)
        self.assertEqual(REQUEST_COUNT._value.get(), 1)
        self.assertEqual(PASS_RATE._value.get(), 1)

    def test_metrics_endpoint(self):
        response = self.app.get('/metrics')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'request_latency_seconds_count', response.data)
        self.assertIn(b'request_count_total', response.data)
        self.assertIn(b'error_rate_total', response.data)
        self.assertIn(b'pass_rate_total', response.data)

    @patch("app.db_connection")
    def test_get_endpoint(self, mock_db_connection):

        mock_db_connection.return_value.cursor.return_value.__enter__.return_value.fetchall.return_value = [
            (1, 16)]
        response = self.app.get('/get')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [(1, 16)])
        self.assertEqual(REQUEST_COUNT._value.get(), 1)
        self.assertEqual(PASS_RATE._value.get(), 1)

    @patch("app.db_connection")
    def test_add_endpoint(self, mock_db_connection):

        mock_db_connection.return_value.cursor.return_value.__enter__.return_value = MagicMock()
        response = self.app.post('/add', json={"item_id": 1, "data": 15})
        self.assertEqual(response.status_code, 201)
        self.assertIn(b'Added', response.data)
        self.assertEqual(REQUEST_COUNT._value.get(), 1)
        self.assertEqual(PASS_RATE._value.get(), 1)

if __name__ == '__main__':
    unittest.main()