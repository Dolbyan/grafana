import unittest
from unittest.mock import patch, MagicMock
from app import app, REQUEST_COUNT, ERROR_RATE, PASS_RATE


class TestCrud(unittest.TestCase):
    """Test case for CRUD operations and metrics endpoints."""
    def setUp(self):
        """Set up test client and reset metrics."""
        self.app = app.test_client()
        self.app.testing = True

        # Access metrics through public getters (if available)
        if hasattr(REQUEST_COUNT, 'get'):
            REQUEST_COUNT.set(0)  # Assuming a public set method exists
            self.reset_metric = REQUEST_COUNT.get
        else:
            self.reset_metric = lambda: setattr(REQUEST_COUNT, '_value', 0)

        if hasattr(ERROR_RATE, 'get'):
            ERROR_RATE.set(0)
            self.get_error_rate = ERROR_RATE.get
        else:
            self.get_error_rate = lambda: getattr(ERROR_RATE, '_value')

        if hasattr(PASS_RATE, 'get'):
            PASS_RATE.set(0)
            self.get_pass_rate = PASS_RATE.get
        else:
            self.get_pass_rate = lambda: getattr(PASS_RATE, '_value')

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
        # mock_db_connection.return_value.cursor.return_value.__enter__.return_value = MagicMock()
        response = self.app.post('/add', json={"item_id": 1, "data": 15})
        self.assertEqual(response.status_code, 201)
        self.assertIn(b'Added', response.data)
        self.assertEqual(self.reset_metric(), 1)
        self.assertEqual(self.get_pass_rate(), 1)


if __name__ == '__main__':
    unittest.main()
