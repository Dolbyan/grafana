import unittest
from unittest.mock import patch, MagicMock
from app import app, REQUEST_COUNT, ERROR_RATE, PASS_RATE


class TestCrud(unittest.TestCase):
    """Test case for CRUD operations and metrics endpoints."""
    def setUp(self):
        """Set up test client and reset metrics."""
        self.app = app.test_client()
        self.app.testing = True

        self.reset_metric = lambda:REQUEST_COUNT._value.get()
        self.get_error_rate = lambda:ERROR_RATE._value.get()
        self.get_pass_rate = lambda:PASS_RATE._value.get()

    def test_latency_endpoint(self):
        """Test latency endpoint."""
        response = self.app.get('/latency')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Latency endpoint', response.data)
        self.assertEqual(self.reset_metric(), 1)

    def test_error_endpoint(self):
        """Test error endpoint."""
        response = self.app.get("/get")
        self.assertEqual(response.status_code, 500)
        self.assertIn(b"Database error occurred", response.data)
        self.assertEqual(self.reset_metric(), 1)
        self.assertEqual(self.get_error_rate(), 1)

    def test_timeout_endpoint(self):
        """Test timeout endpoint."""
        response = self.app.get('/timeout')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'End after 2sec', response.data)
        self.assertEqual(self.reset_metric(), 1)
        self.assertEqual(self.get_pass_rate(), 1)

    def test_timeout5_endpoint(self):
        """Test timeout5 endpoint."""
        response = self.app.get('/timeout5')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'End after 5sec', response.data)
        self.assertEqual(self.reset_metric(), 1)
        self.assertEqual(self.get_pass_rate(), 1)

    def test_mstimeout_endpoint(self):
        """Test ms timeout endpoint."""
        response = self.app.get('/mstimeout')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'End after 20ms', response.data)
        self.assertEqual(self.reset_metric(), 1)
        self.assertEqual(self.get_pass_rate(), 1)

    def test_metrics_endpoint(self):
        """Test metrics endpoint."""
        response = self.app.get('/metrics')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'request_latency_seconds_count', response.data)
        self.assertIn(b'request_count_total', response.data)
        self.assertIn(b'error_rate_total', response.data)
        self.assertIn(b'pass_rate_total', response.data)

    @patch("app.db_connection")
    def test_get_endpoint(self, mock_db_connection):
        """Test get endpoint with mocked database connection."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(1, 16)]
        mock_db_connection.cursor.return_value.__enter__.return_value = mock_cursor
        response = self.app.get('/get')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [[1, 16]])
        self.assertEqual(self.reset_metric(), 1)
        self.assertEqual(self.get_pass_rate(), 1)

    @patch("app.db_connection")
    def test_add_endpoint(self, mock_db_connection):
        """Test add endpoint with mocked database connection."""
        mock_cursor = MagicMock()
        mock_db_connection.cursor.return_value.__enter__.return_value = mock_cursor
        response = self.app.post('/add', json={"item_id": 1, "data": 15})
        self.assertEqual(response.status_code, 201)
        self.assertIn(b'Added', response.data)
        self.assertEqual(self.reset_metric(), 1)
        self.assertEqual(self.get_pass_rate(), 1)


if __name__ == '__main__':
    unittest.main()
